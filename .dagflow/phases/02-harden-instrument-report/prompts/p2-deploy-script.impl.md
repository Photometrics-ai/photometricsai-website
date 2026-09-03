You are executing one independently-verifiable work item inside a larger dependency-aware phase. You have no access to any other agent's reasoning or chat history — everything you need is below or must be read from disk.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website

WORK ITEM: p2-deploy-script
KIND: implementation
PURPOSE / EXPECTED OUTCOME:
Replace the manual zip-and-update-function-code ritual with a repeatable, verifying deploy script, so every future deploy proves the running CodeSha256 equals the artifact that was built.

REQUIRED READING BEFORE ANY CHANGE — read every predecessor handoff in full first:
(none — no predecessors)

EXPECTED INPUTS / DURABLE SOURCE FILES:
(none specified)

FILES/MODULES/SERVICES YOU OWN (write only inside this boundary):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip

SHARED/CONTENDED RESOURCES IN PLAY:
(none)

ASSIGNMENT DETAIL:
OBJECTIVE
Write a repeatable, self-verifying deploy script for the Take Action Lambda. Deploying is currently manual (zip lambda_function.py, aws lambda update-function-code), with no proof that what is running equals what was built.

REPO / OWNERSHIP
Repo root: C:/Users/aisaa/Projects/photometricsai-website
You own: lambda/take-action/deploy.sh (new) and lambda/take-action/function.zip (the build artifact — only if you produce one; see below). Nothing else. In particular do NOT edit lambda_function.py — another item is editing it concurrently.

TARGET (verified)
Function: photometrics-take-action, region us-east-2, account 794038225197, role photometrics-take-action-lambda-role. Source: lambda/take-action/lambda_function.py, a single file with no third-party deps to bundle. Currently deployed CodeSha256: vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=.

HOST FACTS (verified on this machine — do not assume otherwise)
- Git Bash is the shell; `zip` is NOT installed. `openssl` (/mingw64/bin/openssl), `base64` (/usr/bin/base64), `python` 3.11.5, and `aws` (v2.18.6) ARE installed.
- Therefore the python zipfile fallback is the path that will actually execute here. Test that path, not just the `zip` branch.

SCRIPT REQUIREMENTS
1. `set -euo pipefail`; export AWS_PAGER=''.
2. cd to the script's own directory, derived from "$0" (e.g. `cd "$(dirname "$0")"`), so it works from any cwd.
3. Package: prefer `zip -j function.zip lambda_function.py` when `command -v zip` succeeds; otherwise `python -c` with the zipfile module writing lambda_function.py at the archive root (arcname 'lambda_function.py', no directory prefix — Lambda will not find the handler otherwise).
4. `aws lambda update-function-code --function-name photometrics-take-action --region us-east-2 --zip-file fileb://function.zip`
5. `aws lambda wait function-updated --function-name photometrics-take-action --region us-east-2`
6. Compute `LOCAL=$(openssl dgst -sha256 -binary function.zip | base64)`; read `REMOTE=$(aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text)`; print both; exit non-zero with a clear message on mismatch; print the CodeSha256 on success.
7. `--dry-run` flag: print every command that would run, make zero AWS calls, create or modify no files, exit 0. It must work with bogus/absent credentials.
8. Accept an optional `--function-name` override defaulting to photometrics-take-action, but keep the region pinned to us-east-2.

HARD CONSTRAINTS
- Do NOT run a real deploy from this item. A separate integration item does that, and Ari's pre-authorization for production deploys is scoped to that item. Test only with --dry-run.
- The script must never call update-function-configuration, touch environment variables, IAM, SES, or Google Ads/GA4.
- Do not edit lambda_function.py or generate a real function.zip in this item (a stale artifact would confuse the deploy item). If you build a zip while testing the packaging fallback, build it into a scratch directory, not into lambda/take-action/.

