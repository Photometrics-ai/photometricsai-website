"""Contract clause (j): log_send item shape.

Exercised through handle_send (rather than calling log_send directly) so
these tests are robust to log_send's exact parameter list, which the
p2-exclusion-hardening contract explicitly allows to change ("log_send's
signature may gain parameters ... update its call site in handle_send
accordingly") — what's fixed by the data contract is the shape of the
DynamoDB Item actually written to SEND_LOG_TABLE, which is what's asserted
here.

See p2-exclusion-hardening.impl.md DATA CONTRACT (sends row).
"""
import lambda_function
from builders import generate_row_item
from ddb import n, s

REP_A = {
    "name": "Rep A", "title": "Council Member", "organization": "City Council",
    "email": "success@simulator.amazonses.com",
}
REP_B = {
    "name": "Rep B", "title": "Public Works Director", "organization": "Public Works",
    "email": "success+2@simulator.amazonses.com",
}


def _send_body(session_id, representatives):
    return {
        "session_id": session_id,
        "name": "A Concerned Resident",
        "email": "ari@sdgis.com",
        "location": "San Diego, CA",
        "letter": "Dear [Representative Name], please consider precision lighting.",
        "representatives": representatives,
    }


def _sends_row(fake_dynamodb, session_id):
    rows = [
        item for item in fake_dynamodb.put_items
        if item.get("session_id", {}).get("S") == session_id and "constituent_email" in item
    ]
    assert len(rows) == 1, f"expected exactly one sends-row put_item, found {len(rows)}"
    return rows[0]


def test_log_send_item_shape_includes_new_contract_fields(fake_dynamodb, fake_ses):
    session_id = "test-log-send-shape-1"
    generate_item = generate_row_item(
        session_id,
        [REP_A, REP_B],
        priorities=["Crime & Safety", "Energy Waste"],
        source={"utm_source": "google", "utm_campaign": "take-action"},
        location_city="San Diego",
        location_state="CA",
    )
    fake_dynamodb.set_get_item(lambda_function.DYNAMO_TABLE, {"Item": generate_item})
    fake_dynamodb.set_get_item(lambda_function.SEND_LOG_TABLE, {})

    resp = lambda_function.handle_send(_send_body(session_id, [REP_A, REP_B]))
    assert resp["statusCode"] == 200

    item = _sends_row(fake_dynamodb, session_id)

    # pre-existing fields must survive untouched
    assert item["session_id"] == s(session_id)
    assert "timestamp" in item
    assert item["constituent_email"] == s("ari@sdgis.com")
    assert "location" in item
    assert "representatives_sent" in item
    assert "message_ids" in item
    assert "ttl" in item

    # new contract fields
    assert item["priorities"] == {"L": [s("Crime & Safety"), s("Energy Waste")]}
    assert item["source"] == {"M": {"utm_source": s("google"), "utm_campaign": s("take-action")}}
    assert item["location_city"] == s("San Diego")
    assert item["location_state"] == s("CA")
    assert item["representatives_offered"] == n(2), "= len(generate row's representatives)"
    assert "representatives_failed" in item
    assert item["representatives_failed"]["L"] == []


def test_log_send_omits_source_and_location_when_absent_on_generate_row(fake_dynamodb, fake_ses):
    """The pre-existing generate rows (118 as of the Phase 1 baseline) have
    no source/location_city/location_state. log_send must OMIT those
    attributes entirely rather than writing an empty S/M (DynamoDB rejects
    an empty S)."""
    session_id = "test-log-send-omit-1"
    generate_item = generate_row_item(session_id, [REP_A])  # no source/location kwargs
    fake_dynamodb.set_get_item(lambda_function.DYNAMO_TABLE, {"Item": generate_item})
    fake_dynamodb.set_get_item(lambda_function.SEND_LOG_TABLE, {})

    resp = lambda_function.handle_send(_send_body(session_id, [REP_A]))
    assert resp["statusCode"] == 200

    item = _sends_row(fake_dynamodb, session_id)

    assert "source" not in item
    assert "location_city" not in item
    assert "location_state" not in item
