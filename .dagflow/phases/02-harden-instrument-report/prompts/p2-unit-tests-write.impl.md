You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-unit-tests-write
KIND: test
PURPOSE / EXPECTED OUTCOME:
Write the pytest suite for the hardened send path, exclusion, bounce recording, source sanitization and normalized-location parsing — authored against the fixed data contract so it can be built in parallel with the Lambda changes rather than after them.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
(none — no predecessors)

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
OBJECTIVE
Write (do not run against the final code — a sibling item runs it) the pytest suite that proves the hardened Take Action send path behaves per the data contract. You are writing these tests CONCURRENTLY with the Lambda changes, against the contract below, so the suite is ready the moment the implementation lands.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own exactly: C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ (new directory). You may READ C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py but you must NOT edit it — another item is editing that same file at the same time as you. Expect the working-tree copy to be mid-edit and possibly momentarily inconsistent; for any command that imports the module, import a pristine copy instead:
  mkdir -p "$TMPDIR/lfhead" && git show HEAD:lambda/take-action/lambda_function.py > "$TMPDIR/lfhead/lambda_function.py"
  TAKE_ACTION_SRC="$TMPDIR/lfhead" python -m pytest lambda/take-action/tests --collect-only -q

ENVIRONMENT (verified)
Python 3.11.5, pytest 9.0.2, boto3 1.42.70. moto is NOT installed and must not be used. Windows host; both Git Bash and PowerShell available.

SYSTEM UNDER TEST
lambda_function.py is a single-file Lambda that creates its clients at module level: `dynamodb = boto3.client("dynamodb")`, `ses = boto3.client("sesv2")` (~lines 79-80). Tests must monkeypatch `lambda_function.dynamodb` and `lambda_function.ses` with small in-process fakes that record calls and return canned responses in raw DynamoDB wire format ({'S':..},{'L':..},{'M':..},{'N':..}). Read the current code to get the exact call shapes right: get_flagged_emails/get_bounced_emails use dynamodb.scan with ProjectionExpression and ExpressionAttributeNames {'#st':'subtype'}; get_verified_representative_emails and already_sent use get_item; log_generation/log_send/record_bounce_event use put_item; the send uses ses.send_email (sesv2). handle_send takes a parsed body dict and returns the object produced by `respond(status, body)` — assert on that structure.

