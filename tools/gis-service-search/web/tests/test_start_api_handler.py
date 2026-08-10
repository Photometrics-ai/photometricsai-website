import json
import re

from conftest import load_handler


def _load(monkeypatch, initial_budget="45"):
    monkeypatch.setenv("DATA_BUCKET", "test-bucket")
    monkeypatch.setenv("STATE_MACHINE_ARN", "arn:aws:states:us-east-2:123:stateMachine:test")
    monkeypatch.setenv("INITIAL_BUDGET_SECONDS", initial_budget)
    return load_handler("start_api")


def _event(body_dict, ip="203.0.113.5"):
    return {
        "requestContext": {"identity": {"sourceIp": ip}},
        "body": json.dumps(body_dict),
    }


class _FakeSfn:
    def __init__(self):
        self.calls = []

    def start_execution(self, **kwargs):
        self.calls.append(kwargs)
        return {"executionArn": "arn:execution"}


def test_success_writes_job_and_starts_initial_execution(monkeypatch):
    handler = _load(monkeypatch, initial_budget="12")
    writes = []
    fake_sfn = _FakeSfn()
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: True)
    monkeypatch.setattr(handler.job_store, "write_job", lambda bucket, job_id, doc: writes.append((bucket, job_id, doc)))
    monkeypatch.setattr(handler, "_client", fake_sfn)

    response = handler.lambda_handler(
        _event(
            {
                "query": "  sidewalk  ",
                "matchMode": "phrase",
                "sources": ["https://X.gov/arcgis/rest/services/", "ftp://bad"],
            }
        ),
        None,
    )

    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert re.match(r"^[0-9a-f]{32}$", payload["jobId"])
    assert payload["status"] == "processing"

    bucket, job_id, doc = writes[0]
    assert bucket == "test-bucket"
    assert job_id == payload["jobId"]
    assert doc["status"] == "processing"
    assert doc["query"] == "sidewalk"
    assert doc["matchMode"] == "phrase"
    assert doc["sources"] == ["https://x.gov/arcgis/rest/services"]
    assert doc["invalidSources"] == ["ftp://bad"]
    assert doc["sourceResults"] == []
    assert doc["totalResults"] == 0
    assert doc["error"] is None
    assert doc["createdAt"] == doc["updatedAt"]

    call = fake_sfn.calls[0]
    assert call["stateMachineArn"] == "arn:aws:states:us-east-2:123:stateMachine:test"
    assert call["name"] == job_id
    execution_input = json.loads(call["input"])
    assert execution_input["jobId"] == job_id
    assert execution_input["bucket"] == "test-bucket"
    assert execution_input["mode"] == "initial"
    assert execution_input["budgetSeconds"] == 12
    assert execution_input["sources"] == ["https://x.gov/arcgis/rest/services"]
    assert execution_input["invalidSources"] == ["ftp://bad"]


def test_missing_query_is_rejected(monkeypatch):
    handler = _load(monkeypatch)
    response = handler.lambda_handler(_event({"sources": ["https://x.gov/arcgis/rest/services"]}), None)
    assert response["statusCode"] == 400


def test_zero_valid_sources_is_rejected(monkeypatch):
    handler = _load(monkeypatch)
    response = handler.lambda_handler(_event({"query": "sidewalk", "sources": ["ftp://bad"]}), None)
    assert response["statusCode"] == 400


def test_invalid_match_mode_falls_back_to_any(monkeypatch):
    handler = _load(monkeypatch)
    writes = []
    fake_sfn = _FakeSfn()
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: True)
    monkeypatch.setattr(handler.job_store, "write_job", lambda bucket, job_id, doc: writes.append(doc))
    monkeypatch.setattr(handler, "_client", fake_sfn)

    response = handler.lambda_handler(
        _event({"query": "sidewalk", "matchMode": "bad", "sources": ["https://x.gov/arcgis/rest/services"]}),
        None,
    )

    assert response["statusCode"] == 200
    assert writes[0]["matchMode"] == "any"
    assert json.loads(fake_sfn.calls[0]["input"])["matchMode"] == "any"


def test_rate_limit_returns_429(monkeypatch):
    handler = _load(monkeypatch)
    monkeypatch.setattr(handler.rate_limit, "check_and_increment", lambda ip: False)

    response = handler.lambda_handler(
        _event({"query": "sidewalk", "sources": ["https://x.gov/arcgis/rest/services"]}),
        None,
    )

    assert response["statusCode"] == 429
    assert "rate limit" in json.loads(response["body"])["error"].lower()


def test_malformed_json_body_is_rejected(monkeypatch):
    handler = _load(monkeypatch)
    response = handler.lambda_handler({"requestContext": {}, "body": "{not-json"}, None)
    assert response["statusCode"] == 400
