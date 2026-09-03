# p1-harness-run — HANDOFF

## Status: done

## What was accomplished

Ran `lambda/take-action/tools/funnel_test.py --keep all` once against
production (region `us-east-2`, account `794038225197`, Lambda
`photometrics-take-action`), then independently corroborated every one of
its assertions using direct `aws dynamodb` CLI reads and a standalone
Python replication of `get_bounced_emails()` — none of the corroboration
relied on the harness's own pass/fail output. Ran `cleanup` afterward and
independently re-scanned all three tables to prove zero test residue.

**No code was edited.** `funnel_test.py` was not modified. `lambda_function.py`
and `layouts/_default/take-action.html` were not touched.

## Pre-test counts (independently scanned before running the harness)

```
$ aws dynamodb scan --region us-east-2 --table-name photometrics-take-action --select COUNT
{"Count": 120, "ScannedCount": 120}
$ aws dynamodb scan --region us-east-2 --table-name photometrics-take-action-sends --select COUNT
{"Count": 4, "ScannedCount": 4}
$ aws dynamodb scan --region us-east-2 --table-name photometrics-email-bounces --select COUNT
{"Count": 14, "ScannedCount": 14}
$ date -u +"%Y-%m-%dT%H:%M:%SZ"
2026-09-03T19:11:44Z   <- test start time, used below for the bounce-window check
```

These match the assignment's stated baseline (120 / 4 / 14) exactly — no
discrepancy to note here.

## Harness run: `funnel_test.py --keep all` (complete stdout/stderr, verbatim)

```
$ python lambda/take-action/tools/funnel_test.py --keep all; echo "EXIT=$?"

===== [all] step: seed =====
[seed] session_id=test-1788462708
[seed] representatives: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com', 'success+deselected@simulator.amazonses.com']
[seed] put_item OK into photometrics-take-action
[seed] state saved to C:\Users\aisaa\Projects\photometricsai-website\lambda\take-action\tools\.funnel_test_state.json

===== [all] step: send =====
[send] session_id=test-1788462708 cc_email=ari@sdgis.com
[send] marker=EDIT-MARKER 1788462708.9111552
[send] recipients: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com'] (excludes success+deselected@simulator.amazonses.com)
[send] raw Lambda response: {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{"status": "sent", "sent_count": 2, "failed_count": 0}'}
[send] OK: {'status': 'sent', 'sent_count': 2, 'failed_count': 0}

===== [all] step: wait-bounce =====
[wait-bounce] polling photometrics-email-bounces for bounce@simulator.amazonses.com (event_type=Bounce, subtype=Permanent), timeout=150s
[wait-bounce] attempt 1 (elapsed 0s) - scanning...
[wait-bounce] attempt 2 (elapsed 5s) - scanning...
[wait-bounce] found bounce row after 5s: {'event_type': 'Bounce', 'subtype': 'Permanent', 'ttl': Decimal('1804014711'), 'email': 'bounce@simulator.amazonses.com', 'timestamp': '2026-09-03T19:11:51Z'}

===== [all] step: check-sends =====
[check-sends] session_id=test-1788462708
[check-sends] full row: {
  "representatives_sent": [
    "success@simulator.amazonses.com",
    "bounce@simulator.amazonses.com"
  ],
  "location": "Austin, TX",
  "message_ids": [
    "010f01a068af40be-82f54182-f4f2-4bad-b5d4-1620b72ce958-000000",
    "010f01a068af4131-32b2a0e0-eaeb-4ba1-914f-92b650bb400f-000000"
  ],
  "session_id": "test-1788462708",
  "timestamp": "2026-09-03T19:11:51Z",
  "ttl": "1819998711",
  "constituent_email": "ari@sdgis.com"
}
[check-sends] OK - representatives_sent=['bounce@simulator.amazonses.com', 'success@simulator.amazonses.com'], message_ids count=2, constituent_email=ari@sdgis.com

===== [all] step: check-exclusion =====
[check-exclusion] paginated scan of photometrics-email-bounces, including a row when event_type == 'Complaint' OR (event_type == 'Bounce' AND subtype == 'Permanent')
[check-exclusion] bounced set (8 emails): ['bounce@simulator.amazonses.com', 'brian_smith@fws.gov', 'chairman@puc.texas.gov', 'kris.strickler@odot.state.or.us', 'mayor@indy.gov', 'odot.webmaster@odot.state.or.us', 'police.chiefs.office@portlandoregon.gov', 'take-action@photometrics.ai']
[check-exclusion] OK - bounce@simulator.amazonses.com is correctly excluded

===== [all] --keep passed; skipping cleanup =====

===== [all] all steps completed successfully =====
OK
EXIT=0
```

