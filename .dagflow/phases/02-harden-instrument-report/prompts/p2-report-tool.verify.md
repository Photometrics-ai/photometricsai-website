You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-report-tool — Build the one command that answers 'which ad group, keyword, priority and city actually produced letters and sends' — the deliverable the whole phase exists to enable.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
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

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py | head -60
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py --out "$TMPDIR/rpt" >/dev/null && ls -la "$TMPDIR/rpt"
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py | grep -i 'total'
- python -c "import json;d=json.load(open(r'C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/adgroups.json'));print(json.dumps(d,indent=2))"
- grep -n 'put_item\|delete_item\|update_item\|batch_write' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py || echo 'READ-ONLY: no write calls'
- grep -n 'ProjectionExpression\|LastEvaluatedKey\|letter' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/report.py
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/adgroups.json

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
