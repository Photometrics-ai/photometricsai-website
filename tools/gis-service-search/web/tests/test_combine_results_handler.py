from conftest import load_handler


def _source_result(source, state="success", total_results=1, retrying=False):
    return {
        "source": source,
        "state": state,
        "reasonCode": None,
        "message": None,
        "results": [{}] * total_results,
        "totalResults": total_results,
        "servicesScanned": 1,
        "servicesTotal": 1,
        "truncated": False,
        "retrying": retrying,
        "elapsedSeconds": 0.1,
    }


def test_initial_mode_builds_and_writes_complete_doc(monkeypatch):
    handler = load_handler("combine_results")
    writes = []
    source_results = [_source_result("https://a.gov", total_results=2), _source_result("https://b.gov", total_results=3)]
    monkeypatch.setattr(handler.time, "time", lambda: 200)
    monkeypatch.setattr(handler.job_store, "write_job", lambda bucket, job_id, doc: writes.append((bucket, job_id, doc)))

    result = handler.lambda_handler(
        {
            "jobId": "a" * 32,
            "bucket": "test-bucket",
            "query": "sidewalk",
            "matchMode": "any",
            "sources": ["https://a.gov", "https://b.gov"],
            "invalidSources": ["bad"],
            "createdAt": 100,
            "mode": "initial",
            "budgetSeconds": 45,
            "sourceResults": source_results,
        },
        None,
    )

    assert result == {"jobId": "a" * 32, "status": "complete", "totalResults": 5}
    bucket, job_id, doc = writes[0]
    assert bucket == "test-bucket"
    assert job_id == "a" * 32
    assert doc["status"] == "complete"
    assert doc["query"] == "sidewalk"
    assert doc["matchMode"] == "any"
    assert doc["sources"] == ["https://a.gov", "https://b.gov"]
    assert doc["invalidSources"] == ["bad"]
    assert doc["createdAt"] == 100
    assert doc["updatedAt"] == 200
    assert doc["sourceResults"] == source_results
    assert doc["totalResults"] == 5
    assert doc["error"] is None


def test_full_mode_replaces_matching_source_and_recomputes_total(monkeypatch):
    handler = load_handler("combine_results")
    existing = {
        "jobId": "a" * 32,
        "status": "complete",
        "sourceResults": [
            _source_result("https://a.gov", total_results=1),
            _source_result("https://b.gov", state="partial", total_results=2, retrying=True),
        ],
        "totalResults": 3,
        "error": None,
    }
    fresh = _source_result("https://b.gov", total_results=5)
    writes = []
    monkeypatch.setattr(handler.time, "time", lambda: 300)
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: existing)
    monkeypatch.setattr(handler.job_store, "write_job", lambda bucket, job_id, doc: writes.append(doc.copy()))

    result = handler.lambda_handler(
        {
            "jobId": "a" * 32,
            "bucket": "test-bucket",
            "query": "sidewalk",
            "matchMode": "any",
            "sources": ["https://b.gov"],
            "mode": "full",
            "budgetSeconds": 240,
            "sourceResults": [fresh],
        },
        None,
    )

    assert result == {"jobId": "a" * 32, "status": "complete", "totalResults": 6}
    written = writes[0]
    assert written["sourceResults"][0]["source"] == "https://a.gov"
    assert written["sourceResults"][1] == fresh
    assert written["totalResults"] == 6
    assert written["updatedAt"] == 300
    assert written["status"] == "complete"


def test_full_mode_missing_existing_doc_does_not_raise(monkeypatch):
    handler = load_handler("combine_results")
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: None)

    result = handler.lambda_handler(
        {"jobId": "a" * 32, "bucket": "test-bucket", "mode": "full", "sourceResults": [_source_result("https://a.gov")]},
        None,
    )

    assert result == {"jobId": "a" * 32, "status": "missing"}


def test_error_mode_writes_generic_error_onto_existing_doc(monkeypatch):
    handler = load_handler("combine_results")
    existing = {"jobId": "a" * 32, "status": "processing", "query": "sidewalk", "sourceResults": []}
    writes = []
    monkeypatch.setattr(handler.time, "time", lambda: 400)
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: existing)
    monkeypatch.setattr(handler.job_store, "write_job", lambda bucket, job_id, doc: writes.append(doc.copy()))

    result = handler.lambda_handler(
        {
            "mode": "error",
            "jobId": "a" * 32,
            "bucket": "test-bucket",
            "error": {"Error": "States.TaskFailed", "Cause": "internal stack trace"},
        },
        None,
    )

    assert result == {"jobId": "a" * 32, "status": "error"}
    assert writes[0]["status"] == "error"
    assert writes[0]["error"] == handler.GENERIC_ERROR_MESSAGE
    assert "internal stack trace" not in writes[0]["error"]
    assert writes[0]["query"] == "sidewalk"
    assert writes[0]["updatedAt"] == 400


def test_error_mode_missing_existing_doc_does_not_raise(monkeypatch):
    handler = load_handler("combine_results")
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: None)
    result = handler.lambda_handler({"mode": "error", "jobId": "a" * 32, "bucket": "test-bucket", "error": "boom"}, None)
    assert result == {"jobId": "a" * 32, "status": "missing"}


def test_error_mode_write_failure_does_not_raise(monkeypatch):
    handler = load_handler("combine_results")
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: {"jobId": job_id})

    def fail_write(bucket, job_id, doc):
        raise RuntimeError("write failed")

    monkeypatch.setattr(handler.job_store, "write_job", fail_write)
    result = handler.lambda_handler({"mode": "error", "jobId": "a" * 32, "bucket": "test-bucket", "error": "boom"}, None)
    assert result == {"jobId": "a" * 32, "status": "error"}
