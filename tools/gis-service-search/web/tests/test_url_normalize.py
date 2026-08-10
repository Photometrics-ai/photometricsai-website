import pytest

from url_normalize import dedupe_urls, normalize_source_url


def test_trims_whitespace():
    assert normalize_source_url("  https://example.gov/arcgis/rest/services  ") == "https://example.gov/arcgis/rest/services"


def test_strips_trailing_slash_but_keeps_meaning():
    assert normalize_source_url("https://example.gov/arcgis/rest/services/") == "https://example.gov/arcgis/rest/services"


def test_root_path_stays_root():
    assert normalize_source_url("https://example.gov") == "https://example.gov"
    assert normalize_source_url("https://example.gov/") == "https://example.gov"


def test_lowercases_scheme_and_host_but_not_path():
    assert normalize_source_url("HTTPS://Example.GOV/ArcGIS/rest/Services") == "https://example.gov/ArcGIS/rest/Services"


def test_preserves_non_default_port():
    assert normalize_source_url("https://example.gov:8443/arcgis/rest/services") == "https://example.gov:8443/arcgis/rest/services"


def test_drops_default_port():
    assert normalize_source_url("https://example.gov:443/arcgis/rest/services") == "https://example.gov/arcgis/rest/services"
    assert normalize_source_url("http://example.gov:80/arcgis/rest/services") == "http://example.gov/arcgis/rest/services"


def test_strips_query_string():
    assert (
        normalize_source_url("https://example.gov/arcgis/rest/services?f=pjson&token=abc")
        == "https://example.gov/arcgis/rest/services"
    )


def test_different_ports_are_distinct():
    a = normalize_source_url("https://example.gov:8443/arcgis/rest/services")
    b = normalize_source_url("https://example.gov:9443/arcgis/rest/services")
    assert a != b


def test_different_protocols_are_distinct():
    a = normalize_source_url("http://example.gov/arcgis/rest/services")
    b = normalize_source_url("https://example.gov/arcgis/rest/services")
    assert a != b


@pytest.mark.parametrize("scheme", ["ftp", "file", "javascript", "data", "gopher"])
def test_rejects_unsupported_schemes(scheme):
    with pytest.raises(ValueError, match="unsupported scheme"):
        normalize_source_url(f"{scheme}://example.gov/arcgis/rest/services")


def test_rejects_credentials_in_url():
    with pytest.raises(ValueError, match="credentials"):
        normalize_source_url("https://user:pass@example.gov/arcgis/rest/services")


def test_rejects_missing_hostname():
    with pytest.raises(ValueError):
        normalize_source_url("https:///arcgis/rest/services")


def test_rejects_empty_string():
    with pytest.raises(ValueError, match="empty"):
        normalize_source_url("   ")


def test_rejects_non_string():
    with pytest.raises(ValueError):
        normalize_source_url(None)


def test_dedupe_collapses_equivalent_urls():
    valid, invalid = dedupe_urls(
        [
            "https://example.gov/arcgis/rest/services",
            "https://example.gov/arcgis/rest/services/",
            "  https://example.gov/arcgis/rest/services  ",
            "HTTPS://EXAMPLE.GOV/arcgis/rest/services",
        ]
    )
    assert valid == ["https://example.gov/arcgis/rest/services"]
    assert invalid == []


def test_dedupe_keeps_first_occurrence_order():
    valid, _ = dedupe_urls(
        [
            "https://b.example.gov/arcgis/rest/services",
            "https://a.example.gov/arcgis/rest/services",
            "https://b.example.gov/arcgis/rest/services",
        ]
    )
    assert valid == [
        "https://b.example.gov/arcgis/rest/services",
        "https://a.example.gov/arcgis/rest/services",
    ]


def test_dedupe_reports_invalid_entries_without_dropping_valid_ones():
    valid, invalid = dedupe_urls(
        [
            "https://example.gov/arcgis/rest/services",
            "ftp://bad.example.gov/",
            "",
            "   ",
        ]
    )
    assert valid == ["https://example.gov/arcgis/rest/services"]
    assert len(invalid) == 1
    assert invalid[0]["raw"] == "ftp://bad.example.gov/"
