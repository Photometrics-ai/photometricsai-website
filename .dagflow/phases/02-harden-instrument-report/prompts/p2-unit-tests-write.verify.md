You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-unit-tests-write — Write the pytest suite for the hardened send path, exclusion, bounce recording, source sanitization and normalized-location parsing — authored against the fixed data contract so it can be built in parallel with the Lambda changes rather than after them.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- Directory C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ exists containing conftest.py and one or more test_*.py files.
- conftest.py inserts the Lambda source directory on sys.path BEFORE importing lambda_function, honouring an override env var TAKE_ACTION_SRC when set (default: the repo's lambda/take-action directory), and sets the env vars the module needs at import time (AWS_DEFAULT_REGION=us-east-2, dummy AWS credentials, DYNAMODB_TABLE/SEND_LOG_TABLE/BOUNCE_TABLE/FLAGGED_TABLE/BOOSTED_TABLE, SES_SENDER_EMAIL) so import never touches AWS.
- No test makes a network or AWS call: lambda_function.dynamodb and lambda_function.ses are monkeypatched with in-process fakes (or botocore.stub.Stubber). moto is NOT installed and must not be imported.
- Tests exist, named recognisably, covering every one of: (a) filter_excluded; (b) get_bounced_emails pagination — fake scan returns LastEvaluatedKey on the first page and not the second, both pages' rows appear in the result; (c) get_bounced_emails classification — Bounce/Permanent in, Complaint in, Bounce/Transient out; (d) record_bounce_event against a realistic SES bounce notification JSON fixture; (e) record_bounce_event sender-skip rule — email == SES_SENDER_EMAIL writes nothing; (f) handle_send suppression path — a rep in the excluded set lands in failed with reason 'suppressed' and ses.send_email is never called for it; (g) handle_send ses_error path; (h) handle_send open-relay rejection — an email not in the session's verified set still yields 400; (i) handle_send already_sent — 409; (j) log_send item shape including priorities, source, location_city, location_state, representatives_offered, representatives_failed; (k) source sanitization — unknown key dropped, >200 chars truncated, empty map omitted; (l) normalized_location parsing and its fallback when the field is absent.
- No module-level reference to a function that does not yet exist in lambda_function.py (new symbols may only be referenced inside test bodies or fixtures), so collection succeeds even against the pre-change source.
- Running collection against a pristine copy of git HEAD's lambda_function.py succeeds with zero collection errors and at least 12 collected tests.

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
- ls -la C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/
- cat C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/conftest.py
- grep -rn 'moto\|boto3.client(' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ || echo 'no moto, no direct client construction'
- cd C:/Users/aisaa/Projects/photometricsai-website && mkdir -p "$TMPDIR/lfhead" && git show HEAD:lambda/take-action/lambda_function.py > "$TMPDIR/lfhead/lambda_function.py" && TAKE_ACTION_SRC="$TMPDIR/lfhead" python -m pytest lambda/take-action/tests --collect-only -q
- cd C:/Users/aisaa/Projects/photometricsai-website && python -m pytest lambda/take-action/tests --collect-only -q | tail -5
- grep -rn 'def test_' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-write-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
