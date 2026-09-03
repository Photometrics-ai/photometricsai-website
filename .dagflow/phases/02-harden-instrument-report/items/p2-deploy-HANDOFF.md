# p2-deploy — Handoff

**Status:** done
**Scope:** Deploy the hardened, instrumented Take Action Lambda (`lambda_function.py` at git HEAD `2d927f8748678fc39e4b06b4776d4daccee4088a`) to production (`photometrics-take-action`, us-east-2) via `bash lambda/take-action/deploy.sh`, and prove the running code is exactly the built artifact and initializes/serves without error.
**File owned/edited:** `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip` (rebuilt by `deploy.sh`; only file this item wrote). No commit/push (standing rule 4). No configuration/env/IAM/SES/GA4/Google Ads change of any kind (standing rule / assignment constraint — confirmed below).

---

## Required reading done first

- `.dagflow/phases/02-harden-instrument-report/items/p2-source-and-location-HANDOFF.md` — read in full.
- `.dagflow/phases/02-harden-instrument-report/items/p2-unit-tests-run-HANDOFF.md` — read in full (suite already green, 20/20, at handoff time).
- `.dagflow/phases/02-harden-instrument-report/items/p2-deploy-script-HANDOFF.md` — read in full (deploy.sh mechanics, python-zipfile fallback since `zip` is absent on this host, exit-code contract).

---

## PRE-FLIGHT (all passed — deploy would have been aborted otherwise)

