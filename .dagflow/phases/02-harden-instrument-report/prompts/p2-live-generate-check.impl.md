You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-live-generate-check
KIND: test
PURPOSE / EXPECTED OUTCOME:
Spend the phase's one allowed /generate call to prove the deployed backend actually stores the source map and the Haiku-normalized city/state/country on a real generate row.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
(none — this is read-only work)

SHARED/CONTENDED RESOURCES IN PLAY:
- anthropic-api-budget
- aws:take-action-tables

ASSIGNMENT DETAIL:
OBJECTIVE
Prove, against the deployed production Lambda, that a real /generate call stores the attribution `source` map and the Haiku-normalized location on the generate row. This item is the ONLY one in the phase authorized to call /generate, and it may call it exactly once.

OWNERSHIP
You own no repo files. You write one handoff. Shared resources: anthropic-api-budget, aws:take-action-tables.

REQUIRED READING
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md (the deployed CodeSha256 — confirm it is current before you spend the call)
- .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md (exactly what the backend should now store, and the fallback behaviour)

WHAT TO DO
1. Confirm `aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256` equals the value in p2-deploy-HANDOFF.md. If it does not, STOP and report — do not spend the Anthropic call against unknown code.
2. Build a synthetic Function-URL event for rawPath ending '/generate' with a JSON body containing:
   - session_id: 'test-livegen-<epoch>'
   - location: 'Columbus, OH'
   - priorities: ['Migratory Birds']
   - name / email: a plausible constituent name and ari@sdgis.com (nothing is mailed by /generate)
   - source: {utm_source:'google', utm_medium:'cpc', utm_campaign:'TESTCAMP', utm_content:'TBD-2', utm_term:'migratory bird lighting', utm_match:'p', gclid:'TESTGCLID', landed_priorities:'Migratory Birds', referrer:'https://www.google.com/'}
   Match the event shape the existing harness uses for /send (see lambda/take-action/tools/funnel_test.py's send command) so the router takes the right branch.
3. Invoke via the AWS Lambda Invoke API (never over HTTPS, never through the real Function URL). ONE call. Capture the raw response payload.
4. `aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{"session_id":{"S":"test-livegen-<epoch>"}}'` and paste the RAW JSON (you may elide the `letter` attribute's body for length — say so — but paste `source`, `location_city`, `location_state`, `location_country`, `priorities`, and `representatives` in full).
5. Assert: source.utm_content == 'TBD-2' and the other eight keys present with the supplied values; location_city == 'Columbus'; location_state == 'OH'; location_country == 'US'. Print the returned representatives (name, title, email).
6. Pull the CloudWatch log stream for the invocation and quote the request id, START/END/REPORT lines and any hard-filter log line.
7. DELETE the row (`aws dynamodb delete-item`) and prove absence with a follow-up get-item returning no Item.

HARD CONSTRAINTS
- Exactly one /generate call. If an assertion fails, do NOT retry the call — report the failure with full evidence. (The phase holds one spare call, reserved for the verifier.)
- Do NOT invoke /send. Nothing is mailed by this item.
- Do not deploy, do not change configuration, IAM, SES, GA4 or Google Ads.
- Because your cleanup destroys the row, your handoff IS the evidence: paste raw command output for every step, in order, with timestamps, so an independent verifier can judge the chain without re-spending the budget.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

NOTE FOR THE VERIFIER (state this in the handoff)
The phase permits a second /generate call ONLY to a verifier that finds the evidence chain here inconsistent, and only if that verifier deletes its own row and says so.

DEFINITION OF DONE
Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md containing, in order: the CodeSha256 check, the exact event JSON sent, the raw invoke response, the raw get-item JSON, the assertion results, the returned representatives table, the CloudWatch excerpt with request id, the delete-item output, and the proof-of-absence get-item.

ACCEPTANCE CRITERIA:
- Exactly ONE /generate invocation was made in this item (the phase's allowed call), via the AWS Lambda Invoke API with a synthetic Function-URL event — evidenced by the raw invoke output and a matching CloudWatch request id.
- The event body included a `source` object with all nine contract keys populated with recognisable test values, location 'Columbus, OH', priorities ['Migratory Birds'], and a session_id prefixed 'test-'.
- The stored generate row, fetched with `aws dynamodb get-item` and pasted RAW, shows: `source` map containing utm_content and the other supplied keys with the supplied values (truncated to 200 chars where applicable); `location_city` = 'Columbus'; `location_state` = 'OH'; `location_country` = 'US'.
- The representatives returned by the invoke are printed (name, title, email) in the handoff.
- No email was sent — /send was not invoked.
- The generate row was deleted afterwards and its absence is proven by a get-item returning no Item.
- The CloudWatch log stream for the invocation is quoted (request id, START/END/REPORT lines, and the hard-filter log line if any officials were dropped), with no line exposing ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
- MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c "import time;print(int(time.time()*1000)-10800000)") --filter-pattern 'REPORT' --max-items 50 --output json
- MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c "import time;print(int(time.time()*1000)-10800000)") --filter-pattern 'Columbus' --max-items 20 --output json
- AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text

CONTEXT BUDGET: sized to use no more than ~20% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
