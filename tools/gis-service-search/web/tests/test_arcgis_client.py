"""HTTP-level tests for the shared ArcGIS client."""

import datetime
import http.server
import ipaddress
import json
import socket
import ssl
import threading
import urllib.error

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import AuthorityInformationAccessOID, NameOID

import arcgis_client


class _Handler(http.server.BaseHTTPRequestHandler):
    routes = {}
    request_counts = {}

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        type(self).request_counts[self.path] = type(self).request_counts.get(self.path, 0) + 1
        spec = self.routes.get(self.path)
        if callable(spec):
            spec = spec(self)
        if spec is None:
            spec = {"status": 404, "body": {"error": "not found"}}

        status = spec.get("status", 200)
        self.send_response(status)
        for name, value in spec.get("headers", {}).items():
            self.send_header(name, value)

        raw_body = spec.get("raw_body")
        if raw_body is None:
            raw_body = json.dumps(spec.get("body", {}))
            content_type = "application/json"
        else:
            content_type = spec.get("content_type", "text/plain")

        body_bytes = raw_body.encode("utf-8")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        if body_bytes:
            self.wfile.write(body_bytes)


@pytest.fixture
def server(monkeypatch):
    handler_cls = type("Handler", (_Handler,), {"routes": {}, "request_counts": {}})
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setattr(arcgis_client.ssrf_guard, "is_safe_host", lambda hostname: True)
    httpd.handler_cls = handler_cls
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def _url(server, path):
    return f"http://127.0.0.1:{server.server_address[1]}{path}"


def test_get_ssl_context_uses_certifi_bundle():
    assert isinstance(arcgis_client.get_ssl_context(), ssl.SSLContext)


def test_build_url_percent_encodes_each_segment():
    url = arcgis_client.build_url(
        "https://example.gov/arcgis/rest/services/",
        "Aggregation of fq jobs (2,3,4 blks)",
        "FeatureServer",
    )
    assert (
        url
        == "https://example.gov/arcgis/rest/services/Aggregation%20of%20fq%20jobs%20%282%2C3%2C4%20blks%29/FeatureServer?f=json"
    )


def test_fetch_json_rejects_initial_private_host_without_connecting():
    result = arcgis_client.fetch_json("http://127.0.0.1:1/arcgis/rest/services")
    assert result.error_type == "unreachable"
    assert result.status_code is None
    assert result.raw_text == ""


def test_fetch_json_success(server):
    server.handler_cls.routes["/ok"] = {"status": 200, "body": {"currentVersion": 11.2}}
    result = arcgis_client.fetch_json(_url(server, "/ok"))
    assert result.error_type == "ok"
    assert result.status_code == 200
    assert result.json_body == {"currentVersion": 11.2}


def test_fetch_json_non_json_200(server):
    server.handler_cls.routes["/waf"] = {"status": 200, "raw_body": "<html>challenge</html>"}
    result = arcgis_client.fetch_json(_url(server, "/waf"))
    assert result.error_type == "non_json"
    assert result.status_code == 200
    assert result.json_body is None
    assert "challenge" in result.raw_text


def test_fetch_json_http_error_parses_json_body(server):
    server.handler_cls.routes["/forbidden"] = {"status": 403, "body": {"error": {"message": "Forbidden"}}}
    result = arcgis_client.fetch_json(_url(server, "/forbidden"))
    assert result.error_type == "http_error"
    assert result.status_code == 403
    assert result.json_body == {"error": {"message": "Forbidden"}}


