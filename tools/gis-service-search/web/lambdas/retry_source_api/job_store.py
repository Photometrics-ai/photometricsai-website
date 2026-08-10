"""Single S3 I/O choke point for GIS search job documents.

Handlers should use this module for all job metadata reads and writes. Keeping
S3 access behind the lazy `_s3()` accessor gives the local development server a
single monkeypatch point for replacing real AWS S3 with an in-memory fake.
"""

import json

import boto3
from botocore.exceptions import ClientError

_client = None


def _s3():
    global _client
    if _client is None:
        _client = boto3.client("s3")
    return _client


def job_key(job_id: str) -> str:
    """Return the S3 key for a job metadata document."""
    return f"jobs/{job_id}/meta.json"


def read_job(bucket: str, job_id: str) -> dict | None:
    """Read and parse a job document from S3, or return None if missing."""
    try:
        response = _s3().get_object(Bucket=bucket, Key=job_key(job_id))
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
            return None
        raise

    return json.loads(response["Body"].read().decode("utf-8"))


def write_job(bucket: str, job_id: str, doc: dict) -> None:
    """Write a job document to S3 as JSON."""
    _s3().put_object(
        Bucket=bucket,
        Key=job_key(job_id),
        Body=json.dumps(doc),
        ContentType="application/json",
    )
