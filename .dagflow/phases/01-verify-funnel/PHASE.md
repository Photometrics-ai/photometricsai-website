# Phase 01: Verify the funnel as it exists today

## Objective

Establish, with independently reproducible evidence, exactly what the photometrics.ai/take-action/ funnel does today — the managed send path, the SES bounce pipeline, the bounce-exclusion lookup, the live UI and GA4 instrumentation, and the current data baseline — while changing nothing in lambda_function.py, take-action.html, Google Ads, GA4, or Lambda configuration. Build the reusable test harness that Phase 2 will re-run after it hardens the send path, and surface the two known problems (the take-action@photometrics.ai sender mailbox and the four keywords that cannot serve) as fully-specified decisions for Ari.

## Entry Criteria

- [x] Repo present and readable at C:/Users/aisaa/Projects/photometricsai-website, with lambda/take-action/lambda_function.py and layouts/_default/take-action.html on disk.
- [x] AWS CLI authenticated as IAM user 'ari' with admin-level access to account 794038225197; region us-east-2 reachable; AWS_PAGER='' set by each agent.
- [x] Python 3 available and boto3 importable (`python -c 'import boto3'` succeeds).
- [x] Chrome MCP tools (mcp__claude-in-chrome__*) available for read-only browser work in Google Ads, GA4, and the live site.
- [x] Directory .dagflow/phases/01-verify-funnel/items/ exists or can be created by each item.
- [x] Baseline table counts noted for comparison: photometrics-take-action 120 rows, photometrics-take-action-sends 4, photometrics-email-bounces 14.

## Exit Criteria

- [x] lambda/take-action/tools/funnel_test.py exists, compiles, dry-runs clean with no AWS calls, and has been executed green against production at least once.
- [x] The send path, the per-recipient deselect behavior, the edited-letter behavior, the SES->SNS->DynamoDB bounce pipeline, and the get_bounced_emails() read have each been confirmed by direct AWS CLI evidence independent of the harness's own assertions.
- [x] The live UI path has been walked in a real browser through generate, deselect, and letter edit — without any send — and take_action_submit has been observed in GA4.
- [x] A quantitative baseline of all three DynamoDB tables exists, including the hard-bounce rate of AI-discovered official addresses, with no constituent email addresses written to disk.
- [x] The take-action@photometrics.ai sender-mailbox problem and the four ineligible Google Ads keywords are each documented as a needs_human_decision with fully-specified, runnable options awaiting Ari.
- [x] C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md carries a current-state '## Funnel verification (2026-09-03)' section and a Test harness reference bullet.
- [x] Zero test residue: no session_id beginning 'test-' in photometrics-take-action or photometrics-take-action-sends, no simulator-address rows in photometrics-email-bounces, and the browser check's session row deleted.
- [x] No change was made to lambda_function.py, take-action.html, Lambda configuration, IAM, SES configuration, Google Ads, GA4, or Google Workspace.
- [x] At most two /generate calls were made across the entire phase.

## Phase Gate

Status: closed 2026-09-03 (all items done or parked as decisions; exit criteria checked by the lead via CLI: 2 pre-existing test- rows from before this phase (test-gap-framing-001/-004, dated 2026-03-03, excluded from baseline), 0 simulator bounce rows, sends=4, generate=120; /generate called 2x) — previously: open — all entry criteria verified by the lead on 2026-09-03 (aws sts get-caller-identity = user/ari; boto3 1.42.70; Chrome MCP connected; repo clean on master).

## Concurrency Limits

- `max_total`: 8
- `max_write`: 2

## Notes

Planner: opus/high, run wf_9b18b31e-88b. Tiering deviation notes:
- p1-harness-build: verifier raised from the guidance's sonnet/high (harness scripts) to opus/high. The lead's more specific rule — 'anything touching handle_send or the open-relay guard -> security_critical true, verifier opus' — governs, because this script is what constructs the recipient list handed to handle_send. A defect that admits a non-simulator address into representatives, or a cleanup that computes bounce-table delete keys wrongly, mails or destroys real data.
- p1-browser-ui-check, p1-sender-mailbox, p1-baseline-data: all three are investigation/analysis items that guidance would put at sonnet/medium verifier, but each is marked security_critical and given an opus/medium verifier for a specific reason. Browser check: one wrong click emails real Austin officials, and the evidence cannot be re-created by the verifier. Sender mailbox: the artifact carries the Lambda's env map, so a leak of ANTHROPIC_API_KEY or a dropped env var in the proposed update-function-configuration command is a real production/security failure. Baseline data: the handoff lands in a git repo and must contain constituent email domains only, so PII leakage is the failure mode.
- p1-docs: implementer raised from the guidance's haiku/medium to sonnet/medium. The item is not transcription — it synthesizes three technical handoffs into a document with an explicit 'readable cold' voice contract, must insert a section at a precise location in a 21KB file without disturbing anything else, and must preserve partial/negative findings (GA4 params unobservable because the property has zero custom dimensions; exclusion advisory-only) rather than rounding them into passes. Verifier left at sonnet/medium per guidance, since checking placement and tracing claims to handoffs is mechanical.
- Scheduling note, not a tiering deviation: p1-harness-run, p1-browser-ui-check and p1-baseline-data all declare shared_resources 'aws:take-action-tables' so they serialize. This is deliberate and is a correctness requirement, not caution — p1-baseline-data's counts would be polluted by the other two items' live rows, and the browser check's scan (location 'Austin, TX') overlaps the harness's seeded location, risking cross-deletion. p1-browser-ui-check and p1-keyword-research share 'browser:chrome-mcp' because two agents driving one Chrome instance would collide on tab focus and screenshots.
- p1-sender-mailbox and p1-keyword-research are deliberately left as leaf nodes with no downstream, despite p1-docs mentioning both topics. Making p1-docs depend on them would risk blocking the phase's main deliverable behind two items designed to terminate in needs_human_decision. p1-docs is instead briefed to incorporate those two handoffs if the files exist and otherwise to write from facts already established in its brief.
