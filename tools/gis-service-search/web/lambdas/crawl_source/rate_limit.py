"""Per-IP rate limiting via DynamoDB, following the same
boto3.client("dynamodb") raw-item pattern already used by lambda/take-action
-- no new AWS service class introduced for this feature.

Fails open: if DynamoDB is unreachable, the request is allowed rather than
letting a rate-limiter outage take down the whole tool.
"""

import os
import time

import boto3

TABLE_NAME = os.environ.get("RATE_LIMIT_TABLE", "gis-search-rate-limit")

WINDOW_SECONDS = 600
MAX_CALLS_PER_WINDOW = 60

_client = None


def _dynamodb():
    global _client
    if _client is None:
        _client = boto3.client("dynamodb")
    return _client


def _increment(item_key, expires_at):
    response = _dynamodb().update_item(
        TableName=TABLE_NAME,
        Key={"ip": {"S": item_key}},
        UpdateExpression="ADD callCount :inc SET expiresAt = :exp",
        ExpressionAttributeValues={
            ":inc": {"N": "1"},
            ":exp": {"N": str(expires_at)},
        },
        ReturnValues="UPDATED_NEW",
    )
    return int(response["Attributes"]["callCount"]["N"])


def check_and_increment(ip_address):
    """Increment this IP's counter for the current 10-minute window and
    return True if the call is allowed, False if the IP is over
    MAX_CALLS_PER_WINDOW.
    """
    if not ip_address:
        return True

    now = int(time.time())
    window_start = now - (now % WINDOW_SECONDS)
    item_key = f"{ip_address}:{window_start}"
    expires_at = window_start + (2 * WINDOW_SECONDS)

    try:
        count = _increment(item_key, expires_at)
    except Exception as exc:  # noqa: BLE001 -- deliberately broad, this must never break search
        print(f"[rate_limit] dynamodb_error scope=ip ip={ip_address} error={exc}")
        return True

    return count <= MAX_CALLS_PER_WINDOW
