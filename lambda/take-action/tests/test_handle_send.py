"""Contract clause (f): handle_send suppression path.
Contract clause (g): handle_send ses_error path.
Contract clause (h): handle_send open-relay guard (SECURITY REGRESSION TEST).
Contract clause (i): handle_send already_sent -> 409.

Simulator addresses only (amazonses.com simulator), per this phase's
STANDING RULES — no real official is ever addressed by these tests, and
ses.send_email is a fake (see fakes.FakeSES), so nothing is actually sent.
"""
import json

import lambda_function
from builders import generate_row_item
from ddb import s

REP_A = {
    "name": "Rep A", "title": "Council Member", "organization": "City Council",
    "email": "success@simulator.amazonses.com",
}
REP_B = {
    "name": "Rep B", "title": "Public Works Director", "organization": "Public Works",
    "email": "success+2@simulator.amazonses.com",
}


def _seed_session(fake_dynamodb, session_id, representatives, already_sent=False):
    """Seed the two get_item lookups handle_send depends on: the generate
    row (get_verified_representative_emails, and possibly log_send's own
    lookup) and the send-log row (already_sent)."""
    fake_dynamodb.set_get_item(
        lambda_function.DYNAMO_TABLE,
        {"Item": generate_row_item(session_id, representatives)},
    )
    fake_dynamodb.set_get_item(
        lambda_function.SEND_LOG_TABLE,
        {"Item": {"session_id": s(session_id)}} if already_sent else {},
    )


def _send_body(session_id, representatives):
    return {
        "session_id": session_id,
        "name": "A Concerned Resident",
        "email": "ari@sdgis.com",
        "location": "San Diego, CA",
        "letter": "Dear [Representative Name], please consider precision lighting.",
        "representatives": representatives,
    }


def test_handle_send_suppresses_bounced_representative(fake_dynamodb, fake_ses):
    session_id = "test-suppression-1"
    _seed_session(fake_dynamodb, session_id, [REP_A, REP_B])
    fake_dynamodb.queue_scan(lambda_function.BOUNCE_TABLE, {
        "Items": [{"email": s(REP_A["email"]), "event_type": s("Bounce"), "subtype": s("Permanent")}],
    })

    resp = lambda_function.handle_send(_send_body(session_id, [REP_A, REP_B]))
    payload = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert {"email": REP_A["email"], "reason": "suppressed"} in payload.get("failed", [])

    sent_addrs = {c["Destination"]["ToAddresses"][0] for c in fake_ses.calls}
    assert REP_A["email"] not in sent_addrs, "a suppressed rep must never reach ses.send_email"
    assert REP_B["email"] in sent_addrs, "a non-suppressed rep must still be sent"


def test_handle_send_ses_error_marks_one_rep_failed_and_still_sends_the_other(fake_dynamodb, fake_ses):
    session_id = "test-ses-error-1"
    _seed_session(fake_dynamodb, session_id, [REP_A, REP_B])
    fake_ses.raise_for.add(REP_A["email"].lower())

    resp = lambda_function.handle_send(_send_body(session_id, [REP_A, REP_B]))
    payload = json.loads(resp["body"])

    assert resp["statusCode"] == 200
    assert {"email": REP_A["email"], "reason": "ses_error"} in payload.get("failed", [])

    sent_addrs = {c["Destination"]["ToAddresses"][0] for c in fake_ses.calls}
    assert REP_B["email"] in sent_addrs, "the other representative must still be sent"


def test_handle_send_rejects_unverified_email_SECURITY_open_relay_guard(fake_dynamodb, fake_ses):
    """SECURITY REGRESSION TEST: a representative email that was NOT part
    of this session's verified /generate result must be rejected with 400
    and must never reach ses.send_email. A Lambda Function URL has no
    built-in auth, so without this guard anyone who finds the /send
    endpoint could POST an arbitrary address into the To field of a mail
    sent from our verified sending domain (open relay)."""
    session_id = "test-open-relay-1"
    _seed_session(fake_dynamodb, session_id, [REP_A])  # only REP_A is verified for this session
    intruder = {
        "name": "Not Verified", "title": "Nobody", "organization": "N/A",
        "email": "arbitrary-target@example.com",
    }

    resp = lambda_function.handle_send(_send_body(session_id, [intruder]))

    assert resp["statusCode"] == 400
    assert fake_ses.calls == [], "no send may occur for an unverified recipient"


def test_handle_send_already_sent_returns_409_and_sends_nothing(fake_dynamodb, fake_ses):
    session_id = "test-already-sent-1"
    _seed_session(fake_dynamodb, session_id, [REP_A], already_sent=True)

    resp = lambda_function.handle_send(_send_body(session_id, [REP_A]))

    assert resp["statusCode"] == 409
    assert fake_ses.calls == [], "a duplicate send for an already-sent session must send nothing"
