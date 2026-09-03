"""Contract clause (b): get_bounced_emails pagination.
Contract clause (c): get_bounced_emails classification rule.

See p2-exclusion-hardening.impl.md WHAT TO IMPLEMENT item 3: paginate via
LastEvaluatedKey/ExclusiveStartKey; keep the classification rule exactly
(bounced iff event_type == "Complaint" or (event_type == "Bounce" and
subtype == "Permanent")); transient bounces stay excluded from the set.
"""
import lambda_function
from ddb import s


def test_get_bounced_emails_paginates_across_scan_pages(fake_dynamodb):
    page1 = {
        "Items": [
            {"email": s("bounced1@city.gov"), "event_type": s("Bounce"), "subtype": s("Permanent")},
        ],
        "LastEvaluatedKey": {"email": s("bounced1@city.gov")},
    }
    page2 = {
        "Items": [
            {"email": s("bounced2@city.gov"), "event_type": s("Complaint"), "subtype": s("abuse")},
        ],
        # no LastEvaluatedKey -> final page
    }
    fake_dynamodb.queue_scan(lambda_function.BOUNCE_TABLE, page1)
    fake_dynamodb.queue_scan(lambda_function.BOUNCE_TABLE, page2)

    result = lambda_function.get_bounced_emails()

    assert result == {"bounced1@city.gov", "bounced2@city.gov"}, (
        "both pages' addresses must be in the result"
    )

    scan_calls = fake_dynamodb.calls_for("scan", lambda_function.BOUNCE_TABLE)
    assert len(scan_calls) == 2, "expected exactly one scan call per page"
    assert "ExclusiveStartKey" not in scan_calls[0], "first scan must not send a start key"
    assert scan_calls[1].get("ExclusiveStartKey") == page1["LastEvaluatedKey"], (
        "second scan must pass the first page's LastEvaluatedKey as ExclusiveStartKey"
    )


def test_get_bounced_emails_classification_permanent_and_complaint_in_transient_out(fake_dynamodb):
    fake_dynamodb.queue_scan(lambda_function.BOUNCE_TABLE, {
        "Items": [
            {"email": s("permanent@city.gov"), "event_type": s("Bounce"), "subtype": s("Permanent")},
            {"email": s("complainer@city.gov"), "event_type": s("Complaint"), "subtype": s("abuse")},
            {"email": s("transient@city.gov"), "event_type": s("Bounce"), "subtype": s("Transient")},
        ],
    })

    result = lambda_function.get_bounced_emails()

    assert "permanent@city.gov" in result
    assert "complainer@city.gov" in result
    assert "transient@city.gov" not in result
