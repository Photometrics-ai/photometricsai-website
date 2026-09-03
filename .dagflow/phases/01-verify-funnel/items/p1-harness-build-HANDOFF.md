# p1-harness-build — HANDOFF

## Status: done

## What was accomplished

Built a self-contained, safety-constrained boto3 CLI harness at
`lambda/take-action/tools/funnel_test.py` that exercises the Take Action
managed-send funnel (seed → send → bounce → exclusion → cleanup) end to end
using only SES mailbox-simulator addresses, plus documentation at
`lambda/take-action/tools/README.md`. Added one line to the repo
`.gitignore` for the harness's local state file.

The harness was built strictly from reading `lambda_function.py` (not
modified) — specifically `log_generation()` (~line 706), `dynamo_serialize()`
(~line 689), `handle_send()` (~line 969), `get_verified_representative_emails()`
(~line 890), `log_send()` (~line 947), `get_bounced_emails()` (~line 864),
`respond()` (~line 89), and `lambda_handler()`'s routing (~line 1141,
`path.endswith("/send")`).

**No AWS calls were made against the live system in this item** beyond
`--dry-run` verification (which makes zero AWS calls by design). Running the
harness for real against production is a separate item's job.

## Canonical outputs

- `lambda/take-action/tools/funnel_test.py` — the CLI harness
- `lambda/take-action/tools/README.md` — usage/safety documentation
- `.gitignore` — one line added: `lambda/take-action/tools/.funnel_test_state.json`

## Decisions / assumptions

- **State persistence in dry-run too.** `--dry-run` never makes an AWS call,
  but it does still read/write the local `.funnel_test_state.json` file (pure
  local file I/O, no credentials needed) so that `--dry-run seed` followed by
  `--dry-run send` in separate invocations chains correctly, and so `--dry-run
  all` can print a coherent, non-placeholder session_id/letter/marker through
  every step. This does not violate "zero AWS calls."
- **Bounce-table key-schema handling strategy.** `cleanup` and
  `check-exclusion` never hardcode the bounce table's key shape. `cleanup`
  calls `describe_table` on `photometrics-email-bounces` at runtime, reads
  `Table.KeySchema` (a list of `{AttributeName, KeyType}` — one entry for a
  simple partition key, two for partition+sort), and builds each
  `delete_item` `Key=` dict dynamically from whichever attribute names
  actually appear in the schema, by projecting those key attributes (plus
  `email`) out of a paginated scan and filtering client-side for
  `email.endswith("@simulator.amazonses.com")`. All projected attribute
  names are aliased (`#a0`, `#a1`, ...) defensively, since it isn't known in
  advance whether a key attribute name collides with a DynamoDB reserved
  word. `check-exclusion` mirrors `get_bounced_emails()`'s inclusion logic
  exactly but paginates via `LastEvaluatedKey` (the production function does
  a single non-paginated `scan`, which is fine for it but would be wrong for
  a harness meant to prove correctness against a table that could exceed one
  scan page).
- **`send` body only includes `email`/`name`/`title` per representative** —
  matching what `handle_send()` actually reads off each rep dict (it doesn't
  look at `organization`/`relevance` from the request body, only from the
  stored session row via `get_verified_representative_emails()`, which only
  extracts `email`).
- **Rep 3 (deselected) is seeded but never sent to**, by construction — the
  `send` subcommand slices `REPS[0:2]` into the request body. This is what
  proves `/send` only mails recipients present in the request, not every rep
  ever associated with the session.
- **EDIT-MARKER mechanism**: `send` appends `\n\nEDIT-MARKER <unix-float-ts>`
  to the seeded letter before sending, proving the letter text that ships is
  the one in the request body (i.e., what a user would have edited
  client-side) rather than whatever was written to DynamoDB at seed time.
- Test row TTL is 1 day (`now + 86400`), not the 1-year production value,
  per the assignment.
- `--cc-email` defaults to `ari@sdgis.com` (the only non-simulator address
  the tool will ever use) per the standing safety rule.

## Interface / contract downstream work must follow

- Invoke shape for `/send` (verified by reading `lambda_handler` +
  `handle_send`):
  ```json
  {
    "rawPath": "/send",
    "requestContext": {"http": {"method": "POST"}},
    "body": "<JSON string — see below>",
    "isBase64Encoded": false
  }
  ```
  Body JSON: `{session_id, name, email, location, letter, representatives: [{email, name, title}, ...]}`.
  Response is a Function-URL-style dict: `{"statusCode": int, "headers": {...}, "body": "<JSON string>"}`.
  Success body: `{"status": "sent", "sent_count": int, "failed_count": int}`.
