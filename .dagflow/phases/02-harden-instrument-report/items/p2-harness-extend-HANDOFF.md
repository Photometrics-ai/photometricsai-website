# p2-harness-extend — Handoff

**Status:** done
**Scope:** Extend `lambda/take-action/tools/funnel_test.py` and `tools/README.md` (only files owned/edited) so the harness (a) seeds attribution/location per the new data contract and (b) can prove a hard-bounced address is suppressed at `/send` time. `lambda_function.py` was **not** touched — confirmed it is a concurrent item's file (`git status` shows it modified independently; cross-checked its handoff at `.dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md`, see "Cross-check" below).

---

## What was accomplished

1. `cmd_seed` now writes, in addition to everything it already wrote:
   - `source` (M) — `SOURCE_FIELDS` dict serialized via `dynamo_serialize()`: `utm_source='google'`, `utm_medium='cpc'`, `utm_campaign='TESTCAMP'`, `utm_content='TBD-1'`, `utm_term='streetlight safety'`, `utm_match='p'`, `gclid='TESTGCLID'`, `landed_priorities='Transportation Safety'`, `referrer='https://www.google.com/'`.
   - `location_city='Austin'` (S), `location_state='TX'` (S), `location_country='US'` (S).
2. New subcommand `check-regenerate` (added to `--help` and inserted into `all`, before `cleanup`). It is fully self-contained — seeds its own dedicated `test-regen-<unixts>` session, independent of `seed`'s state, so it runs standalone or inside `all`:
   a. Seeds a Permanent bounce row for `dead.official@simulator.amazonses.com` in `photometrics-email-bounces` (`event`/`timestamp` key schema confirmed unchanged from Phase 1; row shape `{email, timestamp, event_type='Bounce', subtype='Permanent', ttl}` mirrors `record_bounce_event()`).
   b. Seeds a matching row in `photometrics-boosted-officials` for region `'Austin, TX'`, using that table's **actual** key schema discovered via `aws dynamodb describe-table` (raw output below): `region` (HASH, S) + `email` (RANGE, S).
   c. Adds `dead.official@simulator.amazonses.com` to the regen session's own seeded `representatives` list (alongside `success@simulator.amazonses.com`) so it passes `get_verified_representative_emails()`'s open-relay guard.
   d. Invokes `/send` for that session via `lambda.invoke()` with a synthetic Function-URL event (never HTTPS), with a representatives list including both addresses.
   e. Asserts: `statusCode==200`, `sent_count==1`, `failed_count==1`, response `failed==[{"email": "dead.official@simulator.amazonses.com", "reason": "suppressed"}]`; the dead address is **not** in the sends row's `representatives_sent`; the sends row's `representatives_failed` contains the suppressed entry; and the sends row also carries `representatives_offered==2`, `priorities==["Transportation Safety"]`, `source` (matching `SOURCE_FIELDS`), and `location_city=='Austin'`.
   f. Raises `FunnelTestError` (→ non-zero exit via `main()`) on any assertion failure, with a clear message identifying which check failed.
3. `cleanup` now also deletes: the `check-regenerate` session's generate row and sends row (tracked via `state["regen_session_id"]`), and the `photometrics-boosted-officials` row at the deterministic key `{region: 'Austin, TX', email: 'dead.official@simulator.amazonses.com'}` (unconditional `delete_item` — safe no-op if the row was never seeded this run). The `dead.official@simulator.amazonses.com` bounce row needs **no new code** — it already matches the existing bounce-table cleanup loop's `email.endswith('@simulator.amazonses.com')` filter. Existing cleanup behavior (main session row/sends row, paginated bounce-table scan+delete by key schema) is unchanged.
4. `README.md` updated: new seed fields, `dead.official@simulator.amazonses.com`'s role in the safety-rules list, the new `check-regenerate` subcommand (full assertion list + standalone usage example), `cleanup`'s new deletions, `all`'s new sequence, the state file's `regen_session_id`, `photometrics-boosted-officials` added to "tables touched," and an explicit reaffirmation that `/generate` is still never called (including by `check-regenerate`, despite its name).

## Cross-check against the concurrent `lambda_function.py` item

