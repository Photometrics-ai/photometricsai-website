"""Contract clause (a): filter_excluded(officials, excluded_emails).

filter_excluded is a module-level pure function (no I/O, no globals) that
drops any official whose 'email' matches an entry in excluded_emails,
case-insensitively. See p2-exclusion-hardening.impl.md WHAT TO IMPLEMENT
item 1.
"""
import copy

import lambda_function


def test_filter_excluded_is_case_insensitive():
    officials = [
        {"name": "A", "email": "Jane.Doe@City.GOV"},
        {"name": "B", "email": "other@city.gov"},
    ]
    excluded = {"jane.doe@city.gov"}

    result = lambda_function.filter_excluded(officials, excluded)

    emails = {o["email"] for o in result}
    assert emails == {"other@city.gov"}


def test_filter_excluded_keeps_official_with_no_email():
    officials = [
        {"name": "No Email Key"},
        {"name": "Empty Email", "email": ""},
    ]

    result = lambda_function.filter_excluded(officials, {"anything@x.com"})

    assert len(result) == 2


def test_filter_excluded_with_excluded_none_returns_input_unchanged():
    officials = [{"name": "A", "email": "a@x.com"}, {"name": "B", "email": "b@x.com"}]

    result = lambda_function.filter_excluded(officials, None)

    assert result == officials


def test_filter_excluded_with_excluded_empty_returns_input_unchanged():
    officials = [{"name": "A", "email": "a@x.com"}]

    result = lambda_function.filter_excluded(officials, set())

    assert result == officials


def test_filter_excluded_does_not_mutate_input_list_or_dicts():
    officials = [
        {"name": "A", "email": "a@x.com"},
        {"name": "B", "email": "b@x.com"},
    ]
    original = copy.deepcopy(officials)

    lambda_function.filter_excluded(officials, {"a@x.com"})

    assert officials == original, "filter_excluded must not mutate its input"
