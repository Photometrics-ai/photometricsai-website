You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-exclusion-hardening
KIND: implementation
PURPOSE / EXPECTED OUTCOME:
Make a bounced or flagged address impossible to re-suggest (hard filter in handle_generate) and impossible to re-send (suppression in handle_send), paginate the exclusion scans, stop the sender address polluting the bounce table, and record what failed on the sends row.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
(none — no predecessors)

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
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

ACCEPTANCE CRITERIA:
- A module-level pure function `filter_excluded(officials, excluded_emails) -> list` exists in lambda_function.py; it is case-insensitive on email, tolerates officials without an 'email' key (keeps them), tolerates excluded_emails being None or empty (returns the input list unchanged), and does not mutate its arguments.
- handle_generate applies filter_excluded to the search_officials result BEFORE call_claude is invoked, and prints a log line containing the count of officials dropped.
- get_bounced_emails and get_flagged_emails both paginate with LastEvaluatedKey (loop until absent). The existing Permanent/Complaint classification rule in get_bounced_emails is unchanged.
- record_bounce_event skips writing any row whose email equals SES_SENDER_EMAIL.lower() and prints a loud warning line instead of writing.
- handle_send computes `excluded = get_bounced_emails() | get_flagged_emails()`; any rep that passed the existing verification whose email.lower() is in excluded is appended to a failed list with reason 'suppressed' and ses.send_email is NOT called for it. SES exceptions produce reason 'ses_error'.
- get_verified_representative_emails (the open-relay guard) and already_sent are byte-for-byte unchanged, and their call sites in handle_send are unchanged in order and effect: an unverified email is still rejected 400 and a duplicate session still returns 409.
- log_send writes the new sends-row fields per the data contract: `priorities` (L of S), `source` (M), `location_city` (S), `location_state` (S) copied from the generate row via a single get_item, `representatives_offered` (N = len of the generate row's representatives list), `representatives_failed` (L of M with keys email/reason). Absent source/location on the generate row means the field is omitted, not written empty. Existing fields (session_id, timestamp, constituent_email, location, representatives_sent, message_ids, ttl) are unchanged.
- The /send response body gains a `failed` list of {email, reason} objects.
- No AWS write calls were made by this item; the file parses (ast.parse) and the working tree diff touches only lambda_function.py.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff --stat -- lambda/take-action/lambda_function.py
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U15 -- lambda/take-action/lambda_function.py
- python -c "import ast;ast.parse(open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py',encoding='utf-8').read());print('SYNTAX OK')"
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -- lambda/take-action/lambda_function.py | grep -c 'LastEvaluatedKey'
- cd C:/Users/aisaa/Projects/photometricsai-website && git show HEAD:lambda/take-action/lambda_function.py > /tmp/head_lf.py && python - <<'PY'
import re
old=open('/tmp/head_lf.py',encoding='utf-8').read()
new=open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py',encoding='utf-8').read()
def body(src,name):
    m=re.search(r'\ndef '+name+r'\(.*?(?=\ndef )',src,re.S)
    return m.group(0) if m else None
for fn in ('get_verified_representative_emails','already_sent'):
    print(fn,'UNCHANGED' if body(old,fn)==body(new,fn) else 'CHANGED <-- INSPECT')
PY
- AWS_DEFAULT_REGION=us-east-2 AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x python -c "import sys;sys.path.insert(0,r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action');import lambda_function as lf;print(lf.filter_excluded([{'email':'A@x.com','name':'a'},{'email':'b@x.com'},{'name':'no-email'}],{'a@x.com'}));print(lf.filter_excluded([{'email':'b@x.com'}],None))"
- grep -n 'SES_SENDER_EMAIL' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py

CONTEXT BUDGET: sized to use no more than ~35% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
