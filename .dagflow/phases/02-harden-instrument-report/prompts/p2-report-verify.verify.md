You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-report-verify — Independently confirm the report tool's numbers are true — totals reconcile with the Phase 01 baseline once the harness and live-generate items have added and cleaned up their rows.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- `python report.py` was run against production after p2-harness-run and p2-live-generate-check completed their cleanups, and its full raw markdown output is pasted in the handoff.
- The report's generated total equals 118 and its sends total equals 4 — the Phase 01 baseline — or any deviation is explained row by row with corroborating `aws dynamodb` CLI output showing exactly which session_ids account for it.
- Independent corroboration: paginated `aws dynamodb scan --select COUNT` on both tables, and a scan filtered on begins_with(session_id,'test-') showing only test-gap-framing-001 and test-gap-framing-004 remain.
- The 'pre-attribution' bucket accounts for all rows lacking `source` — consistent with no production traffic having been attributed yet.
- `--out <dir>` CSV output was produced and its row counts match the markdown cuts.
- No writes were made by this item.

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py --out "$TMPDIR/rptverify" >/dev/null && for f in "$TMPDIR/rptverify"/*.csv; do echo "$f: $(wc -l < "$f") lines"; done
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-report-verify-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): (none — read-only work)

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
