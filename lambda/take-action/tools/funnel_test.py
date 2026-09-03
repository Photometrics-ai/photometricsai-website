#!/usr/bin/env python3
"""funnel_test.py — Take Action send/bounce/exclusion funnel test harness.

Exercises the Photometrics AI "Take Action" managed-send path end to end
against the Lambda function `photometrics-take-action` (region us-east-2)
using ONLY SES mailbox-simulator addresses:

    success@simulator.amazonses.com              -> always delivers
    bounce@simulator.amazonses.com                -> always hard-bounces
    success+deselected@simulator.amazonses.com    -> delivers, but is never
                                                       sent to (proves /send
                                                       only mails the reps in
                                                       the request body)
    dead.official@simulator.amazonses.com         -> never actually mailed;
                                                       seeded as a prior
                                                       Permanent bounce so
                                                       check-regenerate can
                                                       prove /send suppresses
                                                       it instead of calling
                                                       SES

SAFETY RULES (see README.md for the full writeup):
  - No real official inbox and no inbox other than the configured --cc-email
    (default ari@sdgis.com) may ever receive mail from this tool.
  - This tool NEVER calls the Lambda's /generate endpoint (no Anthropic
    tokens spent). It seeds DynamoDB directly with a synthetic session row
    and invokes only the /send path.
  - All rows this tool creates use a session_id prefixed "test-" and are
    deleted by the `cleanup` subcommand (or automatically at the end of
    `all`, unless --keep is passed).
  - /send is invoked via the AWS Lambda Invoke API with a synthetic
    Function-URL event, never over HTTPS.

Subcommands: seed, send, wait-bounce, check-sends, check-exclusion,
check-regenerate, cleanup, all. Run `funnel_test.py --help` or
`funnel_test.py <cmd> --help` for details. State is persisted between
separate invocations in .funnel_test_state.json next to this script
(git-ignored).

--dry-run prints every intended AWS action and makes ZERO AWS calls — it
never constructs a live boto3 client, so it works even with bogus/empty
AWS credentials in the environment.
"""

import argparse
import json
import os
import sys
import time

import boto3
from boto3.dynamodb.types import TypeDeserializer

# ---------------------------------------------------------------------------
# Constants — system under test
# ---------------------------------------------------------------------------

DEFAULT_REGION = "us-east-2"
DEFAULT_CC_EMAIL = "ari@sdgis.com"

LAMBDA_NAME = "photometrics-take-action"
DYNAMO_TABLE = "photometrics-take-action"
SEND_LOG_TABLE = "photometrics-take-action-sends"
BOUNCE_TABLE = "photometrics-email-bounces"
BOOSTED_TABLE = "photometrics-boosted-officials"

LOCATION = "Austin, TX"
PRIORITIES = ["Transportation Safety"]

# Attribution + normalized location seeded onto the generate row's `source`
# map and location_* attributes, per the data contract: source is an M of S
# (utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match,
# gclid, landed_priorities, referrer — each <=200 chars, absent keys
# omitted), and location_city/location_state/location_country are top-level
# S attributes.
SOURCE_FIELDS = {
    "utm_source": "google",
    "utm_medium": "cpc",
    "utm_campaign": "TESTCAMP",
    "utm_content": "TBD-1",
    "utm_term": "streetlight safety",
    "utm_match": "p",
    "gclid": "TESTGCLID",
    "landed_priorities": "Transportation Safety",
    "referrer": "https://www.google.com/",
}
LOCATION_CITY = "Austin"
LOCATION_STATE = "TX"
LOCATION_COUNTRY = "US"

# check-regenerate's hard-bounced address. Never actually mailed — SES never
# sees it, because the point of check-regenerate is to prove /send suppresses
# a known-bad address BEFORE attempting delivery.
DEAD_OFFICIAL_EMAIL = "dead.official@simulator.amazonses.com"
DEAD_OFFICIAL = {
    "email": DEAD_OFFICIAL_EMAIL,
    "name": "Test Dead Official",
    "title": "Commissioner",
    "organization": "City of Austin",
    "relevance": (
        "Seeded by funnel_test.py check-regenerate — hard-bounced and also "
        "present in photometrics-boosted-officials, to prove suppression at "
        "send time wins even over a boosted/trusted official."
    ),
}

