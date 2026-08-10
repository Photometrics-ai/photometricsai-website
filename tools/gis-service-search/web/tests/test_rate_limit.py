"""Tests rate_limit.py against a fake in-memory DynamoDB client (no real AWS
calls, no credentials needed) so the counting/window/fail-open logic can be
verified directly rather than only indirectly through handler.py.
"""

import pytest

import rate_limit


class _FakeDynamoDB:
    """Mimics the one boto3 dynamodb client call rate_limit.py makes."""

    def __init__(self):
        self.items = {}

    def update_item(self, TableName, Key, UpdateExpression, ExpressionAttributeValues, ReturnValues):
        key = Key["ip"]["S"]
        count = self.items.get(key, 0) + int(ExpressionAttributeValues[":inc"]["N"])
        self.items[key] = count
        return {"Attributes": {"callCount": {"N": str(count)}}}


class _BrokenDynamoDB:
    def update_item(self, **kwargs):
        raise RuntimeError("simulated DynamoDB outage")


@pytest.fixture
def fake_client(monkeypatch):
    client = _FakeDynamoDB()
    monkeypatch.setattr(rate_limit, "_client", client)
    return client


def test_ip_calls_within_window_are_allowed(fake_client):
    for _ in range(rate_limit.MAX_CALLS_PER_WINDOW):
        assert rate_limit.check_and_increment("203.0.113.5") is True


def test_ip_call_over_window_limit_is_denied(fake_client):
    for _ in range(rate_limit.MAX_CALLS_PER_WINDOW):
        rate_limit.check_and_increment("203.0.113.5")
    assert rate_limit.check_and_increment("203.0.113.5") is False


def test_different_ips_have_independent_counters(fake_client):
    for _ in range(rate_limit.MAX_CALLS_PER_WINDOW):
        rate_limit.check_and_increment("203.0.113.5")
    assert rate_limit.check_and_increment("198.51.100.9") is True


def test_missing_ip_is_always_allowed(fake_client):
    assert rate_limit.check_and_increment("") is True
    assert rate_limit.check_and_increment(None) is True


def test_ip_limiter_fails_open_on_dynamodb_error(monkeypatch):
    monkeypatch.setattr(rate_limit, "_client", _BrokenDynamoDB())
    assert rate_limit.check_and_increment("203.0.113.5") is True
