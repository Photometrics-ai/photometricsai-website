"""Tiny helpers for building/reading DynamoDB wire-format values in tests.

Not a test module (no test_* functions) — pytest will not collect this
file as tests.
"""


def s(value):
    return {"S": value}


def n(value):
    return {"N": str(value)}


def l(items):  # noqa: E743 (short name mirrors DynamoDB's own "L" type key)
    return {"L": items}


def m(mapping):
    return {"M": mapping}


def bool_(value):
    return {"BOOL": value}
