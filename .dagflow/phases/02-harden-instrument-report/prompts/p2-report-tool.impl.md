You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-report-tool
KIND: implementation
PURPOSE / EXPECTED OUTCOME:
Build the one command that answers 'which ad group, keyword, priority and city actually produced letters and sends' — the deliverable the whole phase exists to enable.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
(none — no predecessors)

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/adgroups.json

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
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

ACCEPTANCE CRITERIA:
- lambda/take-action/tools/report.py exists and runs read-only: it issues only dynamodb Scan calls (paginated with LastEvaluatedKey) and makes zero writes.
- Scans of photometrics-take-action use a ProjectionExpression that EXCLUDES the `letter` attribute; the sends-table scan likewise projects only what it needs.
- Rows whose session_id starts with 'test-' are excluded from every output.
- The two tables are joined on session_id; a generate row with no matching sends row still appears (counted as generated, not sent).
- Cut 1 (per ad group × keyword × top priority × location) outputs columns: ad group (utm_content resolved via adgroups.json; an id not in the map prints raw; a row with no source prints 'pre-attribution'), keyword (utm_term), top priority (priorities[0]), location (location_city + ', ' + location_state, falling back to the raw `location` string when the normalized fields are absent), generated, sent sessions, reps emailed (sum of len(representatives_sent)), suppressed (count of representatives_failed entries with reason 'suppressed'), hard bounces (representatives_sent addresses that appear in photometrics-email-bounces as Bounce/Permanent or Complaint).
- Cut 2 (priority × state) and a totals line are both produced.
- Output is markdown to stdout, and `--out <dir>` additionally writes CSV files (one per cut) into that directory.
- adgroups.json exists mapping placeholder ids 'TBD-1'..'TBD-7' to the 7 real ad group NAMES, with a clearly-labelled note field instructing the lead to replace the placeholder ids with the real numeric ad group ids from the Google Ads UI. The file is valid JSON (a JSON string field carries the note — JSON has no comments).
- The tool runs correctly TODAY against production, where no row has `source` and no row has location_city: every row buckets as 'pre-attribution' with the raw location, and totals match the Phase 01 baseline of 118 non-test generate rows and 4 sends.
- No crash on missing/None/empty attributes anywhere; no KeyError on a sends row with no representatives_failed.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py | head -60
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py --out "$TMPDIR/rpt" >/dev/null && ls -la "$TMPDIR/rpt"
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py | grep -i 'total'
- python -c "import json;d=json.load(open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/adgroups.json'));print(json.dumps(d,indent=2))"
- grep -n 'put_item\|delete_item\|update_item\|batch_write' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py || echo 'READ-ONLY: no write calls'
- grep -n 'ProjectionExpression\|LastEvaluatedKey\|letter' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text

CONTEXT BUDGET: sized to use no more than ~35% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
