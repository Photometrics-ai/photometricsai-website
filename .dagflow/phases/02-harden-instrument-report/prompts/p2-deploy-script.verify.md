You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-deploy-script — Replace the manual zip-and-update-function-code ritual with a repeatable, verifying deploy script, so every future deploy proves the running CodeSha256 equals the artifact that was built.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh exists, is a bash script, and runs under Git Bash on this Windows host.
- `bash lambda/take-action/deploy.sh --dry-run` prints every command it would run, makes ZERO AWS calls, creates/modifies no files, and exits 0 — including with no or bogus AWS credentials in the environment.
- The script cds to its own directory (derived from $0, not a hardcoded absolute path or the caller's cwd) and packages ONLY lambda_function.py at the archive root.
- Packaging works on this host where the `zip` binary is ABSENT: the script detects that and falls back to `python -c` using the zipfile module, producing function.zip with lambda_function.py at the archive root.
- Real (non-dry-run) mode runs, in order: package -> `aws lambda update-function-code --function-name photometrics-take-action --region us-east-2 --zip-file fileb://function.zip` -> `aws lambda wait function-updated --function-name photometrics-take-action --region us-east-2` -> compute `openssl dgst -sha256 -binary function.zip | base64` -> `aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text` -> compare, print both values, and exit non-zero on mismatch.
- The script sets AWS_PAGER='' , uses `set -euo pipefail`, and prints the final CodeSha256 on success.
- Nothing in the script deploys anything else, changes function configuration, environment variables, IAM, or SES.

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
- cat C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh
- cd C:/Users/aisaa/Projects/photometricsai-website && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus bash lambda/take-action/deploy.sh --dry-run; echo "exit=$?"
- cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain lambda/take-action/
- cd /tmp && bash C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh --dry-run; echo "cwd-independent exit=$?"
- grep -n 'update-function-configuration\|iam\|sesv2\|put-\|delete-' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh || echo 'no config/IAM/SES/destructive commands'
- command -v zip || echo 'zip absent as expected — python fallback must be present'
- grep -n 'zipfile\|command -v zip' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh
- C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