# The three seeded representatives, in the exact order required. Only the
# first two are ever passed to /send — the third ("deselected") proves the
# endpoint mails exactly the recipients in the request body, not everyone
# who was ever seeded for the session.
REPS = [
    {
        "email": "success@simulator.amazonses.com",
        "name": "Test Mayor",
        "title": "Mayor",
        "organization": "City of Austin",
        "relevance": "Seeded by funnel_test.py — success delivery path.",
    },
    {
        "email": "bounce@simulator.amazonses.com",
        "name": "Test Director",
        "title": "Director",
        "organization": "City of Austin",
        "relevance": "Seeded by funnel_test.py — permanent bounce path.",
    },
    {
        "email": "success+deselected@simulator.amazonses.com",
        "name": "Test Council",
        "title": "Council Member",
        "organization": "City of Austin",
        "relevance": "Seeded by funnel_test.py — must NOT receive mail from /send.",
    },
]

LETTER_TEMPLATE = (
    "Dear [Representative Name],\n\n"
    "I am writing as a resident of Austin, TX to urge continued investment in "
    "transportation safety improvements in our community, including "
    "better-lit crosswalks, safer intersections, and traffic-calming "
    "measures on high-risk corridors. These changes save lives and make our "
    "streets safer for everyone who walks, bikes, or drives through our "
    "neighborhood.\n\n"
    "Thank you for your attention to this issue and for your service to our "
    "community.\n\n"
    "Sincerely,\nFunnel Test"
)

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".funnel_test_state.json")

WAIT_BOUNCE_TIMEOUT_S = 150
WAIT_BOUNCE_POLL_INTERVAL_S = 5


class FunnelTestError(Exception):
    """Raised on any assertion failure or unrecoverable state problem."""


# ---------------------------------------------------------------------------
# State file helpers (local file I/O only — never an AWS call)
# ---------------------------------------------------------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)


# ---------------------------------------------------------------------------
# DynamoDB item helpers
# ---------------------------------------------------------------------------

def dynamo_serialize(obj):
    """Mirror of lambda_function.py's dynamo_serialize() — recursively
    converts a Python object into DynamoDB's typed attribute-value shape."""
    if isinstance(obj, dict):
        return {"M": {k: dynamo_serialize(v) for k, v in obj.items()}}
    elif isinstance(obj, list):
        return {"L": [dynamo_serialize(item) for item in obj]}
    elif isinstance(obj, str):
        return {"S": obj}
    elif isinstance(obj, (int, float)):
        return {"N": str(obj)}
    elif isinstance(obj, bool):
        return {"BOOL": obj}
    elif obj is None:
        return {"NULL": True}
    return {"S": str(obj)}


def to_python(item):
    """Deserialize a DynamoDB item (attr name -> AttributeValue) to plain
    Python values, for readable printing."""
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in item.items()}


def build_source_item():
    """The `source` M seeded on generate rows — contract keys per
    SOURCE_FIELDS, serialized the same way dynamo_serialize() would."""
    return dynamo_serialize(SOURCE_FIELDS)


def get_bounced_emails_paginated(ddb):
    """Re-implementation of lambda_function.py's get_bounced_emails()
    (~line 864) semantics, but with a PAGINATED scan (the production
    function does a single non-paginated scan — fine for its purposes, but
    this harness must not silently miss rows past the first page)."""
    bounced = set()
    scan_kwargs = {
        "TableName": BOUNCE_TABLE,
        "ProjectionExpression": "email, event_type, #st",
        # "subtype" is a DynamoDB reserved word — must be aliased.
        "ExpressionAttributeNames": {"#st": "subtype"},
    }
    while True:
        resp = ddb.scan(**scan_kwargs)
        for item in resp.get("Items", []):
            email = item.get("email", {}).get("S", "")
            event_type = item.get("event_type", {}).get("S", "")
            subtype = item.get("subtype", {}).get("S", "")
            if not email:
                continue
            if event_type == "Complaint" or (event_type == "Bounce" and subtype == "Permanent"):
                bounced.add(email.lower())
        if "LastEvaluatedKey" in resp:
            scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        else:
            break
    return bounced


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_seed(args, clients):
    state = load_state()
    session_id = f"test-{int(time.time())}"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ttl = int(time.time()) + 86400  # 1 day — test row, not the 1-year prod TTL
    letter = LETTER_TEMPLATE

    item = {
        "session_id": {"S": session_id},
        "timestamp": {"S": now},
        "location": {"S": LOCATION},
        "priorities": {"L": [{"S": p} for p in PRIORITIES]},
        "letter": {"S": letter},
        "representatives": dynamo_serialize(REPS),
        "actions": {"L": []},
        "ttl": {"N": str(ttl)},
        "name": {"S": "Funnel Test"},
        "source": build_source_item(),
        "location_city": {"S": LOCATION_CITY},
        "location_state": {"S": LOCATION_STATE},
        "location_country": {"S": LOCATION_COUNTRY},
    }

    print(f"[seed] session_id={session_id}")
    print(f"[seed] representatives: {[r['email'] for r in REPS]}")

    if args.dry_run:
        print(f"[dry-run] would put_item into {DYNAMO_TABLE}:")
        print(json.dumps(item, indent=2))
    else:
        clients["dynamodb"].put_item(TableName=DYNAMO_TABLE, Item=item)
        print(f"[seed] put_item OK into {DYNAMO_TABLE}")

    state["session_id"] = session_id
    state["seed_ts"] = time.time()
    state["letter"] = letter
    save_state(state)
    print(f"[seed] state saved to {STATE_FILE}")


