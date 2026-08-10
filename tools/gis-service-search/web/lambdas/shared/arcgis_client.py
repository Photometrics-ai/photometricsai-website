"""Low-level HTTP fetch helpers for ArcGIS REST endpoints."""

from dataclasses import dataclass
import json
import random
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

import certifi
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import AuthorityInformationAccessOID

import ssrf_guard

ERROR_TYPES = (
    "ok",
    "tls_error",
    "connection_error",
    "timeout",
    "http_error",
    "non_json",
    "self_throttled",
    "unreachable",
)
RETRYABLE_STATUSES = (429, 503)
MAX_REDIRECTS = 3

# Some servers (commonly small/municipal government sites) send an incomplete
# TLS chain -- a valid leaf certificate, but missing the intermediate CA cert
# that links it to a trusted root. Browsers silently recover from this by
# fetching the missing intermediate from the CA's own well-known distribution
# point (its "Authority Information Access" / AIA extension) and caching it.
# Python's ssl module does not do this. _recover_from_incomplete_chain below
# reproduces that browser behavior -- it does NOT weaken validation: the
# recovered chain must still validate up to a certifi-trusted root, it just
# assembles the chain the server failed to send.
_INCOMPLETE_CHAIN_VERIFY_CODES = {20}  # X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY
_INCOMPLETE_CHAIN_MESSAGE_MARKERS = (
    "unable to get local issuer certificate",
    "unable to get issuer certificate",
)
_recovered_ssl_contexts = {}  # hostname -> ssl.SSLContext | None (None = already tried, failed)


@dataclass
class FetchResult:
    status_code: int | None
    json_body: dict | None
    raw_text: str
    error_type: str


def get_ssl_context() -> ssl.SSLContext:
    """Return an SSL context backed by certifi's CA bundle."""
    return ssl.create_default_context(cafile=certifi.where())


def build_url(base, *segments, query="f=json") -> str:
    """Build an ArcGIS REST URL, percent-encoding each path segment."""
    url = str(base).rstrip("/")
    encoded_segments = [urllib.parse.quote(str(segment), safe="") for segment in segments]
    if encoded_segments:
        url = f"{url}/{'/'.join(encoded_segments)}"
    if query:
        url = f"{url}?{query}"
    return url


def fetch_json(url, timeout=8.0, max_retries=2) -> FetchResult:
    """Fetch a URL and parse its JSON body without raising expected network errors."""
    if not _is_url_safe(url):
        return FetchResult(status_code=None, json_body=None, raw_text="", error_type="unreachable")

    attempts = max_retries + 1
    last_status = None
    last_body = ""

    # If we already recovered an incomplete chain for this host on an earlier
    # call within this process, use it immediately -- avoids repeating a
    # doomed-to-fail default-context handshake on every single request to a
    # host that can crawl into the hundreds of requests per source.
    parsed_url = urllib.parse.urlsplit(url)
    known_context = _recovered_ssl_contexts.get(parsed_url.hostname) if parsed_url.scheme == "https" else None

    for attempt in range(attempts):
        try:
            status_code, raw_text = _open_and_read(url, timeout, ssl_context=known_context)
        except _UnsafeRedirectError:
            return FetchResult(status_code=None, json_body=None, raw_text="", error_type="unreachable")
        except ssl.SSLCertVerificationError as exc:
            recovered = _recover_from_incomplete_chain(url, timeout, exc)
            if recovered is None:
                return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="tls_error")
            status_code, raw_text = recovered
        except ssl.SSLError as exc:
            return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="tls_error")
        except TimeoutError as exc:
            return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="timeout")
        except socket.timeout as exc:
            return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="timeout")
        except urllib.error.HTTPError as exc:
            status_code = exc.code
            raw_text = _read_error_body(exc)
            if status_code not in RETRYABLE_STATUSES:
                return FetchResult(
                    status_code=status_code,
                    json_body=_parse_json_or_none(raw_text),
                    raw_text=raw_text,
                    error_type="http_error",
                )
        except urllib.error.URLError as exc:
            # urllib wraps handshake-time SSL failures (including cert
            # verification errors) as URLError(reason=<the ssl error>), not
            # as a bare ssl.SSLError -- this is the path incomplete-chain
            # recovery actually needs to hook, not the bare-SSLError except
            # clause above (kept for defense in depth / directly-injected cases).
            if isinstance(exc.reason, ssl.SSLCertVerificationError):
                recovered = _recover_from_incomplete_chain(url, timeout, exc.reason)
                if recovered is None:
                    return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="tls_error")
                status_code, raw_text = recovered
            elif _is_tls_error(exc.reason):
                return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="tls_error")
            elif isinstance(exc.reason, (TimeoutError, socket.timeout)):
                return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="timeout")
            else:
                return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="connection_error")
        except OSError as exc:
            return FetchResult(status_code=None, json_body=None, raw_text=str(exc), error_type="connection_error")

        last_status = status_code
        last_body = raw_text
        if status_code in RETRYABLE_STATUSES:
            if attempt < max_retries:
                _sleep_before_retry(attempt)
                continue
            return FetchResult(
                status_code=last_status,
                json_body=_parse_json_or_none(last_body),
                raw_text=last_body,
                error_type="self_throttled",
            )

        if not 200 <= status_code <= 299:
            return FetchResult(
                status_code=status_code,
                json_body=_parse_json_or_none(raw_text),
                raw_text=raw_text,
                error_type="http_error",
            )

        json_body = _parse_json_or_none(raw_text)
        if json_body is None:
            return FetchResult(status_code=status_code, json_body=None, raw_text=raw_text, error_type="non_json")
        return FetchResult(status_code=status_code, json_body=json_body, raw_text=raw_text, error_type="ok")

    return FetchResult(
        status_code=last_status,
        json_body=_parse_json_or_none(last_body),
        raw_text=last_body,
        error_type="self_throttled",
    )