- Session row shape for seeding (`photometrics-take-action`, PK
  `session_id` S): `session_id` S, `timestamp` S (`%Y-%m-%dT%H:%M:%SZ`),
  `location` S, `priorities` L of S, `letter` S, `representatives` L of M
  (each M has `email`/`name`/`title`/`organization`/`relevance`, all S),
  `actions` L (empty), `ttl` N, `name` S.
- `photometrics-take-action-sends` row (PK `session_id` S) has
  `constituent_email`, `location` (S), `representatives_sent` (L of S),
  `message_ids` (L of S), `timestamp`, `ttl`.
- `photometrics-email-bounces` key schema is NOT assumed by any caller —
  always `describe_table` first. `subtype` is a reserved word requiring
  `ExpressionAttributeNames` aliasing in any `FilterExpression` or
  `ProjectionExpression` that touches it.
- Any subsequent item that runs this harness for real should invoke:
  `python lambda/take-action/tools/funnel_test.py all` (or run subcommands
  individually) and capture the printed output as its own evidence — this
  item did not run it against live AWS.

## Files changed

- `lambda/take-action/tools/funnel_test.py` (new)
- `lambda/take-action/tools/README.md` (new)
- `.gitignore` (+1 line: `lambda/take-action/tools/.funnel_test_state.json`)

Confirmed untouched: `lambda/take-action/lambda_function.py`,
`layouts/_default/take-action.html` (not present in `git status --porcelain`
output at all).

## Commands / tests run, with outcomes

### 1. boto3 importable
```
$ python -c "import boto3; print(boto3.__version__)"
1.42.70
```

### 2. py_compile
```
$ cd C:/Users/aisaa/Projects/photometricsai-website && python -m py_compile lambda/take-action/tools/funnel_test.py && echo COMPILE_OK
COMPILE_OK
```

### 3. --help
```
$ python lambda/take-action/tools/funnel_test.py --help
usage: funnel_test.py [-h] [--dry-run] [--keep] [--cc-email CC_EMAIL]
                      [--region REGION]
                      {seed,send,wait-bounce,check-sends,check-exclusion,cleanup,all}
                      ...

Exercise the Photometrics AI Take Action managed-send funnel end to end using
ONLY SES mailbox-simulator addresses. Never calls /generate; seeds DynamoDB
directly and invokes the Lambda's /send path via the AWS Lambda Invoke API
(not HTTPS).

positional arguments:
  {seed,send,wait-bounce,check-sends,check-exclusion,cleanup,all}
                        Subcommand to run.
    seed                Seed a test session row in photometrics-take-action.
    send                Invoke Lambda /send for the seeded session (first two
                        reps only).
    wait-bounce         Poll photometrics-email-bounces for the simulated
                        permanent bounce (up to 150s).
    check-sends         Verify the photometrics-take-action-sends row for the
                        seeded session.
    check-exclusion     Verify the bounced address is excluded per
                        get_bounced_emails() semantics.
    cleanup             Delete all test rows created by this harness.
    all                 Run seed -> send -> wait-bounce -> check-sends ->
                        check-exclusion -> cleanup.

options:
  -h, --help            show this help message and exit
  --dry-run             Print every intended AWS action and make ZERO AWS
                        calls. Exits 0 even with bogus credentials.
  --keep                For 'all': skip the final cleanup step (leaves test
                        rows in place).
  --cc-email CC_EMAIL   Constituent CC address used in /send and checked in
                        check-sends (default: ari@sdgis.com).
  --region REGION       AWS region (default: us-east-2).
```

