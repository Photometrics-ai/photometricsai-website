"""GET /api/gis-service-search/status?jobId=."""

import json
import os
import re

import job_store

DATA_BUCKET = os.environ["DATA_BUCKET"]
JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")


def _error_response(status_code: int, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }


def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    job_id = params.get("jobId")

    if not job_id:
        return _error_response(400, "jobId is required")
    if not JOB_ID_RE.match(job_id):
        return _error_response(400, "invalid jobId")

    doc = job_store.read_job(DATA_BUCKET, job_id)
    if doc is None:
        return _error_response(404, "Job not found")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(doc),
    }
