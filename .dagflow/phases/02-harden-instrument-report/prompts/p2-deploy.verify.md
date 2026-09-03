You are an INDEPENDENT VERIFIER. You did not write this code and have not seen the implementer's prompt, reasoning, or chat history — that is deliberate. Determine, from actual repository state, whether this work item is genuinely complete. Treat the implementer's handoff and summary as claims to check, not facts.

REPO ROOT: C:/Users/aisaa/Projects/photometricsai-website
WORK ITEM: p2-deploy — Put the hardened, instrumented Lambda into production and prove the running code is exactly the built artifact and that it initialises and serves without error.

ACCEPTANCE CRITERIA (each must have concrete evidence — "the handoff says so" is not evidence):
- `bash lambda/take-action/deploy.sh` ran to completion and exited 0 against function photometrics-take-action in us-east-2.
- The local artifact hash (`openssl dgst -sha256 -binary function.zip | base64`) equals the deployed CodeSha256 reported by `aws lambda get-function-configuration`, and the new CodeSha256 differs from the pre-deploy value vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=.
- The new CodeSha256 is recorded verbatim in the handoff.
- A read-only smoke invoke succeeded: a synthetic Function-URL /send event with a non-existent session_id 'test-smoke-<epoch>' returns HTTP 400 ('couldn't verify this session'), proving the new module imports and the send path runs. No email was sent and no row was written.
- A CloudWatch scan of /aws/lambda/photometrics-take-action covering the deploy window shows no ERROR, no 'Unable to import module', no 'Task timed out', and no unhandled exception; the raw filter-log-events output is pasted in the handoff.
- Nothing other than the function code changed: no update-function-configuration, no env var, IAM, SES, GA4 or Google Ads change.

VERIFICATION COMMANDS — re-run every one yourself and record actual output:
- AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus,Runtime,Role]' --output text
- cd C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action && openssl dgst -sha256 -binary function.zip | base64
- MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c "import time;print(int(time.time()*1000)-3600000)") --filter-pattern 'ERROR' --max-items 50 --output json
- MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time $(python -c "import time;print(int(time.time()*1000)-3600000)") --filter-pattern 'Unable to import module' --max-items 20 --output json
- cd C:/Users/aisaa/Projects/photometricsai-website && python -c "import zipfile;z=zipfile.ZipFile('lambda/take-action/function.zip');print(z.namelist())"
- cd C:/Users/aisaa/Projects/photometricsai-website && python -c "import zipfile,hashlib;z=zipfile.ZipFile('lambda/take-action/function.zip');a=z.read('lambda_function.py');b=open('lambda/take-action/lambda_function.py','rb').read();print('ZIP MATCHES WORKING TREE' if a==b else 'MISMATCH')"

IMPLEMENTER'S HANDOFF (their claim): .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md
FILES CHANGED PER THE IMPLEMENTER: - (read the handoff for the list)
IMPLEMENTER'S OWNED BOUNDARY (verify nothing outside it was touched): - C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip

RULES: you are read-only with respect to repo files and AWS state (no edits, no writes, no deploys, no emails, no /generate calls unless the item's own brief explicitly reserves one for the verifier). Inspect changed files directly. Re-run each verification command. For each criterion mark met/not-met with concrete evidence. Default to rejecting if unsure.

Your FINAL MESSAGE must be exactly: first line `VERDICT: verified` or `VERDICT: rejected`; then `FINDINGS:` as a bullet list (specific, actionable, one per line; for verified, list the evidence per criterion briefly); then `SUMMARY:` 2-5 lines. Nothing else.