@pytest.mark.parametrize("status_code", [429, 503])
def test_fetch_json_retries_then_self_throttled(server, monkeypatch, status_code):
    sleeps = []
    monkeypatch.setattr(arcgis_client.time, "sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr(arcgis_client.random, "uniform", lambda low, high: 0.0)
    server.handler_cls.routes["/busy"] = {"status": status_code, "body": {"error": "busy"}}

    result = arcgis_client.fetch_json(_url(server, "/busy"), max_retries=2)

    assert result.error_type == "self_throttled"
    assert result.status_code == status_code
    assert server.handler_cls.request_counts["/busy"] == 3
    assert sleeps == [0.5, 1.5]


def test_fetch_json_follows_valid_redirect_chain(server):
    server.handler_cls.routes["/start"] = {"status": 302, "headers": {"Location": "/middle"}, "raw_body": ""}
    server.handler_cls.routes["/middle"] = {"status": 302, "headers": {"Location": "/final"}, "raw_body": ""}
    server.handler_cls.routes["/final"] = {"status": 200, "body": {"ok": True}}

    result = arcgis_client.fetch_json(_url(server, "/start"))

    assert result.error_type == "ok"
    assert result.json_body == {"ok": True}


def test_fetch_json_redirect_cap_returns_unreachable(server):
    server.handler_cls.routes["/r0"] = {"status": 302, "headers": {"Location": "/r1"}, "raw_body": ""}
    server.handler_cls.routes["/r1"] = {"status": 302, "headers": {"Location": "/r2"}, "raw_body": ""}
    server.handler_cls.routes["/r2"] = {"status": 302, "headers": {"Location": "/r3"}, "raw_body": ""}
    server.handler_cls.routes["/r3"] = {"status": 302, "headers": {"Location": "/r4"}, "raw_body": ""}
    server.handler_cls.routes["/r4"] = {"status": 200, "body": {"ok": True}}

    result = arcgis_client.fetch_json(_url(server, "/r0"))

    assert result.error_type == "unreachable"
    assert "/r4" not in server.handler_cls.request_counts


def test_fetch_json_rejects_private_redirect_target(server, monkeypatch):
    checked_hosts = []

    def fake_is_safe_host(hostname):
        checked_hosts.append(hostname)
        return hostname == "127.0.0.1"

    monkeypatch.setattr(arcgis_client.ssrf_guard, "is_safe_host", fake_is_safe_host)
    server.handler_cls.routes["/redirect-private"] = {
        "status": 302,
        "headers": {"Location": "http://blocked.example/internal"},
        "raw_body": "",
    }

    result = arcgis_client.fetch_json(_url(server, "/redirect-private"))

    assert result.error_type == "unreachable"
    assert "blocked.example" in checked_hosts


class _FailingOpener:
    def __init__(self, exc):
        self.exc = exc

    def open(self, request, timeout):
        raise self.exc


@pytest.mark.parametrize(
    ("exc", "error_type"),
    [
        (ssl.SSLCertVerificationError("certificate verify failed"), "tls_error"),
        (urllib.error.URLError("connection refused"), "connection_error"),
        (TimeoutError("timed out"), "timeout"),
    ],
)
def test_fetch_json_network_exception_paths(monkeypatch, exc, error_type):
    monkeypatch.setattr(arcgis_client.ssrf_guard, "is_safe_host", lambda hostname: True)
    monkeypatch.setattr(arcgis_client.urllib.request, "build_opener", lambda *handlers: _FailingOpener(exc))

    result = arcgis_client.fetch_json("http://public.example/arcgis/rest/services")

    assert result.error_type == error_type
    assert result.status_code is None


# --- Incomplete TLS chain recovery (Authority Information Access chasing) ---
#
# Real-world trigger: some servers (commonly small/municipal government
# sites) send a leaf certificate without the intermediate CA certificate
# that links it to a trusted root -- browsers silently recover by fetching
# the missing intermediate from the CA's own well-known "Authority
# Information Access" distribution point. These tests build a real, from-
# scratch 2-tier certificate hierarchy (a self-signed "intermediate" acting
# as its own trust anchor, and a leaf signed by it) and a REAL local HTTPS
# server presenting ONLY the leaf -- genuinely reproducing the misconfigured-
# chain scenario end to end, rather than mocking the TLS layer away.


def _generate_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _self_signed_ca_cert(key, common_name):
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )


def _leaf_cert(leaf_key, issuer_key, issuer_cert, hostname, aia_url):
    now = datetime.datetime.now(datetime.timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)]))
        .issuer_name(issuer_cert.subject)
        .public_key(leaf_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(hostname))]),
            critical=False,
        )
        .add_extension(
            x509.AuthorityInformationAccess(
                [x509.AccessDescription(AuthorityInformationAccessOID.CA_ISSUERS, x509.UniformResourceIdentifier(aia_url))]
            ),
            critical=False,
        )
        .sign(issuer_key, hashes.SHA256())
    )


def _pem(cert):
    return cert.public_bytes(serialization.Encoding.PEM)


def _der(cert):
    return cert.public_bytes(serialization.Encoding.DER)


class _DerHandler(http.server.BaseHTTPRequestHandler):
    """Minimal raw-bytes HTTP server standing in for a CA's AIA distribution point."""

    der_bytes = b""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/pkix-cert")
        self.send_header("Content-Length", str(len(self.der_bytes)))
        self.end_headers()
        self.wfile.write(self.der_bytes)