def cmd_send(args, clients):
    state = load_state()
    session_id = state.get("session_id")
    letter_base = state.get("letter")

    if not session_id or not letter_base:
        if args.dry_run:
            print("[dry-run] no seeded state found; using synthetic placeholder values")
            session_id = session_id or "test-DRYRUN"
            letter_base = letter_base or LETTER_TEMPLATE
        else:
            raise FunnelTestError("No seeded session in state; run 'seed' first (or use 'all').")

    marker_ts = time.time()
    marker = f"EDIT-MARKER {marker_ts}"
    letter = f"{letter_base}\n\n{marker}"

    # Only the first two seeded reps are sent to — rep 3 (deselected) is
    # deliberately omitted from the request body.
    send_reps = [
        {"email": REPS[0]["email"], "name": REPS[0]["name"], "title": REPS[0]["title"]},
        {"email": REPS[1]["email"], "name": REPS[1]["name"], "title": REPS[1]["title"]},
    ]
    body = {
        "session_id": session_id,
        "name": "Funnel Test",
        "email": args.cc_email,
        "location": LOCATION,
        "letter": letter,
        "representatives": send_reps,
    }
    event_payload = {
        "rawPath": "/send",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }

    print(f"[send] session_id={session_id} cc_email={args.cc_email}")
    print(f"[send] marker={marker}")
    print(f"[send] recipients: {[r['email'] for r in send_reps]} (excludes {REPS[2]['email']})")

    if args.dry_run:
        print(f"[dry-run] would lambda.invoke(FunctionName='{LAMBDA_NAME}') with event:")
        print(json.dumps(event_payload, indent=2))
        print("[dry-run] would then assert statusCode==200, sent_count==2, failed_count==0")
    else:
        resp = clients["lambda"].invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(event_payload).encode("utf-8"),
        )
        raw = resp["Payload"].read()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            raise FunnelTestError(f"Lambda returned non-JSON payload: {raw!r}")

        if resp.get("FunctionError"):
            raise FunnelTestError(f"Lambda FunctionError={resp['FunctionError']}: {payload}")

        print(f"[send] raw Lambda response: {payload}")

        status_code = payload.get("statusCode")
        if status_code != 200:
            raise FunnelTestError(f"Expected statusCode 200, got {status_code}: {payload.get('body')}")

        try:
            parsed_body = json.loads(payload.get("body", "{}"))
        except json.JSONDecodeError:
            raise FunnelTestError(f"/send body was not valid JSON: {payload.get('body')!r}")

        if parsed_body.get("sent_count") != 2:
            raise FunnelTestError(f"Expected sent_count == 2, got: {parsed_body}")
        if parsed_body.get("failed_count") != 0:
            raise FunnelTestError(f"Expected failed_count == 0, got: {parsed_body}")

        print(f"[send] OK: {parsed_body}")

    state["marker"] = marker
    state["send_ts"] = marker_ts
    state["cc_email"] = args.cc_email
    save_state(state)


def cmd_wait_bounce(args, clients):
    print(f"[wait-bounce] polling {BOUNCE_TABLE} for bounce@simulator.amazonses.com "
          f"(event_type=Bounce, subtype=Permanent), timeout={WAIT_BOUNCE_TIMEOUT_S}s")

    if args.dry_run:
        print(f"[dry-run] would scan {BOUNCE_TABLE} with FilterExpression on email/event_type/#st "
              f"every {WAIT_BOUNCE_POLL_INTERVAL_S}s for up to {WAIT_BOUNCE_TIMEOUT_S}s")
        return

    start = time.time()
    attempt = 0
    while True:
        attempt += 1
        elapsed = time.time() - start
        print(f"[wait-bounce] attempt {attempt} (elapsed {elapsed:.0f}s) — scanning...")

        resp = clients["dynamodb"].scan(
            TableName=BOUNCE_TABLE,
            FilterExpression="email = :e AND event_type = :et AND #st = :st",
            ExpressionAttributeNames={"#st": "subtype"},
            ExpressionAttributeValues={
                ":e": {"S": "bounce@simulator.amazonses.com"},
                ":et": {"S": "Bounce"},
                ":st": {"S": "Permanent"},
            },
        )
        items = resp.get("Items", [])
        if items:
            print(f"[wait-bounce] found bounce row after {elapsed:.0f}s: {to_python(items[0])}")
            return

        if time.time() - start >= WAIT_BOUNCE_TIMEOUT_S:
            raise FunnelTestError(
                f"Timed out after {WAIT_BOUNCE_TIMEOUT_S}s waiting for a Permanent bounce "
                f"row for bounce@simulator.amazonses.com in {BOUNCE_TABLE}"
            )
        time.sleep(WAIT_BOUNCE_POLL_INTERVAL_S)


