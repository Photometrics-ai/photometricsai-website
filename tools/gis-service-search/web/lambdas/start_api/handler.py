"""POST /api/gis-service-search/start.

Validates a live ArcGIS crawl request, creates the initial job document, and
starts the Step Functions workflow.
"""

import json
import os
import time
import uuid

import boto3

import job_store
import rate_limit
from url_normalize import dedupe_urls

MATCH_MODE_ANY = "any"
MATCH_MODE_PHRASE = "phrase"
MATCH_MODE_ALL = "all"
VALID_MATCH_MODES = (MATCH_MODE_ANY, MATCH_MODE_PHRASE, MATCH_MODE_ALL)

MAX_SOURCES = 25
MAX_QUERY_LENGTH = 200

DATA_BUCKET = os.environ["DATA_BUCKET"]
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]
INITIAL_BUDGET_SECONDS = int(os.environ.get("INITIAL_BUDGET_SECONDS", "45"))

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

    if not rate_limit.check_and_increment(ip):
        print(f"[gis-start] ip={ip} rate_limited=ip")
        return _error_response(429, "Search rate limit reached. Please wait a few minutes and try again.")

    query = body.get("query")
    if not isinstance(query, str) or not query.strip():
        return _error_response(400, "query is required")
    query = query.strip()[:MAX_QUERY_LENGTH]

    match_mode = body.get("matchMode", MATCH_MODE_ANY)
    if match_mode not in VALID_MATCH_MODES:
        match_mode = MATCH_MODE_ANY

    raw_sources = body.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        return _error_response(400, "sources must be a non-empty list of URLs")

    valid_sources, invalid_sources = dedupe_urls(raw_sources[: MAX_SOURCES * 2])
    valid_sources = valid_sources[:MAX_SOURCES]
    invalid_sources_raw = [entry["raw"] for entry in invalid_sources]
    if not valid_sources:
        return _error_response(400, "no valid http(s) source URLs were provided")

    job_id = uuid.uuid4().hex
    created_at = int(time.time())
    doc = {
        "jobId": job_id,
        "status": "processing",
        "query": query,
        "matchMode": match_mode,
        "sources": valid_sources,
        "invalidSources": invalid_sources_raw,
        "createdAt": created_at,
        "updatedAt": created_at,
        "sourceResults": [],
        "totalResults": 0,
        "error": None,
    }
    job_store.write_job(DATA_BUCKET, job_id, doc)

    execution_input = {
        "jobId": job_id,
        "bucket": DATA_BUCKET,
        "query": query,
        "matchMode": match_mode,
        "sources": valid_sources,
        "invalidSources": invalid_sources_raw,
        "createdAt": created_at,
        "mode": "initial",
        "budgetSeconds": INITIAL_BUDGET_SECONDS,
    }
    _sfn().start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=job_id,
        input=json.dumps(execution_input),
    )

    print(f"[gis-start] ip={ip} jobId={job_id} sources={len(valid_sources)}")
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"jobId": job_id, "status": "processing"}),
    }
