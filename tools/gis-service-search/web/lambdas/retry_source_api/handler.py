"""POST /api/gis-service-search/retry-source."""

import json
import os
import re
import time

import boto3

import job_store
import rate_limit
from url_normalize import normalize_source_url

DATA_BUCKET = os.environ["DATA_BUCKET"]
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]
FULL_BUDGET_SECONDS = int(os.environ.get("FULL_BUDGET_SECONDS", "240"))
JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")

_client = None


def _sfn():
    global _client
    if _client is None:
        _client = boto3.client("stepfunctions")
    return _client


def _error_response(status_code: int, message: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }


def _source_ip(event: dict) -> str:
    return event.get("requestContext", {}).get("identity", {}).get("sourceIp", "unknown")


def lambda_handler(event, context):
    ip = _source_ip(event)

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _error_response(400, "request body must be valid JSON")

    job_id = body.get("jobId")
    if not job_id:
        return _error_response(400, "jobId is required")
    if not isinstance(job_id, str) or not JOB_ID_RE.match(job_id):
        return _error_response(400, "invalid jobId")

    source = body.get("source")
    if not isinstance(source, str) or not source.strip():
        return _error_response(400, "source is required")
    try:
        normalized_source = normalize_source_url(source)
    except ValueError as exc:
        return _error_response(400, str(exc))

    if not rate_limit.check_and_increment(ip):
        print(f"[gis-retry] ip={ip} jobId={job_id} rate_limited=ip")
        return _error_response(429, "Search rate limit reached. Please wait a few minutes and try again.")

    doc = job_store.read_job(DATA_BUCKET, job_id)
    if doc is None:
        return _error_response(404, "Job not found")

    source_results = doc.get("sourceResults", [])
    entry = next((result for result in source_results if result.get("source") == normalized_source), None)
    if entry is None:
        return _error_response(400, "source is not part of this job")
    if entry.get("state") != "partial":
        return _error_response(400, "only partial-state sources can be retried")

    entry["retrying"] = True
    doc["updatedAt"] = int(time.time())
    job_store.write_job(DATA_BUCKET, job_id, doc)

    execution_name = f"{job_id}-retry-{int(time.time() * 1000)}"
    execution_input = {
        "jobId": job_id,
        "bucket": DATA_BUCKET,
        "query": doc["query"],
        "matchMode": doc["matchMode"],
        "sources": [normalized_source],
        "invalidSources": [],
        "createdAt": doc.get("createdAt"),
        "mode": "full",
        "budgetSeconds": FULL_BUDGET_SECONDS,
    }
    _sfn().start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=execution_name,
        input=json.dumps(execution_input),
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"jobId": job_id, "source": normalized_source, "status": "retrying"}),
    }