def cmd_check_sends(args, clients):
    state = load_state()
    session_id = state.get("session_id")
    cc_email = state.get("cc_email", args.cc_email)

    if not session_id:
        if args.dry_run:
            session_id = "test-DRYRUN"
        else:
            raise FunnelTestError("No session_id in state; run 'seed'/'send' first.")

    print(f"[check-sends] session_id={session_id}")

    if args.dry_run:
        print(f"[dry-run] would get_item({SEND_LOG_TABLE}, Key session_id={session_id}) and assert shape")
        return

    resp = clients["dynamodb"].get_item(TableName=SEND_LOG_TABLE, Key={"session_id": {"S": session_id}})
    item = resp.get("Item")
    if not item:
        raise FunnelTestError(f"No row found in {SEND_LOG_TABLE} for session_id={session_id}")

    print(f"[check-sends] full row: {json.dumps(to_python(item), indent=2, default=str)}")

    reps_sent = {r["S"] for r in item.get("representatives_sent", {}).get("L", [])}
    expected = {REPS[0]["email"], REPS[1]["email"]}
    if reps_sent != expected or len(reps_sent) != 2:
        raise FunnelTestError(f"representatives_sent mismatch: got {reps_sent}, expected exactly {expected}")
    if REPS[2]["email"] in reps_sent:
        raise FunnelTestError(f"Deselected rep {REPS[2]['email']} unexpectedly present in representatives_sent")

    message_ids = item.get("message_ids", {}).get("L", [])
    if len(message_ids) != 2:
        raise FunnelTestError(f"Expected 2 message_ids, got {len(message_ids)}: {message_ids}")

    constituent_email = item.get("constituent_email", {}).get("S", "")
    if constituent_email != cc_email:
        raise FunnelTestError(f"constituent_email mismatch: got {constituent_email!r}, expected {cc_email!r}")

    print(f"[check-sends] OK — representatives_sent={sorted(reps_sent)}, "
          f"message_ids count={len(message_ids)}, constituent_email={constituent_email}")


def cmd_check_exclusion(args, clients):
    print(f"[check-exclusion] paginated scan of {BOUNCE_TABLE}, including a row when "
          f"event_type == 'Complaint' OR (event_type == 'Bounce' AND subtype == 'Permanent')")

    if args.dry_run:
        print(f"[dry-run] would paginate-scan {BOUNCE_TABLE} (ExpressionAttributeNames alias for "
              f"reserved word 'subtype', following LastEvaluatedKey) and assert "
              f"bounce@simulator.amazonses.com is present")
        return

    bounced = get_bounced_emails_paginated(clients["dynamodb"])
    print(f"[check-exclusion] bounced set ({len(bounced)} emails): {sorted(bounced)}")

    if "bounce@simulator.amazonses.com" not in bounced:
        raise FunnelTestError(
            "bounce@simulator.amazonses.com not present in exclusion set "
            "(get_bounced_emails() semantics) — funnel does not prove exclusion works"
        )

    print("[check-exclusion] OK — bounce@simulator.amazonses.com is correctly excluded")


