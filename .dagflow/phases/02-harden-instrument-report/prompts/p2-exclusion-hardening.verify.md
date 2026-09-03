You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-exclusion-hardening — Make a bounced or flagged address impossible to re-suggest (hard filter in handle_generate) and impossible to re-send (suppression in handle_send), paginate the exclusion scans, stop the sender address polluting the bounce table, and record what failed on the sends row.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- A module-level pure function `filter_excluded(officials, excluded_emails) -> list` exists in lambda_function.py; it is case-insensitive on email, tolerates officials without an 'email' key (keeps them), tolerates excluded_emails being None or empty (returns the input list unchanged), and does not mutate its arguments.
- handle_generate applies filter_excluded to the search_officials result BEFORE call_claude is invoked, and prints a log line containing the count of officials dropped.
- get_bounced_emails and get_flagged_emails both paginate with LastEvaluatedKey (loop until absent). The existing Permanent/Complaint classification rule in get_bounced_emails is unchanged.
- record_bounce_event skips writing any row whose email equals SES_SENDER_EMAIL.lower() and prints a loud warning line instead of writing.
- handle_send computes `excluded = get_bounced_emails() | get_flagged_emails()`; any rep that passed the existing verification whose email.lower() is in excluded is appended to a failed list with reason 'suppressed' and ses.send_email is NOT called for it. SES exceptions produce reason 'ses_error'.
- get_verified_representative_emails (the open-relay guard) and already_sent are byte-for-byte unchanged, and their call sites in handle_send are unchanged in order and effect: an unverified email is still rejected 400 and a duplicate session still returns 409.
- log_send writes the new sends-row fields per the data contract: `priorities` (L of S), `source` (M), `location_city` (S), `location_state` (S) copied from the generate row via a single get_item, `representatives_offered` (N = len of the generate row's representatives list), `representatives_failed` (L of M with keys email/reason). Absent source/location on the generate row means the field is omitted, not written empty. Existing fields (session_id, timestamp, constituent_email, location, representatives_sent, message_ids, ttl) are unchanged.
- The /send response body gains a `failed` list of {email, reason} objects.
- No AWS write calls were made by this item; the file parses (ast.parse) and the working tree diff touches only lambda_function.py.

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
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

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