COVERAGE REQUIRED (one clearly-named test each, minimum)
(a) filter_excluded(officials, excluded) — case-insensitive; official with no email is kept; excluded=None returns input unchanged; inputs not mutated.
(b) get_bounced_emails pagination — fake scan returns LastEvaluatedKey on call 1 and omits it on call 2; both pages' addresses are in the result; ExclusiveStartKey was passed on call 2.
(c) get_bounced_emails classification — Bounce/Permanent included, Complaint included, Bounce/Transient excluded.
(d) record_bounce_event with a realistic SES bounce notification JSON fixture (bounce.bounceType='Permanent', bounceSubType, bouncedRecipients[].emailAddress, mail.destination, timestamps) — asserts a row is written with the expected key attributes.
(e) record_bounce_event sender-skip — when the bounced recipient equals SES_SENDER_EMAIL, put_item is NOT called.
(f) handle_send suppression — session has verified reps; one of them is in the bounced/flagged set; response failed list contains {email, reason:'suppressed'}; ses.send_email was never called with that address.
(g) handle_send ses_error — ses.send_email raises for one rep; that rep appears in failed with reason 'ses_error'; the other rep still sends.
(h) handle_send open-relay guard — a representative email absent from the session's stored representatives still produces HTTP 400 and no send. This is the security regression test; make its intent explicit in the test name and a comment.
(i) handle_send already_sent — a session with an existing sends row returns 409 and sends nothing.
(j) log_send item shape — asserts the put_item Item contains priorities (L of S), source (M), location_city, location_state, representatives_offered (N, = len of the generate row's representatives), representatives_failed (L of M with email/reason), alongside the pre-existing session_id, timestamp, constituent_email, location, representatives_sent, message_ids, ttl. Also assert that when the generate row has no source/location_city, those attributes are OMITTED rather than written empty.
(k) source sanitization — unknown key dropped; a 250-char value truncated to exactly 200; all-empty input yields no `source` attribute on the generate row.
(l) normalized_location — parsed from a fake Haiku response into location_city/location_state/location_country; and a fallback test where the field is absent and city/state come from parse_location with country 'US'.

STYLE CONSTRAINTS
- conftest.py must set env vars and sys.path BEFORE `import lambda_function`, and honour TAKE_ACTION_SRC as an override of the source directory (default: the repo's lambda/take-action).
- Do not reference symbols that do not exist yet at module import/collection time — put new-symbol references inside test bodies or fixtures. Collection must succeed against the pre-change HEAD source; individual tests failing at that point is expected and fine.
- Keep fakes small and local to tests/; do not add third-party dependencies.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
Collection against the pristine HEAD copy succeeds with zero errors and >=12 tests. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-write-HANDOFF.md listing every test name mapped to the contract clause (a)-(l) it covers, plus the raw `pytest --collect-only -q` output. State plainly in the handoff which tests you expect to FAIL until the implementation items land.

ACCEPTANCE CRITERIA:
- Directory C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ exists containing conftest.py and one or more test_*.py files.
- conftest.py inserts the Lambda source directory on sys.path BEFORE importing lambda_function, honouring an override env var TAKE_ACTION_SRC when set (default: the repo's lambda/take-action directory), and sets the env vars the module needs at import time (AWS_DEFAULT_REGION=us-east-2, dummy AWS credentials, DYNAMODB_TABLE/SEND_LOG_TABLE/BOUNCE_TABLE/FLAGGED_TABLE/BOOSTED_TABLE, SES_SENDER_EMAIL) so import never touches AWS.
- No test makes a network or AWS call: lambda_function.dynamodb and lambda_function.ses are monkeypatched with in-process fakes (or botocore.stub.Stubber). moto is NOT installed and must not be imported.
- Tests exist, named recognisably, covering every one of: (a) filter_excluded; (b) get_bounced_emails pagination — fake scan returns LastEvaluatedKey on the first page and not the second, both pages' rows appear in the result; (c) get_bounced_emails classification — Bounce/Permanent in, Complaint in, Bounce/Transient out; (d) record_bounce_event against a realistic SES bounce notification JSON fixture; (e) record_bounce_event sender-skip rule — email == SES_SENDER_EMAIL writes nothing; (f) handle_send suppression path — a rep in the excluded set lands in failed with reason 'suppressed' and ses.send_email is never called for it; (g) handle_send ses_error path; (h) handle_send open-relay rejection — an email not in the session's verified set still yields 400; (i) handle_send already_sent — 409; (j) log_send item shape including priorities, source, location_city, location_state, representatives_offered, representatives_failed; (k) source sanitization — unknown key dropped, >200 chars truncated, empty map omitted; (l) normalized_location parsing and its fallback when the field is absent.
- No module-level reference to a function that does not yet exist in lambda_function.py (new symbols may only be referenced inside test bodies or fixtures), so collection succeeds even against the pre-change source.
- Running collection against a pristine copy of git HEAD's lambda_function.py succeeds with zero collection errors and at least 12 collected tests.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- ls -la C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/
- cat C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/conftest.py
- grep -rn 'moto\|boto3.client(' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ || echo 'no moto, no direct client construction'
- cd C:/Users/aisaa/Projects/photometricsai-website && mkdir -p "$TMPDIR/lfhead" && git show HEAD:lambda/take-action/lambda_function.py > "$TMPDIR/lfhead/lambda_function.py" && TAKE_ACTION_SRC="$TMPDIR/lfhead" python -m pytest lambda/take-action/tests --collect-only -q
- cd C:/Users/aisaa/Projects/photometricsai-website && python -m pytest lambda/take-action/tests --collect-only -q | tail -5
- grep -rn 'def test_' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/

CONTEXT BUDGET: sized to use no more than ~35% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-write-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-write-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
