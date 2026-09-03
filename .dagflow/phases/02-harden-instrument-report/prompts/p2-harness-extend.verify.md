You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-harness-extend — Extend the funnel test harness with attribution/location seeding and a check-regenerate subcommand that proves a hard-bounced address is suppressed on send — authored ahead of the deploy so only the run itself waits on production.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- funnel_test.py's `seed` writes a `source` map (contract keys) and `location_city`/`location_state`/`location_country` on the seeded generate row, in addition to everything it already wrote.
- A new subcommand `check-regenerate` exists and is listed in `--help` and in the `all` sequence.
- check-regenerate: (a) seeds a Permanent bounce row for dead.official@simulator.amazonses.com in photometrics-email-bounces (key schema email + timestamp) AND a matching row in photometrics-boosted-officials for region 'Austin, TX' using that table's ACTUAL key schema, discovered at runtime or documented from `aws dynamodb describe-table`; (b) adds dead.official@simulator.amazonses.com to the seeded generate row's representatives so it passes the open-relay guard; (c) invokes /send for the seeded session including that address; (d) asserts the response reports failed_count 1 with reason 'suppressed' for that address, and that ses did not mail it; (e) asserts the sends row contains representatives_failed (with the suppressed entry), representatives_offered, priorities, source, and location_city; (f) exits non-zero on any assertion failure.
- `cleanup` deletes everything check-regenerate created, including the bounce row and the boosted-officials row, and the existing cleanup behaviour is preserved.
- The harness still never calls /generate — grep confirms no '/generate' invocation path.
- All representative addresses remain SES mailbox-simulator addresses; the only real address anywhere is the --cc-email default ari@sdgis.com.
- `python funnel_test.py --dry-run all` prints the full plan including the new check-regenerate step, makes ZERO AWS calls, and exits 0 (works with bogus credentials).
- tools/README.md documents the new seed fields, the new subcommand, its assertions, and its cleanup.
- The pre-existing rows test-gap-framing-001 and test-gap-framing-004 are never targeted by any seed or cleanup path (cleanup must key off this run's own session_id / a test- prefix scoped to rows it created).

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && python funnel_test.py --help
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus AWS_DEFAULT_REGION=us-east-2 python funnel_test.py --dry-run all; echo "exit=$?"
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus python funnel_test.py --dry-run check-regenerate; echo "exit=$?"
- grep -n 'generate' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py | grep -v 'check-regenerate\|check_regenerate\|regenerate' | head -20
- grep -n '@' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py | grep -v simulator.amazonses.com | head -20
- grep -n 'test-gap-framing' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py || echo 'no reference to pre-existing rows (good)'
- AWS_PAGER='' aws dynamodb describe-table --table-name photometrics-boosted-officials --region us-east-2 --query 'Table.KeySchema' --output json
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain lambda/take-action/tools/

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/funnel_test.py
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools/README.md

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
