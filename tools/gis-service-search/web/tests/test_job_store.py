"""Tests job_store.py against a fake in-memory S3 client.

No test calls real AWS. Missing objects raise a real-shaped ClientError so
read_job's NoSuchKey handling is tested through the production error path.
"""

import io
import json

import pytest
from botocore.exceptions import ClientError

import job_store


class _FakeS3:
    """Mimics the S3 get_object/put_object calls job_store.py makes."""

    def __init__(self):
        self.objects = {}

    def get_object(self, Bucket, Key):
        object_key = (Bucket, Key)
        if object_key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
                "GetObject",
            )
        return {"Body": io.BytesIO(self.objects[object_key])}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = Body.encode("utf-8")
        return {"ETag": '"fake"'}


class _AccessDeniedS3:
    def get_object(self, Bucket, Key):
        raise ClientError({"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "GetObject")


@pytest.fixture
def fake_client(monkeypatch):
    client = _FakeS3()
    monkeypatch.setattr(job_store, "_client", client)
    return client


def test_job_key_uses_expected_shape():
    assert job_store.job_key("abc-123") == "jobs/abc-123/meta.json"


def test_write_then_read_round_trips_exact_dict(fake_client):
    doc = {
        "jobId": "job-1",
        "status": "queued",
        "sources": ["https://example.gov/arcgis/rest/services"],
        "nested": {"count": 2, "ok": True},
    }

    job_store.write_job("test-bucket", "job-1", doc)

    assert json.loads(fake_client.objects[("test-bucket", "jobs/job-1/meta.json")].decode("utf-8")) == doc
    assert job_store.read_job("test-bucket", "job-1") == doc


def test_read_missing_job_returns_none(fake_client):
    assert job_store.read_job("test-bucket", "missing-job") is None


def test_read_non_no_such_key_client_error_propagates(monkeypatch):
    monkeypatch.setattr(job_store, "_client", _AccessDeniedS3())

    with pytest.raises(ClientError) as exc_info:
        job_store.read_job("test-bucket", "job-1")

    assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
