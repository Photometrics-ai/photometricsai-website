import json

from conftest import load_handler


def _load(monkeypatch):
    monkeypatch.setenv("DATA_BUCKET", "test-bucket")
    return load_handler("status_api")


def test_found_job_returns_stored_doc(monkeypatch):
    handler = _load(monkeypatch)
    doc = {"jobId": "a" * 32, "status": "complete", "sourceResults": []}
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: doc)

    response = handler.lambda_handler({"queryStringParameters": {"jobId": "a" * 32}}, None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == doc


def test_missing_job_returns_404(monkeypatch):
    handler = _load(monkeypatch)
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: None)

    response = handler.lambda_handler({"queryStringParameters": {"jobId": "a" * 32}}, None)

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {"error": "Job not found"}


def test_missing_job_id_returns_400(monkeypatch):
    handler = _load(monkeypatch)
    response = handler.lambda_handler({"queryStringParameters": {}}, None)
    assert response["statusCode"] == 400


def test_malformed_job_id_returns_400_before_s3_read(monkeypatch):
    handler = _load(monkeypatch)
    calls = []
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: calls.append((bucket, job_id)))

    response = handler.lambda_handler({"queryStringParameters": {"jobId": "../bad"}}, None)

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"error": "invalid jobId"}
    assert calls == []
