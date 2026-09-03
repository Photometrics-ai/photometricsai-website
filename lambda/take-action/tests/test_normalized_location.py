"""Contract clause (l): normalized_location parsing and its fallback.

NAMING/SIGNATURE ASSUMPTION: p2-source-and-location.impl.md fixes the DATA
(location_city/location_state/location_country stored on the generate row,
sourced from a Haiku `normalized_location: {city, state, country}` field
parsed "where the model JSON is already parsed" in search_officials, with a
fallback to parse_location(location) for city/state and 'US' for country
when the field is missing/unparseable/partially empty) but does NOT fix a
function name or signature for the parsing step itself.

These tests assume a module-level pure function
`normalized_location(parsed, location) -> dict` returning
{"location_city": ..., "location_state": ..., "location_country": ...},
where `parsed` is whatever dict search_officials already parses out of the
Haiku JSON response (i.e. it may or may not contain a `normalized_location`
sub-dict with city/state/country keys). If the implementing item structures
this differently (e.g. inlines the logic directly into search_officials
instead of exposing a standalone pure function), these tests will
fail/error with AttributeError until reconciled — see this suite's
HANDOFF 'Discovered' section.
"""
import lambda_function


def test_normalized_location_uses_haiku_provided_fields():
    parsed = {
        "normalized_location": {"city": "San Diego", "state": "CA", "country": "US"},
    }

    result = lambda_function.normalized_location(parsed, "San Diego, CA")

    assert result["location_city"] == "San Diego"
    assert result["location_state"] == "CA"
    assert result["location_country"] == "US"


def test_normalized_location_falls_back_to_parse_location_and_us_when_field_absent():
    result = lambda_function.normalized_location({}, "Austin, TX")

    expected_city, expected_state = lambda_function.parse_location("Austin, TX")
    assert result["location_city"] == expected_city
    assert result["location_state"] == expected_state
    assert result["location_country"] == "US"