@pytest.fixture
def aia_server():
    handler_cls = type("DerHandler", (_DerHandler,), {"der_bytes": b""})
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler_cls)
    httpd.handler_cls = handler_cls
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def broken_chain_https_server(aia_server):
    """A real local HTTPS server presenting ONLY a leaf certificate signed by
    a self-signed test "intermediate" -- the intermediate is never sent by
    this server, only made available via the AIA URL, exactly like a real
    misconfigured server.
    """
    intermediate_key = _generate_key()
    intermediate_cert = _self_signed_ca_cert(intermediate_key, "Test Intermediate CA")
    aia_server.handler_cls.der_bytes = _der(intermediate_cert)
    aia_url = f"http://127.0.0.1:{aia_server.server_address[1]}/intermediate.crt"

    leaf_key = _generate_key()
    leaf_cert = _leaf_cert(leaf_key, intermediate_key, intermediate_cert, "127.0.0.1", aia_url)

    server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    import tempfile, os

    tmpdir = tempfile.mkdtemp()
    cert_path = os.path.join(tmpdir, "leaf.pem")
    key_path = os.path.join(tmpdir, "leaf.key.pem")
    with open(cert_path, "wb") as fh:
        fh.write(_pem(leaf_cert))
    with open(key_path, "wb") as fh:
        fh.write(leaf_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    server_ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)  # leaf ONLY -- no intermediate sent

    handler_cls = type("Handler", (_Handler,), {"routes": {}, "request_counts": {}})
    httpd = http.server.HTTPServer(("127.0.0.1", 0), handler_cls)
    httpd.socket = server_ctx.wrap_socket(httpd.socket, server_side=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    httpd.handler_cls = handler_cls
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def test_fetch_json_recovers_from_incomplete_chain_via_aia(broken_chain_https_server, monkeypatch):
    monkeypatch.setattr(arcgis_client.ssrf_guard, "is_safe_host", lambda hostname: True)
    arcgis_client._recovered_ssl_contexts.clear()
    broken_chain_https_server.handler_cls.routes["/arcgis/rest/services"] = {
        "status": 200,
        "body": {"folders": [], "services": []},
    }
    url = f"https://127.0.0.1:{broken_chain_https_server.server_address[1]}/arcgis/rest/services"

    result = arcgis_client.fetch_json(url)

    assert result.error_type == "ok"
    assert result.json_body == {"folders": [], "services": []}


def test_fetch_json_reuses_cached_recovered_context_on_subsequent_calls(broken_chain_https_server, monkeypatch):
    monkeypatch.setattr(arcgis_client.ssrf_guard, "is_safe_host", lambda hostname: True)
    arcgis_client._recovered_ssl_contexts.clear()
    broken_chain_https_server.handler_cls.routes["/one"] = {"status": 200, "body": {"n": 1}}
    broken_chain_https_server.handler_cls.routes["/two"] = {"status": 200, "body": {"n": 2}}
    base = f"https://127.0.0.1:{broken_chain_https_server.server_address[1]}"

    build_calls = []
    original_build = arcgis_client._build_recovered_context

    def counting_build(hostname, port, timeout):
        build_calls.append(hostname)
        return original_build(hostname, port, timeout)

    monkeypatch.setattr(arcgis_client, "_build_recovered_context", counting_build)

    first = arcgis_client.fetch_json(f"{base}/one")
    second = arcgis_client.fetch_json(f"{base}/two")

    assert first.error_type == "ok" and first.json_body == {"n": 1}
    assert second.error_type == "ok" and second.json_body == {"n": 2}
    assert len(build_calls) == 1  # second call reused the cached recovered context


def test_is_incomplete_chain_error_matches_by_verify_code_or_message():
    exc_by_code = ssl.SSLCertVerificationError("some message")
    exc_by_code.verify_code = 20
    assert arcgis_client._is_incomplete_chain_error(exc_by_code) is True

    exc_by_message = ssl.SSLCertVerificationError("unable to get local issuer certificate")
    assert arcgis_client._is_incomplete_chain_error(exc_by_message) is True

    unrelated = ssl.SSLCertVerificationError("hostname mismatch")
    unrelated.verify_code = 62  # X509_V_ERR_HOSTNAME_MISMATCH, unrelated to chain completeness
    assert arcgis_client._is_incomplete_chain_error(unrelated) is False


def test_recover_from_incomplete_chain_returns_none_for_unrelated_ssl_errors(monkeypatch):
    monkeypatch.setattr(arcgis_client, "_get_or_build_recovered_context", lambda *a, **k: pytest.fail("should not attempt recovery"))
    unrelated = ssl.SSLCertVerificationError("hostname mismatch")
    unrelated.verify_code = 62

    result = arcgis_client._recover_from_incomplete_chain("https://example.gov/x", 8.0, unrelated)

    assert result is None


def test_get_or_build_recovered_context_caches_failed_recovery(monkeypatch):
    arcgis_client._recovered_ssl_contexts.clear()
    calls = []

    def failing_build(hostname, port, timeout):
        calls.append(hostname)
        return None

    monkeypatch.setattr(arcgis_client, "_build_recovered_context", failing_build)

    first = arcgis_client._get_or_build_recovered_context("broken.example", 443, 8.0)
    second = arcgis_client._get_or_build_recovered_context("broken.example", 443, 8.0)

    assert first is None and second is None
    assert calls == ["broken.example"]  # second call did not re-attempt the AIA dance