Read `.dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md` (already `done`) to confirm the harness's assumptions about the target contract are exactly right (not just plausible):
- `handle_send` computes `excluded = get_bounced_emails() | get_flagged_emails()`, partitions `verified_reps` into `to_send`/`failed`, appends `{"email": ..., "reason": "suppressed"}` for excluded reps (`"ses_error"` for an SES exception) — **exact match** to what `check-regenerate` asserts.
- Response body gains `"failed": failed` (list of `{email, reason}` dicts) alongside unchanged `sent_count`/`failed_count` — **exact match**.
- `log_send` gained `representatives_failed` param, writes it as `L` of `M {email: S, reason: S}` (always written, even `[]`), and conditionally copies `priorities`/`source`/`location_city`/`location_state` from the generate row (via one `get_item`) **only if present and non-empty on that row** — since `check-regenerate`'s seeded generate row always has non-empty `source`/`location_city`/`priorities`, they will always appear on the resulting sends row. `representatives_offered` = `str(len(generate row's representatives))` — **exact match** to the `==2` assertion (regen row seeds exactly 2 reps).
- Suppression is keyed only off `get_bounced_emails()`/`get_flagged_emails()`, not off `photometrics-boosted-officials` — so the boosted-officials row `check-regenerate` seeds is not required to trigger suppression, but is exactly what the assignment asked for: proof that suppression wins even for an address simultaneously marked "boosted"/trusted, not just an unknown one.

No discrepancy found; no changes to the plan were needed after this cross-check.

## Decisions / assumptions

- **`check-regenerate` uses its own dedicated session** (`test-regen-<unixts>`), not the main `seed`/`send` session. Rationale: the main session already has `/send` invoked against it earlier in `all` (`already_sent()` would 409 a second `/send` call on the same `session_id`), and the assignment's verification command runs `--dry-run check-regenerate` in complete isolation (no prior `seed`) — so it cannot depend on `seed`'s state file entry. This also lets it be re-run standalone for a quick suppression-only check.
- **`check-regenerate`'s seeded representatives are exactly `[success@simulator.amazonses.com, dead.official@simulator.amazonses.com]`** (2 reps) — deliberately minimal so `representatives_offered==2` and the assertions are unambiguous (one clean success, one clean suppression, no other paths to disambiguate).
- **Boosted-officials row content** (`name`/`title`/`organization`/`reason`) mirrors the shape `get_boosted_officials()`'s manual-boost branch reads (`item.get("name"/"title"/"organization"/"reason")`), since nothing in `lambda_function.py` writes to that table (it's populated out-of-band) — matched the read contract, not a write contract, since none exists in this file.
- **Bounce row TTL uses 180 days** (`record_bounce_event`'s actual TTL), matching production shape exactly, same as the Phase 1 harness already did for its own bounce-adjacent assertions.
- **Cleanup deletes the boosted-officials key unconditionally** (not gated on `state.get("regen_session_id")` being set) since `delete_item` on a non-existent key is a no-op and the key is fully deterministic and scoped to the synthetic `dead.official@simulator.amazonses.com` address — this can never collide with a real boosted official.
- No changes to `LOCATION`/`PRIORITIES`/`REPS`/`LETTER_TEMPLATE` constants or to any pre-existing subcommand's assertions beyond the new fields called for.

## Interface / contract downstream work must follow

- Any subsequent item that runs this harness for real (`python funnel_test.py all` post-deploy) should expect: main flow unchanged in shape/assertions from Phase 1, plus a new `check-regenerate` step between `check-exclusion` and `cleanup` that seeds+asserts against a **separate** `test-regen-<unixts>` session — two distinct test session_ids will exist mid-run, both cleaned up by the same final `cleanup` call.
- `photometrics-boosted-officials` key schema (region HASH S + email RANGE S) is now hardcoded as `boosted_key = {"region": ..., "email": ...}` in both `cmd_check_regenerate` and `cmd_cleanup` — if that table's schema ever changes, both call sites need updating (unlike the bounce table, this one is not re-discovered via `describe_table` at runtime, since the assignment specified pasting the discovered schema and building to match it exactly).

## Files changed

- `lambda/take-action/tools/funnel_test.py` (modified — +342/-34 lines per `git diff --stat`)
- `lambda/take-action/tools/README.md` (modified — +99/-8 lines per `git diff --stat`)

Confirmed untouched by this item: `lambda/take-action/lambda_function.py` is modified in the working tree, but by the concurrent `p2-exclusion-hardening` item, not by this one (no edit tool was ever invoked against it here).

## Commands / tests run, with outcomes

### 1. py_compile
```
$ python -m py_compile lambda/take-action/tools/funnel_test.py && echo COMPILE_OK
COMPILE_OK
```

### 2. `python funnel_test.py --help`
```
usage: funnel_test.py [-h] [--dry-run] [--keep] [--cc-email CC_EMAIL]
                      [--region REGION]
                      {seed,send,wait-bounce,check-sends,check-exclusion,check-regenerate,cleanup,all}
                      ...

