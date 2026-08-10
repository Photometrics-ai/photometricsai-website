"""Step Functions task: merge crawl results into the GIS search job document."""

import time

import job_store

GENERIC_ERROR_MESSAGE = "An internal error occurred while searching. Please try again."


def _total_results(source_results: list[dict]) -> int:
    return sum(result.get("totalResults", 0) for result in source_results)


def _initial(event: dict) -> dict:
    source_results = event["sourceResults"]
    updated_at = int(time.time())
    doc = {
        "jobId": event["jobId"],
        "status": "complete",
        "query": event["query"],
        "matchMode": event["matchMode"],
        "sources": event["sources"],
        "invalidSources": event["invalidSources"],
        "createdAt": event["createdAt"],
        "updatedAt": updated_at,
        "sourceResults": source_results,
        "totalResults": _total_results(source_results),
        "error": None,
    }
    job_store.write_job(event["bucket"], event["jobId"], doc)
    return {"jobId": event["jobId"], "status": "complete", "totalResults": doc["totalResults"]}


def _full(event: dict) -> dict:
    existing = job_store.read_job(event["bucket"], event["jobId"])
    if existing is None:
        print(f"[gis-combine] jobId={event.get('jobId')} missing_doc=true mode=full")
        return {"jobId": event.get("jobId"), "status": "missing"}

    fresh_result = event["sourceResults"][0]
    fresh_source = fresh_result["source"]
    source_results = [
        fresh_result if result.get("source") == fresh_source else result
        for result in existing.get("sourceResults", [])
    ]
    existing["sourceResults"] = source_results
    existing["totalResults"] = _total_results(source_results)
    existing["updatedAt"] = int(time.time())
    existing["status"] = "complete"
    existing["error"] = None
    job_store.write_job(event["bucket"], event["jobId"], existing)
    return {"jobId": event["jobId"], "status": "complete", "totalResults": existing["totalResults"]}


def _error(event: dict) -> dict:
    job_id = event.get("jobId")
    bucket = event.get("bucket")
    print(f"[gis-combine] jobId={job_id} raw_error={event.get('error')}")

    try:
        if not job_id or not bucket:
            return {"jobId": job_id, "status": "error"}

        existing = job_store.read_job(bucket, job_id)
        if existing is None:
            return {"jobId": job_id, "status": "missing"}

        existing.update(
            {
                "status": "error",
                "error": GENERIC_ERROR_MESSAGE,
                "updatedAt": int(time.time()),
            }
        )
        job_store.write_job(bucket, job_id, existing)
    except Exception as exc:  # noqa: BLE001 -- failure handler must return cleanly
        print(f"[gis-combine] jobId={job_id} error_handler_failed={exc}")

    return {"jobId": job_id, "status": "error"}


def lambda_handler(event, context):
    mode = event["mode"]
    if mode == "initial":
        return _initial(event)
    if mode == "full":
        return _full(event)
    if mode == "error":
        return _error(event)
    raise ValueError(f"unsupported combine mode: {mode}")
