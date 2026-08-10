"""Local-only dev server for the GIS service search Lambda handlers.

Imports the Lambda handlers directly and translates plain HTTP requests into
Lambda-shaped events, so the Hugo dev server can exercise the real
crawl/classify/status flow before anything is deployed. NOT used in production;
production runs on Lambda + API Gateway + Step Functions.

This server fakes only AWS-facing dependencies in memory. ArcGIS outbound HTTP
fetching and SSRF validation still run through the real shared modules.

Usage:
    cd tools/gis-service-search/web
    .venv/Scripts/python local_dev_server.py   # Windows
    .venv/bin/python local_dev_server.py       # macOS/Linux
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from botocore.exceptions import ClientError

# These are read by handler modules at import time, so they must exist before
# any handler import happens.
os.environ.setdefault("AWS_ACCESS_KEY_ID", "local-dev-access-key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "local-dev-secret-key")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
os.environ.setdefault("DATA_BUCKET", "local-dev-bucket")
os.environ.setdefault("STATE_MACHINE_ARN", "local-dev-state-machine")
os.environ.setdefault("INITIAL_BUDGET_SECONDS", "45")
os.environ.setdefault("FULL_BUDGET_SECONDS", "240")

BASE_DIR = Path(__file__).resolve().parent
LAMBDAS_DIR = BASE_DIR / "lambdas"
SHARED_DIR = LAMBDAS_DIR / "shared"

sys.path.insert(0, str(SHARED_DIR))

import job_store  # noqa: E402
import rate_limit  # noqa: E402

PORT = int(os.environ.get("PORT", "3001"))

POST_ROUTES = {
    "/api/gis-service-search/start": "start_api",
    "/api/gis-service-search/retry-source": "retry_source_api",
}
GET_ROUTES = {
    "/api/gis-service-search/status": "status_api",
}


def _load_handler(name: str):
    path = LAMBDAS_DIR / name / "handler.py"
    spec = importlib.util.spec_from_file_location(f"local_dev_{name}_handler", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load handler module at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


start_api = _load_handler("start_api")
status_api = _load_handler("status_api")
crawl_source = _load_handler("crawl_source")
combine_results = _load_handler("combine_results")
retry_source_api = _load_handler("retry_source_api")

HANDLERS = {
    "start_api": start_api.lambda_handler,
    "status_api": status_api.lambda_handler,
    "retry_source_api": retry_source_api.lambda_handler,
}


class _FakeS3:
    """Thread-safe in-memory subset of the S3 client used by job_store.py."""

    def __init__(self):
        self._objects: dict[tuple[str, str], bytes] = {}
        self._lock = threading.Lock()

    def get_object(self, Bucket, Key):
        object_key = (Bucket, Key)
        with self._lock:
            body = self._objects.get(object_key)

        if body is None:
            raise ClientError(
                {
                    "Error": {
                        "Code": "NoSuchKey",
                        "Message": "The specified key does not exist.",
                    }
                },
                "GetObject",
            )

        return {"Body": io.BytesIO(body)}

    def put_object(self, Bucket, Key, Body, ContentType=None):
        if isinstance(Body, str):
            body = Body.encode("utf-8")
        else:
            body = bytes(Body)

        with self._lock:
            self._objects[(Bucket, Key)] = body

        return {"ResponseMetadata": {"HTTPStatusCode": 200}}


class _FakeDynamoDB:
    """Thread-safe in-memory subset of the DynamoDB client rate_limit.py uses."""

    def __init__(self):
        self._items: dict[str, int] = {}
        self._lock = threading.Lock()

    def update_item(self, TableName, Key, UpdateExpression, ExpressionAttributeValues, ReturnValues):
        item_key = Key["ip"]["S"]
        increment = int(ExpressionAttributeValues[":inc"]["N"])

        with self._lock:
            count = self._items.get(item_key, 0) + increment
            self._items[item_key] = count

        return {"Attributes": {"callCount": {"N": str(count)}}}


class _FakeStepFunctions:
    """Starts the local state-machine simulation in a background thread."""

    def start_execution(self, stateMachineArn, name, input):
        execution_input = json.loads(input)
        thread = threading.Thread(
            target=_run_state_machine,
            args=(execution_input,),
            name=f"local-sfn-{name}",
            daemon=True,
        )
        thread.start()
        return {"executionArn": f"local:{name}", "startDate": None}


def _crawl_failed_fallback(source: str) -> dict:
    return {
        "source": source,
        "state": "try_google",
        "reasonCode": "internal_error",
        "message": "The crawler hit an unexpected internal error searching this source.",
        "results": [],
        "totalResults": 0,
        "servicesScanned": 0,
        "servicesTotal": 0,
        "truncated": False,
        "retrying": False,
        "elapsedSeconds": 0,
    }


def _crawl_one_source(execution_input: dict, source_url: str) -> dict:
    event = {
        "jobId": execution_input["jobId"],
        "query": execution_input["query"],
        "matchMode": execution_input["matchMode"],
        "budgetSeconds": execution_input["budgetSeconds"],
        "source": source_url,
    }

    try:
        return crawl_source.lambda_handler(event, None)
    except Exception as exc:  # noqa: BLE001 -- mirrors the ASL per-item Catch
        print(f"[dev-server] crawl source failed source={source_url} error={exc}")
        traceback.print_exc()
        return _crawl_failed_fallback(source_url)


def _run_state_machine(execution_input: dict) -> None:
    try:
        source_results = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(_crawl_one_source, execution_input, source_url)
                for source_url in execution_input["sources"]
            ]
            for future in as_completed(futures):
                source_results.append(future.result())

        combine_event = {
            "mode": execution_input["mode"],
            "jobId": execution_input["jobId"],
            "bucket": execution_input["bucket"],
            "query": execution_input["query"],
            "matchMode": execution_input["matchMode"],
            "sources": execution_input["sources"],
            "invalidSources": execution_input.get("invalidSources", []),
            "createdAt": execution_input.get("createdAt"),
            "sourceResults": source_results,
        }
        combine_results.lambda_handler(combine_event, None)
    except Exception as exc:  # noqa: BLE001 -- mirrors the ASL MarkJobFailed path
        print(f"[dev-server] local state machine failed error={exc}")
        traceback.print_exc()
        combine_results.lambda_handler(
            {
                "mode": "error",
                "jobId": execution_input.get("jobId"),
                "bucket": execution_input.get("bucket"),
                "error": str(exc),
            },
            None,
        )


fake_s3 = _FakeS3()
fake_dynamodb = _FakeDynamoDB()
fake_sfn = _FakeStepFunctions()

job_store._client = fake_s3
rate_limit._client = fake_dynamodb
start_api._client = fake_sfn
retry_source_api._client = fake_sfn


class DevHandler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_lambda_result(self, result: dict) -> None:
        self.send_response(result["statusCode"])
        self._cors_headers()
        for key, value in result.get("headers", {}).items():
            self.send_header(key, value)
        body_bytes = result.get("body", "").encode("utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def _send_not_found(self) -> None:
        body_bytes = json.dumps({"error": "not found"}).encode("utf-8")
        self.send_response(404)
        self._cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        handler_name = GET_ROUTES.get(path)
        if handler_name is None:
            self._send_not_found()
            return

        query_values = parse_qs(urlsplit(self.path).query)
        params = {key: values[0] for key, values in query_values.items() if values}
        event = {
            "queryStringParameters": params,
            "requestContext": {"identity": {"sourceIp": self.client_address[0]}},
        }
        self._send_lambda_result(HANDLERS[handler_name](event, None))

    def do_POST(self):
        path = urlsplit(self.path).path
        handler_name = POST_ROUTES.get(path)
        if handler_name is None:
            self._send_not_found()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length else ""
        event = {
            "requestContext": {"identity": {"sourceIp": self.client_address[0]}},
            "body": raw_body,
        }
        self._send_lambda_result(HANDLERS[handler_name](event, None))

    def log_message(self, fmt, *args):
        print("[dev-server] " + (fmt % args))


def main():
    print(f"GIS Service Search local dev server -- http://127.0.0.1:{PORT}")
    print("Routes:")
    for route in POST_ROUTES:
        print(f"  POST {route}")
    for route in GET_ROUTES:
        print(f"  GET  {route}")
    print("Ctrl+C to stop.")

    server = ThreadingHTTPServer(("127.0.0.1", PORT), DevHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
