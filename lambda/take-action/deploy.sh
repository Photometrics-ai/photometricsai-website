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
