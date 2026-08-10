import json

from conftest import load_handler


def _load(monkeypatch, full_budget="240"):
    monkeypatch.setenv("DATA_BUCKET", "test-bucket")
    monkeypatch.setenv("STATE_MACHINE_ARN", "arn:aws:states:us-east-2:123:stateMachine:test")
    monkeypatch.setenv("FULL_BUDGET_SECONDS", full_budget)
    return load_handler("retry_source_api")


def _event(body_dict, ip="203.0.113.5"):
    return {
        "requestContext": {"identity": {"sourceIp": ip}},
        "body": json.dumps(body_dict),
    }


def _doc(state="partial"):
    return {
        "jobId": "a" * 32,
        "query": "sidewalk",
        "matchMode": "any",
        "createdAt": 100,
        "sourceResults": [
            {
                "source": "https://x.gov/arcgis/rest/services",
                "state": state,
                "totalResults": 1,
                "retrying": False,
            }
        ],
    }


class _FakeSfn:
    def __init__(self):
        self.calls = []

    def start_execution(self, **kwargs):
        self.calls.append(kwargs)
        return {"executionArn": "arn:execution"}


def test_missing_job_id_and_source_are_rejected(monkeypatch):
    handler = _load(monkeypatch)
    assert handler.lambda_handler(_event({"source": "https://x.gov/arcgis/rest/services"}), None)["statusCode"] == 400
    assert handler.lambda_handler(_event({"jobId": "a" * 32}), None)["statusCode"] == 400


def test_malformed_job_id_is_rejected(monkeypatch):
    handler = _load(monkeypatch)
    response = handler.lambda_handler(_event({"jobId": "../bad", "source": "https://x.gov"}), None)
    assert response["statusCode"] == 400


def test_source_not_in_job_is_rejected(monkeypatch):
    handler = _load(monkeypatch)
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: True)
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: _doc())

    response = handler.lambda_handler(_event({"jobId": "a" * 32, "source": "https://other.gov"}), None)

    assert response["statusCode"] == 400
    assert "not part" in json.loads(response["body"])["error"]


def test_non_partial_source_is_rejected(monkeypatch):
    handler = _load(monkeypatch)
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: True)
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: _doc(state="success"))

    response = handler.lambda_handler(_event({"jobId": "a" * 32, "source": "https://x.gov/arcgis/rest/services"}), None)

    assert response["statusCode"] == 400
    assert "partial" in json.loads(response["body"])["error"]


def test_rate_limit_returns_429(monkeypatch):
    handler = _load(monkeypatch)
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: False)

    response = handler.lambda_handler(_event({"jobId": "a" * 32, "source": "https://x.gov"}), None)

    assert response["statusCode"] == 429


def test_missing_job_returns_404(monkeypatch):
    handler = _load(monkeypatch)
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: True)
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: None)

    response = handler.lambda_handler(_event({"jobId": "a" * 32, "source": "https://x.gov"}), None)

    assert response["statusCode"] == 404


def test_success_marks_retrying_and_starts_full_execution(monkeypatch):
    handler = _load(monkeypatch, full_budget="99")
    doc = _doc()
    writes = []
    fake_sfn = _FakeSfn()
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: True)
    monkeypatch.setattr(handler.job_store, "read_job", lambda bucket, job_id: doc)
    monkeypatch.setattr(handler.job_store, "write_job", lambda bucket, job_id, patched_doc: writes.append(patched_doc))
    monkeypatch.setattr(handler, "_client", fake_sfn)

    response = handler.lambda_handler(
        _event({"jobId": "a" * 32, "source": "https://X.gov/arcgis/rest/services/"}),
        None,
    )

    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload == {
        "jobId": "a" * 32,
        "source": "https://x.gov/arcgis/rest/services",
        "status": "retrying",
    }
    assert writes[0]["sourceResults"][0]["retrying"] is True

    call = fake_sfn.calls[0]
    assert call["name"].startswith(f"{'a' * 32}-retry-")
    assert call["name"] != "a" * 32
    execution_input = json.loads(call["input"])
    assert execution_input["mode"] == "full"
    assert execution_input["budgetSeconds"] == 99
    assert execution_input["sources"] == ["https://x.gov/arcgis/rest/services"]
    assert execution_input["invalidSources"] == []
