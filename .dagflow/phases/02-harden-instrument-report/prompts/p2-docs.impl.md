You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-docs
KIND: implementation
PURPOSE / EXPECTED OUTCOME:
Write down what now exists — the Lambda's operational shape and data contract in the repo's CLAUDE.md, and the current funnel state in the campaign doc — so the next person (or session) does not have to rediscover it.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-frontend-source-HANDOFF.md

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md
- C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
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

ACCEPTANCE CRITERIA:
- CLAUDE.md (website repo) gains a 'Take Action Lambda' section covering: function name photometrics-take-action, region us-east-2, account 794038225197, role photometrics-take-action-lambda-role; source path lambda/take-action/lambda_function.py; the route suffixes (/generate, /send, /track, /flag) plus the SNS bounce branch; environment variable NAMES only (no values) — DYNAMODB_TABLE, BOOSTED_TABLE, FLAGGED_TABLE, SEND_LOG_TABLE, BOUNCE_TABLE, ANTHROPIC_API_KEY, GOOGLE_CIVIC_API_KEY, SES_SENDER_EMAIL, SES_CONFIGURATION_SET; the five DynamoDB tables with their key schemas; the SES config set → SNS → Lambda bounce wiring; deploy via lambda/take-action/deploy.sh (and the note that `zip` is absent on this host so the python zipfile fallback runs); tests at lambda/take-action/tests/ run with `python -m pytest lambda/take-action/tests -q` (no moto; module-level clients are monkeypatched); the harness lambda/take-action/tools/funnel_test.py incl. check-regenerate and the simulator-only rule; the report tool lambda/take-action/tools/report.py and adgroups.json.
- CLAUDE.md documents the full data contract: the generate row's source map keys, location_city/state/country; the sends row's priorities, source, location_city/state, representatives_offered, representatives_failed (with reasons 'suppressed' and 'ses_error'); and the frontend's source payload plus the GA4 params landed_priorities, utm_content, preselected.
- No secret VALUE appears anywhere — names only. A grep for likely key material finds nothing.
- C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md's 'Funnel verification' section is updated to the current state: hard filter live (with the deployed CodeSha256), sender mailbox fixed, attribution + normalized location captured, report tool available and how to run it.
- The campaign doc keeps its existing readable-cold style: it describes the current state, not a changelog of what changed; no dated diff entries are appended.
- Every factual claim in both documents is traceable to a Phase 01 or Phase 02 handoff; the docs handoff lists claim → source handoff.
- Only the two owned files are modified.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -- CLAUDE.md
- grep -n -A5 'Take Action Lambda' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md | head -60
- grep -n 'photometrics-take-action\|deploy.sh\|funnel_test.py\|report.py\|representatives_failed\|location_city\|preselected' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md
- grep -rn -E 'sk-ant|AIza|AKIA|[A-Za-z0-9_-]{35,}' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md' || echo 'no secret-shaped strings'
- grep -n -A30 'Funnel verification' 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md'
- AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text

CONTEXT BUDGET: sized to use no more than ~30% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-docs-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-docs-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