STANDING RULES (apply to every item in this phase)
(1) Simulator addresses only for any send test (success@/bounce@simulator.amazonses.com and plus-variants); never email a real official; the only real inbox allowed is ari@sdgis.com as CC. (2) Test rows use session_id prefix 'test-' and are deleted by the creating item; two pre-existing rows test-gap-framing-001/-004 from 2026-03 must be left alone. (3) Region us-east-2, AWS_PAGER=''. Under Git Bash prefix aws logs commands with MSYS_NO_PATHCONV=1. (4) Do NOT git commit or push — the lead commits; leave changes in the working tree. (5) Handoff at .dagflow/phases/02-harden-instrument-report/items/<id>-HANDOFF.md with raw command output. (6) /generate costs Anthropic tokens: at most 2 calls in this whole phase, only by the item explicitly allowed. (7) Do not print or copy the values of ANTHROPIC_API_KEY or GOOGLE_CIVIC_API_KEY anywhere. (8) No Chrome/browser tools.

DEFINITION OF DONE
deploy.sh exists and `bash lambda/take-action/deploy.sh --dry-run` exits 0 from at least two different working directories with bogus credentials, printing the full command plan. Handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md with the full script text, the raw --dry-run output, and evidence (raw output) that the python zipfile fallback produces an archive whose only member is 'lambda_function.py' at the root — built in a scratch directory.

ACCEPTANCE CRITERIA:
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh exists, is a bash script, and runs under Git Bash on this Windows host.
- `bash lambda/take-action/deploy.sh --dry-run` prints every command it would run, makes ZERO AWS calls, creates/modifies no files, and exits 0 — including with no or bogus AWS credentials in the environment.
- The script cds to its own directory (derived from $0, not a hardcoded absolute path or the caller's cwd) and packages ONLY lambda_function.py at the archive root.
- Packaging works on this host where the `zip` binary is ABSENT: the script detects that and falls back to `python -c` using the zipfile module, producing function.zip with lambda_function.py at the archive root.
- Real (non-dry-run) mode runs, in order: package -> `aws lambda update-function-code --function-name photometrics-take-action --region us-east-2 --zip-file fileb://function.zip` -> `aws lambda wait function-updated --function-name photometrics-take-action --region us-east-2` -> compute `openssl dgst -sha256 -binary function.zip | base64` -> `aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text` -> compare, print both values, and exit non-zero on mismatch.
- The script sets AWS_PAGER='' , uses `set -euo pipefail`, and prints the final CodeSha256 on success.
- Nothing in the script deploys anything else, changes function configuration, environment variables, IAM, or SES.

VERIFICATION COMMANDS (run every one that applies and record the exact outcome — a separate verifier will independently re-run these, so do not paper over a failure):
- cat C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh
- cd C:/Users/aisaa/Projects/photometricsai-website && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus bash lambda/take-action/deploy.sh --dry-run; echo "exit=$?"
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain lambda/take-action/
- cd /tmp && bash C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh --dry-run; echo "cwd-independent exit=$?"
- grep -n 'update-function-configuration\|iam\|sesv2\|put-\|delete-' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh || echo 'no config/IAM/SES/destructive commands'
- command -v zip || echo 'zip absent as expected — python fallback must be present'
- grep -n 'zipfile\|command -v zip' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh

CONTEXT BUDGET: sized to use no more than ~15% of your context window. If you reach roughly 60% before finishing: stop at a stable point, run focused verification, write a COMPLETE handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md describing exactly what's done/left, and report explicitly that this is a context-exhaustion handoff.

OWNERSHIP RULES:
- Do not edit any file outside your owned boundary above.
- Do not edit another work item's handoff document.
- If you discover a genuinely new prerequisite, conflicting assumption, or missing work, record it under a 'Discovered' heading in your handoff; if it blocks you, stop and report FAILED with a clear description rather than expanding scope.
- If completing this item genuinely requires a human decision with no safe default, report NEEDS_HUMAN_DECISION with the question and a suggested default. Reserve this for real blockers.

ON COMPLETION:
1. Produce your canonical output(s) inside your owned boundary.
2. Write a durable handoff at .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md covering: what was accomplished, canonical outputs, decisions/assumptions, any interface/contract downstream work must follow, files changed, commands/tests run with outcomes, known limitations/risks, discovered dependencies.
3. Your FINAL MESSAGE must be exactly this structure: first line one of `STATUS: done` / `STATUS: failed` / `STATUS: needs_human_decision`; second line `HANDOFF: <path>`; then `FILES_CHANGED:` list; then `SUMMARY:` 3-8 lines. Nothing else.

An independent verifier will re-run your verification commands and check your acceptance criteria against actual repo state — a plausible-sounding summary is not sufficient.
