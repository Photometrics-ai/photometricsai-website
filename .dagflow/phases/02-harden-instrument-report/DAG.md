# Phase 02 DAG

Machine-readable copy: `plan.json`. Statuses updated by the lead after each scheduler run.

## Work Item: p2-exclusion-hardening

```yaml
id: "p2-exclusion-hardening"
kind: "implementation"
purpose: "Make a bounced or flagged address impossible to re-suggest (hard filter in handle_generate) and impossible to re-send (suppression in handle_send), paginate the exclusion scans, stop the sender address polluting the bounce table, and record what failed on the sends row."
hard_prereqs: []
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py"]
shared_resources: []
acceptance_criteria: ["A module-level pure function `filter_excluded(officials, excluded_emails) -> list` exists in lambda_function.py; it is case-insensitive on email, tolerates officials without an 'email' key (keeps them), tolerates excluded_emails being None or empty (returns the input list unchanged), and does not mutate its arguments.", "handle_generate applies filter_excluded to the search_officials result BEFORE call_claude is invoked, and prints a log line containing the count of officials dropped.", "get_bounced_emails and get_flagged_emails both paginate with LastEvaluatedKey (loop until absent). The existing Permanent/Complaint classification rule in get_bounced_emails is unchanged.", "record_bounce_event skips writing any row whose email equals SES_SENDER_EMAIL.lower() and prints a loud warning line instead of writing.", "handle_send computes `excluded = get_bounced_emails() | get_flagged_emails()`; any rep that passed the existing verification whose email.lower() is in excluded is appended to a failed list with reason 'suppressed' and ses.send_email is NOT called for it. SES exceptions produce reason 'ses_error'.", "get_verified_representative_emails (the open-relay guard) and already_sent are byte-for-byte unchanged, and their call sites in handle_send are unchanged in order and effect: an unverified email is still rejected 400 and a duplicate session still returns 409.", "log_send writes the new sends-row fields per the data contract: `priorities` (L of S), `source` (M), `location_city` (S), `location_state` (S) copied from the generate row via a single get_item, `representatives_offered` (N = len of the generate row's representatives list), `representatives_failed` (L of M with keys email/reason). Absent source/location on the generate row means the field is omitted, not written empty. Existing fields (session_id, timestamp, constituent_email, location, representatives_sent, message_ids, ttl) are unchanged.", "The /send response body gains a `failed` list of {email, reason} objects.", "No AWS write calls were made by this item; the file parses (ast.parse) and the working tree diff touches only lambda_function.py."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff --stat -- lambda/take-action/lambda_function.py", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U15 -- lambda/take-action/lambda_function.py", "python -c \"import ast;ast.parse(open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py',encoding='utf-8').read());print('SYNTAX OK')\"", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff -- lambda/take-action/lambda_function.py | grep -c 'LastEvaluatedKey'", "cd C:/Users/aisaa/Projects/photometricsai-website && git show HEAD:lambda/take-action/lambda_function.py > /tmp/head_lf.py && python - <<'PY'\nimport re\nold=open('/tmp/head_lf.py',encoding='utf-8').read()\nnew=open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py',encoding='utf-8').read()\ndef body(src,name):\n    m=re.search(r'\\ndef '+name+r'\\(.*?(?=\\ndef )',src,re.S)\n    return m.group(0) if m else None\nfor fn in ('get_verified_representative_emails','already_sent'):\n    print(fn,'UNCHANGED' if body(old,fn)==body(new,fn) else 'CHANGED <-- INSPECT')\nPY", "AWS_DEFAULT_REGION=us-east-2 AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x python -c \"import sys;sys.path.insert(0,r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action');import lambda_function as lf;print(lf.filter_excluded([{'email':'A@x.com','name':'a'},{'email':'b@x.com'},{'name':'no-email'}],{'a@x.com'}));print(lf.filter_excluded([{'email':'b@x.com'}],None))\"", "grep -n 'SES_SENDER_EMAIL' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py"]
downstream: ["p2-source-and-location"]
context_budget_pct: 35
max_correction_rounds: 2
security_critical: true
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "opus"
verifier_effort: "high"
model_rationale: "Lambda code item per MODEL-TIERING guidance (sonnet/high implementer, opus/high verifier). It edits handle_send and the suppression path, so security_critical=true forces an opus verifier that must independently confirm the open-relay guard and already_sent are untouched — a judgment call an implementer summary cannot substitute for."
status: "done"
```

**Assignment brief:**

OBJECTIVE
Harden the Take Action Lambda so a hard-bounced or user-flagged official address can neither be re-suggested by /generate nor be mailed by /send, and so the sends row records what was offered and what failed. You are editing production Lambda source in the working tree only; the lead deploys and commits.

REPO / FILE
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own exactly one file: C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py (~1175 lines, single-file Python 3.x Lambda, boto3 clients created at module level: `dynamodb = boto3.client("dynamodb")` and `ses = boto3.client("sesv2")` around line 79-80). Do not create, edit or delete any other file except your handoff.

Current landmarks (line numbers approximate, re-grep them): get_flagged_emails :847, get_bounced_emails :864, get_verified_representative_emails :890, already_sent :919, log_send :947, handle_send :969, record_bounce_event :1069, handle_generate :757, search_officials :202, log_generation :706. The Lambda routes by rawPath suffix (/generate, /send, /track, /flag) plus an SNS branch.

REQUIRED READING
- The file itself, at least: get_flagged_emails, get_bounced_emails, get_verified_representative_emails, already_sent, log_send, handle_send, record_bounce_event, handle_generate.
- .dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md (section on the bounce table; note that take-action@photometrics.ai has 6 self-bounce rows — that is exactly what sub-task 3 stops recurring).

