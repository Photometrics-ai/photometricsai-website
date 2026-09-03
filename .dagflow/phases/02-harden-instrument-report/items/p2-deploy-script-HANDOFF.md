# p2-deploy-script — HANDOFF

## Status
Done. `deploy.sh` created; verified with `--dry-run` only. No real deploy was run in this item.

## What was accomplished
Wrote `lambda/take-action/deploy.sh`, a repeatable, self-verifying deploy script for the
`photometrics-take-action` Lambda (region us-east-2). It:
- `cd`s to its own directory (derived from `$0`), so it is caller-cwd independent.
- Packages `lambda_function.py` into `function.zip` at the archive root, preferring `zip -j`
  and falling back to a `python -c` zipfile-module packer when `zip` is absent (verified absent
  on this host — the fallback is the path that actually executes here).
- Runs `aws lambda update-function-code` then `aws lambda wait function-updated`.
- Computes local SHA-256 (`openssl dgst -sha256 -binary function.zip | base64`), reads the
  deployed `CodeSha256` via `aws lambda get-function-configuration --query CodeSha256`, prints
  both, and exits non-zero with a clear error message on mismatch; prints the CodeSha256 on
  success.
- Supports `--dry-run` (prints the full command plan, makes zero AWS calls, creates/modifies no
  files, exits 0, works with bogus/absent credentials) and `--function-name` (region stays
  pinned to us-east-2).
- Sets `set -euo pipefail` and `export AWS_PAGER=''`.
- Does not call `update-function-configuration`, and never touches env vars, IAM, SES, or Google
  Ads/GA4 (grep-verified — see below).

## Canonical outputs
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh` (new file, full
  text below).
- No new/modified `function.zip` — per the hard constraint, no real artifact was built into
  `lambda/take-action/`. The packaging fallback was proven separately in a scratch directory
  (see Verification below) and that scratch directory was deleted afterward.

### Full script text (`lambda/take-action/deploy.sh`)
```bash
#!/usr/bin/env bash
# Deploy script for the Take Action Lambda (photometrics-take-action).
#
# Packages lambda_function.py into function.zip, updates the Lambda's code,
# waits for the update to settle, then verifies the deployed CodeSha256
# matches the sha256 of the local artifact that was just uploaded.
#
# Usage:
#   ./deploy.sh                        # real deploy of photometrics-take-action
#   ./deploy.sh --function-name NAME   # deploy to a different function name
#   ./deploy.sh --dry-run              # print the command plan, make no AWS calls, touch no files
#
set -euo pipefail
export AWS_PAGER=''

# Always operate relative to this script's own directory, regardless of caller cwd.
cd "$(dirname "$0")"

REGION="us-east-2"
FUNCTION_NAME="photometrics-take-action"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --function-name)
      FUNCTION_NAME="$2"
      shift 2
      ;;
    --function-name=*)
      FUNCTION_NAME="${1#--function-name=}"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if command -v zip >/dev/null 2>&1; then
  PACKAGE_CMD='zip -j function.zip lambda_function.py'
else
  PACKAGE_CMD='python -c "import zipfile; zf = zipfile.ZipFile(\"function.zip\", \"w\", zipfile.ZIP_DEFLATED); zf.write(\"lambda_function.py\", arcname=\"lambda_function.py\"); zf.close()"'
fi

UPDATE_CODE_CMD="aws lambda update-function-code --function-name $FUNCTION_NAME --region $REGION --zip-file fileb://function.zip"
WAIT_CMD="aws lambda wait function-updated --function-name $FUNCTION_NAME --region $REGION"
LOCAL_SHA_CMD='openssl dgst -sha256 -binary function.zip | base64'
REMOTE_SHA_CMD="aws lambda get-function-configuration --function-name $FUNCTION_NAME --region $REGION --query CodeSha256 --output text"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run] cd $(pwd)"
  echo "[dry-run] package: $PACKAGE_CMD"
  echo "[dry-run] $UPDATE_CODE_CMD"
  echo "[dry-run] $WAIT_CMD"
  echo "[dry-run] LOCAL=\$($LOCAL_SHA_CMD)"
  echo "[dry-run] REMOTE=\$($REMOTE_SHA_CMD)"
  echo "[dry-run] compare LOCAL and REMOTE; exit non-zero on mismatch, else print CodeSha256"
  echo "[dry-run] no AWS calls made, no files created or modified."
  exit 0
