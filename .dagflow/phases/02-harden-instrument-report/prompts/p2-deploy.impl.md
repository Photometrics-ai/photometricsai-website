You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-deploy
KIND: integration
PURPOSE / EXPECTED OUTCOME:
Put the hardened, instrumented Lambda into production and prove the running code is exactly the built artifact and that it initialises and serves without error.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
- .dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip

SHARED/CONTENDED RESOURCES IN PLAY:
- aws:lambda:photometrics-take-action

ASSIGNMENT DETAIL:
OBJECTIVE
Deploy the hardened Take Action Lambda to production and prove the deploy landed cleanly.

AUTHORIZATION
Production Lambda deploys are PRE-AUTHORIZED by Ari for this phase (2026-09-03). This item is the one authorized to deploy. You do NOT need to stop and ask. You may not change anything else: no function configuration, no environment variables, no IAM, no SES, no GA4, no Google Ads.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/function.zip (the build artifact deploy.sh produces). Do not edit lambda_function.py, deploy.sh, tests/, or anything else.
Shared resource: aws:lambda:photometrics-take-action — you are the only item touching the function during your run.

REQUIRED READING
- .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md (how deploy.sh works, incl. the python zipfile fallback — `zip` is not installed on this host)
- .dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md (confirm the suite is green before you ship)
- .dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md and p2-source-and-location-HANDOFF.md (what is going live)

PRE-FLIGHT (do these first, abort if any fails)
1. Re-run `python -m pytest lambda/take-action/tests -q` from the repo root yourself. If it is not green, STOP and report — do not deploy.
2. `python -c "import ast;ast.parse(open('lambda/take-action/lambda_function.py',encoding='utf-8').read())"`.
3. Record the pre-deploy state: `AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus]' --output text`. Expected pre-deploy CodeSha256: vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=.

DEPLOY
4. `bash lambda/take-action/deploy.sh` (real run). Capture full raw output. If deploy.sh exits non-zero on the sha comparison, STOP and report — do not hand-patch around it.
5. Confirm the zip contains exactly lambda_function.py at the archive root and that its bytes equal the working-tree file.

POST-DEPLOY CHECKS
6. Smoke invoke, read-only: `aws lambda invoke` with a synthetic Function-URL event for rawPath '/send' whose body has session_id 'test-smoke-<epoch>' (a session that does not exist), a valid-looking constituent email, a non-empty letter, and one simulator representative address. Expect HTTP 400 with the 'couldn't verify this session' error — that proves the module imported and the send path executed. It writes nothing and mails nothing. Paste the raw response payload. Do NOT invoke /generate (Anthropic tokens; the phase budget is reserved for another item).
7. CloudWatch: `MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time <now-5min in ms> --output json`. Scan for ERROR, 'Unable to import module', 'Task timed out', tracebacks. Paste the raw output (redact nothing except any accidental secret; if a log line would expose ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY, do not paste that line and say so).
8. Record the new CodeSha256 verbatim — the next items and the docs item depend on it.

NOTE ON SCOPE
The end-to-end harness run and its own CloudWatch window are a separate downstream item (p2-harness-run); do not attempt to run the harness here.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md containing: pre-deploy and post-deploy CodeSha256 (both verbatim), the local artifact base64 sha256, the full raw deploy.sh output, the raw smoke-invoke response, the raw CloudWatch output for the deploy window, and a one-line statement that no configuration/IAM/SES change was made.

ACCEPTANCE CRITERIA:
- `bash lambda/take-action/deploy.sh` ran to completion and exited 0 against function photometrics-take-action in us-east-2.
- The local artifact hash (`openssl dgst -sha256 -binary function.zip | base64`) equals the deployed CodeSha256 reported by `aws lambda get-function-configuration`, and the new CodeSha256 differs from the pre-deploy value vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=.
- The new CodeSha256 is recorded verbatim in the handoff.
- A read-only smoke invoke succeeded: a synthetic Function-URL /send event with a non-existent session_id 'test-smoke-<epoch>' returns HTTP 400 ('couldn't verify this session'), proving the new module imports and the send path runs. No email was sent and no row was written.
- A CloudWatch scan of /aws/lambda/photometrics-take-action covering the deploy window shows no ERROR, no 'Unable to import module', no 'Task timed out', and no unhandled exception; the raw filter-log-events output is pasted in the handoff.
- Nothing other than the function code changed: no update-function-configuration, no env var, IAM, SES, GA4 or Google Ads change.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus,Runtime,Role]' --output text
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action && openssl dgst -sha256 -binary function.zip | base64
- MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c "import time;print(int(time.time()*1000)-3600000)") --filter-pattern 'ERROR' --max-items 50 --output json
- MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c "import time;print(int(time.time()*1000)-3600000)") --filter-pattern 'Unable to import module' --max-items 20 --output json
- cd C:/Users/aisaa/Projects/photometricsai-website && python -c "import zipfile;z=zipfile.ZipFile('lambda/take-action/function.zip');print(z.namelist())"
- cd C:/Users/aisaa/Projects/photometricsai-website && python -c "import zipfile,hashlib;z=zipfile.ZipFile('lambda/take-action/function.zip');a=z.read('lambda_function.py');b=open('lambda/take-action/lambda_function.py','rb').read();print('ZIP MATCHES WORKING TREE' if a==b else 'MISMATCH')"

CONTEXT BUDGET: sized to use no more than ~20% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