### 4. --dry-run all with bogus credentials (full output)
```
$ AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus AWS_SESSION_TOKEN= AWS_PROFILE= python lambda/take-action/tools/funnel_test.py --dry-run all; echo "EXIT=$?"

===== [all] step: seed =====
[seed] session_id=test-1788462339
[seed] representatives: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com', 'success+deselected@simulator.amazonses.com']
[dry-run] would put_item into photometrics-take-action:
{
  "session_id": {"S": "test-1788462339"},
  "timestamp": {"S": "2026-09-03T19:05:39Z"},
  "location": {"S": "Austin, TX"},
  "priorities": {"L": [{"S": "Transportation Safety"}]},
  "letter": {"S": "Dear [Representative Name],\n\nI am writing as a resident of Austin, TX to urge continued investment in transportation safety improvements in our community, including better-lit crosswalks, safer intersections, and traffic-calming measures on high-risk corridors. These changes save lives and make our streets safer for everyone who walks, bikes, or drives through our neighborhood.\n\nThank you for your attention to this issue and for your service to our community.\n\nSincerely,\nFunnel Test"},
  "representatives": {"L": [
    {"M": {"email": {"S": "success@simulator.amazonses.com"}, "name": {"S": "Test Mayor"}, "title": {"S": "Mayor"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py \u2014 success delivery path."}}},
    {"M": {"email": {"S": "bounce@simulator.amazonses.com"}, "name": {"S": "Test Director"}, "title": {"S": "Director"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py \u2014 permanent bounce path."}}},
    {"M": {"email": {"S": "success+deselected@simulator.amazonses.com"}, "name": {"S": "Test Council"}, "title": {"S": "Council Member"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py \u2014 must NOT receive mail from /send."}}}
  ]},
  "actions": {"L": []},
  "ttl": {"N": "1788548739"},
  "name": {"S": "Funnel Test"}
}
[seed] state saved to C:\Users\aisaa\Projects\photometricsai-website\lambda\take-action\tools\.funnel_test_state.json

===== [all] step: send =====
[send] session_id=test-1788462339 cc_email=ari@sdgis.com
[send] marker=EDIT-MARKER 1788462339.8376617
[send] recipients: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com'] (excludes success+deselected@simulator.amazonses.com)
[dry-run] would lambda.invoke(FunctionName='photometrics-take-action') with event:
{
  "rawPath": "/send",
  "requestContext": {"http": {"method": "POST"}},
  "body": "{\"session_id\": \"test-1788462339\", \"name\": \"Funnel Test\", \"email\": \"ari@sdgis.com\", \"location\": \"Austin, TX\", \"letter\": \"Dear [Representative Name],\\n\\nI am writing as a resident of Austin, TX to urge continued investment in transportation safety improvements in our community, including better-lit crosswalks, safer intersections, and traffic-calming measures on high-risk corridors. These changes save lives and make our streets safer for everyone who walks, bikes, or drives through our neighborhood.\\n\\nThank you for your attention to this issue and for your service to our community.\\n\\nSincerely,\\nFunnel Test\\n\\nEDIT-MARKER 1788462339.8376617\", \"representatives\": [{\"email\": \"success@simulator.amazonses.com\", \"name\": \"Test Mayor\", \"title\": \"Mayor\"}, {\"email\": \"bounce@simulator.amazonses.com\", \"name\": \"Test Director\", \"title\": \"Director\"}]}",
  "isBase64Encoded": false
}
[dry-run] would then assert statusCode==200, sent_count==2, failed_count==0

===== [all] step: wait-bounce =====
[wait-bounce] polling photometrics-email-bounces for bounce@simulator.amazonses.com (event_type=Bounce, subtype=Permanent), timeout=150s
[dry-run] would scan photometrics-email-bounces with FilterExpression on email/event_type/#st every 5s for up to 150s

===== [all] step: check-sends =====
[check-sends] session_id=test-1788462339
[dry-run] would get_item(photometrics-take-action-sends, Key session_id=test-1788462339) and assert shape

===== [all] step: check-exclusion =====
[check-exclusion] paginated scan of photometrics-email-bounces, including a row when event_type == 'Complaint' OR (event_type == 'Bounce' AND subtype == 'Permanent')
[dry-run] would paginate-scan photometrics-email-bounces (ExpressionAttributeNames alias for reserved word 'subtype', following LastEvaluatedKey) and assert bounce@simulator.amazonses.com is present

===== [all] step: cleanup =====
[cleanup] session_id in state: test-1788462339
[dry-run] would delete_item(photometrics-take-action, session_id=test-1788462339)
[dry-run] would delete_item(photometrics-take-action-sends, session_id=test-1788462339)
[dry-run] would describe_table(photometrics-email-bounces) to discover its key schema, then paginate-scan it and delete_item every row whose email ends with '@simulator.amazonses.com'
[dry-run] would clear the state file

===== [all] all steps completed successfully =====
OK
EXIT=0
```
(The dry run wrote `.funnel_test_state.json` to disk as pure local file I/O
— no AWS calls occurred. That file has been deleted after verification and
is git-ignored.)

