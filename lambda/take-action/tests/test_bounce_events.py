"""Contract clause (d): record_bounce_event against a realistic SES bounce
notification JSON fixture.
Contract clause (e): record_bounce_event sender-skip rule — a bounce for
our own sending address must not be written.

See p2-exclusion-hardening.impl.md WHAT TO IMPLEMENT item 4.
"""
import lambda_function

# A realistic SES bounce notification, shaped like what arrives via SNS in
# handle_ses_notification -> json.loads(record["Sns"]["Message"]).
REALISTIC_BOUNCE_NOTIFICATION = {
    "notificationType": "Bounce",
    "bounce": {
        "bounceType": "Permanent",
        "bounceSubType": "General",
        "bouncedRecipients": [
            {"emailAddress": "official@cityhall.gov", "action": "failed", "status": "5.1.1"},
        ],
        "timestamp": "2026-03-01T12:00:00.000Z",
        "feedbackId": "0000018f-fake-feedback-id-000000000000",
    },
    "mail": {
        "timestamp": "2026-03-01T11:59:00.000Z",
        "messageId": "0000018f-fake-message-id",
        "source": "take-action@photometrics.ai",
        "destination": ["official@cityhall.gov"],
    },
}


def test_record_bounce_event_writes_row_for_realistic_bounce_notification(fake_dynamodb):
    lambda_function.record_bounce_event(REALISTIC_BOUNCE_NOTIFICATION, "Bounce")

    assert len(fake_dynamodb.put_items) == 1
    item = fake_dynamodb.put_items[0]
    assert item["email"]["S"] == "official@cityhall.gov"
    assert item["event_type"]["S"] == "Bounce"
    assert item["subtype"]["S"] == "Permanent"
    assert "timestamp" in item
    assert "ttl" in item

    put_calls = fake_dynamodb.calls_for("put_item", lambda_function.BOUNCE_TABLE)
    assert len(put_calls) == 1


def test_record_bounce_event_skips_row_for_sender_address(fake_dynamodb):
    """SECURITY/HYGIENE REGRESSION TEST: a bounce report naming our own
    sending address must NOT be written to the bounce table. If it were,
    take-action@photometrics.ai would end up in get_bounced_emails() and
    start being treated as an excluded/suppressed address, and the table
    would keep accumulating self-bounce noise (see
    p1-baseline-data-HANDOFF.md: 6 such rows were already found under the
    pre-fix behaviour). Comparison must be case-insensitive."""
    sender_email = lambda_function.SES_SENDER_EMAIL
    notification = {
        "notificationType": "Bounce",
        "bounce": {
            "bounceType": "Permanent",
            "bounceSubType": "General",
            "bouncedRecipients": [{"emailAddress": sender_email.upper()}],
        },
        "mail": {"destination": [sender_email]},
    }

    lambda_function.record_bounce_event(notification, "Bounce")

    assert fake_dynamodb.put_items == [], "no row should be written for the sender's own address"