fi

echo "Packaging lambda_function.py -> function.zip"
if command -v zip >/dev/null 2>&1; then
  zip -j function.zip lambda_function.py
else
  python -c "import zipfile; zf = zipfile.ZipFile('function.zip', 'w', zipfile.ZIP_DEFLATED); zf.write('lambda_function.py', arcname='lambda_function.py'); zf.close()"
fi

echo "Updating function code for $FUNCTION_NAME in $REGION"
aws lambda update-function-code --function-name "$FUNCTION_NAME" --region "$REGION" --zip-file fileb://function.zip

echo "Waiting for function update to complete"
aws lambda wait function-updated --function-name "$FUNCTION_NAME" --region "$REGION"

LOCAL=$(openssl dgst -sha256 -binary function.zip | base64)
REMOTE=$(aws lambda get-function-configuration --function-name "$FUNCTION_NAME" --region "$REGION" --query CodeSha256 --output text)

echo "LOCAL  CodeSha256: $LOCAL"
echo "REMOTE CodeSha256: $REMOTE"

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "ERROR: deployed CodeSha256 does not match local build artifact. Deploy verification FAILED." >&2
  exit 1
fi

echo "Deploy verified. CodeSha256: $REMOTE"
```

## Decisions / assumptions
- `--function-name` overrides only the function name; region stays hardcoded to `us-east-2` per
  spec even with the override.
- Unknown arguments cause the script to print an error and exit 1 (fail-closed rather than
  silently ignoring typos).
- Did not touch the pre-existing `lambda/take-action/function.zip` (dated Sep 1, unrelated to
  this item) — left byte-for-byte untouched; confirmed via unchanged mtime and no diff/git-status
  entry for it after all testing.
- Did not touch `lambda_function.py` (owned by a concurrent item) or `tools/adgroups.json`
  (unrelated untracked file already present, not created by this item).

## Interface / contract for downstream work
- The forthcoming "real deploy" item can run `bash lambda/take-action/deploy.sh` (no flags) from
  any cwd to package, deploy, wait, and verify CodeSha256 in one shot, or
  `bash lambda/take-action/deploy.sh --function-name <other>` to target a different function
  while staying in us-east-2.
- Exit code contract: `0` on success (or on `--dry-run`), non-zero on any AWS CLI failure
  (propagated via `set -e`) or on a CodeSha256 mismatch after deploy.

## Files changed
- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh` (new)
- No other files modified. `function.zip` was NOT created or modified by this item.

## Commands / tests run, with outcomes

1. `cat C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh`
   → printed full script text as above.

2. `cd C:/Users/aisaa/Projects/photometricsai-website && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus bash lambda/take-action/deploy.sh --dry-run; echo "exit=$?"`
   → output:
   ```
   [dry-run] cd /c/Users/aisaa/Projects/photometricsai-website/lambda/take-action
   [dry-run] package: python -c "import zipfile; zf = zipfile.ZipFile(\"function.zip\", \"w\", zipfile.ZIP_DEFLATED); zf.write(\"lambda_function.py\", arcname=\"lambda_function.py\"); zf.close()"
   [dry-run] aws lambda update-function-code --function-name photometrics-take-action --region us-east-2 --zip-file fileb://function.zip
   [dry-run] aws lambda wait function-updated --function-name photometrics-take-action --region us-east-2
   [dry-run] LOCAL=$(openssl dgst -sha256 -binary function.zip | base64)
   [dry-run] REMOTE=$(aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text)
   [dry-run] compare LOCAL and REMOTE; exit non-zero on mismatch, else print CodeSha256
   [dry-run] no AWS calls made, no files created or modified.
   exit=0
   ```

3. `cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain lambda/take-action/`
   → output:
   ```
   ?? lambda/take-action/deploy.sh
   ?? lambda/take-action/tools/adgroups.json
   ```
   (`tools/adgroups.json` is a pre-existing untracked file, not created by this item; not touched
   by this item.)

