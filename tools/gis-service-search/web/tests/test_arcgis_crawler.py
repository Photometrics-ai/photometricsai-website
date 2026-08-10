"""Tests for ArcGIS REST catalog crawling and classification."""

import http.server
import json
import threading
import urllib.parse

import pytest

import arcgis_client
import arcgis_crawler


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
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setattr(arcgis_client.ssrf_guard, "is_safe_host", lambda hostname: True)
    httpd.handler_cls = handler_cls
    yield httpd
    httpd.shutdown()
    httpd.server_close()


def _root_url(server, path="/arcgis/rest/services"):
    return f"http://127.0.0.1:{server.server_address[1]}{path}"


def _route(path):
    return f"{path}?f=json"


def _service_route(*segments):
    quoted = [urllib.parse.quote(str(segment), safe="") for segment in segments]
    return _route("/arcgis/rest/services/" + "/".join(quoted))


def test_tokenize_lowercases_and_splits_whitespace():
    assert arcgis_crawler.tokenize("  Road   CENTERLINE\nLayer  ") == ["road", "centerline", "layer"]


@pytest.mark.parametrize(
    ("match_mode", "query", "expected"),
    [
        ("any", "road parcels", True),
        ("any", "zoning parcels", False),
        ("all", "street center", True),
        ("all", "street parcel", False),
        ("phrase", "Main Street", True),
        ("phrase", "Street Main", False),
    ],
)
def test_matches_document_for_all_match_modes(match_mode, query, expected):
    doc = {
        "title": "Layer: Main Street Centerline",
        "description": "Road network and transportation features",
    }

    assert arcgis_crawler.matches_document(doc, arcgis_crawler.tokenize(query), query, match_mode) is expected


def test_search_documents_returns_frontend_shape_for_matches():
    documents = [
        {
            "title": "Layer: Centerline (ID: 4)",
            "url": "https://example.test/FeatureServer/4",
            "kind": "layer",
            "description": "Road centerlines",
        },
        {
            "title": "MapServer: Parcels",
            "url": "https://example.test/MapServer",
            "kind": "service",
            "description": "Property boundaries",
        },
    ]

    assert arcgis_crawler.search_documents(documents, "centerline", "any") == [
        {
            "title": "Layer: Centerline (ID: 4)",
            "link": "https://example.test/FeatureServer/4",
            "snippet": "Road centerlines",
        }
    ]


def test_discover_tree_collects_services_and_layers(server):
    server.handler_cls.routes[_route("/arcgis/rest/services")] = {
        "body": {
            "folders": ["Transportation", "Empty"],
            "services": [{"name": "Root Service", "type": "MapServer"}],
        }
    }
    server.handler_cls.routes[_route("/arcgis/rest/services/Transportation")] = {
        "body": {
            "services": [
                {"name": "Road Centerline", "type": "FeatureServer"},
                {"name": "Parcels", "type": "MapServer"},
            ]
        }
    }
    server.handler_cls.routes[_route("/arcgis/rest/services/Empty")] = {"body": {"services": []}}
    server.handler_cls.routes[_service_route("Root Service", "MapServer")] = {
        "body": {
            "serviceDescription": "Root map service",
            "layers": [{"id": 0, "name": "Root layer", "description": "Root layer description"}],
        }
    }
    server.handler_cls.routes[_service_route("Transportation", "Road Centerline", "FeatureServer")] = {
        "body": {
            "description": "Transportation centerline service",
            "layers": [
                {"id": 0, "name": "Roads", "description": "All roads"},
                {"id": 4, "name": "Centerline", "description": "Road centerlines"},
                {"id": 7, "name": "Intersections", "description": "Street intersections"},
            ],
        }
    }
    server.handler_cls.routes[_service_route("Transportation", "Parcels", "MapServer")] = {
        "body": {
            "description": "Parcel service",
            "layers": [
                {"id": 1, "name": "Lots", "description": "Lot boundaries"},
                {"id": 2, "name": "Addresses", "description": "Address points"},
            ],
        }
    }

    result = arcgis_crawler.discover_tree(_root_url(server), budget_seconds=10, per_host_concurrency=2)

    assert result.terminal_error is None
    assert result.truncated is False
    assert result.services_scanned == 3
    assert result.services_total == 3
    assert len(result.documents) == 9
    assert {
        "title": "FeatureServer: Transportation/Road Centerline",
        "url": f"{_root_url(server)}/Transportation/Road%20Centerline/FeatureServer",
        "kind": "service",
        "description": "Transportation centerline service",
    } in result.documents
    assert {
        "title": "Layer: Centerline (ID: 4)",
        "url": f"{_root_url(server)}/Transportation/Road%20Centerline/FeatureServer/4",
        "kind": "layer",
        "description": "Road centerlines",
    } in result.documents


