"""pytest configuration for the take-action Lambda unit test suite.

CRITICAL ORDERING: env vars and sys.path MUST be set before `import
lambda_function`, because lambda_function.py reads its config
(DYNAMODB_TABLE, SES_SENDER_EMAIL, etc.) and constructs its boto3 clients
(`dynamodb = boto3.client("dynamodb")`, `ses = boto3.client("sesv2")`) at
MODULE level, at import time.

TAKE_ACTION_SRC overrides the source directory this suite imports
lambda_function from (default: the repo's lambda/take-action directory,
i.e. this file's parent). This lets a caller point collection at a
pristine copy of the file — see p2-unit-tests-write.impl.md, which notes
the real working-tree copy may be mid-edit by a sibling work item:

    mkdir -p "$TMPDIR/lfhead" && git show HEAD:lambda/take-action/lambda_function.py > "$TMPDIR/lfhead/lambda_function.py"
    TAKE_ACTION_SRC="$TMPDIR/lfhead" python -m pytest lambda/take-action/tests --collect-only -q

No test in this suite makes a network or AWS call: lambda_function.dynamodb
and lambda_function.ses are monkeypatched per-test with small in-process
fakes (see fakes.py). moto is NOT installed and must not be imported.
"""
import os
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_DEFAULT_SRC_DIR = _TESTS_DIR.parent  # lambda/take-action

# Make this tests/ directory's own helper modules (fakes.py, ddb.py,
# builders.py) importable regardless of pytest's import mode.
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

_src_dir = os.environ.get("TAKE_ACTION_SRC", str(_DEFAULT_SRC_DIR))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# lambda_function.py reads these via os.environ.get(...) at module import
# time, and constructs boto3 clients at module level. Setting a region and
# dummy credentials lets client construction succeed with zero network
# calls (boto3.client(...) itself never talks to AWS). Table/sender names
# are harmless dummies — every test that touches DynamoDB/SES monkeypatches
# lambda_function.dynamodb / lambda_function.ses before calling in.
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-2")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("DYNAMODB_TABLE", "test-photometrics-take-action")
os.environ.setdefault("SEND_LOG_TABLE", "test-photometrics-take-action-sends")
os.environ.setdefault("BOUNCE_TABLE", "test-photometrics-email-bounces")
os.environ.setdefault("FLAGGED_TABLE", "test-photometrics-flagged-officials")
os.environ.setdefault("BOOSTED_TABLE", "test-photometrics-boosted-officials")
os.environ.setdefault("SES_SENDER_EMAIL", "take-action@photometrics.ai")
# Dummy placeholders only — never real values. lambda_function reads these
# into module-level constants at import time; nothing in this suite
# exercises search_officials/call_claude/research_location (they require a
# live Anthropic API call and are out of scope for these unit tests), so
# these are never sent anywhere.
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-unit-test-placeholder")
os.environ.setdefault("GOOGLE_CIVIC_API_KEY", "unit-test-placeholder")

import lambda_function  # noqa: E402  (must follow the setup above)

import pytest  # noqa: E402

from fakes import FakeDynamoDB, FakeSES  # noqa: E402


@pytest.fixture
def fake_dynamodb(monkeypatch):
    """Monkeypatch lambda_function.dynamodb with an in-process fake that
    records every call and serves canned per-table responses. No test using
    this fixture ever reaches real DynamoDB."""
    fake = FakeDynamoDB()
    monkeypatch.setattr(lambda_function, "dynamodb", fake)
    return fake


@pytest.fixture
def fake_ses(monkeypatch):
    """Monkeypatch lambda_function.ses with an in-process fake send_email
    that records every call and can be told to raise for specific
    addresses. No test using this fixture ever reaches real SES."""
    fake = FakeSES()
    monkeypatch.setattr(lambda_function, "ses", fake)
    return fake