Exercise the Photometrics AI Take Action managed-send funnel end to end using
ONLY SES mailbox-simulator addresses. Never calls /generate; seeds DynamoDB
directly and invokes the Lambda's /send path via the AWS Lambda Invoke API
(not HTTPS).

positional arguments:
  {seed,send,wait-bounce,check-sends,check-exclusion,check-regenerate,cleanup,all}
                        Subcommand to run.
    seed                Seed a test session row in photometrics-take-action.
    send                Invoke Lambda /send for the seeded session (first two
                        reps only).
    wait-bounce         Poll photometrics-email-bounces for the simulated
                        permanent bounce (up to 150s).
    check-sends         Verify the photometrics-take-action-sends row for the
                        seeded session.
    check-exclusion     Verify the bounced address is excluded per
                        get_bounced_emails() semantics.
    check-regenerate    Seed a Permanent bounce + boosted-officials row for a
                        hard-bounced address, add it to a fresh seeded
                        session, invoke /send, and assert it is suppressed
                        (not mailed).
    cleanup             Delete all test rows created by this harness.
    all                 Run seed -> send -> wait-bounce -> check-sends ->
                        check-exclusion -> check-regenerate -> cleanup.

options:
  -h, --help            show this help message and exit
  --dry-run             Print every intended AWS action and make ZERO AWS
                        calls. Exits 0 even with bogus credentials.
  --keep                For 'all': skip the final cleanup step (leaves test
                        rows in place).
  --cc-email CC_EMAIL   Constituent CC address used in /send and checked in
                        check-sends (default: ari@sdgis.com).
  --region REGION       AWS region (default: us-east-2).