### 5. Email address grep (every hit is a simulator address or ari@sdgis.com)
```
$ grep -nE "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" lambda/take-action/tools/funnel_test.py
8:    success@simulator.amazonses.com              -> always delivers
9:    bounce@simulator.amazonses.com                -> always hard-bounces
10:    success+deselected@simulator.amazonses.com    -> delivers, but is never
17:    (default ari@sdgis.com) may ever receive mail from this tool.
51:DEFAULT_CC_EMAIL = "ari@sdgis.com"
67:        "email": "success@simulator.amazonses.com",
74:        "email": "bounce@simulator.amazonses.com",
81:        "email": "success+deselected@simulator.amazonses.com",
317:    print(f"[wait-bounce] polling {BOUNCE_TABLE} for bounce@simulator.amazonses.com "
337:                ":e": {"S": "bounce@simulator.amazonses.com"},
350:                f"row for bounce@simulator.amazonses.com in {BOUNCE_TABLE}"
405:              f"bounce@simulator.amazonses.com is present")
411:    if "bounce@simulator.amazonses.com" not in bounced:
413:            "bounce@simulator.amazonses.com not present in exclusion set "
417:    print("[check-exclusion] OK — bounce@simulator.amazonses.com is correctly excluded")
476:        # (e.g. success+deselected@simulator.amazonses.com) — both end with
```
All hits are `@simulator.amazonses.com` addresses or `ari@sdgis.com`. Confirmed clean.

### 6. describe_table / LastEvaluatedKey usage
```
$ grep -n "describe_table" lambda/take-action/tools/funnel_test.py
428:        print(f"[dry-run] would describe_table({BOUNCE_TABLE}) to discover its key schema, then "
450:    desc = clients["dynamodb"].describe_table(TableName=BOUNCE_TABLE)

$ grep -n "LastEvaluatedKey" lambda/take-action/tools/funnel_test.py
184:        if "LastEvaluatedKey" in resp:
185:            scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
404:              f"reserved word 'subtype', following LastEvaluatedKey) and assert "
467:        if "LastEvaluatedKey" in resp:
468:            scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
```
(Real pagination logic is in `get_bounced_emails_paginated()` at lines
184-185 and in `cmd_cleanup()`'s bounce-table scan loop at lines 467-468;
line 404 is just a dry-run print string mentioning the mechanism. Both real
loops paginate correctly.)

### 7. .gitignore entry
```
$ grep -n "funnel_test_state" .gitignore
45:lambda/take-action/tools/.funnel_test_state.json
```

### 8. git status — lambda_function.py and take-action.html untouched
```
$ git status --porcelain
 M .gitignore
?? .dagflow/
?? lambda/take-action/tools/
```
Neither `lambda/take-action/lambda_function.py` nor
`layouts/_default/take-action.html` appears — confirmed untouched.

### 9. README present and documents "simulator"
```
$ test -f lambda/take-action/tools/README.md && grep -ni "simulator" lambda/take-action/tools/README.md
(exit 0)
6:`us-east-2`, account `794038225197`), using **only SES mailbox-simulator
15:   mailbox-simulator addresses:
16:   - `success@simulator.amazonses.com` — always delivers
17:   - `bounce@simulator.amazonses.com` — always hard-bounces (Permanent)
18:   - `success+deselected@simulator.amazonses.com` — delivers, but is never
   (plus more matches throughout the doc — every subcommand section and the
   safety-rules section reference simulator addresses)
```

## Known limitations / risks / follow-up

- This harness has **not been run against live AWS** in this item (only
  `--dry-run`). The next phase item that runs it for real should capture
  its own command output as evidence, and should watch specifically for:
  - Whether `photometrics-email-bounces`' actual key schema is single or
    composite — `cleanup`'s `describe_table` call handles either, but this
    wasn't observed against the real table in this item.
  - SES sandbox/production-access status for the account, and whether the
    Lambda's SES configuration set / IAM role actually permits sending to
    mailbox-simulator addresses (this item did not verify Lambda IAM/SES
    config — out of scope per the "no IAM/Lambda config changes" standing
    rule).
  - Real-world bounce delivery latency (`wait-bounce` polls up to 150s; SES
    simulator bounces are typically fast but this is unverified against the
    live pipeline).
- `check-sends`'s `constituent_email` assertion compares against
  `state.get("cc_email", args.cc_email)` — if `check-sends` is run standalone
  in a separate process after a `send` that used a different `--cc-email`,
  the state file's persisted `cc_email` is used automatically, which is the
  correct behavior for chaining across separate invocations.
- No new prerequisites, conflicting assumptions, or architectural
  constraints were discovered beyond what's already documented in
  `lambda_function.py`. The `discovered` field for this item is empty.

## Newly discovered dependencies or conflicts

None.