def test_discover_tree_handles_explicit_json_null_for_folders_and_layers(server):
    # Real-world case (tiles.arcgis.com): some ArcGIS servers return an
    # explicit JSON null for "folders"/"layers" rather than omitting the key
    # or using [] -- dict.get(key, []) does NOT substitute the default for a
    # present-but-null key, only a missing one, so this used to crash with
    # TypeError: 'NoneType' object is not subscriptable.
    server.handler_cls.routes[_route("/arcgis/rest/services")] = {
        "body": {
            "folders": None,
            "services": [{"name": "Aerial", "type": "MapServer"}],
        }
    }
    server.handler_cls.routes[_service_route("Aerial", "MapServer")] = {
        "body": {"description": "Aerial imagery", "layers": None}
    }

    result = arcgis_crawler.discover_tree(_root_url(server), budget_seconds=10)

    assert result.terminal_error is None
    assert result.services_scanned == 1
    assert result.services_total == 1
    assert result.documents == [
        {
            "title": "MapServer: Aerial",
            "url": f"{_root_url(server)}/Aerial/MapServer",
            "kind": "service",
            "description": "Aerial imagery",
        }
    ]


def test_discover_tree_truncates_before_dispatching_next_batch(server):
    server.handler_cls.routes[_route("/arcgis/rest/services")] = {
        "body": {
            "folders": [],
            "services": [{"name": f"Service {index}", "type": "MapServer"} for index in range(20)],
        }
    }

    result = arcgis_crawler.discover_tree(_root_url(server), budget_seconds=0, per_host_concurrency=4)

    assert result.truncated is True
    assert result.services_total == 20
    assert result.services_scanned < result.services_total


@pytest.mark.parametrize(
    ("terminal_error", "truncated", "documents", "matches", "state", "reason_code", "expected_total"),
    [
        ("tls_error", False, [], 0, "try_google", "tls_error", 0),
        ("unreachable", False, [], 0, "try_google", "unreachable", 0),
        ("directory_forbidden", False, [], 0, "try_google", "directory_forbidden", 0),
        ("non_json", False, [], 0, "try_google", "waf_or_nonjson", 0),
        ("token_required", False, [], 0, "contact_admin", "token_required", 0),
        ("malformed_root", False, [], 0, "check_url", "malformed_root", 0),
        ("self_throttled", False, [{"title": "Layer: Roads", "url": "u", "description": "roads"}], 1, "partial", "self_throttled", 1),
        ("self_throttled", False, [], 0, "try_google", "self_throttled", 0),
        (None, True, [{"title": "Layer: Roads", "url": "u", "description": "roads"}], 1, "partial", "time_budget", 1),
        (None, False, [{"title": "Layer: Roads", "url": "u", "description": "roads"}], 1, "success", None, 1),
        (None, False, [{"title": "Layer: Roads", "url": "u", "description": "roads"}], 0, "success_empty", None, 0),
    ],
)
def test_crawl_and_classify_covers_classification_table(
    monkeypatch,
    terminal_error,
    truncated,
    documents,
    matches,
    state,
    reason_code,
    expected_total,
):
    def fake_discover_tree(source_url, budget_seconds):
        return arcgis_crawler.DiscoveryResult(
            documents=documents,
            services_scanned=3,
            services_total=5,
            truncated=truncated,
            terminal_error=terminal_error,
        )

    monkeypatch.setattr(arcgis_crawler, "discover_tree", fake_discover_tree)
    query = "roads" if matches else "not-present"

    result = arcgis_crawler.crawl_and_classify("https://example.test/arcgis/rest/services", query, "any", 45)

    assert result["state"] == state
    assert result["reasonCode"] == reason_code
    assert result["message"] == arcgis_crawler.MESSAGES.get(reason_code)
    assert result["totalResults"] == expected_total
    assert len(result["results"]) == expected_total
    assert result["servicesScanned"] == 3
    assert result["servicesTotal"] == 5
    assert result["truncated"] is truncated
    assert result["retrying"] is False
    assert isinstance(result["elapsedSeconds"], float)