1. `git rev-parse HEAD` → `2d927f8748678fc39e4b06b4776d4daccee4088a` — matches the assigned commit. `git status --porcelain` showed only an unrelated, out-of-boundary `.dagflow/phases/02-harden-instrument-report/DAG.md` modification (another item's work, untouched by this item).

2. `python -m pytest lambda/take-action/tests -q`:
   ```
   ....................                                                     [100%]
   20 passed in 0.07s
   ```

3. `python -c "import ast;ast.parse(open('lambda/take-action/lambda_function.py',encoding='utf-8').read())"` → no output / no exception, i.e. `SYNTAX OK`.

4. Pre-deploy state:
   ```
   AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus]' --output text
   ```
   ```
   vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=	2026-09-02T03:10:46.000+0000	Successful
   ```
   Matches the expected pre-deploy CodeSha256 given in the assignment exactly.

---

## DEPLOY

`bash lambda/take-action/deploy.sh` (real run, from repo root). **Full raw output** (env vars in the `update-function-code` response are redacted per standing rule (7) — `ANTHROPIC_API_KEY` and `GOOGLE_CIVIC_API_KEY` are secrets and must never be printed/copied; every other field is verbatim):

```
Packaging lambda_function.py -> function.zip
Updating function code for photometrics-take-action in us-east-2
{
    "FunctionName": "photometrics-take-action",
    "FunctionArn": "arn:aws:lambda:us-east-2:794038225197:function:photometrics-take-action",
    "Runtime": "python3.12",
    "Role": "arn:aws:iam::794038225197:role/photometrics-take-action-lambda-role",
    "Handler": "lambda_function.lambda_handler",
    "CodeSize": 20423,
    "Description": "",
    "Timeout": 120,
    "MemorySize": 256,
    "LastModified": "2026-09-03T21:06:10.000+0000",
    "CodeSha256": "r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=",
    "Version": "$LATEST",
    "Environment": {
        "Variables": {
            "SEND_LOG_TABLE": "photometrics-take-action-sends",
            "BOUNCE_TABLE": "photometrics-email-bounces",
            "DYNAMODB_TABLE": "photometrics-take-action",
            "BOOSTED_TABLE": "photometrics-boosted-officials",
            "SES_CONFIGURATION_SET": "take-action-sends",
            "SES_SENDER_EMAIL": "take-action@photometrics.ai",
            "GOOGLE_CIVIC_API_KEY": "[REDACTED per standing rule 7]",
            "ANTHROPIC_API_KEY": "[REDACTED per standing rule 7]"
        }
    },
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "f1bbc7cf-0731-4d4e-9bf8-e00fe4d5b1d2",
    "State": "Active",
    "LastUpdateStatus": "InProgress",
    "LastUpdateStatusReason": "The function is being created.",
    "LastUpdateStatusReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-2::runtime:c1ab740f3656a72d7917665a940f8634df245489445f5a660de5a634d06c5433"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/photometrics-take-action"
    }
}
Waiting for function update to complete
LOCAL  CodeSha256: r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=
REMOTE CodeSha256: r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=
Deploy verified. CodeSha256: r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=
```

`deploy.sh` exited 0 (the script's own sha comparison passed — no non-zero exit, no hand-patching needed).

**No `update-function-configuration` call, no env var change, no IAM change, no SES/GA4/Google Ads change was made.** `deploy.sh` only calls `update-function-code`, `wait function-updated`, and `get-function-configuration` (read). The `Environment.Variables` block shown above is Lambda's own response to `update-function-code` (it always echoes current config back) — this item did not set, edit, or touch any of those values.

**Artifact verification (step 5 of the assignment):**
```
python -c "import zipfile;z=zipfile.ZipFile('lambda/take-action/function.zip');print(z.namelist())"
→ ['lambda_function.py']

python -c "import zipfile,hashlib;z=zipfile.ZipFile('lambda/take-action/function.zip');a=z.read('lambda_function.py');b=open('lambda/take-action/lambda_function.py','rb').read();print('ZIP MATCHES WORKING TREE' if a==b else 'MISMATCH')"
→ ZIP MATCHES WORKING TREE
```
The zip contains exactly `lambda_function.py` at the archive root and its bytes are byte-identical to the working-tree file (which is git HEAD `2d927f8`, confirmed clean of any deploy-item edits).

---

## Local artifact hash vs. deployed CodeSha256 (acceptance criterion)

```
cd lambda/take-action && openssl dgst -sha256 -binary function.zip | base64
→ r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=
```
Equals the deployed `CodeSha256` exactly, and differs from the pre-deploy value `vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=`.

Post-settle confirmation:
```
AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus,Runtime,Role]' --output text
→ r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=	2026-09-03T21:06:10.000+0000	Successful	python3.12	arn:aws:iam::794038225197:role/photometrics-take-action-lambda-role
```
`LastUpdateStatus: Successful`, `Runtime: python3.12` (unchanged), `Role` (unchanged) — confirms no configuration drift.

**Pre-deploy CodeSha256:** `vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=`
**Post-deploy CodeSha256 (new, verbatim):** `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`

---

## POST-DEPLOY: Smoke invoke (read-only, no email sent, no row written)

Synthetic Function-URL v2.0 event, `rawPath: /send`, body:
```json
{
  "session_id": "test-smoke-1788469692",
  "name": "Test Constituent",
  "email": "test.citizen@example.com",
  "letter": "This is a non-empty test letter body for smoke testing the deploy.",
  "representatives": [
    {"name": "Test Official", "email": "success@simulator.amazonses.com", "title": "Test Title", "organization": "Test Org"}
  ]
}
```
(`session_id` prefix `test-`, per standing rule (2); this session does not exist in DynamoDB. Representative email is a real SES simulator address per standing rule (1). No real official was addressed.)

Invoked via `aws lambda invoke --function-name photometrics-take-action --region us-east-2 --cli-binary-format raw-in-base64-out --payload file://_smoke_event.json` → `{"StatusCode": 200, "ExecutedVersion": "$LATEST"}`.

**Raw response payload:**
```json
{"statusCode": 400, "headers": {"Content-Type": "application/json"}, "body": "{\"error\": \"We couldn't verify this session. Please generate your letter again.\"}"}
```

Exactly the expected outcome: HTTP 400, "couldn't verify this session" — proves the new module imported cleanly and the `/send` handler's session-verification path executed against the newly deployed code. No SES call was made (rejected before any send logic runs), no DynamoDB row was written.

Temp files `_smoke_event.json`/`_smoke_response.json` were created inside `lambda/take-action/` for the single invoke command and deleted immediately afterward in the same command — confirmed absent from `git status --porcelain` (they were never tracked/added).

---

## POST-DEPLOY: CloudWatch scan of the deploy/smoke window

```
MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time <now-5min in ms> --output json
```
**Raw output:**
```json
{
    "events": [
        {
            "logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10",
            "timestamp": 1788469694945,
            "message": "INIT_START Runtime Version: python:3.12.mainlinev2.v31\tRuntime Version ARN: arn:aws:lambda:us-east-2::runtime:c1ab740f3656a72d7917665a940f8634df245489445f5a660de5a634d06c5433\n",
            "ingestionTime": 1788469700185,
            "eventId": "39884206962262237034345270816056979902206612763524464640"
        },
        {
            "logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10",
            "timestamp": 1788469695644,
            "message": "START RequestId: f56c2ed4-7b70-43ef-9a7b-95a9b34ae5c5 Version: $LATEST\n",
            "ingestionTime": 1788469700185,
            "eventId": "39884206977850457928118176391990446974787817456204775425"
        },
        {
            "logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10",
            "timestamp": 1788469695814,
            "message": "END RequestId: f56c2ed4-7b70-43ef-9a7b-95a9b34ae5c5\n",
            "ingestionTime": 1788469700185,
            "eventId": "39884206981641584611868382326051519081138038912221446146"
        },
        {
            "logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10",
            "timestamp": 1788469695814,
            "message": "REPORT RequestId: f56c2ed4-7b70-43ef-9a7b-95a9b34ae5c5\tDuration: 168.98 ms\tBilled Duration: 866 ms\tMemory Size: 256 MB\tMax Memory Used: 96 MB\tInit Duration: 696.42 ms\t\n",
            "ingestionTime": 1788469700185,
            "eventId": "39884206981641584611868382326051519081138038912221446147"
        }
    ],
    "searchedLogStreams": []
}
```
Clean cold start (`INIT_START` → `START` → `END` → `REPORT`, `Init Duration: 696.42 ms`), no `ERROR`, no `Unable to import module`, no `Task timed out`, no traceback. No secret values appear in these lines — nothing was redacted from this block.

Additional targeted filters (assignment's verification-commands list), same 1-hour window, both empty (confirms no ERROR / import-failure anywhere in the surrounding hour, not just the 5-minute deploy window):
```
--filter-pattern 'ERROR'                      → {"events": [], "searchedLogStreams": []}
--filter-pattern 'Unable to import module'    → {"events": [], "searchedLogStreams": []}
```

---

## Explicit statement: no configuration/IAM/SES change was made

Only `aws lambda update-function-code`, `aws lambda wait function-updated`, and read-only `aws lambda get-function-configuration` / `aws lambda invoke` / `aws logs filter-log-events` calls were made by this item (via `deploy.sh` plus the smoke-invoke and log-scan steps I ran directly) — no `update-function-configuration`, no environment-variable change, no IAM/role change, no SES/GA4/Google Ads change of any kind.

---

## Commands / tests run, with outcomes (summary)

| Command | Outcome |
|---|---|
| `git rev-parse HEAD` | `2d927f8748678fc39e4b06b4776d4daccee4088a` |
| `python -m pytest lambda/take-action/tests -q` | 20 passed |
| `python -c "import ast;ast.parse(...)"` | syntax OK |
| pre-deploy `get-function-configuration` | `vtoOJDgbXwneH9v5Wg24Yj8lQ+0gtvA6n9nSd7gVI2E=`, `Successful` |
| `bash lambda/take-action/deploy.sh` | exit 0, LOCAL==REMOTE |
| zip namelist | `['lambda_function.py']` |
| zip bytes vs working tree | `ZIP MATCHES WORKING TREE` |
| `openssl dgst -sha256 -binary function.zip \| base64` | `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=` |
| post-deploy `get-function-configuration` | `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`, `Successful`, `python3.12`, unchanged role |
| smoke `aws lambda invoke` `/send` | `{"statusCode": 400, ... "couldn't verify this session"}` |
| CloudWatch scan (5-min window) | clean INIT/START/END/REPORT, no errors |
| CloudWatch `ERROR` filter (1hr) | empty |
| CloudWatch `Unable to import module` filter (1hr) | empty |
| `git checkout -- lambda/take-action/__pycache__/lambda_function.cpython-311.pyc` | reverted pytest's tracked-bytecode side effect |

---

## Decisions / assumptions

- Constituent email used in the smoke test (`test.citizen@example.com`) is a syntactically valid but non-real address — the assignment calls for "a valid-looking constituent email" (distinct from "one simulator representative address," which is the representative's email). Since the session-verification check short-circuits before any SES call, this choice has no observable effect on the test's outcome, but it keeps the constituent-email field realistic while the representative field uses the required SES simulator address.
- Temp payload/response files (`_smoke_event.json`, `_smoke_response.json`) were written and deleted within `lambda/take-action/` inside a single Bash invocation (this session's Bash tool does not reliably persist files written to `/tmp` or the nominal scratchpad path across separate tool calls on this host — confirmed by two failed round-trip attempts before falling back to an in-repo, same-command temp file). Confirmed via `git status --porcelain` that neither file is present/tracked after the run.
- Redacted `ANTHROPIC_API_KEY` and `GOOGLE_CIVIC_API_KEY` values from the pasted `deploy.sh` output per standing rule (7); every other field of that JSON response is verbatim. These are Lambda's pre-existing environment variables, echoed back by `update-function-code`'s response — not something this item set or changed.

## Interface / contract downstream work must follow

- New production CodeSha256 for `photometrics-take-action`: `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`. Downstream items (harness run, docs) should cite this value as the deployed artifact identity.
- The deployed code is git HEAD `2d927f8748678fc39e4b06b4776d4daccee4088a`'s `lambda_function.py`, unmodified — confirmed byte-identical between the zip, the working tree, and (transitively) git HEAD.
- `lambda/take-action/function.zip` in the working tree now reflects this deploy's artifact (git-tracked file, now modified vs. its prior committed state — left uncommitted per standing rule (4), for the lead to commit).

## Known limitations / risks

- Per NOTE ON SCOPE, the full end-to-end harness run (`p2-harness-run`) and its own CloudWatch window are explicitly out of scope for this item and were not attempted here. This item's smoke test only exercises the `/send` path's session-verification branch (a 400 short-circuit) — it does not exercise `/generate`, a successful `/send`, the new `source`/`normalized_location` write path, or the bounce-suppression logic end-to-end in production. That live-path verification is the harness item's job.
- The CloudWatch 5-minute-window scan captured only the smoke invoke's own cold-start log lines (no other traffic hit the function in that window) — a clean scan here is strong but not exhaustive; the harness item's own broader window is the fuller validation.

## Discovered

- Nothing new that blocks or changes this item's scope. `.dagflow/phases/02-harden-instrument-report/DAG.md` is modified in the working tree by some other concurrent process/item, outside this item's boundary — not touched.

## Files changed

- `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/function.zip` — rebuilt by `deploy.sh` (git-tracked, now modified vs. its prior committed state; left uncommitted per standing rule 4).
- `C:/Users/aisaa/Projects/photometricsai-website/.dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md` — this file (created).
- No other files created, edited, or deleted by this item. `lambda_function.py`, `deploy.sh`, `tests/` were read-only inputs, not touched.

## STANDING RULES compliance

1. Simulator address used for the representative in the smoke test (`success@simulator.amazonses.com`); no real official emailed; no CC used (test never reached the send/SES step — 400 short-circuit before any email logic).
2. `session_id` used `test-smoke-1788469692` (prefix `test-`); this item did not create a durable DynamoDB row (the 400 response confirms nothing was written) so there is nothing for this item to delete. `test-gap-framing-001`/`-004` were not touched or referenced.
3. Region `us-east-2` throughout; `AWS_PAGER=''` set on every `aws` call; `MSYS_NO_PATHCONV=1` prefixed on both `aws logs` calls under Git Bash.
4. No git commit or push performed.
5. This handoff, at the path above.
6. Zero `/generate` calls made (0 of the phase's 2-call Anthropic budget used by this item; explicitly avoided per assignment step 6).
7. `ANTHROPIC_API_KEY`/`GOOGLE_CIVIC_API_KEY` values redacted from the pasted deploy output; never printed elsewhere.
8. No Chrome/browser tools used.
