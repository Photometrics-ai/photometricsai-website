"""URL trim/validate/normalize for submitted GIS source URLs.

Used to clean up visitor-submitted ArcGIS service-root URLs before crawling
them. This is input hygiene (reject junk, reject credentials, dedupe), not the
SSRF boundary; direct outbound-request protection lives in ssrf_guard.py and is
called at crawl time.
Runs server-side regardless of what the browser already validated.
"""

from urllib.parse import urlsplit, urlunsplit

ALLOWED_SCHEMES = ("http", "https")
DEFAULT_PORTS = {"http": 80, "https": 443}


def normalize_source_url(raw_url):
    """Return a normalized URL string, or raise ValueError with a human-readable reason."""
    if not isinstance(raw_url, str):
        raise ValueError("URL must be a string")

    trimmed = raw_url.strip()
    if not trimmed:
        raise ValueError("URL is empty")

    try:
        parsed = urlsplit(trimmed)
    except ValueError as exc:
        raise ValueError(f"malformed URL: {exc}") from exc

    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"unsupported scheme '{parsed.scheme or '(none)'}' -- only http/https are allowed")

    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URLs with embedded credentials are not allowed")

    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f"malformed host or port: {exc}") from exc

    if not hostname:
        raise ValueError("URL is missing a hostname")

    hostname = hostname.lower()

    netloc = hostname
    if port is not None and port != DEFAULT_PORTS.get(scheme):
        netloc = f"{hostname}:{port}"

    path = parsed.path or ""
    if path in ("", "/"):
        path = ""
    else:
        path = path.rstrip("/")

    normalized = urlunsplit((scheme, netloc, path, "", ""))
    return normalized


def dedupe_urls(raw_urls):
    """Normalize a list of raw URL strings, dropping duplicates (first occurrence wins).

    Returns (valid_urls, invalid_entries) where invalid_entries is a list of
    {"raw": ..., "reason": ...} dicts for lines that failed to normalize.
    """
    seen = set()
    valid_urls = []
    invalid_entries = []

    for raw in raw_urls:
        raw_stripped = raw.strip() if isinstance(raw, str) else raw
        if not raw_stripped:
            continue
        try:
            normalized = normalize_source_url(raw_stripped)
        except ValueError as exc:
            invalid_entries.append({"raw": raw_stripped, "reason": str(exc)})
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        valid_urls.append(normalized)

    return valid_urls, invalid_entries