@pytest.mark.parametrize(
    ("route_spec", "terminal_error"),
    [
        ({"status": 403, "body": {"error": "forbidden"}}, "directory_forbidden"),
        ({"status": 200, "raw_body": "<html>challenge</html>"}, "non_json"),
        ({"status": 200, "body": {"error": {"code": 499, "message": "Token Required"}}}, "token_required"),
        ({"status": 200, "body": {"error": {"code": 123, "message": "Some ArcGIS error"}}}, "unreachable"),
        ({"status": 200, "body": {"currentVersion": 11.2}}, "malformed_root"),
    ],
)
def test_discover_tree_root_terminal_error_paths(server, route_spec, terminal_error):
    server.handler_cls.routes[_route("/arcgis/rest/services")] = route_spec

    result = arcgis_crawler.discover_tree(_root_url(server), budget_seconds=10)

    assert result.terminal_error == terminal_error
    assert result.documents == []
    assert result.services_scanned == 0
    assert result.services_total == 0
    assert result.truncated is False


def test_self_throttle_heuristic_returns_partial_when_some_documents_collected(server, monkeypatch):
    _disable_retry_sleep(monkeypatch)
    server.handler_cls.routes[_route("/arcgis/rest/services")] = {
        "body": {
            "folders": [],
            "services": [
                {"name": "Good", "type": "MapServer"},
                {"name": "Busy 1", "type": "MapServer"},
                {"name": "Busy 2", "type": "MapServer"},
                {"name": "Busy 3", "type": "MapServer"},
            ],
        }
    }
    server.handler_cls.routes[_service_route("Good", "MapServer")] = {
        "body": {"description": "Good service", "layers": [{"id": 1, "name": "Roads"}]}
    }
    for name in ("Busy 1", "Busy 2", "Busy 3"):
        server.handler_cls.routes[_service_route(name, "MapServer")] = {"status": 429, "body": {"error": "busy"}}

    result = arcgis_crawler.crawl_and_classify(_root_url(server), "roads", "any", 10)

    assert result["state"] == "partial"
    assert result["reasonCode"] == "self_throttled"
    assert result["results"]
    assert result["servicesScanned"] == 4
    assert result["servicesTotal"] == 4


def test_self_throttle_heuristic_returns_try_google_when_no_documents_collected(server, monkeypatch):
    _disable_retry_sleep(monkeypatch)
    server.handler_cls.routes[_route("/arcgis/rest/services")] = {
        "body": {
            "folders": [],
            "services": [
                {"name": "Busy 1", "type": "MapServer"},
                {"name": "Busy 2", "type": "MapServer"},
                {"name": "Busy 3", "type": "MapServer"},
            ],
        }
    }
    for name in ("Busy 1", "Busy 2", "Busy 3"):
        server.handler_cls.routes[_service_route(name, "MapServer")] = {"status": 503, "body": {"error": "busy"}}

    result = arcgis_crawler.crawl_and_classify(_root_url(server), "roads", "any", 10)

    assert result["state"] == "try_google"
    assert result["reasonCode"] == "self_throttled"
    assert result["results"] == []
    assert result["totalResults"] == 0
    assert result["servicesScanned"] == 3
    assert result["servicesTotal"] == 3


def test_discover_tree_passes_folder_name_and_type_to_build_url_separately(monkeypatch):
    calls = []

    def fake_build_url(base, *segments, query="f=json"):
        calls.append((base, segments, query))
        return "https://example.test/" + "/".join(segments) + ("?f=json" if query else "")

    def fake_fetch_json(url, timeout=8.0, max_retries=2):
        if url == "https://example.test/?f=json":
            return arcgis_client.FetchResult(
                status_code=200,
                json_body={
                    "folders": ["Transportation"],
                    "services": [],
                },
                raw_text="{}",
                error_type="ok",
            )
        if url == "https://example.test/Transportation?f=json":
            return arcgis_client.FetchResult(
                status_code=200,
                json_body={
                    "services": [
                        {"name": "Aggregation of fq jobs (2,3,4 blks)", "type": "FeatureServer"}
                    ]
                },
                raw_text="{}",
                error_type="ok",
            )
        return arcgis_client.FetchResult(status_code=200, json_body={"layers": []}, raw_text="{}", error_type="ok")

    monkeypatch.setattr(arcgis_crawler.arcgis_client, "build_url", fake_build_url)
    monkeypatch.setattr(arcgis_crawler.arcgis_client, "fetch_json", fake_fetch_json)

    result = arcgis_crawler.discover_tree("https://example.test", budget_seconds=10)

    assert result.services_scanned == 1
    assert (
        "https://example.test",
        ("Transportation", "Aggregation of fq jobs (2,3,4 blks)", "FeatureServer"),
        "f=json",
    ) in calls


def _disable_retry_sleep(monkeypatch):
    monkeypatch.setattr(arcgis_client.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(arcgis_client.random, "uniform", lambda low, high: 0.0)
