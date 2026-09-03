You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-unit-tests-run
KIND: test
PURPOSE / EXPECTED OUTCOME:
Run the pytest suite against the implemented Lambda source and get it fully green — the gate that must pass before anything is deployed to production.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
- .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-write-HANDOFF.md

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/lambda_function.py

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
OBJECTIVE
Get the Take Action unit test suite fully green against the implemented Lambda source. This is the gate in front of the production deploy: if it is not honestly green, nothing ships.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/tests/ (free to edit) and lambda/take-action/lambda_function.py (edit ONLY under the narrow allowance below). Nothing else.

REQUIRED READING
- .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-write-HANDOFF.md — the test-to-contract map (a)-(l) and which tests were expected to fail before the implementation landed.
- .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md

WHAT TO DO
1. Run `python -m pytest lambda/take-action/tests -q` from the repo root. Capture raw output.
2. For each failure, decide honestly which side is wrong:
   - Test wrong (fake shaped incorrectly, wrong expected key name, wrong wire format): fix the test. Record before/after of the assertion and why in the handoff.
   - Implementation wrong, OUTSIDE the authorization path: you may make a minimal fix to lambda_function.py. Keep it surgical; show the diff in the handoff.
   - Implementation wrong INSIDE the authorization path (get_verified_representative_emails, already_sent, or the suppression/failed-reason logic in handle_send): do NOT patch it. Stop, and report it in the handoff as a blocking finding with the exact failing assertion and your diagnosis. The lead will schedule a repair.
3. Re-run until green. Confirm the suite passes with bogus AWS credentials in the environment, proving no test touches AWS.

FORBIDDEN
- Do not delete, skip, xfail, loosen or tautologise a test to make the suite green. A verifier greps for skip/xfail markers and diffs lambda/take-action/tests/.
- Do not weaken any guard. The open-relay test (an unverified representative email must still produce 400) and the already_sent 409 test must pass on their original assertions.
- Do not deploy, do not call /generate, do not send email, do not make AWS write calls.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
pytest exits 0 with >=12 passing and 0 skipped. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md containing: the final raw pytest output (verbose enough to show every test name), a table of every change you made (file, what, why), the full diff of any lambda_function.py edit, and an explicit statement that no test was skipped or weakened.

ACCEPTANCE CRITERIA:
- `python -m pytest lambda/take-action/tests -q` from the repo root exits 0 with zero failures, zero errors, and at least 12 tests passing.
- The run made no AWS or network calls (evidenced by the fakes being in place and by the suite passing with bogus credentials in the environment).
- Every contract area (a)-(l) listed in p2-unit-tests-write-HANDOFF.md still has a passing test; no test was deleted, skipped, xfailed, or reduced to a tautology to make the suite green. Any test that was legitimately corrected is listed in the handoff with a before/after of the assertion and the reason.
- If lambda_function.py was modified, the change is minimal, is described line-by-line in the handoff with its diff, and does NOT weaken get_verified_representative_emails, already_sent, or the suppression check in handle_send. Any defect found in that authorization path is REPORTED, not patched.
- `git status --porcelain` shows changes confined to lambda/take-action/tests/, lambda/take-action/lambda_function.py, and .dagflow/.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cd C:/Users/aisaa/Projects/photometricsai-website && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus AWS_DEFAULT_REGION=us-east-2 python -m pytest lambda/take-action/tests -q
- cd C:/Users/aisaa/Projects/photometricsai-website && python -m pytest lambda/take-action/tests -q --tb=short | tail -20
- grep -rn 'skip\|xfail\|pytest.mark' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tests/ || echo 'no skips/xfails'
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff --stat
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -U15 -- lambda/take-action/lambda_function.py | grep -n -A15 -B5 'verified_emails\|already_sent\|suppressed' | head -80
- cd C:/Users/aisaa/Projects/photometricsai-website && git diff -- lambda/take-action/tests/

CONTEXT BUDGET: sized to use no more than ~25% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