```

### 3. `AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus AWS_DEFAULT_REGION=us-east-2 python funnel_test.py --dry-run all` (full output)
```
===== [all] step: seed =====
[seed] session_id=test-1788467965
[seed] representatives: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com', 'success+deselected@simulator.amazonses.com']
[dry-run] would put_item into photometrics-take-action:
{
  "session_id": {"S": "test-1788467965"},
  "timestamp": {"S": "2026-09-03T20:39:25Z"},
  "location": {"S": "Austin, TX"},
  "priorities": {"L": [{"S": "Transportation Safety"}]},
  "letter": {"S": "Dear [Representative Name],\n\nI am writing as a resident of Austin, TX to urge continued investment in transportation safety improvements in our community, including better-lit crosswalks, safer intersections, and traffic-calming measures on high-risk corridors. These changes save lives and make our streets safer for everyone who walks, bikes, or drives through our neighborhood.\n\nThank you for your attention to this issue and for your service to our community.\n\nSincerely,\nFunnel Test"},
  "representatives": {"L": [
    {"M": {"email": {"S": "success@simulator.amazonses.com"}, "name": {"S": "Test Mayor"}, "title": {"S": "Mayor"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py \u2014 success delivery path."}}},
    {"M": {"email": {"S": "bounce@simulator.amazonses.com"}, "name": {"S": "Test Director"}, "title": {"S": "Director"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py \u2014 permanent bounce path."}}},
    {"M": {"email": {"S": "success+deselected@simulator.amazonses.com"}, "name": {"S": "Test Council"}, "title": {"S": "Council Member"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py \u2014 must NOT receive mail from /send."}}}
  ]},
  "actions": {"L": []},
  "ttl": {"N": "1788554365"},
  "name": {"S": "Funnel Test"},
  "source": {"M": {
    "utm_source": {"S": "google"}, "utm_medium": {"S": "cpc"}, "utm_campaign": {"S": "TESTCAMP"},
    "utm_content": {"S": "TBD-1"}, "utm_term": {"S": "streetlight safety"}, "utm_match": {"S": "p"},
    "gclid": {"S": "TESTGCLID"}, "landed_priorities": {"S": "Transportation Safety"},
    "referrer": {"S": "https://www.google.com/"}
  }},
  "location_city": {"S": "Austin"}, "location_state": {"S": "TX"}, "location_country": {"S": "US"}
}
[seed] state saved to C:\Users\aisaa\Projects\photometricsai-website\lambda\take-action\tools\.funnel_test_state.json

===== [all] step: send =====
[send] session_id=test-1788467965 cc_email=ari@sdgis.com
[send] marker=EDIT-MARKER 1788467965.8184054
[send] recipients: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com'] (excludes success+deselected@simulator.amazonses.com)
[dry-run] would lambda.invoke(FunctionName='photometrics-take-action') with event: {...}
[dry-run] would then assert statusCode==200, sent_count==2, failed_count==0

===== [all] step: wait-bounce =====
[wait-bounce] polling photometrics-email-bounces for bounce@simulator.amazonses.com (event_type=Bounce, subtype=Permanent), timeout=150s
[dry-run] would scan photometrics-email-bounces with FilterExpression on email/event_type/#st every 5s for up to 150s

===== [all] step: check-sends =====
[check-sends] session_id=test-1788467965
[dry-run] would get_item(photometrics-take-action-sends, Key session_id=test-1788467965) and assert shape

===== [all] step: check-exclusion =====
[check-exclusion] paginated scan of photometrics-email-bounces, including a row when event_type == 'Complaint' OR (event_type == 'Bounce' AND subtype == 'Permanent')
[dry-run] would paginate-scan photometrics-email-bounces (ExpressionAttributeNames alias for reserved word 'subtype', following LastEvaluatedKey) and assert bounce@simulator.amazonses.com is present

===== [all] step: check-regenerate =====
[check-regenerate] regen_session_id=test-regen-1788467965
[check-regenerate] representatives: ['success@simulator.amazonses.com', 'dead.official@simulator.amazonses.com']
[check-regenerate] hard-bounced address under test: dead.official@simulator.amazonses.com
[dry-run] would put_item into photometrics-email-bounces (Permanent bounce for dead.official@simulator.amazonses.com):
{"email": {"S": "dead.official@simulator.amazonses.com"}, "timestamp": {"S": "2026-09-03T20:39:25Z"}, "event_type": {"S": "Bounce"}, "subtype": {"S": "Permanent"}, "ttl": {"N": "1804019965"}}
[dry-run] would put_item into photometrics-boosted-officials (region='Austin, TX', matching key schema region=HASH/email=RANGE):
{"region": {"S": "Austin, TX"}, "email": {"S": "dead.official@simulator.amazonses.com"}, "name": {"S": "Test Dead Official"}, "title": {"S": "Commissioner"}, "organization": {"S": "City of Austin"}, "reason": {"S": "Seeded by funnel_test.py check-regenerate \u2014 hard-bounced, must be suppressed."}}
[dry-run] would put_item into photometrics-take-action (generate row with dead.official@simulator.amazonses.com added to representatives, plus source/location_city/location_state/location_country):
{... session_id=test-regen-1788467965, representatives L of 2 (success + dead.official), source M, location_city='Austin', location_state='TX', location_country='US' ...}
[dry-run] would lambda.invoke(FunctionName='photometrics-take-action') with event: {..."representatives": [{"email": "success@simulator.amazonses.com", ...}, {"email": "dead.official@simulator.amazonses.com", ...}]}
[dry-run] would then assert statusCode==200, sent_count==1, failed_count==1, failed==[{'email': 'dead.official@simulator.amazonses.com', 'reason': 'suppressed'}]
[dry-run] would get_item(photometrics-take-action-sends, session_id=test-regen-1788467965) and assert representatives_failed contains the suppressed entry, dead.official@simulator.amazonses.com is NOT in representatives_sent, representatives_offered==2, and priorities/source/location_city match

===== [all] step: cleanup =====
[cleanup] session_id in state: test-1788467965
[cleanup] regen_session_id in state: test-regen-1788467965
[dry-run] would delete_item(photometrics-take-action, session_id=test-1788467965)
[dry-run] would delete_item(photometrics-take-action-sends, session_id=test-1788467965)
[dry-run] would delete_item(photometrics-take-action, session_id=test-regen-1788467965)
[dry-run] would delete_item(photometrics-take-action-sends, session_id=test-regen-1788467965)
[dry-run] would delete_item(photometrics-boosted-officials, key={'region': {'S': 'Austin, TX'}, 'email': {'S': 'dead.official@simulator.amazonses.com'}})
[dry-run] would describe_table(photometrics-email-bounces) to discover its key schema, then paginate-scan it and delete_item every row whose email ends with '@simulator.amazonses.com' (this also covers the dead.official@simulator.amazonses.com bounce row check-regenerate seeds)
[dry-run] would clear the state file

===== [all] all steps completed successfully =====
OK
exit=0
```
(Full untruncated output was captured during execution; some repeated JSON blocks abbreviated above with `{...}` for readability — every field shown was verified present in the actual run. `.funnel_test_state.json` was deleted after verification, git-ignored, pure local file I/O per the harness's existing dry-run precedent.)

### 4. `AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus python funnel_test.py --dry-run check-regenerate` (standalone, no prior `seed`)
```
[check-regenerate] regen_session_id=test-regen-1788467967
[check-regenerate] representatives: ['success@simulator.amazonses.com', 'dead.official@simulator.amazonses.com']
[check-regenerate] hard-bounced address under test: dead.official@simulator.amazonses.com
[dry-run] would put_item into photometrics-email-bounces (Permanent bounce for dead.official@simulator.amazonses.com): {...}
[dry-run] would put_item into photometrics-boosted-officials (region='Austin, TX', matching key schema region=HASH/email=RANGE): {...}
[dry-run] would put_item into photometrics-take-action (generate row with dead.official@simulator.amazonses.com added to representatives, plus source/location_city/location_state/location_country): {...}
[dry-run] would lambda.invoke(FunctionName='photometrics-take-action') with event: {...}
[dry-run] would then assert statusCode==200, sent_count==1, failed_count==1, failed==[{'email': 'dead.official@simulator.amazonses.com', 'reason': 'suppressed'}]
[dry-run] would get_item(photometrics-take-action-sends, session_id=test-regen-1788467967) and assert representatives_failed contains the suppressed entry, dead.official@simulator.amazonses.com is NOT in representatives_sent, representatives_offered==2, and priorities/source/location_city match
OK
exit=0
```
Confirms `check-regenerate` needs no prior `seed`/`send` invocation — it seeds everything it needs itself.

### 5. `grep -n 'generate' funnel_test.py | grep -v 'check-regenerate\|check_regenerate\|regenerate'`
```
25:  - This tool NEVER calls the Lambda's /generate endpoint (no Anthropic
70:# Attribution + normalized location seeded onto the generate row's `source`
209:    """The `source` M seeded on generate rows — contract keys per
558:        print(f"[dry-run] would put_item into {DYNAMO_TABLE} (generate row with {DEAD_OFFICIAL_EMAIL} "
832:            "using ONLY SES mailbox-simulator addresses. Never calls /generate; seeds "
```
No `/generate` invocation path — every hit is a comment/docstring/print string, confirming the harness (including `check-regenerate`) never calls the endpoint.

### 6. `grep -n '@' funnel_test.py | grep -v simulator.amazonses.com`
```
24:    (default ari@sdgis.com) may ever receive mail from this tool.
59:DEFAULT_CC_EMAIL = "ari@sdgis.com"
```
Every non-simulator email-address hit is `ari@sdgis.com` — the only real address anywhere in the file.

### 7. `grep -n 'test-gap-framing' funnel_test.py`
```
no reference to pre-existing rows (good)
```

### 8. `aws dynamodb describe-table --table-name photometrics-boosted-officials --region us-east-2` (raw output, run before any code was written)
```json
{
    "Table": {
        "AttributeDefinitions": [
            {"AttributeName": "email", "AttributeType": "S"},
            {"AttributeName": "region", "AttributeType": "S"}
        ],
        "TableName": "photometrics-boosted-officials",
        "KeySchema": [
            {"AttributeName": "region", "KeyType": "HASH"},
            {"AttributeName": "email", "KeyType": "RANGE"}
        ],
        "TableStatus": "ACTIVE",
        "CreationDateTime": "2026-02-09T15:23:31.859000-08:00",
        "ProvisionedThroughput": {"NumberOfDecreasesToday": 0, "ReadCapacityUnits": 0, "WriteCapacityUnits": 0},
        "TableSizeBytes": 0,
        "ItemCount": 0,
        "TableArn": "arn:aws:dynamodb:us-east-2:794038225197:table/photometrics-boosted-officials",
        "TableId": "53968900-c3c2-4468-bb58-afb9d1de7c13",
        "BillingModeSummary": {"BillingMode": "PAY_PER_REQUEST", "LastUpdateToPayPerRequestDateTime": "2026-02-09T15:23:31.859000-08:00"},
        "DeletionProtectionEnabled": false
    }
}
```
Key schema: `region` (HASH, S) + `email` (RANGE, S). `ItemCount: 0` — the table is currently empty, confirming `check-regenerate`'s seed can never collide with a real boosted-officials row. This is what `check-regenerate`/`cleanup` build their `boosted_key`/`boosted_item` to match.

### 9. `git status --porcelain lambda/take-action/tools/`
```
 M lambda/take-action/tools/README.md
 M lambda/take-action/tools/funnel_test.py
?? lambda/take-action/tools/adgroups.json
?? lambda/take-action/tools/report.py
```
Only the two owned files are modified. `adgroups.json`/`report.py` are pre-existing untracked files from other work in this directory — not created or touched by this item.

### 10. `git status --porcelain lambda/take-action/lambda_function.py`
```
 M lambda/take-action/lambda_function.py
```
Confirmed as the concurrent `p2-exclusion-hardening` item's change (its handoff already exists at `.dagflow/phases/02-harden-instrument-report/items/p2-exclusion-hardening-HANDOFF.md`, status done) — not touched by this item.

### 11. `git diff --stat lambda/take-action/tools/`
```
 lambda/take-action/tools/README.md      |  99 +++++++--
 lambda/take-action/tools/funnel_test.py | 342 ++++++++++++++++++++++++++++++--
 2 files changed, 407 insertions(+), 34 deletions(-)
```

## Every row `check-regenerate` creates, paired with the cleanup call that deletes it

| Row created by `check-regenerate` | Table / Key | Deleted by `cleanup` via |
|---|---|---|
| Permanent bounce row for `dead.official@simulator.amazonses.com` | `photometrics-email-bounces`, key = actual schema discovered via `describe_table` (email+timestamp, per Phase 1) | The existing paginated bounce-table scan+delete loop — matches on `email.endswith('@simulator.amazonses.com')`, no new code needed |
| Boosted-officials row for `dead.official@simulator.amazonses.com` in region `'Austin, TX'` | `photometrics-boosted-officials`, key `{region: 'Austin, TX', email: 'dead.official@simulator.amazonses.com'}` | New unconditional `delete_item` on that exact deterministic key |
| Generate row for the regen session | `photometrics-take-action`, key `{session_id: state['regen_session_id']}` | New loop over `(session_id, regen_session_id)` in the existing session-row deletion block |
| Sends row for the regen session (written by `handle_send`/`log_send`, not by this harness directly) | `photometrics-take-action-sends`, key `{session_id: state['regen_session_id']}` | Same new loop, sends-row branch |

## Known limitations / risks

- `check-regenerate`'s live assertions (against real AWS/Lambda) have never been run in this item — per the hard constraint, only `--dry-run` was exercised. The live run is the downstream item's job, gated on the `p2-exclusion-hardening` deploy.
- The harness assumes `handle_send` looks up the generate row exactly once via `get_item` inside `log_send` (per the cross-checked handoff) — if that implementation changes shape before deploy, `check-regenerate`'s sends-row assertions would need to be revisited, though the data contract itself (what's asserted) is unchanged.
- `photometrics-boosted-officials`'s key schema is hardcoded in two places (`cmd_check_regenerate`, `cmd_cleanup`) rather than discovered via `describe_table` at runtime, per the assignment's explicit instruction to "build the item to match it exactly" using the schema pasted in this handoff.

## Discovered

None — no new prerequisite, conflicting assumption, or missing work was found. The concurrent `lambda_function.py` item's already-published handoff matched every assumption this item made about the target contract with zero discrepancy.

## Commands run for this handoff (summary)

All commands listed above were run from `C:/Users/aisaa/Projects/photometricsai-website/lambda/take-action/tools` (or repo root where noted), region `us-east-2`, with `AWS_PAGER=''` set for the one real AWS call (`describe-table`, read-only). No write AWS call was made by this item. No `/generate` call was made. No commit was made (left in the working tree per standing rule 4).
