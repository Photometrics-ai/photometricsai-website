You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-report-verify
KIND: test
PURPOSE / EXPECTED OUTCOME:
Independently confirm the report tool's numbers are true — totals reconcile with the Phase 01 baseline once the harness and live-generate items have added and cleaned up their rows.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
- .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
(none — this is read-only work)

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
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

ACCEPTANCE CRITERIA:
- `python report.py` was run against production after p2-harness-run and p2-live-generate-check completed their cleanups, and its full raw markdown output is pasted in the handoff.
- The report's generated total equals 118 and its sends total equals 4 — the Phase 01 baseline — or any deviation is explained row by row with corroborating `aws dynamodb` CLI output showing exactly which session_ids account for it.
- Independent corroboration: paginated `aws dynamodb scan --select COUNT` on both tables, and a scan filtered on begins_with(session_id,'test-') showing only test-gap-framing-001 and test-gap-framing-004 remain.
- The 'pre-attribution' bucket accounts for all rows lacking `source` — consistent with no production traffic having been attributed yet.
- `--out <dir>` CSV output was produced and its row counts match the markdown cuts.
- No writes were made by this item.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python report.py --out "$TMPDIR/rptverify" >/dev/null && for f in "$TMPDIR/rptverify"/*.csv; do echo "$f: $(wc -l < "$f") lines"; done
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json

CONTEXT BUDGET: sized to use no more than ~20% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-report-verify-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-report-verify-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
