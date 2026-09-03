You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-docs — Write down what now exists — the Lambda's operational shape and data contract in the repo's CLAUDE.md, and the current funnel state in the campaign doc — so the next person (or session) does not have to rediscover it.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- CLAUDE.md (website repo) gains a 'Take Action Lambda' section covering: function name photometrics-take-action, region us-east-2, account 794038225197, role photometrics-take-action-lambda-role; source path lambda/take-action/lambda_function.py; the route suffixes (/generate, /send, /track, /flag) plus the SNS bounce branch; environment variable NAMES only (no values) — DYNAMODB_TABLE, BOOSTED_TABLE, FLAGGED_TABLE, SEND_LOG_TABLE, BOUNCE_TABLE, ANTHROPIC_API_KEY, GOOGLE_CIVIC_API_KEY, SES_SENDER_EMAIL, SES_CONFIGURATION_SET; the five DynamoDB tables with their key schemas; the SES config set → SNS → Lambda bounce wiring; deploy via lambda/take-action/deploy.sh (and the note that `zip` is absent on this host so the python zipfile fallback runs); tests at lambda/take-action/tests/ run with `python -m pytest lambda/take-action/tests -q` (no moto; module-level clients are monkeypatched); the harness lambda/take-action/tools/funnel_test.py incl. check-regenerate and the simulator-only rule; the report tool lambda/take-action/tools/report.py and adgroups.json.
- CLAUDE.md documents the full data contract: the generate row's source map keys, location_city/state/country; the sends row's priorities, source, location_city/state, representatives_offered, representatives_failed (with reasons 'suppressed' and 'ses_error'); and the frontend's source payload plus the GA4 params landed_priorities, utm_content, preselected.
- No secret VALUE appears anywhere — names only. A grep for likely key material finds nothing.
- C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md's 'Funnel verification' section is updated to the current state: hard filter live (with the deployed CodeSha256), sender mailbox fixed, attribution + normalized location captured, report tool available and how to run it.
- The campaign doc keeps its existing readable-cold style: it describes the current state, not a changelog of what changed; no dated diff entries are appended.
- Every factual claim in both documents is traceable to a Phase 01 or Phase 02 handoff; the docs handoff lists claim → source handoff.
- Only the two owned files are modified.

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -- CLAUDE.md
- grep -n -A5 'Take Action Lambda' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md | head -60
- grep -n 'photometrics-take-action\|deploy.sh\|funnel_test.py\|report.py\|representatives_failed\|location_city\|preselected' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md
- grep -rn -E 'sk-ant|AIza|AKIA|[A-Za-z0-9_-]{35,}' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md' || echo 'no secret-shaped strings'
- grep -n -A30 'Funnel verification' 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md'
- AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-docs-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md
- C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