WHAT TO IMPLEMENT
1. Pure function `filter_excluded(officials, excluded_emails) -> list`. Module-level, no I/O, no globals. Case-insensitive comparison on the official's 'email' value. An official dict with no email or an empty email is KEPT (there is nothing to exclude on). excluded_emails may be None or empty -> return the list unchanged. Must not mutate the input list or its dicts.
2. In handle_generate, apply filter_excluded to the officials returned by search_officials BEFORE call_claude is invoked, using the same excluded set the code already computes for the prompt (flagged ∪ bounced). Print a log line that includes the number dropped, e.g. `print(f"Hard filter dropped {n} excluded officials")`.
3. Paginate the scans in get_bounced_emails and get_flagged_emails: loop on LastEvaluatedKey, passing ExclusiveStartKey, until the key is absent. Keep the existing ProjectionExpression and ExpressionAttributeNames ("subtype" is a DynamoDB reserved word — keep the #st alias). Keep the existing classification rule exactly: an address is bounced iff event_type == "Complaint" or (event_type == "Bounce" and subtype == "Permanent"). Transient bounces stay excluded from the set. Keep the try/except so a scan failure still returns a set rather than raising.
4. record_bounce_event: if the bouncing recipient's email, lowercased, equals SES_SENDER_EMAIL.lower(), do NOT write the row — print a loud warning instead (e.g. `print(f"WARNING: bounce for sender address {email} — not recording")`) and continue with the remaining recipients.
5. handle_send: after the existing verification produces the list of verified reps, compute `excluded = get_bounced_emails() | get_flagged_emails()`. Any verified rep whose email.lower() is in `excluded` is appended to a `failed` list as {"email": <email>, "reason": "suppressed"} and is NOT passed to ses.send_email. Any rep whose SES send raises appends {"email": <email>, "reason": "ses_error"}. The response body gains `failed`: the list of {email, reason}. Keep whatever failed_count/other response fields already exist.
6. log_send: fetch the generate row once (dynamodb.get_item on DYNAMO_TABLE with key session_id) and write the new sends-row fields per the DATA CONTRACT below. One get_item, not one per field. If the generate row is missing or a field is absent, omit that attribute entirely rather than writing an empty string/list/map (DynamoDB rejects empty S anyway). log_send's signature may gain parameters (e.g. representatives_failed) — update its call site in handle_send accordingly.

HARD CONSTRAINTS
- get_verified_representative_emails (the open-relay guard) and already_sent must remain byte-for-byte unchanged, and their call sites in handle_send must remain in the same order with the same effect. An unverified email must still produce 400; a second send for the same session must still produce 409. A verifier will diff these function bodies against git HEAD and will read the handle_send diff specifically looking for a weakened guard. Suppression is an ADDITIONAL filter layered after verification, never a replacement for it.
- Do not change search_officials' prompt, call_claude, or anything in the letter-generation path — a separate item owns that.
- Do not run /generate, do not send any email, do not deploy, do not make any AWS write call. Read-only AWS calls are unnecessary for this item; you should need none at all.

DATA CONTRACT (sends row — photometrics-take-action-sends, PK session_id) — new attributes:
- `priorities` (L of S) copied from the generate row
- `source` (M of S) copied from the generate row
- `location_city` (S), `location_state` (S) copied from the generate row
- `representatives_offered` (N) = len(generate row's `representatives` list)
- `representatives_failed` (L of M) each {email: S, reason: S} where reason ∈ {'suppressed','ses_error'}
Existing attributes unchanged. Note the generate row will only start carrying `source`/`location_city`/`location_state` after the next item lands — your code must behave correctly (omit the attribute) when they are absent, which is the case for all 118 existing rows.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
All acceptance criteria met; `python -c "import ast;ast.parse(open(path).read())"` clean; `git status --porcelain` shows lambda_function.py modified and nothing else outside .dagflow; handoff written to .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md containing the full `git diff -U15` of your change, the exact new log lines you added, and an explicit statement (with the diff evidence) that the open-relay guard and already_sent are unchanged.

---

## Work Item: p2-source-and-location

```yaml
id: "p2-source-and-location"
kind: "implementation"
purpose: "Store campaign attribution (`source` map) and a normalized city/state/country on the generate row, including asking Haiku for normalized_location, so the report tool can group sessions by ad group, keyword and place."
hard_prereqs: ["p2-exclusion-hardening"]
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py"]
shared_resources: []
acceptance_criteria: ["handle_generate reads body['source'], accepts only the 9 contract keys (utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer), drops unknown keys, coerces values to str, truncates each to 200 chars, omits keys whose value is empty after sanitization, and omits the whole `source` attribute when the resulting map is empty or the request had no source.", "The generate row written by log_generation carries `source` (M of S) when non-empty, and `location_city` (S), `location_state` (S), `location_country` (S) when non-empty.", "search_officials' Haiku prompt and JSON/tool schema request a `normalized_location` object with keys city, state (2-letter US code when US), country (ISO-2); the response parser reads it if present.", "Fallback is robust: if normalized_location is absent, unparseable, or partially empty, city/state fall back to parse_location(location) and country falls back to 'US'. A missing field never raises and never blocks letter generation.", "call_claude and the letter prompt are unchanged; the officials-search behaviour (which officials are returned, and the hard filter added by p2-exclusion-hardening) is unchanged.", "The file parses (ast.parse) and the working-tree diff touches only lambda_function.py.", "No AWS calls, no /generate call, no deploy."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U15 -- lambda/take-action/lambda_function.py", "python -c \"import ast;ast.parse(open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py',encoding='utf-8').read());print('SYNTAX OK')\"", "grep -n 'normalized_location\\|location_city\\|location_state\\|location_country' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py", "cd C:/Users/aisaa/Projects/photometricsai-website && python - <<'PY'\nimport re,subprocess\nnew=open(r'lambda/take-action/lambda_function.py',encoding='utf-8').read()\nold=subprocess.run(['git','show','HEAD:lambda/take-action/lambda_function.py'],capture_output=True,text=True).stdout\ndef body(src,name):\n    m=re.search(r'\\ndef '+name+r'\\(.*?(?=\\ndef )',src,re.S)\n    return m.group(0) if m else None\nfor fn in ('call_claude','get_verified_representative_emails','already_sent'):\n    print(fn,'UNCHANGED vs HEAD' if body(old,fn)==body(new,fn) else 'CHANGED <-- INSPECT')\nPY", "AWS_DEFAULT_REGION=us-east-2 AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x python -c \"import sys;sys.path.insert(0,r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action');import lambda_function as lf;print([n for n in dir(lf) if 'source' in n.lower() or 'normal' in n.lower()])\""]
downstream: ["p2-unit-tests-run", "p2-deploy"]
context_budget_pct: 30
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "opus"
verifier_effort: "high"
model_rationale: "Lambda code item per MODEL-TIERING guidance (sonnet/high implementer, opus/high verifier). Not security_critical — no authorization surface — but the opus verifier is retained because a malformed Haiku prompt/schema edit breaks production /generate for every visitor and cannot be re-tested cheaply (the phase allows only 2 /generate calls), so the verification is a careful static read rather than a re-run."
status: "running"
```

**Assignment brief:**

OBJECTIVE
Add campaign attribution and a normalized location to the Take Action generate row, so every session can later be attributed to an ad group / keyword / city.

REPO / FILE
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own exactly one file: C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py. Do not edit any other file except your handoff.

REQUIRED READING (in order)
1. .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md — the immediately preceding change to this same file. Your edit builds on it; do not revert or reflow any of it.
2. lambda_function.py: handle_generate (~:757), log_generation (~:706), search_officials (~:202, ~220 lines including the Haiku prompt and its JSON/tool schema; the model response JSON is parsed around :380-425), parse_location (~:194), sanitize_string (~:97).

WHAT TO IMPLEMENT
1. `source` capture. handle_generate accepts body['source'] as a dict. Sanitize per contract (below) and pass it through to log_generation so it lands on the generate row as a DynamoDB map of strings. Prefer a small dedicated helper (e.g. `sanitize_source(raw) -> dict`) so it is unit-testable in isolation — a sibling item's pytest suite will import and exercise it.
2. `normalized_location`. Extend the existing Haiku prompt and its JSON/tool schema in search_officials so the model also returns `normalized_location: {"city": str, "state": str, "country": str}` — state as the 2-letter US postal code when the location is in the US, country as an ISO-2 code. Read the current prompt and schema carefully and keep the change MINIMAL: add the field, describe it in one or two sentences, do not restructure the prompt, do not rename existing fields, do not change what officials the model is asked for.
3. Parse it where the model JSON is already parsed. Return/propagate city/state/country to handle_generate and store them on the generate row as `location_city`, `location_state`, `location_country`. Fallback chain, and it must never raise: if `normalized_location` is missing or not a dict, or a field is empty/whitespace, fall back to parse_location(location) for city and state and to 'US' for country. Sanitize each to a sane length (<=100). Omit any attribute that is still empty (DynamoDB rejects empty S).

HARD CONSTRAINTS
- Nothing in the LETTER prompt (call_claude) changes. A verifier diffs call_claude against git HEAD and expects it identical.
- Do not touch handle_send, log_send, get_verified_representative_emails, already_sent, or the exclusion functions — the previous item just changed those and its work must survive your edit intact.
- Do NOT call /generate to test. The phase budget is 2 /generate calls total and both are reserved for another item. Verify statically and by exercising your pure helpers offline (`AWS_DEFAULT_REGION=us-east-2 AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x python -c "import sys;sys.path.insert(0,'lambda/take-action');import lambda_function as lf; ..."` — module import creates boto3 clients but makes no network calls).
- Do not deploy. Do not make AWS write calls.

DATA CONTRACT (generate row — photometrics-take-action, PK session_id) — new attributes:
- `source` (M): string keys utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer. Each value sanitized to <=200 chars. Absent/empty keys omitted. Whole map omitted if empty. Unknown keys dropped.
- `location_city` (S), `location_state` (S, 2-letter US code when US), `location_country` (S, ISO-2).
Existing fields unchanged.
Context you do not need to implement: the frontend sends this `source` object in the /generate payload (another item), and Google Ads will populate utm_content with a numeric ad group id.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
All acceptance criteria met; ast.parse clean; handoff at .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md containing the full diff, the before/after text of the Haiku prompt fragment and schema you changed (quoted verbatim), and the output of an offline exercise of your sanitizer showing: unknown key dropped, 250-char value truncated to 200, empty map omitted, and normalized_location fallback producing city/state from parse_location plus country 'US'.

---

## Work Item: p2-unit-tests-write

```yaml
id: "p2-unit-tests-write"
kind: "test"
purpose: "Write the pytest suite for the hardened send path, exclusion, bounce recording, source sanitization and normalized-location parsing — authored against the fixed data contract so it can be built in parallel with the Lambda changes rather than after them."
hard_prereqs: []
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/"]
shared_resources: []
acceptance_criteria: ["Directory C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ exists containing conftest.py and one or more test_*.py files.", "conftest.py inserts the Lambda source directory on sys.path BEFORE importing lambda_function, honouring an override env var TAKE_ACTION_SRC when set (default: the repo's lambda/take-action directory), and sets the env vars the module needs at import time (AWS_DEFAULT_REGION=us-east-2, dummy AWS credentials, DYNAMODB_TABLE/SEND_LOG_TABLE/BOUNCE_TABLE/FLAGGED_TABLE/BOOSTED_TABLE, SES_SENDER_EMAIL) so import never touches AWS.", "No test makes a network or AWS call: lambda_function.dynamodb and lambda_function.ses are monkeypatched with in-process fakes (or botocore.stub.Stubber). moto is NOT installed and must not be imported.", "Tests exist, named recognisably, covering every one of: (a) filter_excluded; (b) get_bounced_emails pagination — fake scan returns LastEvaluatedKey on the first page and not the second, both pages' rows appear in the result; (c) get_bounced_emails classification — Bounce/Permanent in, Complaint in, Bounce/Transient out; (d) record_bounce_event against a realistic SES bounce notification JSON fixture; (e) record_bounce_event sender-skip rule — email == SES_SENDER_EMAIL writes nothing; (f) handle_send suppression path — a rep in the excluded set lands in failed with reason 'suppressed' and ses.send_email is never called for it; (g) handle_send ses_error path; (h) handle_send open-relay rejection — an email not in the session's verified set still yields 400; (i) handle_send already_sent — 409; (j) log_send item shape including priorities, source, location_city, location_state, representatives_offered, representatives_failed; (k) source sanitization — unknown key dropped, >200 chars truncated, empty map omitted; (l) normalized_location parsing and its fallback when the field is absent.", "No module-level reference to a function that does not yet exist in lambda_function.py (new symbols may only be referenced inside test bodies or fixtures), so collection succeeds even against the pre-change source.", "Running collection against a pristine copy of git HEAD's lambda_function.py succeeds with zero collection errors and at least 12 collected tests."]
verification_commands: ["ls -la C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/", "cat C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/conftest.py", "grep -rn 'moto\\|boto3.client(' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ || echo 'no moto, no direct client construction'", "cd C:/Users/aisaa/Projects/photometricsai-website && mkdir -p \"$TMPDIR/lfhead\" && git show HEAD:lambda/take-action/lambda_function.py > \"$TMPDIR/lfhead/lambda_function.py\" && TAKE_ACTION_SRC=\"$TMPDIR/lfhead\" python -m pytest lambda/take-action/tests --collect-only -q", "cd C:/Users/aisaa/Projects/photometricsai-website && python -m pytest lambda/take-action/tests --collect-only -q | tail -5", "grep -rn 'def test_' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/"]
downstream: ["p2-unit-tests-run"]
context_budget_pct: 35
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "sonnet"
verifier_effort: "high"
model_rationale: "Test-authoring against a written contract with mechanical acceptance (collection succeeds against a pristine HEAD copy, named tests exist for each contract area) — sonnet/high on both sides matches the MODEL-TIERING guidance for tooling/scripts. The judgment about whether the tests actually assert the right security behaviour is exercised again at run time by p2-unit-tests-run, which carries an opus verifier."
status: "done"
```

**Assignment brief:**

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

---

## Work Item: p2-unit-tests-run

```yaml
id: "p2-unit-tests-run"
kind: "test"
purpose: "Run the pytest suite against the implemented Lambda source and get it fully green — the gate that must pass before anything is deployed to production."
hard_prereqs: ["p2-source-and-location", "p2-unit-tests-write"]
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/", "C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py"]
shared_resources: []
acceptance_criteria: ["`python -m pytest lambda/take-action/tests -q` from the repo root exits 0 with zero failures, zero errors, and at least 12 tests passing.", "The run made no AWS or network calls (evidenced by the fakes being in place and by the suite passing with bogus credentials in the environment).", "Every contract area (a)-(l) listed in p2-unit-tests-write-HANDOFF.md still has a passing test; no test was deleted, skipped, xfailed, or reduced to a tautology to make the suite green. Any test that was legitimately corrected is listed in the handoff with a before/after of the assertion and the reason.", "If lambda_function.py was modified, the change is minimal, is described line-by-line in the handoff with its diff, and does NOT weaken get_verified_representative_emails, already_sent, or the suppression check in handle_send. Any defect found in that authorization path is REPORTED, not patched.", "`git status --porcelain` shows changes confined to lambda/take-action/tests/, lambda/take-action/lambda_function.py, and .dagflow/."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus AWS_DEFAULT_REGION=us-east-2 python -m pytest lambda/take-action/tests -q", "cd C:/Users/aisaa/Projects/photometricsai-website && python -m pytest lambda/take-action/tests -q --tb=short | tail -20", "grep -rn 'skip\\|xfail\\|pytest.mark' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ || echo 'no skips/xfails'", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff --stat", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U15 -- lambda/take-action/lambda_function.py | grep -n -A15 -B5 'verified_emails\\|already_sent\\|suppressed' | head -80", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff -- lambda/take-action/tests/"]
downstream: ["p2-deploy"]
context_budget_pct: 25
max_correction_rounds: 2
security_critical: true
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "opus"
verifier_effort: "high"
model_rationale: "Deviates upward from the sonnet/high verifier that MODEL-TIERING suggests for test items: this item is permitted to make minimal fixes to lambda_function.py when a test exposes a real defect, so its diff can touch the send path. Marked security_critical and given an opus/high verifier, which must re-run pytest itself AND diff lambda_function.py against the p2-source-and-location state to confirm no test was weakened to pass and no guard was loosened."
status: "pending"
```

**Assignment brief:**

OBJECTIVE
Get the Take Action unit test suite fully green against the implemented Lambda source. This is the gate in front of the production deploy: if it is not honestly green, nothing ships.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/tests/ (free to edit) and lambda/take-action/lambda_function.py (edit ONLY under the narrow allowance below). Nothing else.

REQUIRED READING
- .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-write-HANDOFF.md — the test-to-contract map (a)-(l) and which tests were expected to fail before the implementation landed.
- .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md

WHAT TO DO
1. Run `python -m pytest lambda/take-action/tests -q` from the repo root. Capture raw output.
2. For each failure, decide honestly which side is wrong:
   - Test wrong (fake shaped incorrectly, wrong expected key name, wrong wire format): fix the test. Record before/after of the assertion and why in the handoff.
   - Implementation wrong, OUTSIDE the authorization path: you may make a minimal fix to lambda_function.py. Keep it surgical; show the diff in the handoff.
   - Implementation wrong INSIDE the authorization path (get_verified_representative_emails, already_sent, or the suppression/failed-reason logic in handle_send): do NOT patch it. Stop, and report it in the handoff as a blocking finding with the exact failing assertion and your diagnosis. The lead will schedule a repair.
3. Re-run until green. Confirm the suite passes with bogus AWS credentials in the environment, proving no test touches AWS.

FORBIDDEN
- Do not delete, skip, xfail, loosen or tautologise a test to make the suite green. A verifier greps for skip/xfail markers and diffs lambda/take-action/tests/.
- Do not weaken any guard. The open-relay test (an unverified representative email must still produce 400) and the already_sent 409 test must pass on their original assertions.
- Do not deploy, do not call /generate, do not send email, do not make AWS write calls.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
pytest exits 0 with >=12 passing and 0 skipped. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md containing: the final raw pytest output (verbose enough to show every test name), a table of every change you made (file, what, why), the full diff of any lambda_function.py edit, and an explicit statement that no test was skipped or weakened.

---

## Work Item: p2-deploy-script

```yaml
id: "p2-deploy-script"
kind: "implementation"
purpose: "Replace the manual zip-and-update-function-code ritual with a repeatable, verifying deploy script, so every future deploy proves the running CodeSha256 equals the artifact that was built."
hard_prereqs: []
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh", "C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip"]
shared_resources: []
acceptance_criteria: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh exists, is a bash script, and runs under Git Bash on this Windows host.", "`bash lambda/take-action/deploy.sh --dry-run` prints every command it would run, makes ZERO AWS calls, creates/modifies no files, and exits 0 — including with no or bogus AWS credentials in the environment.", "The script cds to its own directory (derived from $0, not a hardcoded absolute path or the caller's cwd) and packages ONLY lambda_function.py at the archive root.", "Packaging works on this host where the `zip` binary is ABSENT: the script detects that and falls back to `python -c` using the zipfile module, producing function.zip with lambda_function.py at the archive root.", "Real (non-dry-run) mode runs, in order: package -> `aws lambda update-function-code --function-name photometrics-take-action --region us-east-2 --zip-file fileb://function.zip` -> `aws lambda wait function-updated --function-name photometrics-take-action --region us-east-2` -> compute `openssl dgst -sha256 -binary function.zip | base64` -> `aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text` -> compare, print both values, and exit non-zero on mismatch.", "The script sets AWS_PAGER='' , uses `set -euo pipefail`, and prints the final CodeSha256 on success.", "Nothing in the script deploys anything else, changes function configuration, environment variables, IAM, or SES."]
verification_commands: ["cat C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh", "cd C:/Users/aisaa/Projects/photometricsai-website && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus bash lambda/take-action/deploy.sh --dry-run; echo \"exit=$?\"", "cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain lambda/take-action/", "cd /tmp && bash C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh --dry-run; echo \"cwd-independent exit=$?\"", "grep -n 'update-function-configuration\\|iam\\|sesv2\\|put-\\|delete-' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh || echo 'no config/IAM/SES/destructive commands'", "command -v zip || echo 'zip absent as expected — python fallback must be present'", "grep -n 'zipfile\\|command -v zip' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh"]
downstream: ["p2-deploy"]
context_budget_pct: 15
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "sonnet"
verifier_effort: "high"
model_rationale: "Tooling/script item — MODEL-TIERING guidance is sonnet/high implementer with sonnet/high verifier. Acceptance is fully mechanical (--dry-run exits 0 and makes zero AWS calls; the script is readable in one pass) so no stronger tier is warranted."
status: "done"
```

**Assignment brief:**

OBJECTIVE
Write a repeatable, self-verifying deploy script for the Take Action Lambda. Deploying is currently manual (zip lambda_function.py, aws lambda update-function-code), with no proof that what is running equals what was built.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/deploy.sh (new) and lambda/take-action/function.zip (the build artifact — only if you produce one; see below). Nothing else. In particular do NOT edit lambda_function.py — another item is editing it concurrently.

TARGET (verified)
Function: photometrics-take-action, region us-east-2, account 794038225197, role photometrics-take-action-lambda-role. Source: lambda/take-action/lambda_function.py, a single file with no third-party deps to bundle. Currently deployed CodeSha256: vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=.

HOST FACTS (verified on this machine — do not assume otherwise)
- Git Bash is the shell; `zip` is NOT installed. `openssl` (/mingw64/bin/openssl), `base64` (/usr/bin/base64), `python` 3.11.5, and `aws` (v2.18.6) ARE installed.
- Therefore the python zipfile fallback is the path that will actually execute here. Test that path, not just the `zip` branch.

SCRIPT REQUIREMENTS
1. `set -euo pipefail`; export AWS_PAGER=''.
2. cd to the script's own directory, derived from "$0" (e.g. `cd "$(dirname "$0")"`), so it works from any cwd.
3. Package: prefer `zip -j function.zip lambda_function.py` when `command -v zip` succeeds; otherwise `python -c` with the zipfile module writing lambda_function.py at the archive root (arcname 'lambda_function.py', no directory prefix — Lambda will not find the handler otherwise).
4. `aws lambda update-function-code --function-name photometrics-take-action --region us-east-2 --zip-file fileb://function.zip`
5. `aws lambda wait function-updated --function-name photometrics-take-action --region us-east-2`
6. Compute `LOCAL=$(openssl dgst -sha256 -binary function.zip | base64)`; read `REMOTE=$(aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text)`; print both; exit non-zero with a clear message on mismatch; print the CodeSha256 on success.
7. `--dry-run` flag: print every command that would run, make zero AWS calls, create or modify no files, exit 0. It must work with bogus/absent credentials.
8. Accept an optional `--function-name` override defaulting to photometrics-take-action, but keep the region pinned to us-east-2.

HARD CONSTRAINTS
- Do NOT run a real deploy from this item. A separate integration item does that, and Ari's pre-authorization for production deploys is scoped to that item. Test only with --dry-run.
- The script must never call update-function-configuration, touch environment variables, IAM, SES, or Google Ads/GA4.
- Do not edit lambda_function.py or generate a real function.zip in this item (a stale artifact would confuse the deploy item). If you build a zip while testing the packaging fallback, build it into a scratch directory, not into lambda/take-action/.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
deploy.sh exists and `bash lambda/take-action/deploy.sh --dry-run` exits 0 from at least two different working directories with bogus credentials, printing the full command plan. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md with the full script text, the raw --dry-run output, and evidence (raw output) that the python zipfile fallback produces an archive whose only member is 'lambda_function.py' at the root — built in a scratch directory.

---

## Work Item: p2-deploy

```yaml
id: "p2-deploy"
kind: "integration"
purpose: "Put the hardened, instrumented Lambda into production and prove the running code is exactly the built artifact and that it initialises and serves without error."
hard_prereqs: ["p2-source-and-location", "p2-unit-tests-run", "p2-deploy-script"]
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip"]
shared_resources: ["aws:lambda:photometrics-take-action"]
acceptance_criteria: ["`bash lambda/take-action/deploy.sh` ran to completion and exited 0 against function photometrics-take-action in us-east-2.", "The local artifact hash (`openssl dgst -sha256 -binary function.zip | base64`) equals the deployed CodeSha256 reported by `aws lambda get-function-configuration`, and the new CodeSha256 differs from the pre-deploy value vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=.", "The new CodeSha256 is recorded verbatim in the handoff.", "A read-only smoke invoke succeeded: a synthetic Function-URL /send event with a non-existent session_id 'test-smoke-<epoch>' returns HTTP 400 ('couldn't verify this session'), proving the new module imports and the send path runs. No email was sent and no row was written.", "A CloudWatch scan of /aws/lambda/photometrics-take-action covering the deploy window shows no ERROR, no 'Unable to import module', no 'Task timed out', and no unhandled exception; the raw filter-log-events output is pasted in the handoff.", "Nothing other than the function code changed: no update-function-configuration, no env var, IAM, SES, GA4 or Google Ads change."]
verification_commands: ["AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus,Runtime,Role]' --output text", "cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action && openssl dgst -sha256 -binary function.zip | base64", "MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c \"import time;print(int(time.time()*1000)-3600000)\") --filter-pattern 'ERROR' --max-items 50 --output json", "MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c \"import time;print(int(time.time()*1000)-3600000)\") --filter-pattern 'Unable to import module' --max-items 20 --output json", "cd C:/Users/aisaa/Projects/photometricsai-website && python -c \"import zipfile;z=zipfile.ZipFile('lambda/take-action/function.zip');print(z.namelist())\"", "cd C:/Users/aisaa/Projects/photometricsai-website && python -c \"import zipfile,hashlib;z=zipfile.ZipFile('lambda/take-action/function.zip');a=z.read('lambda_function.py');b=open('lambda/take-action/lambda_function.py','rb').read();print('ZIP MATCHES WORKING TREE' if a==b else 'MISMATCH')\""]
downstream: ["p2-harness-run", "p2-live-generate-check", "p2-docs"]
context_budget_pct: 20
max_correction_rounds: 1
security_critical: true
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "opus"
verifier_effort: "high"
model_rationale: "Deviates upward from the sonnet verifier MODEL-TIERING suggests for scripted/mechanical work: this is the item that makes the authorization change live in production. security_critical=true and an opus/high verifier, which independently re-reads CodeSha256 from AWS and re-runs the CloudWatch window rather than trusting the handoff. The implementer's own work is mechanical, so sonnet/high suffices there."
status: "pending"
```

**Assignment brief:**

OBJECTIVE
Deploy the hardened Take Action Lambda to production and prove the deploy landed cleanly.

AUTHORIZATION
Production Lambda deploys are PRE-AUTHORIZED by Ari for this phase (2026-09-03). This item is the one authorized to deploy. You do NOT need to stop and ask. You may not change anything else: no function configuration, no environment variables, no IAM, no SES, no GA4, no Google Ads.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/function.zip (the build artifact deploy.sh produces). Do not edit lambda_function.py, deploy.sh, tests/, or anything else.
Shared resource: aws:lambda:photometrics-take-action — you are the only item touching the function during your run.

REQUIRED READING
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md (how deploy.sh works, incl. the python zipfile fallback — `zip` is not installed on this host)
- .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md (confirm the suite is green before you ship)
- .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md and p2-source-and-location-HANDOFF.md (what is going live)

PRE-FLIGHT (do these first, abort if any fails)
1. Re-run `python -m pytest lambda/take-action/tests -q` from the repo root yourself. If it is not green, STOP and report — do not deploy.
2. `python -c "import ast;ast.parse(open('lambda/take-action/lambda_function.py',encoding='utf-8').read())"`.
3. Record the pre-deploy state: `AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus]' --output text`. Expected pre-deploy CodeSha256: vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=.

DEPLOY
4. `bash lambda/take-action/deploy.sh` (real run). Capture full raw output. If deploy.sh exits non-zero on the sha comparison, STOP and report — do not hand-patch around it.
5. Confirm the zip contains exactly lambda_function.py at the archive root and that its bytes equal the working-tree file.

POST-DEPLOY CHECKS
6. Smoke invoke, read-only: `aws lambda invoke` with a synthetic Function-URL event for rawPath '/send' whose body has session_id 'test-smoke-<epoch>' (a session that does not exist), a valid-looking constituent email, a non-empty letter, and one simulator representative address. Expect HTTP 400 with the 'couldn't verify this session' error — that proves the module imported and the send path executed. It writes nothing and mails nothing. Paste the raw response payload. Do NOT invoke /generate (Anthropic tokens; the phase budget is reserved for another item).
7. CloudWatch: `MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time <now-5min in ms> --output json`. Scan for ERROR, 'Unable to import module', 'Task timed out', tracebacks. Paste the raw output (redact nothing except any accidental secret; if a log line would expose ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY, do not paste that line and say so).
8. Record the new CodeSha256 verbatim — the next items and the docs item depend on it.

NOTE ON SCOPE
The end-to-end harness run and its own CloudWatch window are a separate downstream item (p2-harness-run); do not attempt to run the harness here.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md containing: pre-deploy and post-deploy CodeSha256 (both verbatim), the local artifact base64 sha256, the full raw deploy.sh output, the raw smoke-invoke response, the raw CloudWatch output for the deploy window, and a one-line statement that no configuration/IAM/SES change was made.

---

## Work Item: p2-harness-extend

```yaml
id: "p2-harness-extend"
kind: "implementation"
purpose: "Extend the funnel test harness with attribution/location seeding and a check-regenerate subcommand that proves a hard-bounced address is suppressed on send — authored ahead of the deploy so only the run itself waits on production."
hard_prereqs: []
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py", "C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/README.md"]
shared_resources: []
acceptance_criteria: ["funnel_test.py's `seed` writes a `source` map (contract keys) and `location_city`/`location_state`/`location_country` on the seeded generate row, in addition to everything it already wrote.", "A new subcommand `check-regenerate` exists and is listed in `--help` and in the `all` sequence.", "check-regenerate: (a) seeds a Permanent bounce row for dead.official@simulator.amazonses.com in photometrics-email-bounces (key schema email + timestamp) AND a matching row in photometrics-boosted-officials for region 'Austin, TX' using that table's ACTUAL key schema, discovered at runtime or documented from `aws dynamodb describe-table`; (b) adds dead.official@simulator.amazonses.com to the seeded generate row's representatives so it passes the open-relay guard; (c) invokes /send for the seeded session including that address; (d) asserts the response reports failed_count 1 with reason 'suppressed' for that address, and that ses did not mail it; (e) asserts the sends row contains representatives_failed (with the suppressed entry), representatives_offered, priorities, source, and location_city; (f) exits non-zero on any assertion failure.", "`cleanup` deletes everything check-regenerate created, including the bounce row and the boosted-officials row, and the existing cleanup behaviour is preserved.", "The harness still never calls /generate — grep confirms no '/generate' invocation path.", "All representative addresses remain SES mailbox-simulator addresses; the only real address anywhere is the --cc-email default ari@sdgis.com.", "`python funnel_test.py --dry-run all` prints the full plan including the new check-regenerate step, makes ZERO AWS calls, and exits 0 (works with bogus credentials).", "tools/README.md documents the new seed fields, the new subcommand, its assertions, and its cleanup.", "The pre-existing rows test-gap-framing-001 and test-gap-framing-004 are never targeted by any seed or cleanup path (cleanup must key off this run's own session_id / a test- prefix scoped to rows it created)."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python funnel_test.py --help", "cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus AWS_DEFAULT_REGION=us-east-2 python funnel_test.py --dry-run all; echo \"exit=$?\"", "cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus python funnel_test.py --dry-run check-regenerate; echo \"exit=$?\"", "grep -n 'generate' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py | grep -v 'check-regenerate\\|check_regenerate\\|regenerate' | head -20", "grep -n '@' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py | grep -v simulator.amazonses.com | head -20", "grep -n 'test-gap-framing' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py || echo 'no reference to pre-existing rows (good)'", "AWS_PAGER='' aws dynamodb describe-table --table-name photometrics-boosted-officials --region us-east-2 --query 'Table.KeySchema' --output json", "cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain lambda/take-action/tools/"]
downstream: ["p2-harness-run"]
context_budget_pct: 35
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "sonnet"
verifier_effort: "high"
model_rationale: "Harness/tooling item — MODEL-TIERING guidance is sonnet/high both sides, and Phase 01's harness build ran clean at that tier. Acceptance is mechanical (--dry-run makes zero AWS calls and prints the full plan; describe-table output is pasted). The security judgement lives in p2-harness-run, which asserts against production and carries an opus verifier."
status: "done"
```

**Assignment brief:**

OBJECTIVE
Extend the existing funnel test harness so it (a) seeds attribution + normalized location per the new data contract and (b) can prove, end to end against production, that a hard-bounced address is refused at send time with reason 'suppressed'. You WRITE the extension here; a separate downstream item runs it against production after the deploy.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/tools/funnel_test.py and lambda/take-action/tools/README.md. Nothing else — in particular do NOT edit lambda_function.py (a concurrent item owns it).

REQUIRED READING
- lambda/take-action/tools/funnel_test.py (existing, ~600 lines: subcommands seed | send | wait-bounce | check-sends | check-exclusion | cleanup | all, a JSON state file .funnel_test_state.json beside the script, dynamo_serialize/to_python helpers, a get_bounced_emails_paginated replica, and a --dry-run mode that makes zero AWS calls).
- lambda/take-action/tools/README.md (safety rules — keep them true).
- .dagflow/phases/01-verify-funnel/items/p1-harness-build-HANDOFF.md and p1-harness-run-HANDOFF.md (design intent and the last production run).

WHAT TO IMPLEMENT
1. `seed` additionally writes on the generate row: `source` (M) with contract keys — use recognisable test values, e.g. utm_source='google', utm_medium='cpc', utm_campaign='TESTCAMP', utm_content='TBD-1', utm_term='streetlight safety', utm_match='p', gclid='TESTGCLID', landed_priorities='Transportation Safety', referrer='https://www.google.com/' — plus `location_city`='Austin', `location_state`='TX', `location_country`='US'. Keep everything it already writes.
2. New subcommand `check-regenerate`, added to `--help` and inserted into the `all` sequence (before cleanup):
   a. Seed a Permanent bounce row for dead.official@simulator.amazonses.com into photometrics-email-bounces (key schema: email + timestamp) with event_type='Bounce', subtype='Permanent', shaped like the rows record_bounce_event writes.
   b. Seed a matching row into photometrics-boosted-officials for region 'Austin, TX'. Discover that table's key schema with `aws dynamodb describe-table --table-name photometrics-boosted-officials --region us-east-2` (read-only, safe to run now) and paste that output in your handoff; build the item to match it exactly.
   c. Add dead.official@simulator.amazonses.com to the seeded generate row's `representatives` list so it passes the Lambda's open-relay guard (which only allows addresses stored on the session's generate row).
   d. Invoke /send for the seeded session with a representatives list that includes that address (via the AWS Lambda Invoke API and a synthetic Function-URL event, exactly as the existing `send` does — never over HTTPS).
   e. Assert: the response reports failed_count 1 and a `failed` entry {email: dead.official@simulator.amazonses.com, reason: 'suppressed'}; the address is NOT in representatives_sent; the sends row for the session contains representatives_failed with that entry, plus representatives_offered, priorities, source and location_city.
   f. Exit non-zero with a clear message on any assertion failure.
3. `cleanup` removes everything check-regenerate created — the bounce row (email+timestamp key), the boosted-officials row (its real key), and all rows for this run's session_id across the three tables. Preserve existing cleanup behaviour.
4. Update README.md: the new seed fields, the new subcommand, what it asserts, what it cleans up, and the fact that /generate is still never called.

HARD CONSTRAINTS
- Do NOT run the harness against production in this item. --dry-run only. The production run is a separate item, gated on the deploy. Read-only `aws dynamodb describe-table` is allowed and expected.
- The harness must still never call /generate.
- Every representative address stays an SES mailbox-simulator address. The only real address permitted anywhere is the --cc-email default ari@sdgis.com.
- Cleanup must key off rows this run created; never touch the pre-existing rows test-gap-framing-001 or test-gap-framing-004.

DATA CONTRACT you are asserting against
Generate row gains `source` (M of S: utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer, each <=200 chars, absent keys omitted), `location_city` (S), `location_state` (S), `location_country` (S).
Sends row gains `priorities` (L of S), `source` (M), `location_city`, `location_state`, `representatives_offered` (N = len of the generate row's representatives), `representatives_failed` (L of M {email S, reason S}) with reason 'suppressed' or 'ses_error'. The /send response body gains a `failed` list of {email, reason}.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
`python funnel_test.py --dry-run all` and `--dry-run check-regenerate` both exit 0 with bogus credentials and print the full plan. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md with: the raw describe-table output for photometrics-boosted-officials, the raw --dry-run output for `all` and for `check-regenerate`, the diff of funnel_test.py, and an explicit list of every row check-regenerate creates paired with the cleanup call that deletes it.

---

## Work Item: p2-harness-run

```yaml
id: "p2-harness-run"
kind: "test"
purpose: "Prove against production that the deployed Lambda actually suppresses a hard-bounced address at send time and writes the new attribution/location/failure fields on the sends row — then prove zero residue."
hard_prereqs: ["p2-deploy", "p2-harness-extend"]
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py", "C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/README.md"]
shared_resources: ["aws:take-action-tables", "aws:ses-sending"]
acceptance_criteria: ["`python funnel_test.py all` ran against production and exited 0, with every subcommand's assertions passing, including the new check-regenerate step.", "The raw output shows check-regenerate asserting failed_count 1 with reason 'suppressed' for dead.official@simulator.amazonses.com, and that address absent from representatives_sent.", "Independent corroboration via `aws dynamodb get-item` (not the harness's own output) shows the sends row for the run's session_id containing representatives_failed, representatives_offered, priorities, source and location_city, with values matching the contract.", "A CloudWatch filter-log-events scan over the harness run window shows no ERROR, no traceback, and no 'Task timed out' for /aws/lambda/photometrics-take-action.", "Post-cleanup residue proof: paginated scans of photometrics-take-action, photometrics-take-action-sends, photometrics-email-bounces and photometrics-boosted-officials show zero rows created by this run. Row counts return to the pre-run baseline (118 non-test generate rows + 4 sends, per p1-baseline-data-HANDOFF.md, allowing for any rows another concurrent item legitimately added).", "The pre-existing rows test-gap-framing-001 and test-gap-framing-004 still exist and are unmodified.", "No real official received email; the only non-simulator address involved is ari@sdgis.com as CC."]
verification_commands: ["AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-email-bounces --region us-east-2 --filter-expression 'contains(email, :e)' --expression-attribute-values '{\":e\":{\"S\":\"dead.official\"}}' --output json", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{\":p\":{\"S\":\"test-\"}}' --projection-expression 'session_id' --output json", "AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{\"session_id\":{\"S\":\"test-gap-framing-001\"}}' --projection-expression 'session_id' --output json", "MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c \"import time;print(int(time.time()*1000)-7200000)\") --filter-pattern 'ERROR' --max-items 50 --output json", "cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus python funnel_test.py --dry-run all; echo \"dry-run exit=$?\""]
downstream: ["p2-report-verify", "p2-docs"]
context_budget_pct: 30
max_correction_rounds: 2
security_critical: true
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "opus"
verifier_effort: "high"
model_rationale: "Deviates upward from the sonnet verifier MODEL-TIERING suggests for harness items: this run is the only end-to-end evidence that the suppression control works in production, so a false green here ships an unenforced control. security_critical=true with an opus/high verifier that independently re-scans the three tables for residue and re-reads CloudWatch rather than trusting the pasted output."
status: "pending"
```

**Assignment brief:**

OBJECTIVE
Run the extended funnel harness against production on the freshly deployed Lambda, prove the suppression control actually enforces, corroborate the sends row independently of the harness, and leave zero residue.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/tools/funnel_test.py and lambda/take-action/tools/README.md — edit them ONLY if the production run exposes a harness bug; every such edit must be described and justified in the handoff. Do NOT edit lambda_function.py: if the run exposes a LAMBDA defect, stop and report it as a blocking finding.
Shared resources: aws:take-action-tables, aws:ses-sending.

REQUIRED READING
- .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md (what check-regenerate does, what it creates, how cleanup removes it)
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md (the deployed CodeSha256 — confirm it is still current before you run)
- .dagflow/phases/01-verify-funnel/items/p1-harness-run-HANDOFF.md (what a green run looked like before)
- .dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md section 1 (118 non-test generate rows, 4 sends, 14 bounce rows — your residue proof compares against these)

WHAT TO DO
1. Pre-flight: `AWS_PAGER='' aws sts get-caller-identity` (expect account 794038225197); confirm the deployed CodeSha256 matches p2-deploy's recorded value; record pre-run counts for the three tables with paginated `--select COUNT` scans.
2. `python funnel_test.py --dry-run all` first — confirm the plan, zero AWS calls.
3. `python funnel_test.py all` against production. Capture the complete raw output.
4. Corroborate independently — do not rely on the harness's own assertions. With `aws dynamodb get-item`, fetch the sends row for the run's session_id and paste the raw JSON, showing representatives_failed, representatives_offered, priorities, source and location_city. Fetch the generate row and show `source` and `location_city`/`location_state`/`location_country`.
5. CloudWatch: `MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time <run start in ms>` — paste the raw output and confirm no ERROR/traceback/timeout. Do not paste any line that would expose ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY; say so if you suppress one.
6. Cleanup (the `all` sequence runs it unless --keep) and then PROVE zero residue with your own scans: no test- rows other than test-gap-framing-001 and test-gap-framing-004; no dead.official row in the bounce table; no boosted-officials row for 'Austin, TX' created by this run; counts back to baseline.
7. Confirm test-gap-framing-001 and test-gap-framing-004 still exist.

HARD CONSTRAINTS
- Only SES mailbox-simulator addresses receive mail. The only real address permitted is ari@sdgis.com as CC.
- Do NOT call /generate — the harness must not, and neither may you. The phase's 2-call budget is reserved for another item.
- Do not deploy, do not change function configuration, IAM, SES, GA4 or Google Ads.
- If the run reveals that the Lambda does NOT suppress the bounced address, that is a blocking finding: report it with full evidence rather than adjusting the harness's assertions to pass.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md containing: the run's session_id, the full raw output of `all`, the raw get-item JSON for both the sends row and the generate row, the raw CloudWatch output, the pre-run and post-run table counts, the residue-proof scan output, and confirmation that the two gap-framing rows survive.

---

## Work Item: p2-frontend-source

```yaml
id: "p2-frontend-source"
kind: "implementation"
purpose: "Capture first-touch campaign attribution in the browser, send it to /generate, and add landed_priorities / utm_content / preselected to the three GA4 events — without disturbing the existing ?priorities= preselect behaviour."
hard_prereqs: []
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/layouts/_default/take-action.html"]
shared_resources: []
acceptance_criteria: ["On page load the script reads URLSearchParams for utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid and the existing priorities param (as landed_priorities), plus document.referrer, and builds a `source` object with only non-empty values.", "First-touch persistence: the source object is written to sessionStorage['ta_source'] only if that key is not already set, so a reload or an internal navigation preserves the original attribution. All sessionStorage access is wrapped so a browser that throws on storage access does not break the page.", "The /generate request payload gains a `source` object (the persisted first-touch one), alongside everything it already sends.", "GA4 events take_action_submit, send_intent_clicked and send_confirmed each gain params landed_priorities (string, '' when absent), utm_content (string, '' when absent) and preselected (boolean).", "`preselected` is true only when the page loaded with at least one VALID priorities value (a value the existing code accepts and applies), and false for a bare URL or an unrecognised value. The definition used is visible in the diff and stated in the handoff.", "The existing ?priorities= behaviour is byte-for-byte equivalent in effect: the same values preselect the same checkboxes and the same messaging appears. No existing GA4 param was renamed or removed.", "`hugo --quiet` builds the site with exit 0 from the repo root.", "The inline script extracted from the template passes `node --check`.", "The working-tree diff touches only layouts/_default/take-action.html."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website && hugo --quiet; echo \"hugo exit=$?\"", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff --stat", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U20 -- layouts/_default/take-action.html", "grep -n 'ta_source\\|landed_priorities\\|utm_content\\|preselected\\|utm_match\\|gclid\\|document.referrer\\|sessionStorage' C:/Users/aisaa/Projects/photometricsai-website/layouts/_default/take-action.html", "cd C:/Users/aisaa/Projects/photometricsai-website && python - <<'PY'\nimport re,subprocess,tempfile,os\nsrc=open('layouts/_default/take-action.html',encoding='utf-8').read()\nblocks=re.findall(r'<script(?![^>]*\\bsrc=)[^>]*>(.*?)</script>',src,re.S)\nos.makedirs('/tmp/tacheck',exist_ok=True)\nfor i,b in enumerate(blocks):\n    p=f'/tmp/tacheck/block{i}.js'\n    open(p,'w',encoding='utf-8').write(b)\n    print(p, subprocess.run(['node','--check',p],capture_output=True,text=True).returncode)\nPY", "cd C:/Users/aisaa/Projects/photometricsai-website && grep -c 'gtagEvent' layouts/_default/take-action.html && git show HEAD:layouts/_default/take-action.html | grep -c 'gtagEvent'", "cd C:/Users/aisaa/Projects/photometricsai-website && git show HEAD:layouts/_default/take-action.html > /tmp/ta_head.html && diff <(grep -n 'priorities' /tmp/ta_head.html) <(grep -n 'priorities' layouts/_default/take-action.html) | head -40"]
downstream: ["p2-docs"]
context_budget_pct: 30
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "sonnet"
verifier_effort: "high"
model_rationale: "Single-file frontend change with a mechanical verification path (hugo builds, node --check on the extracted inline script, greps for each new parameter, and a static read of the ?priorities= handling for regressions). MODEL-TIERING has no frontend precedent; sonnet/high both sides matches the tooling tier, and the one real risk — regressing the preselect behaviour — is checkable by diff."
status: "done"
```

**Assignment brief:**

OBJECTIVE
Implement the frontend half of the Take Action attribution contract: capture first-touch campaign parameters, send them to /generate, and enrich the three GA4 events — with zero change to how ?priorities= already preselects and messages.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own exactly one file: layouts/_default/take-action.html (Hugo template, ~752 lines, HTML + inline JS). Nothing else. Do not touch lambda/, do not touch hugo.toml, do not build into public/ beyond what `hugo` writes.

CURRENT LANDMARKS (approximate; re-grep)
- /generate payload built ~:589
- /send payload ~:518
- gtagEvent helper ~:248
- GA4 events: take_action_submit ~:619, send_intent_clicked ~:504 / :640 / :652, send_confirmed ~:542
- ?priorities= handling ~:694-748

WHAT TO IMPLEMENT
1. On load, read URLSearchParams: utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid; map the existing `priorities` param to `landed_priorities`; plus document.referrer. Build a plain `source` object containing only non-empty values.
2. First-touch persist: if sessionStorage['ta_source'] is unset, store JSON.stringify(source); otherwise read the stored one and use THAT for the rest of the session — a reload with a bare URL must keep the original attribution. Wrap every sessionStorage read/write in try/catch (private mode / blocked storage must not break the page).
3. Add the resulting `source` object to the /generate request payload.
4. Add three params to take_action_submit, send_intent_clicked and send_confirmed (all call sites of each): landed_priorities (string, '' if absent), utm_content (string, '' if absent), preselected (boolean). Route them through the existing gtagEvent helper rather than bypassing it.
5. `preselected` is true ONLY when the page loaded with at least one VALID priorities value — reuse whatever validity check the existing ?priorities= handling already applies; do not invent a second definition. A bare URL, an empty value, or an unrecognised value ⇒ false.

HARD CONSTRAINTS
- The existing ?priorities= behaviour must be unchanged in effect: the same URLs preselect the same checkboxes and show the same messaging. A verifier diffs every `priorities` line against git HEAD.
- Do not rename or remove any existing GA4 event or param.
- Do not commit or push. The lead pushes to master (Amplify auto-deploys) and verifies live in the browser — that is outside your scope, and so is any GA4 or Google Ads configuration change.
- No Chrome/browser tools are available to you. Verify statically: `hugo --quiet` (Hugo v0.154.5 extended IS installed on this host), `node --check` on the extracted inline script blocks (node IS installed), and greps.

DATA CONTRACT (frontend half)
/generate payload gains a `source` object with keys utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer (omit empties). The Lambda sanitizes each to <=200 chars and drops unknown keys, so sending extra keys is harmless but pointless — send exactly these.
GA4 events take_action_submit, send_intent_clicked, send_confirmed gain landed_priorities (string or ''), utm_content (string or ''), preselected (boolean).
Context: Google Ads will append utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_content={adgroupid}&utm_term={keyword}&utm_match={matchtype}, so utm_content arrives as a numeric ad group id — treat every value as an opaque string.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
`hugo --quiet` exits 0; every extracted inline script block passes `node --check`; greps show each new param at every relevant call site. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-frontend-source-HANDOFF.md with: the full diff, the raw hugo and node --check output, a table of the three GA4 events × three new params showing the line number of each call site, the exact rule you used for `preselected`, and evidence (diff of the priorities-related lines vs HEAD) that the preselect behaviour is unchanged.

---

## Work Item: p2-live-generate-check

```yaml
id: "p2-live-generate-check"
kind: "test"
purpose: "Spend the phase's one allowed /generate call to prove the deployed backend actually stores the source map and the Haiku-normalized city/state/country on a real generate row."
hard_prereqs: ["p2-deploy"]
inputs: []
owns: []
shared_resources: ["anthropic-api-budget", "aws:take-action-tables"]
acceptance_criteria: ["Exactly ONE /generate invocation was made in this item (the phase's allowed call), via the AWS Lambda Invoke API with a synthetic Function-URL event — evidenced by the raw invoke output and a matching CloudWatch request id.", "The event body included a `source` object with all nine contract keys populated with recognisable test values, location 'Columbus, OH', priorities ['Migratory Birds'], and a session_id prefixed 'test-'.", "The stored generate row, fetched with `aws dynamodb get-item` and pasted RAW, shows: `source` map containing utm_content and the other supplied keys with the supplied values (truncated to 200 chars where applicable); `location_city` = 'Columbus'; `location_state` = 'OH'; `location_country` = 'US'.", "The representatives returned by the invoke are printed (name, title, email) in the handoff.", "No email was sent — /send was not invoked.", "The generate row was deleted afterwards and its absence is proven by a get-item returning no Item.", "The CloudWatch log stream for the invocation is quoted (request id, START/END/REPORT lines, and the hard-filter log line if any officials were dropped), with no line exposing ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY."]
verification_commands: ["AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{\":p\":{\"S\":\"test-\"}}' --projection-expression 'session_id' --output json", "MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c \"import time;print(int(time.time()*1000)-10800000)\") --filter-pattern 'REPORT' --max-items 50 --output json", "MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c \"import time;print(int(time.time()*1000)-10800000)\") --filter-pattern 'Columbus' --max-items 20 --output json", "AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text"]
downstream: ["p2-report-verify"]
context_budget_pct: 20
max_correction_rounds: 1
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "opus"
verifier_effort: "high"
model_rationale: "Deviates upward from a sonnet verifier: the evidence for this item is destroyed by its own mandatory cleanup, so the verifier must judge whether the pasted evidence chain (invoke response, get-item JSON, CloudWatch request id, deletion proof) is internally consistent and independently corroborate it from CloudWatch — reasoning about evidence rather than re-running a command. Re-running costs the phase's only spare Anthropic call."
status: "pending"
```

**Assignment brief:**

OBJECTIVE
Prove, against the deployed production Lambda, that a real /generate call stores the attribution `source` map and the Haiku-normalized location on the generate row. This item is the ONLY one in the phase authorized to call /generate, and it may call it exactly once.

OWNERSHIP
You own no repo files. You write one handoff. Shared resources: anthropic-api-budget, aws:take-action-tables.

REQUIRED READING
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md (the deployed CodeSha256 — confirm it is current before you spend the call)
- .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md (exactly what the backend should now store, and the fallback behaviour)

WHAT TO DO
1. Confirm `aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256` equals the value in p2-deploy-HANDOFF.md. If it does not, STOP and report — do not spend the Anthropic call against unknown code.
2. Build a synthetic Function-URL event for rawPath ending '/generate' with a JSON body containing:
   - session_id: 'test-livegen-<epoch>'
   - location: 'Columbus, OH'
   - priorities: ['Migratory Birds']
   - name / email: a plausible constituent name and ari@sdgis.com (nothing is mailed by /generate)
   - source: {utm_source:'google', utm_medium:'cpc', utm_campaign:'TESTCAMP', utm_content:'TBD-2', utm_term:'migratory bird lighting', utm_match:'p', gclid:'TESTGCLID', landed_priorities:'Migratory Birds', referrer:'https://www.google.com/'}
   Match the event shape the existing harness uses for /send (see lambda/take-action/tools/funnel_test.py's send command) so the router takes the right branch.
3. Invoke via the AWS Lambda Invoke API (never over HTTPS, never through the real Function URL). ONE call. Capture the raw response payload.
4. `aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{"session_id":{"S":"test-livegen-<epoch>"}}'` and paste the RAW JSON (you may elide the `letter` attribute's body for length — say so — but paste `source`, `location_city`, `location_state`, `location_country`, `priorities`, and `representatives` in full).
5. Assert: source.utm_content == 'TBD-2' and the other eight keys present with the supplied values; location_city == 'Columbus'; location_state == 'OH'; location_country == 'US'. Print the returned representatives (name, title, email).
6. Pull the CloudWatch log stream for the invocation and quote the request id, START/END/REPORT lines and any hard-filter log line.
7. DELETE the row (`aws dynamodb delete-item`) and prove absence with a follow-up get-item returning no Item.

HARD CONSTRAINTS
- Exactly one /generate call. If an assertion fails, do NOT retry the call — report the failure with full evidence. (The phase holds one spare call, reserved for the verifier.)
- Do NOT invoke /send. Nothing is mailed by this item.
- Do not deploy, do not change configuration, IAM, SES, GA4 or Google Ads.
- Because your cleanup destroys the row, your handoff IS the evidence: paste raw command output for every step, in order, with timestamps, so an independent verifier can judge the chain without re-spending the budget.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

NOTE FOR THE VERIFIER (state this in the handoff)
The phase permits a second /generate call ONLY to a verifier that finds the evidence chain here inconsistent, and only if that verifier deletes its own row and says so.

DEFINITION OF DONE
Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md containing, in order: the CodeSha256 check, the exact event JSON sent, the raw invoke response, the raw get-item JSON, the assertion results, the returned representatives table, the CloudWatch excerpt with request id, the delete-item output, and the proof-of-absence get-item.

---

## Work Item: p2-report-tool

```yaml
id: "p2-report-tool"
kind: "implementation"
purpose: "Build the one command that answers 'which ad group, keyword, priority and city actually produced letters and sends' — the deliverable the whole phase exists to enable."
hard_prereqs: []
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py", "C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/adgroups.json"]
shared_resources: []
acceptance_criteria: ["lambda/take-action/tools/report.py exists and runs read-only: it issues only dynamodb Scan calls (paginated with LastEvaluatedKey) and makes zero writes.", "Scans of photometrics-take-action use a ProjectionExpression that EXCLUDES the `letter` attribute; the sends-table scan likewise projects only what it needs.", "Rows whose session_id starts with 'test-' are excluded from every output.", "The two tables are joined on session_id; a generate row with no matching sends row still appears (counted as generated, not sent).", "Cut 1 (per ad group × keyword × top priority × location) outputs columns: ad group (utm_content resolved via adgroups.json; an id not in the map prints raw; a row with no source prints 'pre-attribution'), keyword (utm_term), top priority (priorities[0]), location (location_city + ', ' + location_state, falling back to the raw `location` string when the normalized fields are absent), generated, sent sessions, reps emailed (sum of len(representatives_sent)), suppressed (count of representatives_failed entries with reason 'suppressed'), hard bounces (representatives_sent addresses that appear in photometrics-email-bounces as Bounce/Permanent or Complaint).", "Cut 2 (priority × state) and a totals line are both produced.", "Output is markdown to stdout, and `--out <dir>` additionally writes CSV files (one per cut) into that directory.", "adgroups.json exists mapping placeholder ids 'TBD-1'..'TBD-7' to the 7 real ad group NAMES, with a clearly-labelled note field instructing the lead to replace the placeholder ids with the real numeric ad group ids from the Google Ads UI. The file is valid JSON (a JSON string field carries the note — JSON has no comments).", "The tool runs correctly TODAY against production, where no row has `source` and no row has location_city: every row buckets as 'pre-attribution' with the raw location, and totals match the Phase 01 baseline of 118 non-test generate rows and 4 sends.", "No crash on missing/None/empty attributes anywhere; no KeyError on a sends row with no representatives_failed."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py | head -60", "cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py --out \"$TMPDIR/rpt\" >/dev/null && ls -la \"$TMPDIR/rpt\"", "cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py | grep -i 'total'", "python -c \"import json;d=json.load(open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/adgroups.json'));print(json.dumps(d,indent=2))\"", "grep -n 'put_item\\|delete_item\\|update_item\\|batch_write' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py || echo 'READ-ONLY: no write calls'", "grep -n 'ProjectionExpression\\|LastEvaluatedKey\\|letter' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text"]
downstream: ["p2-report-verify", "p2-docs"]
context_budget_pct: 35
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "sonnet"
verifier_effort: "high"
model_rationale: "Tooling item per MODEL-TIERING guidance (sonnet/high both sides). Read-only, no authorization surface, and its correctness is checkable numerically — the downstream p2-report-verify reconciles its totals against the independently produced Phase 01 baseline, which is the real check."
status: "done"
```

**Assignment brief:**

OBJECTIVE
Build the reporting tool that answers Ari's question — 'crime or birds, Austin or Columbus, which ad group sent them' — from the two DynamoDB tables, in one command. Build it against the fixed data contract now, so it is ready the moment attributed rows start arriving.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/tools/report.py (new) and lambda/take-action/tools/adgroups.json (new). Nothing else. Do NOT edit lambda_function.py or funnel_test.py (concurrent items own them).

DATA SOURCES (region us-east-2, account 794038225197)
- photometrics-take-action — generate rows, PK session_id. Existing attributes include location (raw string), priorities (L of S), representatives (L of M with email/name/title), letter (LARGE — never project it), timestamp. New per contract: source (M of S), location_city (S), location_state (S), location_country (S).
- photometrics-take-action-sends — PK session_id. Existing: constituent_email, location, representatives_sent (L of S), message_ids, timestamp, ttl. New per contract: priorities (L of S), source (M), location_city, location_state, representatives_offered (N), representatives_failed (L of M {email, reason}) with reason 'suppressed' or 'ses_error'.
- photometrics-email-bounces — key schema email + timestamp; attributes event_type, subtype. Hard bounce = event_type 'Bounce' AND subtype 'Permanent', or event_type 'Complaint'.

WHAT TO BUILD
1. Paginated read-only scans of both take-action tables (LastEvaluatedKey loop), with ProjectionExpression excluding `letter`. Remember 'subtype' and 'timestamp' and 'location' may be DynamoDB reserved words — use ExpressionAttributeNames aliases where needed (the existing Lambda and the Phase 01 baseline script both do this; copy the pattern).
2. Exclude every row whose session_id begins with 'test-'.
3. Join generate rows to sends rows on session_id. A generate row with no send still counts as generated.
4. Cut 1 — ad group × keyword × top priority × location:
   - ad group: source.utm_content resolved through adgroups.json; an id absent from the map prints raw; a row with no `source` (or no utm_content) buckets as 'pre-attribution'.
   - keyword: source.utm_term (blank when absent).
   - top priority: priorities[0] (blank when the list is empty).
   - location: location_city + ', ' + location_state when present, else the raw `location` string.
   - metrics: generated (count of generate rows), sent sessions (count with a sends row), reps emailed (sum of len(representatives_sent)), suppressed (count of representatives_failed entries with reason 'suppressed'), hard bounces (count of representatives_sent addresses found in the bounce table as Permanent/Complaint).
5. Cut 2 — priority × state (state from location_state, else parsed/blank).
6. Totals line.
7. Markdown to stdout; `--out <dir>` also writes one CSV per cut.
8. adgroups.json: map placeholder ids 'TBD-1'..'TBD-7' to the 7 real ad group NAMES. Get the names from C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md (read-only — you do not own that file). Include a JSON string field (e.g. "_note") telling the lead to replace each placeholder id with the real numeric ad group id from Google Ads (Ad groups → Columns → Ad group ID). JSON has no comments — use a field.

HARD CONSTRAINTS
- READ-ONLY. No put_item/update_item/delete_item/batch_write, ever. A verifier greps for them.
- Must run correctly against TODAY's production data, where NO row has `source` and NO row has location_city — everything buckets as 'pre-attribution' with the raw location. Run it and paste the output.
- Totals must reconcile with the Phase 01 baseline: 118 non-test generate rows, 4 sends (see .dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md section 1, which also lists 120 raw generate rows with 2 test- rows excluded, and 14 bounce rows). Concurrent items may transiently add and remove test- rows; your 'test-' exclusion must make that irrelevant.
- Never print a constituent_email or a letter body in the report output.
- Do not deploy, do not call /generate, do not send email.

REQUIRED READING
- .dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md — the baseline numbers, the raw-location distribution you must tolerate (80 distinct raw strings, values like 'Portland or' and '65234'), and a working paginated-scan script you can model the pagination and reserved-word handling on.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
`python report.py` runs clean against production and `python report.py --out <dir>` writes the CSVs. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md containing: the full report.py source or its diff, adgroups.json verbatim, the complete raw markdown output of a production run, the CSV filenames and first lines, and an explicit reconciliation of your totals against the Phase 01 baseline (118 generate / 4 sends) with any discrepancy explained.

---

## Work Item: p2-report-verify

```yaml
id: "p2-report-verify"
kind: "test"
purpose: "Independently confirm the report tool's numbers are true — totals reconcile with the Phase 01 baseline once the harness and live-generate items have added and cleaned up their rows."
hard_prereqs: ["p2-report-tool", "p2-harness-run", "p2-live-generate-check"]
inputs: []
owns: []
shared_resources: []
acceptance_criteria: ["`python report.py` was run against production after p2-harness-run and p2-live-generate-check completed their cleanups, and its full raw markdown output is pasted in the handoff.", "The report's generated total equals 118 and its sends total equals 4 — the Phase 01 baseline — or any deviation is explained row by row with corroborating `aws dynamodb` CLI output showing exactly which session_ids account for it.", "Independent corroboration: paginated `aws dynamodb scan --select COUNT` on both tables, and a scan filtered on begins_with(session_id,'test-') showing only test-gap-framing-001 and test-gap-framing-004 remain.", "The 'pre-attribution' bucket accounts for all rows lacking `source` — consistent with no production traffic having been attributed yet.", "`--out <dir>` CSV output was produced and its row counts match the markdown cuts.", "No writes were made by this item."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py", "cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py --out \"$TMPDIR/rptverify\" >/dev/null && for f in \"$TMPDIR/rptverify\"/*.csv; do echo \"$f: $(wc -l < \"$f\") lines\"; done", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{\":p\":{\"S\":\"test-\"}}' --projection-expression 'session_id' --output json", "AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{\":p\":{\"S\":\"test-\"}}' --projection-expression 'session_id' --output json"]
downstream: []
context_budget_pct: 20
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "high"
verifier_model: "sonnet"
verifier_effort: "high"
model_rationale: "Numerical reconciliation against a documented baseline; read-only, no authorization surface, and fully re-runnable by the verifier (run report.py, run the CLI count scans, compare). sonnet/high on both sides per the MODEL-TIERING tooling default."
status: "pending"
```

**Assignment brief:**

OBJECTIVE
Prove the report tool's numbers are true against production, by reconciling them with the independently produced Phase 01 baseline.

OWNERSHIP
You own no repo files — this is a read-only verification run producing a handoff. If you find a report.py bug, report it as a blocking finding; do NOT patch report.py (its owner will).

REQUIRED READING
- .dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md — section 1 is the baseline: photometrics-take-action 120 raw / 2 test- excluded / 118 counted; photometrics-take-action-sends 4 raw / 0 excluded / 4 counted; photometrics-email-bounces 14 rows. Section 5 details the 4 sends rows.
- .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md — what the tool computes and how it buckets.
- .dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md — what the harness added and removed; its residue proof.
- .dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md — the one live generate row it created and deleted.

WHAT TO DO
1. Run `python lambda/take-action/tools/report.py` against production. Paste the complete raw markdown output.
2. Run `python report.py --out <scratch dir>` and confirm the CSVs match the markdown cuts (row counts and totals).
3. Corroborate independently with the AWS CLI, not with report.py: paginated `--select COUNT` scans of both take-action tables; a scan filtered on begins_with(session_id,'test-') on both tables.
4. Reconcile: report generated total should be 118 and sends total 4. The harness run and the live-generate check are both net zero after their cleanups. If the numbers differ, do NOT hand-wave — identify the exact session_ids responsible with CLI output and say whether the cause is (a) residue another item failed to clean, (b) genuine new production traffic since the Phase 01 scan at 2026-09-03T19:01:59Z, or (c) a report.py defect. Only (c) is a blocking finding against report.py; (a) is a blocking finding against the item that left it.
5. Confirm the 'pre-attribution' bucket accounts for every row lacking `source`.

HARD CONSTRAINTS
- READ-ONLY. No writes of any kind. Do not delete residue you find — report it.
- Do not call /generate, do not send email, do not deploy.
- Do not edit report.py, adgroups.json, or any other repo file.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-report-verify-HANDOFF.md containing: the full raw report output, the raw CLI corroboration, an explicit reconciliation table (baseline vs report vs CLI count, per table), and a clear pass/fail verdict with any discrepancy attributed to a specific cause and session_id.

---

## Work Item: p2-docs

```yaml
id: "p2-docs"
kind: "implementation"
purpose: "Write down what now exists — the Lambda's operational shape and data contract in the repo's CLAUDE.md, and the current funnel state in the campaign doc — so the next person (or session) does not have to rediscover it."
hard_prereqs: ["p2-deploy", "p2-harness-run", "p2-report-tool", "p2-frontend-source"]
inputs: []
owns: ["C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md", "C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md"]
shared_resources: []
acceptance_criteria: ["CLAUDE.md (website repo) gains a 'Take Action Lambda' section covering: function name photometrics-take-action, region us-east-2, account 794038225197, role photometrics-take-action-lambda-role; source path lambda/take-action/lambda_function.py; the route suffixes (/generate, /send, /track, /flag) plus the SNS bounce branch; environment variable NAMES only (no values) — DYNAMODB_TABLE, BOOSTED_TABLE, FLAGGED_TABLE, SEND_LOG_TABLE, BOUNCE_TABLE, ANTHROPIC_API_KEY, GOOGLE_CIVIC_API_KEY, SES_SENDER_EMAIL, SES_CONFIGURATION_SET; the five DynamoDB tables with their key schemas; the SES config set → SNS → Lambda bounce wiring; deploy via lambda/take-action/deploy.sh (and the note that `zip` is absent on this host so the python zipfile fallback runs); tests at lambda/take-action/tests/ run with `python -m pytest lambda/take-action/tests -q` (no moto; module-level clients are monkeypatched); the harness lambda/take-action/tools/funnel_test.py incl. check-regenerate and the simulator-only rule; the report tool lambda/take-action/tools/report.py and adgroups.json.", "CLAUDE.md documents the full data contract: the generate row's source map keys, location_city/state/country; the sends row's priorities, source, location_city/state, representatives_offered, representatives_failed (with reasons 'suppressed' and 'ses_error'); and the frontend's source payload plus the GA4 params landed_priorities, utm_content, preselected.", "No secret VALUE appears anywhere — names only. A grep for likely key material finds nothing.", "C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md's 'Funnel verification' section is updated to the current state: hard filter live (with the deployed CodeSha256), sender mailbox fixed, attribution + normalized location captured, report tool available and how to run it.", "The campaign doc keeps its existing readable-cold style: it describes the current state, not a changelog of what changed; no dated diff entries are appended.", "Every factual claim in both documents is traceable to a Phase 01 or Phase 02 handoff; the docs handoff lists claim → source handoff.", "Only the two owned files are modified."]
verification_commands: ["cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain", "cd C:/Users/aisaa/Projects/photometricsai-website && git diff -- CLAUDE.md", "grep -n -A5 'Take Action Lambda' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md | head -60", "grep -n 'photometrics-take-action\\|deploy.sh\\|funnel_test.py\\|report.py\\|representatives_failed\\|location_city\\|preselected' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md", "grep -rn -E 'sk-ant|AIza|AKIA|[A-Za-z0-9_-]{35,}' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md' || echo 'no secret-shaped strings'", "grep -n -A30 'Funnel verification' 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md'", "AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text"]
downstream: []
context_budget_pct: 30
max_correction_rounds: 2
security_critical: false
implementer_model: "sonnet"
implementer_effort: "medium"
verifier_model: "sonnet"
verifier_effort: "medium"
model_rationale: "Docs item — MODEL-TIERING guidance is sonnet/medium implementer with sonnet/medium verifier, and Phase 01's docs item passed at that tier with the verifier tracing every claim back to a handoff. Same pattern applies here."
status: "pending"
```

**Assignment brief:**

OBJECTIVE
Document the Take Action Lambda's operational shape and data contract in the website repo's CLAUDE.md, and bring the campaign doc's funnel section up to current reality.

OWNERSHIP
You own exactly two files:
- C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md
- C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md (NOT a git repo; edit in place)
Nothing else. Do not edit code, tests, tools, or any handoff other than your own.

REQUIRED READING (every factual claim you write must trace to one of these)
- .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md (the deployed CodeSha256)
- .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md and p2-harness-run-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-frontend-source-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md
- .dagflow/phases/01-verify-funnel/items/p1-sender-mailbox-HANDOFF.md (the sender mailbox fix) and p1-docs-HANDOFF.md (the existing style of the campaign doc's Funnel verification section)
- The existing CLAUDE.md, to match its heading level and prose conventions.

WHAT TO WRITE
A. CLAUDE.md — new 'Take Action Lambda' section:
   - Function photometrics-take-action, region us-east-2, account 794038225197, role photometrics-take-action-lambda-role; source lambda/take-action/lambda_function.py (single file).
   - Routing: rawPath suffixes /generate, /send, /track, /flag, plus the SNS branch that records bounce events.
   - Environment variable NAMES ONLY — DYNAMODB_TABLE, BOOSTED_TABLE, FLAGGED_TABLE, SEND_LOG_TABLE, BOUNCE_TABLE, ANTHROPIC_API_KEY, GOOGLE_CIVIC_API_KEY, SES_SENDER_EMAIL, SES_CONFIGURATION_SET. Never a value.
   - Tables: photometrics-take-action (PK session_id), photometrics-take-action-sends (PK session_id), photometrics-email-bounces (email + timestamp), photometrics-flagged-officials, photometrics-boosted-officials.
   - SNS bounce wiring: SES configuration set take-action-sends → SNS photometrics-ses-bounces → this Lambda → photometrics-email-bounces. Note that bounces addressed to the sender itself are logged loudly and NOT recorded.
   - Deploy: `bash lambda/take-action/deploy.sh` (verifies CodeSha256; `--dry-run` prints the plan; `zip` is absent on this host so the python zipfile fallback runs). Record the currently deployed CodeSha256 from p2-deploy-HANDOFF.md.
   - Tests: `python -m pytest lambda/take-action/tests -q`; moto is not installed, module-level dynamodb/ses clients are monkeypatched, no test touches AWS.
   - Harness: lambda/take-action/tools/funnel_test.py — subcommands incl. check-regenerate; simulator addresses only; never calls /generate.
   - Report: lambda/take-action/tools/report.py plus adgroups.json (placeholder ids TBD-1..TBD-7 pending the real Google Ads ad group ids).
   - Data contract: the generate row's `source` map keys and location_city/state/country; the sends row's priorities, source, location_city/state, representatives_offered, representatives_failed with reasons 'suppressed' and 'ses_error'; the frontend's /generate `source` payload and the GA4 params landed_priorities, utm_content, preselected.
B. take-action-campaign.md — update the existing 'Funnel verification' section to describe the CURRENT state: the hard exclusion filter is live in production (cite the deployed CodeSha256), the sender mailbox take-action@photometrics.ai is working and its suppression was cleared, attribution and normalized location are now captured on every generate row and copied to sends rows, and the report tool exists with the command to run it. Keep the section's readable-cold voice — someone opening this doc months from now should learn the state of the system, not a diff. Do not append a dated changelog.

HARD CONSTRAINTS
- No secret values, ever — names only. A verifier greps both files for secret-shaped strings.
- Do not invent facts. If a handoff does not support a claim, leave it out or mark it explicitly as open. Do not claim the frontend change is live in production — the lead pushes and Amplify deploys that separately; describe it as implemented in the repo.
- Do not change Google Ads, GA4, Workspace, IAM or SES configuration or describe having done so.
- Do not commit or push.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
Both files updated; `git status --porcelain` shows only CLAUDE.md (plus .dagflow) modified in the repo. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-docs-HANDOFF.md containing the diff of CLAUDE.md, the before/after of the campaign doc's Funnel verification section, and a claim-by-claim source table (claim → handoff file that supports it).

---