def cmd_check_regenerate(args, clients):
    """Prove a hard-bounced address is refused at /send time (reason
    'suppressed') rather than being re-mailed. Fully self-contained — seeds
    its own dedicated session (never reuses the main seed/send state), so it
    can run standalone or as part of `all`.

    Also seeds a matching photometrics-boosted-officials row for the same
    address, so this proves suppression wins even over a "boosted"/trusted
    official — not just an address /send has never seen before."""
    state = load_state()
    regen_session_id = f"test-regen-{int(time.time())}"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    bounce_ttl = int(time.time()) + (180 * 24 * 60 * 60)  # matches record_bounce_event()
    gen_ttl = int(time.time()) + 86400  # 1 day — test row, not the 1-year prod TTL

    # success rep + the hard-bounced dead official — representatives_offered
    # on the sends row should equal len(this list) == 2.
    regen_reps = [REPS[0], DEAD_OFFICIAL]
    letter = LETTER_TEMPLATE

    gen_item = {
        "session_id": {"S": regen_session_id},
        "timestamp": {"S": now},
        "location": {"S": LOCATION},
        "priorities": {"L": [{"S": p} for p in PRIORITIES]},
        "letter": {"S": letter},
        "representatives": dynamo_serialize(regen_reps),
        "actions": {"L": []},
        "ttl": {"N": str(gen_ttl)},
        "name": {"S": "Funnel Test"},
        "source": build_source_item(),
        "location_city": {"S": LOCATION_CITY},
        "location_state": {"S": LOCATION_STATE},
        "location_country": {"S": LOCATION_COUNTRY},
    }

    bounce_item = {
        "email": {"S": DEAD_OFFICIAL_EMAIL},
        "timestamp": {"S": now},
        "event_type": {"S": "Bounce"},
        "subtype": {"S": "Permanent"},
        "ttl": {"N": str(bounce_ttl)},
    }

    # Key schema for photometrics-boosted-officials, confirmed via
    # `aws dynamodb describe-table` at build time: region (HASH, S),
    # email (RANGE, S). See tools/README.md for the raw output.
    boosted_key = {"region": {"S": LOCATION}, "email": {"S": DEAD_OFFICIAL_EMAIL}}
    boosted_item = dict(boosted_key)
    boosted_item.update({
        "name": {"S": DEAD_OFFICIAL["name"]},
        "title": {"S": DEAD_OFFICIAL["title"]},
        "organization": {"S": DEAD_OFFICIAL["organization"]},
        "reason": {"S": "Seeded by funnel_test.py check-regenerate — hard-bounced, must be suppressed."},
    })

    send_reps = [{"email": r["email"], "name": r["name"], "title": r["title"]} for r in regen_reps]
    body = {
        "session_id": regen_session_id,
        "name": "Funnel Test",
        "email": args.cc_email,
        "location": LOCATION,
        "letter": letter,
        "representatives": send_reps,
    }
    event_payload = {
        "rawPath": "/send",
        "requestContext": {"http": {"method": "POST"}},
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }

    print(f"[check-regenerate] regen_session_id={regen_session_id}")
    print(f"[check-regenerate] representatives: {[r['email'] for r in regen_reps]}")
    print(f"[check-regenerate] hard-bounced address under test: {DEAD_OFFICIAL_EMAIL}")

    if args.dry_run:
        print(f"[dry-run] would put_item into {BOUNCE_TABLE} (Permanent bounce for {DEAD_OFFICIAL_EMAIL}):")
        print(json.dumps(bounce_item, indent=2))
        print(f"[dry-run] would put_item into {BOOSTED_TABLE} (region={LOCATION!r}, matching key schema "
              f"region=HASH/email=RANGE):")
        print(json.dumps(boosted_item, indent=2))
        print(f"[dry-run] would put_item into {DYNAMO_TABLE} (generate row with {DEAD_OFFICIAL_EMAIL} "
              f"added to representatives, plus source/location_city/location_state/location_country):")
        print(json.dumps(gen_item, indent=2))
        print(f"[dry-run] would lambda.invoke(FunctionName='{LAMBDA_NAME}') with event:")
        print(json.dumps(event_payload, indent=2))
        print("[dry-run] would then assert statusCode==200, sent_count==1, failed_count==1, "
              f"failed==[{{'email': {DEAD_OFFICIAL_EMAIL!r}, 'reason': 'suppressed'}}]")
        print(f"[dry-run] would get_item({SEND_LOG_TABLE}, session_id={regen_session_id}) and assert "
              f"representatives_failed contains the suppressed entry, {DEAD_OFFICIAL_EMAIL} is NOT in "
              f"representatives_sent, representatives_offered==2, and priorities/source/location_city match")
        state["regen_session_id"] = regen_session_id
        save_state(state)
        return

    ddb = clients["dynamodb"]

    ddb.put_item(TableName=BOUNCE_TABLE, Item=bounce_item)
    print(f"[check-regenerate] seeded Permanent bounce row for {DEAD_OFFICIAL_EMAIL} in {BOUNCE_TABLE}")

    ddb.put_item(TableName=BOOSTED_TABLE, Item=boosted_item)
    print(f"[check-regenerate] seeded {BOOSTED_TABLE} row region={LOCATION!r} email={DEAD_OFFICIAL_EMAIL}")

    ddb.put_item(TableName=DYNAMO_TABLE, Item=gen_item)
    print(f"[check-regenerate] seeded generate row session_id={regen_session_id} in {DYNAMO_TABLE} "
          f"(representatives includes {DEAD_OFFICIAL_EMAIL}, passing the open-relay guard)")

    state["regen_session_id"] = regen_session_id
    save_state(state)

    resp = clients["lambda"].invoke(
        FunctionName=LAMBDA_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(event_payload).encode("utf-8"),
    )
    raw = resp["Payload"].read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise FunnelTestError(f"Lambda returned non-JSON payload: {raw!r}")

    if resp.get("FunctionError"):
        raise FunnelTestError(f"Lambda FunctionError={resp['FunctionError']}: {payload}")

    print(f"[check-regenerate] raw Lambda response: {payload}")

    if payload.get("statusCode") != 200:
        raise FunnelTestError(f"Expected statusCode 200, got {payload.get('statusCode')}: {payload.get('body')}")

    try:
        parsed_body = json.loads(payload.get("body", "{}"))
    except json.JSONDecodeError:
        raise FunnelTestError(f"/send body was not valid JSON: {payload.get('body')!r}")

    if parsed_body.get("sent_count") != 1:
        raise FunnelTestError(f"Expected sent_count == 1, got: {parsed_body}")
    if parsed_body.get("failed_count") != 1:
        raise FunnelTestError(f"Expected failed_count == 1, got: {parsed_body}")

    failed_list = parsed_body.get("failed") or []
    matching_failed = [
        f for f in failed_list if isinstance(f, dict) and f.get("email") == DEAD_OFFICIAL_EMAIL
    ]
    if len(matching_failed) != 1:
        raise FunnelTestError(
            f"Expected exactly one 'failed' entry for {DEAD_OFFICIAL_EMAIL} in the /send response, "
            f"got: {failed_list}"
        )
    if matching_failed[0].get("reason") != "suppressed":
        raise FunnelTestError(
            f"Expected /send response failed reason 'suppressed' for {DEAD_OFFICIAL_EMAIL}, "
            f"got: {matching_failed[0]}"
        )

    print(f"[check-regenerate] /send response OK: sent_count=1, failed_count=1, failed={failed_list}")

    sends_resp = ddb.get_item(TableName=SEND_LOG_TABLE, Key={"session_id": {"S": regen_session_id}})
    sends_item = sends_resp.get("Item")
    if not sends_item:
        raise FunnelTestError(f"No row found in {SEND_LOG_TABLE} for session_id={regen_session_id}")

    print(f"[check-regenerate] sends row: {json.dumps(to_python(sends_item), indent=2, default=str)}")

    reps_sent = {r["S"] for r in sends_item.get("representatives_sent", {}).get("L", [])}
    if DEAD_OFFICIAL_EMAIL in reps_sent:
        raise FunnelTestError(
            f"{DEAD_OFFICIAL_EMAIL} unexpectedly present in representatives_sent: {reps_sent} "
            f"— a suppressed address must never be mailed"
        )
    if REPS[0]["email"] not in reps_sent:
        raise FunnelTestError(f"Expected {REPS[0]['email']} in representatives_sent, got: {reps_sent}")

    reps_failed_raw = sends_item.get("representatives_failed", {}).get("L", [])
    reps_failed = [
        {k: v.get("S") for k, v in rf.get("M", {}).items()} for rf in reps_failed_raw
    ]
    matching_row = [
        rf for rf in reps_failed
        if rf.get("email") == DEAD_OFFICIAL_EMAIL and rf.get("reason") == "suppressed"
    ]
    if not matching_row:
        raise FunnelTestError(
            f"sends row representatives_failed missing a suppressed entry for {DEAD_OFFICIAL_EMAIL}: "
            f"{reps_failed}"
        )

    reps_offered = sends_item.get("representatives_offered", {}).get("N")
    if reps_offered != str(len(regen_reps)):
        raise FunnelTestError(
            f"Expected sends row representatives_offered == {len(regen_reps)}, got: {reps_offered!r}"
        )

    priorities_on_row = [p.get("S") for p in sends_item.get("priorities", {}).get("L", [])]
    if priorities_on_row != PRIORITIES:
        raise FunnelTestError(f"Expected sends row priorities == {PRIORITIES}, got: {priorities_on_row}")

    source_map = sends_item.get("source", {}).get("M")
    if not source_map:
        raise FunnelTestError("Expected sends row to carry a non-empty 'source' map, got none")
    source_on_row = {k: v.get("S") for k, v in source_map.items()}
    for key, expected_value in SOURCE_FIELDS.items():
        if source_on_row.get(key) != expected_value:
            raise FunnelTestError(
                f"sends row source.{key} mismatch: expected {expected_value!r}, got {source_on_row.get(key)!r}"
            )

    location_city_on_row = sends_item.get("location_city", {}).get("S")
    if location_city_on_row != LOCATION_CITY:
        raise FunnelTestError(
            f"Expected sends row location_city == {LOCATION_CITY!r}, got {location_city_on_row!r}"
        )

    print(
        "[check-regenerate] OK — hard-bounced (and boosted) representative was correctly suppressed "
        "at send time, never mailed, and the sends row carries representatives_failed, "
        "representatives_offered, priorities, source, and location_city"
    )


