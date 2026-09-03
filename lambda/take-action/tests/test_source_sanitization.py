"""Contract clause (k): source sanitization.

NAMING ASSUMPTION: p2-source-and-location.impl.md WHAT TO IMPLEMENT item 1
says "Prefer a small dedicated helper (e.g. `sanitize_source(raw) -> dict`)
so it is unit-testable in isolation — a sibling item's pytest suite will
import and exercise it." This suite is that sibling, and assumes the
suggested name `sanitize_source(raw) -> dict`. If the implementing item
names it differently, these tests will fail/error with AttributeError
until reconciled — see this suite's HANDOFF 'Discovered' section.

DATA CONTRACT (p2-source-and-location.impl.md): source (M): string keys
utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match,
gclid, landed_priorities, referrer. Each value sanitized to <=200 chars.
Unknown keys dropped. Absent/empty keys omitted. Whole map omitted if
empty.
"""
import lambda_function


def test_sanitize_source_drops_unknown_keys():
    raw = {"utm_source": "google", "not_a_contract_key": "drop-me", "another_bogus_key": "x"}

    result = lambda_function.sanitize_source(raw)

    assert "not_a_contract_key" not in result
    assert "another_bogus_key" not in result
    assert result.get("utm_source") == "google"


def test_sanitize_source_truncates_long_value_to_exactly_200_chars():
    raw = {"utm_campaign": "x" * 250}

    result = lambda_function.sanitize_source(raw)

    assert len(result["utm_campaign"]) == 200
    assert result["utm_campaign"] == "x" * 200


def test_sanitize_source_all_empty_input_yields_no_source_attribute():
    """An all-empty/absent input sanitizes down to an empty map. The
    contract requires the whole `source` attribute be omitted from the
    generate row in that case (never written as an empty M)."""
    assert lambda_function.sanitize_source({}) == {}
    assert lambda_function.sanitize_source({"utm_source": "   "}) == {}
    assert lambda_function.sanitize_source(None) == {}