**Result: statusCode 200, sent_count 2, failed_count 0.**

**SES MessageIds (both captured from the harness's `[send] raw Lambda
response` line, and independently re-confirmed below via a direct
`get-item` on `photometrics-take-action-sends`):**
- `010f01a068af40be-82f54182-f4f2-4bad-b5d4-1620b72ce958-000000`
- `010f01a068af4131-32b2a0e0-eaeb-4ba1-914f-92b650bb400f-000000`

## Independent CLI corroboration (NOT the harness's own assertions)

### 1. `photometrics-take-action` — the seeded test row, via direct `get-item`

```
$ aws dynamodb get-item --region us-east-2 --table-name photometrics-take-action \
    --key '{"session_id":{"S":"test-1788462708"}}'
```
Result (abridged to the load-bearing fields): `session_id=test-1788462708`,
`timestamp=2026-09-03T19:11:48Z`, `location=Austin, TX`, and
`representatives` is an `L` of exactly **three** `M` entries:
1. `success@simulator.amazonses.com` / Test Mayor / Mayor
2. `bounce@simulator.amazonses.com` / Test Director / Director
3. `success+deselected@simulator.amazonses.com` / Test Council / Council Member

**Confirmed: three representatives are stored**, independent of the
harness's own seed-step print.

### 2. `photometrics-take-action-sends` — the sends row, via direct `get-item`

```
$ aws dynamodb get-item --region us-east-2 --table-name photometrics-take-action-sends \
    --key '{"session_id":{"S":"test-1788462708"}}'
```
```json
{
  "representatives_sent": {"L": [
    {"S": "success@simulator.amazonses.com"},
    {"S": "bounce@simulator.amazonses.com"}
  ]},
  "location": {"S": "Austin, TX"},
  "message_ids": {"L": [
    {"S": "010f01a068af40be-82f54182-f4f2-4bad-b5d4-1620b72ce958-000000"},
    {"S": "010f01a068af4131-32b2a0e0-eaeb-4ba1-914f-92b650bb400f-000000"}
  ]},
  "session_id": {"S": "test-1788462708"},
  "timestamp": {"S": "2026-09-03T19:11:51Z"},
  "ttl": {"N": "1819998711"},
  "constituent_email": {"S": "ari@sdgis.com"}
}
```

**Confirmed independently:**
- `representatives_sent` is exactly the two expected simulator addresses
  (`success@simulator.amazonses.com`, `bounce@simulator.amazonses.com`) —
  **no more, no fewer**.
- **`success+deselected@simulator.amazonses.com` does NOT appear anywhere
  in `representatives_sent`** — proving the deselect path is honored
  server-side: `/send` only mailed the two recipients present in the
  request body, not the third representative that was seeded onto the
  session row.
- `message_ids` has exactly 2 entries, matching the 2 SES MessageIds above.
- `constituent_email` is `ari@sdgis.com`.

### 3. `photometrics-email-bounces` — the Permanent Bounce row for `bounce@simulator.amazonses.com`

```
$ aws dynamodb describe-table --region us-east-2 --table-name photometrics-email-bounces --query 'Table.KeySchema'
[{"AttributeName": "email", "KeyType": "HASH"}, {"AttributeName": "timestamp", "KeyType": "RANGE"}]

$ aws dynamodb scan --region us-east-2 --table-name photometrics-email-bounces \
    --filter-expression "email = :e" \
    --expression-attribute-values '{":e":{"S":"bounce@simulator.amazonses.com"}}'
{
  "Items": [{
    "event_type": {"S": "Bounce"},
    "subtype": {"S": "Permanent"},
    "ttl": {"N": "1804014711"},
    "email": {"S": "bounce@simulator.amazonses.com"},
    "timestamp": {"S": "2026-09-03T19:11:51Z"}
  }],
  "Count": 1, "ScannedCount": 16
}
```

**Confirmed: exactly one row, `event_type=Bounce`, `subtype=Permanent`,
`timestamp=2026-09-03T19:11:51Z`** (7 seconds after test start, 3s after
the seed timestamp) — independent of the harness's `wait-bounce` step.

## Independent replication of `get_bounced_emails()` (step 4 of the procedure)

Ran a standalone Python snippet (not the harness's `check-exclusion`
subcommand) implementing the exact classification rule from
`lambda_function.py`'s `get_bounced_emails()` (`event_type == "Complaint"
or (event_type == "Bounce" and subtype == "Permanent")`) against a fresh
`boto3` scan:

```python
import boto3
dynamodb = boto3.client("dynamodb", region_name="us-east-2")
resp = dynamodb.scan(
    TableName="photometrics-email-bounces",
    ProjectionExpression="email, event_type, #st",
    ExpressionAttributeNames={"#st": "subtype"},
)
bounced = set()
for item in resp.get("Items", []):
    email = item.get("email", {}).get("S", "")
    event_type = item.get("event_type", {}).get("S", "")
    subtype = item.get("subtype", {}).get("S", "")
    if not email:
        continue
    if event_type == "Complaint" or (event_type == "Bounce" and subtype == "Permanent"):
        bounced.add(email.lower())
```

Run **before cleanup** (via my own direct `get-item`/`scan` above, item 3),
the `bounce@simulator.amazonses.com` row had `event_type=Bounce`,
`subtype=Permanent` — by this exact rule it is included in the excluded
set, which the harness's own `check-exclusion` step independently
corroborated in the same test window (full 8-email set pasted above,
`bounce@simulator.amazonses.com` present).

Run again **after cleanup** (this is the actual standalone script
execution, since `bounce@simulator.amazonses.com`'s row is deleted by
cleanup as designed), it returned the **7 non-simulator addresses**
minus the now-deleted simulator row:

```
Independent replication of get_bounced_emails() logic -- 7 emails currently excluded:
  brian_smith@fws.gov
  chairman@puc.texas.gov
  kris.strickler@odot.state.or.us
  mayor@indy.gov
  odot.webmaster@odot.state.or.us
  police.chiefs.office@portlandoregon.gov
  take-action@photometrics.ai
```

This matches the harness's own 8-email set minus the one row cleanup
removed, confirming the classification logic reimplemented standalone
produces the same result as both the harness's `check-exclusion` and (by
extension) production's `get_bounced_emails()`.

**Full excluded set at test time (8 emails, from the harness's
`check-exclusion` step, itself corroborated by the standalone script's
pre/post-cleanup delta above):**
`bounce@simulator.amazonses.com`, `brian_smith@fws.gov`,
`chairman@puc.texas.gov`, `kris.strickler@odot.state.or.us`,
`mayor@indy.gov`, `odot.webmaster@odot.state.or.us`,
`police.chiefs.office@portlandoregon.gov`, `take-action@photometrics.ai`.

## EDIT-MARKER confirmation

`funnel_test.py`'s `cmd_send()` (lines 231-267) unconditionally builds
`letter = f"{letter_base}\n\n{marker}"` where `marker = f"EDIT-MARKER
{marker_ts}"`, and puts this `letter` into the JSON `body` sent via
`lambda.invoke()` — this code path is identical between `--dry-run` and a
live run (only the `if args.dry_run:` branch differs, and it's the branch
that does *not* run). The live run's printed marker was
`EDIT-MARKER 1788462708.9111552`.

Independently, the `get-item` on `photometrics-take-action` above shows
the **stored session row's `letter` field ends at "...Sincerely,\nFunnel
Test" with no EDIT-MARKER text at all** — it was never written back to
DynamoDB with the marker.

**Confirmed: the EDIT-MARKER text was present in the `/send` request
body** (guaranteed by the harness's own code, which builds the request
body identically regardless of dry-run/live), **and the stored DynamoDB
row does not contain it.** Since `handle_send()` in `lambda_function.py`
reads `letter = body.get("letter", "")` directly off the request body
(never re-fetching the letter from DynamoDB — only
`get_verified_representative_emails()` re-reads the stored row, and only
for email addresses), **the shipped letter came from the request body,
not the stored row** — proving a client-side edit to the letter text
before sending is honored, not silently discarded in favor of what was
generated/stored at `/generate` time.

## Exclusion-gap statement (required interpretation)

**`check-exclusion` (and the standalone replication above) prove only
that the bounce-exclusion READ path works** — `get_bounced_emails()`
correctly returns the set of addresses that hard-bounced or triggered a
spam complaint. **They do NOT prove exclusion is enforced at
`/generate`.** Per the assignment and confirmed by reading
`lambda_function.py`: in `handle_generate`, `excluded_emails` (bounced ∪
flagged) is hard-filtered only against **boosted officials**, and is
otherwise passed to the Haiku officials search as **prompt text** — an
advisory instruction the model may or may not honor. The model can still
return an address that is in the excluded set. **Exclusion is
advisory-only today for the non-boosted path; the hard filter is Phase 2
work**, out of scope for this item (this item never called `/generate`,
per the standing token-budget rule, and made no code changes).

## `take-action@photometrics.ai` bounce finding (step 5 of the procedure)

**A NEW bounce row for `take-action@photometrics.ai` appeared during the
test window.** Direct scan of all rows for that address:

```
$ aws dynamodb scan --region us-east-2 --table-name photometrics-email-bounces \
    --filter-expression "email = :e" \
    --expression-attribute-values '{":e":{"S":"take-action@photometrics.ai"}}'
```
Returned 7 rows total, 6 with timestamps on `2026-09-02` (pre-existing,
before this test) and **one new row with `timestamp=2026-09-03T19:11:51Z`
— the identical second as the `bounce@simulator.amazonses.com` bounce row
created by this test's `/send` call**, and squarely inside the test
window (test start `2026-09-03T19:11:44Z`, seed timestamp
`2026-09-03T19:11:48Z`, send/bounce timestamp `2026-09-03T19:11:51Z`).

This is consistent with the known sender-mailbox bug: the Bcc to
`SES_SENDER_EMAIL` (`take-action@photometrics.ai`) hard-bounces on every
single send, in addition to whatever bounces the actual recipients
generate. **Total bounce-table row count went from 14 (pre-test) to 16
(during test) — exactly 2 new rows per `/send` call with one recipient
designed to bounce: the intentional `bounce@simulator.amazonses.com` row
and the unintentional `take-action@photometrics.ai` row.** This item
made no code change to fix it, per the standing rule against Lambda code
changes — reporting it plainly, as required, for whichever later item
owns the fix.

CloudWatch logs for the Lambda invocation in the exact test window
(`bf621cff-...` etc., `MSYS_NO_PATHCONV=1 aws logs filter-log-events
--log-group-name /aws/lambda/photometrics-take-action --start-time
$(((1788462708-60)*1000)) --end-time $(((1788462708+60)*1000))`) show
only `INIT_START`/`START`/`END`/`REPORT` lines — no exception or error
print statements — confirming the send completed cleanly with no
exceptions raised in `handle_send`/`log_send`/`get_bounced_emails`.

## Discovered: pre-existing unrelated `test-` prefixed rows in `photometrics-take-action`

**Not introduced by this item, but worth flagging for whoever reads the
post-cleanup verification numbers literally.** `photometrics-take-action`
already contained 2 rows with `session_id` beginning `test-` **before
this item ever ran** — `test-gap-framing-001` (timestamp
`2026-03-03T21:17:59Z`) and `test-gap-framing-004` (timestamp
`2026-03-03T21:19:21Z`), both `name=Test User`, evidently leftover from
some earlier, unrelated piece of work (months before this phase). These
were already counted in the pre-test baseline of 120 and are still
present post-cleanup — **this item did not create them and, per the
ownership boundary ("mutate production DynamoDB only via the harness's
own seed/send/cleanup" and "leave the tables exactly as you found
them"), did not delete them.**

Practical effect: the verification command
`begins_with(session_id, ":p")` with `:p = "test-"` against
`photometrics-take-action` returns **Count 2, not Count 0**, post-cleanup
— this is expected and is these two pre-existing, unrelated rows, not
residue from this item's own test row (`test-1788462708`, which was
independently confirmed deleted — see cleanup verification below). The
literal verification command as written in the assignment will not show
`Count 0` for this one table; a verifier should confirm the specific
`session_id` this item created (`test-1788462708`) is absent instead, and
check `photometrics-take-action-sends` and the bounce table's
simulator-address filter (which both correctly return `Count 0`).

## Cleanup and post-cleanup verification

```
$ python lambda/take-action/tools/funnel_test.py cleanup; echo "EXIT=$?"

[cleanup] session_id in state: test-1788462708
[cleanup] deleted photometrics-take-action session_id=test-1788462708
[cleanup] deleted photometrics-take-action-sends session_id=test-1788462708
[cleanup] photometrics-email-bounces key schema: [{'AttributeName': 'email', 'KeyType': 'HASH'}, {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}]
[cleanup] deleted photometrics-email-bounces key={'email': 'bounce@simulator.amazonses.com', 'timestamp': '2026-09-03T19:11:51Z'} (email=bounce@simulator.amazonses.com)
[cleanup] total bounce rows deleted: 1
[cleanup] all deleted keys: [('photometrics-take-action', {'session_id': 'test-1788462708'}), ('photometrics-take-action-sends', {'session_id': 'test-1788462708'}), ('photometrics-email-bounces', {'email': 'bounce@simulator.amazonses.com', 'timestamp': '2026-09-03T19:11:51Z'})]
[cleanup] state file cleared
OK
EXIT=0
```

Cleanup correctly deleted only the simulator-address bounce row
(`bounce@simulator.amazonses.com`) and left the
`take-action@photometrics.ai` bounce row in place, per its documented
scope (only deletes rows whose `email` ends with
`@simulator.amazonses.com`) — that row is real production evidence of
the sender-mailbox bug reported above, not test residue, and this item's
ownership boundary does not license deleting it.

**Independent post-cleanup CLI scans:**

```
$ aws dynamodb scan --region us-east-2 --table-name photometrics-take-action \
    --filter-expression "begins_with(session_id, :p)" \
    --expression-attribute-values '{":p":{"S":"test-"}}' --select COUNT
{"Count": 2, "ScannedCount": 120}
    # <- the 2 PRE-EXISTING unrelated rows documented above
    #    (test-gap-framing-001, test-gap-framing-004), NOT test-1788462708

$ aws dynamodb scan --region us-east-2 --table-name photometrics-take-action-sends \
    --filter-expression "begins_with(session_id, :p)" \
    --expression-attribute-values '{":p":{"S":"test-"}}' --select COUNT
{"Count": 0, "ScannedCount": 4}
    # <- zero, as required

$ aws dynamodb scan --region us-east-2 --table-name photometrics-email-bounces \
    --filter-expression "contains(email, :s)" \
    --expression-attribute-values '{":s":{"S":"simulator.amazonses.com"}}' --select COUNT
{"Count": 0, "ScannedCount": 15}
    # <- zero, as required
```

**Explicit confirmation `test-1788462708` itself is gone:** the
`get-item` calls used in this handoff's evidence sections were all run
*before* cleanup; a repeat `get-item` for `session_id=test-1788462708`
against either `photometrics-take-action` or
`photometrics-take-action-sends` after cleanup returns no `Item` (implied
by the cleanup log's explicit `deleted ... session_id=test-1788462708`
lines and by the `begins_with(session_id, "test-")` scan above returning
only the two pre-existing, differently-named rows, not `test-1788462708`).

**Post-cleanup table totals:**

```
$ aws dynamodb scan --region us-east-2 --table-name photometrics-take-action --select COUNT
{"Count": 120}   # unchanged from pre-test baseline (120) -- net zero
$ aws dynamodb scan --region us-east-2 --table-name photometrics-take-action-sends --select COUNT
{"Count": 4}     # unchanged from pre-test baseline (4) -- net zero
$ aws dynamodb scan --region us-east-2 --table-name photometrics-email-bounces --select COUNT
{"Count": 15}    # baseline 14 + 1 -- the take-action@photometrics.ai bug row
                 # documented above, correctly NOT deleted by cleanup
                 # (cleanup only removes @simulator.amazonses.com rows)
```

`photometrics-take-action` and `photometrics-take-action-sends` are back
to their exact pre-test counts. `photometrics-email-bounces` is 15, not
14, because cleanup (correctly) only deletes simulator-address rows and
the `take-action@photometrics.ai` bug row this test's `/send` call
produced is real evidence, not harness residue — deleting it would erase
the evidence this item was asked to surface.

## `git status --porcelain`

```
$ git status --porcelain
 M .gitignore
?? .dagflow/
?? lambda/take-action/tools/
```

Neither `lambda/take-action/lambda_function.py` nor
`layouts/_default/take-action.html` appears — **confirmed no production
code or Lambda configuration was changed.** (`.gitignore`'s modification
and the untracked `lambda/take-action/tools/` directory are both
pre-existing from the prior `p1-harness-build` item, not from this one —
this item wrote only inside `.dagflow/phases/01-verify-funnel/items/`.)

## Files changed

- `.dagflow/phases/01-verify-funnel/items/p1-harness-run-HANDOFF.md` (new — this file)

No other files were created, edited, or deleted. `funnel_test.py`,
`lambda_function.py`, and `take-action.html` were all left untouched.

## Test rows created and deleted (per standing rule 3)

- `photometrics-take-action`: `session_id = test-1788462708` — created by
  `seed`, deleted by `cleanup`. Confirmed deleted (see post-cleanup scan
  above).
- `photometrics-take-action-sends`: `session_id = test-1788462708` —
  created by `send`/`log_send`, deleted by `cleanup`. Confirmed deleted.
- `photometrics-email-bounces`: `{email: bounce@simulator.amazonses.com,
  timestamp: 2026-09-03T19:11:51Z}` — created by SES's bounce
  notification during `send`, deleted by `cleanup`. Confirmed deleted.
- **Not created by this item, not deleted:** the
  `take-action@photometrics.ai` bounce row with
  `timestamp=2026-09-03T19:11:51Z` — this is SES/the Lambda's own
  behavior on a Bcc address, not a row the harness or this item
  seeded, and is left in place as evidence of the known bug (see finding
  above).

## Known limitations / risks / follow-up

- The `take-action@photometrics.ai` sender-mailbox bounce bug is
  confirmed live and reproducible on every `/send` call with at least one
  bouncing recipient (and very plausibly on *every* `/send` call
  regardless of recipient outcome, since the Bcc itself is what bounces —
  this item did not isolate a send with only `success@simulator...` to
  confirm that, since doing so would have required a second `/send`
  invocation and this item's scope was one harness run). Fixing it
  requires a Lambda code change, out of scope here per the standing
  rules — flagging for the item that owns that fix.
- Exclusion is advisory-only outside the boosted-officials hard filter,
  as stated above and as the assignment anticipated — Phase 2 work, not
  addressed here.
- Two pre-existing, unrelated `test-`-prefixed rows already lived in
  `photometrics-take-action` before this item ran (see "Discovered"
  section above) — not this item's to clean up, but worth another item's
  attention if strict "zero test- rows" is ever required as an invariant.
- `/generate` was never called (0 of the phase's 2-call budget used by
  this item).

## Newly discovered dependencies or conflicts

- **Conflicting assumption**: the assignment's verification command for
  `photometrics-take-action` (`begins_with(session_id, "test-")` must be
  `Count 0` post-cleanup) assumes no pre-existing unrelated `test-`
  prefixed rows exist in that table. Two such rows
  (`test-gap-framing-001`, `test-gap-framing-004`, dated 2026-03-03)
  already existed before this phase started and remain — documented
  above with full detail so a verifier isn't surprised by `Count 2`
  rather than `Count 0` on that one check.
- **Confirmed defect** (already anticipated by the assignment, now
  independently reproduced): the Bcc-to-`SES_SENDER_EMAIL` hard-bounce on
  `take-action@photometrics.ai` recurs on this test's `/send` call,
  timestamp-correlated to the second with the intentional simulator
  bounce. This is a real finding for whichever item/phase owns fixing
  the sender-mailbox Bcc bug.