def cmd_cleanup(args, clients):
    state = load_state()
    session_id = state.get("session_id")
    regen_session_id = state.get("regen_session_id")
    print(f"[cleanup] session_id in state: {session_id}")
    print(f"[cleanup] regen_session_id in state: {regen_session_id}")

    # Deterministic key for the boosted-officials row check-regenerate seeds
    # (region=HASH, email=RANGE, per describe-table — see README.md). Scoped
    # to the synthetic dead.official@simulator.amazonses.com address, so it
    # is always safe to target even if check-regenerate never ran this time.
    boosted_key = {"region": {"S": LOCATION}, "email": {"S": DEAD_OFFICIAL_EMAIL}}

    if args.dry_run:
        for sid in (session_id, regen_session_id):
            print(f"[dry-run] would delete_item({DYNAMO_TABLE}, session_id={sid})")
            print(f"[dry-run] would delete_item({SEND_LOG_TABLE}, session_id={sid})")
        print(f"[dry-run] would delete_item({BOOSTED_TABLE}, key={boosted_key})")
        print(f"[dry-run] would describe_table({BOUNCE_TABLE}) to discover its key schema, then "
              f"paginate-scan it and delete_item every row whose email ends with "
              f"'@simulator.amazonses.com' (this also covers the {DEAD_OFFICIAL_EMAIL} bounce row "
              f"check-regenerate seeds)")
        print("[dry-run] would clear the state file")
        return

    deleted = []

    for sid in (session_id, regen_session_id):
        if not sid:
            continue
        clients["dynamodb"].delete_item(TableName=DYNAMO_TABLE, Key={"session_id": {"S": sid}})
        deleted.append((DYNAMO_TABLE, {"session_id": sid}))
        print(f"[cleanup] deleted {DYNAMO_TABLE} session_id={sid}")

        clients["dynamodb"].delete_item(TableName=SEND_LOG_TABLE, Key={"session_id": {"S": sid}})
        deleted.append((SEND_LOG_TABLE, {"session_id": sid}))
        print(f"[cleanup] deleted {SEND_LOG_TABLE} session_id={sid}")

    if not session_id and not regen_session_id:
        print("[cleanup] no session_id/regen_session_id in state; skipping session/sends row deletion")

    # Idempotent — delete_item on a non-existent key is a no-op, so this is
    # safe to run even when check-regenerate didn't seed the row this time.
    clients["dynamodb"].delete_item(TableName=BOOSTED_TABLE, Key=boosted_key)
    deleted.append((BOOSTED_TABLE, {"region": LOCATION, "email": DEAD_OFFICIAL_EMAIL}))
    print(f"[cleanup] deleted {BOOSTED_TABLE} region={LOCATION!r} email={DEAD_OFFICIAL_EMAIL}")

    # Bounce table key schema is discovered at runtime — it may be a single
    # partition key or composite (partition + sort). Never assume 'email' is
    # the whole key.
    desc = clients["dynamodb"].describe_table(TableName=BOUNCE_TABLE)
    key_schema = desc["Table"]["KeySchema"]
    key_attr_names = [ks["AttributeName"] for ks in key_schema]
    print(f"[cleanup] {BOUNCE_TABLE} key schema: {key_schema}")

    # Project every key attribute plus 'email', aliasing all of them
    # defensively (we don't know in advance whether any key attribute name
    # collides with a DynamoDB reserved word).
    project_attrs = sorted(set(key_attr_names) | {"email"})
    ean = {f"#a{i}": name for i, name in enumerate(project_attrs)}
    proj_expr = ", ".join(ean.keys())

    items = []
    scan_kwargs = {"TableName": BOUNCE_TABLE, "ProjectionExpression": proj_expr, "ExpressionAttributeNames": ean}
    while True:
        resp = clients["dynamodb"].scan(**scan_kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" in resp:
            scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        else:
            break

    bounce_deletes = 0
    for item in items:
        email = item.get("email", {}).get("S", "")
        # Covers both plain simulator addresses and plus-addressed variants
        # (e.g. success+deselected@simulator.amazonses.com) — both end with
        # the simulator domain.
        if not email.endswith("@simulator.amazonses.com"):
            continue
        key = {attr: item[attr] for attr in key_attr_names if attr in item}
        if len(key) != len(key_attr_names):
            print(f"[cleanup] WARNING: item for email={email} missing key attribute(s), skipping: {item}")
            continue
        clients["dynamodb"].delete_item(TableName=BOUNCE_TABLE, Key=key)
        printable_key = to_python(key)
        deleted.append((BOUNCE_TABLE, printable_key))
        bounce_deletes += 1
        print(f"[cleanup] deleted {BOUNCE_TABLE} key={printable_key} (email={email})")

    print(f"[cleanup] total bounce rows deleted: {bounce_deletes}")
    print(f"[cleanup] all deleted keys: {deleted}")

    clear_state()
    print("[cleanup] state file cleared")


def cmd_all(args, clients, dispatch):
    steps = ["seed", "send", "wait-bounce", "check-sends", "check-exclusion", "check-regenerate"]
    failure = None

    for step in steps:
        print(f"\n===== [all] step: {step} =====")
        try:
            dispatch[step](args, clients)
        except FunnelTestError as e:
            print(f"[all] step '{step}' FAILED: {e}")
            failure = e
            break

    if args.keep:
        print("\n===== [all] --keep passed; skipping cleanup =====")
    else:
        print("\n===== [all] step: cleanup =====")
        try:
            dispatch["cleanup"](args, clients)
        except FunnelTestError as e:
            print(f"[all] cleanup FAILED: {e}")
            if failure is None:
                failure = e

    if failure:
        raise failure

    print("\n===== [all] all steps completed successfully =====")


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="funnel_test.py",
        description=(
            "Exercise the Photometrics AI Take Action managed-send funnel end to end "
            "using ONLY SES mailbox-simulator addresses. Never calls /generate; seeds "
            "DynamoDB directly and invokes the Lambda's /send path via the AWS Lambda "
            "Invoke API (not HTTPS)."
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print every intended AWS action and make ZERO AWS calls. Exits 0 even with bogus credentials.",
    )
    parser.add_argument(
        "--keep", action="store_true",
        help="For 'all': skip the final cleanup step (leaves test rows in place).",
    )
    parser.add_argument(
        "--cc-email", default=DEFAULT_CC_EMAIL,
        help=f"Constituent CC address used in /send and checked in check-sends (default: {DEFAULT_CC_EMAIL}).",
    )
    parser.add_argument(
        "--region", default=DEFAULT_REGION,
        help=f"AWS region (default: {DEFAULT_REGION}).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Subcommand to run.")
    subparsers.add_parser("seed", help="Seed a test session row in photometrics-take-action.")
    subparsers.add_parser("send", help="Invoke Lambda /send for the seeded session (first two reps only).")
    subparsers.add_parser(
        "wait-bounce",
        help="Poll photometrics-email-bounces for the simulated permanent bounce (up to 150s).",
    )
    subparsers.add_parser(
        "check-sends", help="Verify the photometrics-take-action-sends row for the seeded session.",
    )
    subparsers.add_parser(
        "check-exclusion",
        help="Verify the bounced address is excluded per get_bounced_emails() semantics.",
    )
    subparsers.add_parser(
        "check-regenerate",
        help=(
            "Seed a Permanent bounce + boosted-officials row for a hard-bounced address, add it to "
            "a fresh seeded session, invoke /send, and assert it is suppressed (not mailed)."
        ),
    )
    subparsers.add_parser("cleanup", help="Delete all test rows created by this harness.")
    subparsers.add_parser(
        "all",
        help=(
            "Run seed -> send -> wait-bounce -> check-sends -> check-exclusion -> "
            "check-regenerate -> cleanup."
        ),
    )
    return parser


def build_clients(args):
    """Only ever called when args.dry_run is False — dry-run must never
    construct a live boto3 client."""
    return {
        "lambda": boto3.client("lambda", region_name=args.region),
        "dynamodb": boto3.client("dynamodb", region_name=args.region),
    }


def main():
    parser = build_parser()
    args = parser.parse_args()

    clients = None if args.dry_run else build_clients(args)

    dispatch = {
        "seed": cmd_seed,
        "send": cmd_send,
        "wait-bounce": cmd_wait_bounce,
        "check-sends": cmd_check_sends,
        "check-exclusion": cmd_check_exclusion,
        "check-regenerate": cmd_check_regenerate,
        "cleanup": cmd_cleanup,
    }

    try:
        if args.command == "all":
            cmd_all(args, clients, dispatch)
        else:
            dispatch[args.command](args, clients)
    except FunnelTestError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print("OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