4. `cd /tmp && bash C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh --dry-run; echo "cwd-independent exit=$?"`
   → same dry-run output as step 2, ending `cwd-independent exit=0`. Confirms cwd-independence
   (run from `/tmp`, a different working directory than step 2's repo root).

5. `grep -n 'update-function-configuration\|iam\|sesv2\|put-\|delete-' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh || echo 'no config/IAM/SES/destructive commands'`
   → output: `no config/IAM/SES/destructive commands`

6. `command -v zip || echo 'zip absent as expected — python fallback must be present'`
   → output: `zip absent as expected — python fallback must be present` (confirms this host has
   no `zip` binary, so the dry-run's chosen `PACKAGE_CMD` above is genuinely the fallback path
   that would execute).

7. `grep -n 'zipfile\|command -v zip' C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/deploy.sh`
   → output:
   ```
   44:if command -v zip >/dev/null 2>&1; then
   47:  PACKAGE_CMD='python -c "import zipfile; zf = zipfile.ZipFile(\"function.zip\", \"w\", zipfile.ZIP_DEFLATED); zf.write(\"lambda_function.py\", arcname=\"lambda_function.py\"); zf.close()"'
   68:if command -v zip >/dev/null 2>&1; then
   71:  python -c "import zipfile; zf = zipfile.ZipFile('function.zip', 'w', zipfile.ZIP_DEFLATED); zf.write('lambda_function.py', arcname='lambda_function.py'); zf.close()"
   ```

8. Packaging-fallback proof, built in a scratch directory (NOT `lambda/take-action/`), per the
   hard constraint against generating a real `function.zip` in this item:
   ```
   SCRATCH=<session scratchpad>/deploy-fallback-test
   mkdir -p "$SCRATCH"
   cp lambda/take-action/lambda_function.py "$SCRATCH/lambda_function.py"
   cd "$SCRATCH"
   python -c "import zipfile; zf = zipfile.ZipFile('function.zip', 'w', zipfile.ZIP_DEFLATED); zf.write('lambda_function.py', arcname='lambda_function.py'); zf.close()"
   python -c "import zipfile; zf = zipfile.ZipFile('function.zip'); print(zf.namelist())"
   ```
   → output: `['lambda_function.py']` — confirms the archive's only member is `lambda_function.py`
   at the archive root (no directory prefix). Directory listing after the build:
   ```
   -rw-r--r-- 1 aisaa 197609 17014 Sep  3 13:35 function.zip
   -rw-r--r-- 1 aisaa 197609 57275 Sep  3 13:35 lambda_function.py
   ```
   The scratch directory was deleted afterward (`rm -rf "$SCRATCH"`), and
   `lambda/take-action/function.zip`'s mtime (Sep 1 20:10) and git-status entry were re-confirmed
   unchanged post-test.

No real deploy (no non-dry-run invocation) was performed in this item, per the hard constraint.

## Known limitations / risks
- The real (non-dry-run) path — `update-function-code` → `wait` → sha256 compare — was not
  exercised end-to-end against AWS in this item (only `--dry-run` was tested, as required). A
  separate integration item is responsible for the first real deploy and should treat that as the
  first live proof of the full success/mismatch logic.
- `--function-name` validation is minimal (no check that the name is non-empty or that a
  `--function-name` flag isn't followed by another flag); acceptable given this is an internal
  ops script, not user-facing.

## Discovered
- `lambda/take-action/tools/adgroups.json` is an untracked file already present in the working
  tree, unrelated to this item's scope. Not modified. Flagging in case another item or the lead
  needs to account for it.

## Verification summary
All 8 verification commands from the assignment were run and produced the expected outcomes
listed above. `deploy.sh --dry-run` exits 0 from two different cwds (repo root and `/tmp`) with
bogus credentials, prints the full command plan, and makes no AWS calls or file changes. The
python zipfile fallback (the only packaging path available on this host, since `zip` is absent)
was proven in an isolated scratch directory to produce an archive whose sole member is
`lambda_function.py` at the root.
