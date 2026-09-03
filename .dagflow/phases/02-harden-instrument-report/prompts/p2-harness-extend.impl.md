You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-harness-extend
KIND: implementation
PURPOSE / EXPECTED OUTCOME:
Extend the funnel test harness with attribution/location seeding and a check-regenerate subcommand that proves a hard-bounced address is suppressed on send — authored ahead of the deploy so only the run itself waits on production.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
(none — no predecessors)

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/README.md

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
OBJECTIVE
Extend the existing funnel test harness so it (a) seeds attribution + normalized location per the new data contract and (b) can prove, end to end against production, that a hard-bounced address is refused at send time with reason 'suppressed'. You WRITE the extension here; a separate downstream item runs it against production after the deploy.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/tools/funnel_test.py and lambda/take-action/tools/README.md. Nothing else — in particular do NOT edit lambda_function.py (a concurrent item owns it).

REQUIRED READING
- lambda/take-action/tools/funnel_test.py (existing, ~600 lines: subcommands seed | send | wait-bounce | check-sends | check-exclusion | cleanup | all, a JSON state file .funnel_test_state.json beside the script, dynamo_serialize/to_python helpers, a get_bounced_emails_paginated replica, and a --dry-run mode that makes zero AWS calls).
- lambda/take-action/tools/README.md (safety rules — keep them true).
- .dagflow/phases/01-verify-funnel/items/p1-harness-build-HANDOFF.md and p1-harness-run-HANDOFF.md (design intent and the last production run).

WHAT TO IMPLEMENT
1. `seed` additionally writes on the generate row: `source` (M) with contract keys — use recognisable test values, e.g. utm_source='google', utm_medium='cpc', utm_campaign='TESTCAMP', utm_content='TBD-1', utm_term='streetlight safety', utm_match='p', gclid='TESTGCLID', landed_priorities='Transportation Safety', referrer='https://www.google.com/' — plus `location_city`='Austin', `location_state`='TX', `location_country`='US'. Keep everything it already writes.
2. New subcommand `check-regenerate`, added to `--help` and inserted into the `all` sequence (before cleanup):
   a. Seed a Permanent bounce row for dead.official@simulator.amazonses.com into photometrics-email-bounces (key schema: email + timestamp) with event_type='Bounce', subtype='Permanent', shaped like the rows record_bounce_event writes.
   b. Seed a matching row into photometrics-boosted-officials for region 'Austin, TX'. Discover that table's key schema with `aws dynamodb describe-table --table-name photometrics-boosted-officials --region us-east-2` (read-only, safe to run now) and paste that output in your handoff; build the item to match it exactly.
   c. Add dead.official@simulator.amazonses.com to the seeded generate row's `representatives` list so it passes the Lambda's open-relay guard (which only allows addresses stored on the session's generate row).
   d. Invoke /send for the seeded session with a representatives list that includes that address (via the AWS Lambda Invoke API and a synthetic Function-URL event, exactly as the existing `send` does — never over HTTPS).
   e. Assert: the response reports failed_count 1 and a `failed` entry {email: dead.official@simulator.amazonses.com, reason: 'suppressed'}; the address is NOT in representatives_sent; the sends row for the session contains representatives_failed with that entry, plus representatives_offered, priorities, source and location_city.
   f. Exit non-zero with a clear message on any assertion failure.
3. `cleanup` removes everything check-regenerate created — the bounce row (email+timestamp key), the boosted-officials row (its real key), and all rows for this run's session_id across the three tables. Preserve existing cleanup behaviour.
4. Update README.md: the new seed fields, the new subcommand, what it asserts, what it cleans up, and the fact that /generate is still never called.

HARD CONSTRAINTS
- Do NOT run the harness against production in this item. --dry-run only. The production run is a separate item, gated on the deploy. Read-only `aws dynamodb describe-table` is allowed and expected.
- The harness must still never call /generate.
- Every representative address stays an SES mailbox-simulator address. The only real address permitted anywhere is the --cc-email default ari@sdgis.com.
- Cleanup must key off rows this run created; never touch the pre-existing rows test-gap-framing-001 or test-gap-framing-004.

DATA CONTRACT you are asserting against
Generate row gains `source` (M of S: utm_source, utm_medium, utm_campaign, utm_content, utm_term, utm_match, gclid, landed_priorities, referrer, each <=200 chars, absent keys omitted), `location_city` (S), `location_state` (S), `location_country` (S).
Sends row gains `priorities` (L of S), `source` (M), `location_city`, `location_state`, `representatives_offered` (N = len of the generate row's representatives), `representatives_failed` (L of M {email S, reason S}) with reason 'suppressed' or 'ses_error'. The /send response body gains a `failed` list of {email, reason}.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
`python funnel_test.py --dry-run all` and `--dry-run check-regenerate` both exit 0 with bogus credentials and print the full plan. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md with: the raw describe-table output for photometrics-boosted-officials, the raw --dry-run output for `all` and for `check-regenerate`, the diff of funnel_test.py, and an explicit list of every row check-regenerate creates paired with the cleanup call that deletes it.

ACCEPTANCE CRITERIA:
- funnel_test.py's `seed` writes a `source` map (contract keys) and `location_city`/`location_state`/`location_country` on the seeded generate row, in addition to everything it already wrote.
- A new subcommand `check-regenerate` exists and is listed in `--help` and in the `all` sequence.
- check-regenerate: (a) seeds a Permanent bounce row for dead.official@simulator.amazonses.com in photometrics-email-bounces (key schema email + timestamp) AND a matching row in photometrics-boosted-officials for region 'Austin, TX' using that table's ACTUAL key schema, discovered at runtime or documented from `aws dynamodb describe-table`; (b) adds dead.official@simulator.amazonses.com to the seeded generate row's representatives so it passes the open-relay guard; (c) invokes /send for the seeded session including that address; (d) asserts the response reports failed_count 1 with reason 'suppressed' for that address, and that ses did not mail it; (e) asserts the sends row contains representatives_failed (with the suppressed entry), representatives_offered, priorities, source, and location_city; (f) exits non-zero on any assertion failure.
- `cleanup` deletes everything check-regenerate created, including the bounce row and the boosted-officials row, and the existing cleanup behaviour is preserved.
- The harness still never calls /generate — grep confirms no '/generate' invocation path.
- All representative addresses remain SES mailbox-simulator addresses; the only real address anywhere is the --cc-email default ari@sdgis.com.
- `python funnel_test.py --dry-run all` prints the full plan including the new check-regenerate step, makes ZERO AWS calls, and exits 0 (works with bogus credentials).
- tools/README.md documents the new seed fields, the new subcommand, its assertions, and its cleanup.
- The pre-existing rows test-gap-framing-001 and test-gap-framing-004 are never targeted by any seed or cleanup path (cleanup must key off this run's own session_id / a test- prefix scoped to rows it created).

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python funnel_test.py --help
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus AWS_DEFAULT_REGION=us-east-2 python funnel_test.py --dry-run all; echo "exit=$?"
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus python funnel_test.py --dry-run check-regenerate; echo "exit=$?"
- grep -n 'generate' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py | grep -v 'check-regenerate\|check_regenerate\|regenerate' | head -20
- grep -n '@' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py | grep -v simulator.amazonses.com | head -20
- grep -n 'test-gap-framing' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py || echo 'no reference to pre-existing rows (good)'
- AWS_PAGER='' aws dynamodb describe-table --table-name photometrics-boosted-officials --region us-east-2 --query 'Table.KeySchema' --output json
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain lambda/take-action/tools/

CONTEXT BUDGET: sized to use no more than ~35% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
