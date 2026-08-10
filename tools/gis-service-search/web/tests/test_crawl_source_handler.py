from conftest import load_handler


def test_crawl_source_unpacks_event_and_passes_result_through(monkeypatch):
    handler = load_handler("crawl_source")
    expected = {
        "source": "https://x.gov/arcgis/rest/services",
        "state": "success",
        "reasonCode": None,
        "message": None,
        "results": [{"title": "Sidewalks"}],
        "totalResults": 1,
        "servicesScanned": 3,
        "servicesTotal": 3,
        "truncated": False,
        "retrying": False,
        "elapsedSeconds": 1.2,
    }
    calls = []

    def fake_crawl(source, query, match_mode, budget_seconds):
        calls.append((source, query, match_mode, budget_seconds))
        return expected

    monkeypatch.setattr(handler.arcgis_crawler, "crawl_and_classify", fake_crawl)

    result = handler.lambda_handler(
        {
            "jobId": "a" * 32,
            "source": "https://x.gov/arcgis/rest/services",
            "query": "sidewalk",
            "matchMode": "all",
            "budgetSeconds": 45,
        },
        None,
    )

    assert calls == [("https://x.gov/arcgis/rest/services", "sidewalk", "all", 45)]
    assert result == expected
