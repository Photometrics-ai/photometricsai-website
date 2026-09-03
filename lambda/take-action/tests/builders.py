"""Row-shape builders for constructing canned DynamoDB wire-format
responses in tests.

Not a test module (no test_* functions) — pytest will not collect this
file as tests.
"""
from ddb import l, m, n, s


def rep_item(rep):
    """One representative, in the wire format stored inside a generate
    row's `representatives` (L of M)."""
    return m({
        "name": s(rep.get("name", "")),
        "title": s(rep.get("title", "")),
        "organization": s(rep.get("organization", "")),
        "email": s(rep["email"]),
        "relevance": s(rep.get("relevance", "")),
    })


def generate_row_item(session_id, representatives, priorities=None, source=None,
                       location_city=None, location_state=None, location=None):
    """Build a wire-format 'photometrics-take-action' (generate) row, as
    returned inside {"Item": ...} from dynamodb.get_item(TableName=DYNAMODB_TABLE).

    source/location_city/location_state are omitted unless explicitly
    passed, matching the real table: the 118 pre-existing rows (as of the
    Phase 1 baseline) don't carry them, and new rows only carry them once
    p2-source-and-location lands.
    """
    item = {
        "session_id": s(session_id),
        "timestamp": s("2026-03-01T00:00:00Z"),
        "location": s(location or "San Diego, CA"),
        "priorities": l([s(p) for p in (priorities or ["Crime & Safety"])]),
        "letter": s("Dear [Representative Name], ..."),
        "representatives": l([rep_item(r) for r in representatives]),
        "actions": l([]),
        "ttl": n(9999999999),
    }
    if source:
        item["source"] = m({k: s(v) for k, v in source.items()})
    if location_city:
        item["location_city"] = s(location_city)
    if location_state:
        item["location_state"] = s(location_state)
    return item