class _UnsafeRedirectError(Exception):
    """Raised internally when a redirect target is not safe to fetch."""


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise _UnsafeRedirectError()

        absolute_url = urllib.parse.urljoin(req.full_url, newurl)
        if not _is_url_safe(absolute_url):
            raise _UnsafeRedirectError()

        return super().redirect_request(req, fp, code, msg, headers, absolute_url)


def _is_url_safe(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    try:
        hostname = parsed.hostname
    except ValueError:
        return False

    return bool(hostname and ssrf_guard.is_safe_host(hostname))


def _open_and_read(url: str, timeout: float, ssl_context: ssl.SSLContext | None = None) -> tuple[int, str]:
    handlers = [_SafeRedirectHandler()]
    if urllib.parse.urlsplit(url).scheme == "https":
        handlers.append(urllib.request.HTTPSHandler(context=ssl_context or get_ssl_context()))
    opener = urllib.request.build_opener(*handlers)

    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with opener.open(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        status_code = getattr(response, "status", response.getcode())
    return status_code, body


def _is_incomplete_chain_error(exc: ssl.SSLCertVerificationError) -> bool:
    if getattr(exc, "verify_code", None) in _INCOMPLETE_CHAIN_VERIFY_CODES:
        return True
    message = str(exc).lower()
    return any(marker in message for marker in _INCOMPLETE_CHAIN_MESSAGE_MARKERS)


def _fetch_leaf_certificate_der(hostname: str, port: int, timeout: float) -> bytes:
    unverified_context = ssl._create_unverified_context()
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with unverified_context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
            return tls_sock.getpeercert(binary_form=True)


def _authority_issuer_urls(der_bytes: bytes) -> list[str]:
    cert = x509.load_der_x509_certificate(der_bytes)
    try:
        aia = cert.extensions.get_extension_for_class(x509.AuthorityInformationAccess)
    except x509.ExtensionNotFound:
        return []
    return [
        desc.access_location.value
        for desc in aia.value
        if desc.access_method == AuthorityInformationAccessOID.CA_ISSUERS
    ]


def _fetch_intermediate_cert_pem(url: str, timeout: float) -> str | None:
    # The AIA "CA Issuers" URL is set by the issuing CA on its own certificate
    # (not attacker-controlled via a submitted GIS source URL), but this still
    # runs the same SSRF/redirect-safety checks as any other outbound fetch.
    if not _is_url_safe(url):
        return None
    handlers = [_SafeRedirectHandler()]
    if urllib.parse.urlsplit(url).scheme == "https":
        handlers.append(urllib.request.HTTPSHandler(context=get_ssl_context()))
    opener = urllib.request.build_opener(*handlers)
    with opener.open(url, timeout=timeout) as response:
        data = response.read()
    try:
        cert = x509.load_der_x509_certificate(data)
    except ValueError:
        cert = x509.load_pem_x509_certificate(data)
    return cert.public_bytes(serialization.Encoding.PEM).decode("ascii")


def _build_recovered_context(hostname: str, port: int, timeout: float) -> ssl.SSLContext | None:
    try:
        leaf_der = _fetch_leaf_certificate_der(hostname, port, timeout)
        issuer_urls = _authority_issuer_urls(leaf_der)
    except Exception:  # noqa: BLE001 -- any failure here just means recovery isn't possible
        return None

    for issuer_url in issuer_urls:
        try:
            intermediate_pem = _fetch_intermediate_cert_pem(issuer_url, timeout)
            if not intermediate_pem:
                continue
            context = get_ssl_context()
            context.load_verify_locations(cadata=intermediate_pem)
        except Exception:  # noqa: BLE001 -- try the next AIA URL, if any
            continue
        return context

    return None


def _get_or_build_recovered_context(hostname: str, port: int, timeout: float) -> ssl.SSLContext | None:
    if hostname not in _recovered_ssl_contexts:
        _recovered_ssl_contexts[hostname] = _build_recovered_context(hostname, port, timeout)
    return _recovered_ssl_contexts[hostname]


def _recover_from_incomplete_chain(url: str, timeout: float, exc: ssl.SSLCertVerificationError):
    """Return (status_code, raw_text) if the incomplete chain was recovered
    and the retried request succeeded, or None if recovery isn't applicable
    or didn't work -- callers should fall back to a normal tls_error.
    """
    if not _is_incomplete_chain_error(exc):
        return None

    parsed = urllib.parse.urlsplit(url)
    hostname = parsed.hostname
    if not hostname:
        return None
    port = parsed.port or 443

    context = _get_or_build_recovered_context(hostname, port, timeout)
    if context is None:
        return None

    try:
        return _open_and_read(url, timeout, ssl_context=context)
    except Exception:  # noqa: BLE001 -- recovery attempt failed, fall back to tls_error
        return None


def _read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001 -- body extraction failure should not mask HTTP status
        return ""


def _parse_json_or_none(raw_text: str) -> dict | None:
    try:
        parsed = json.loads(raw_text)
    except (TypeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _sleep_before_retry(attempt: int) -> None:
    base_delay = 0.5 if attempt == 0 else 1.5
    time.sleep(base_delay + random.uniform(0, 0.3))


def _is_tls_error(reason) -> bool:
    return isinstance(reason, ssl.SSLError)
