You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-harness-run
KIND: test
PURPOSE / EXPECTED OUTCOME:
Prove against production that the deployed Lambda actually suppresses a hard-bounced address at send time and writes the new attribution/location/failure fields on the sends row — then prove zero residue.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/README.md

SHARED/CONTENDED RESOURCES IN PLAY:
- aws:take-action-tables
- aws:ses-sending

ASSIGNMENT DETAIL:
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

ACCEPTANCE CRITERIA:
- `python funnel_test.py all` ran against production and exited 0, with every subcommand's assertions passing, including the new check-regenerate step.
- The raw output shows check-regenerate asserting failed_count 1 with reason 'suppressed' for dead.official@simulator.amazonses.com, and that address absent from representatives_sent.
- Independent corroboration via `aws dynamodb get-item` (not the harness's own output) shows the sends row for the run's session_id containing representatives_failed, representatives_offered, priorities, source and location_city, with values matching the contract.
- A CloudWatch filter-log-events scan over the harness run window shows no ERROR, no traceback, and no 'Task timed out' for /aws/lambda/photometrics-take-action.
- Post-cleanup residue proof: paginated scans of photometrics-take-action, photometrics-take-action-sends, photometrics-email-bounces and photometrics-boosted-officials show zero rows created by this run. Row counts return to the pre-run baseline (118 non-test generate rows + 4 sends, per p1-baseline-data-HANDOFF.md, allowing for any rows another concurrent item legitimately added).
- The pre-existing rows test-gap-framing-001 and test-gap-framing-004 still exist and are unmodified.
- No real official received email; the only non-simulator address involved is ari@sdgis.com as CC.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-email-bounces --region us-east-2 --filter-expression 'contains(email, :e)' --expression-attribute-values '{":e":{"S":"dead.official"}}' --output json
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
- AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{"session_id":{"S":"test-gap-framing-001"}}' --projection-expression 'session_id' --output json
- MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c "import time;print(int(time.time()*1000)-7200000)") --filter-pattern 'ERROR' --max-items 50 --output json
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus python funnel_test.py --dry-run all; echo "dry-run exit=$?"

CONTEXT BUDGET: sized to use no more than ~30% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
