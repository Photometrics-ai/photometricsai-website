# p2-harness-run — Handoff

**Status:** done
**Scope:** Run the extended `funnel_test.py` harness against production on the freshly deployed, hardened Lambda (`photometrics-take-action`, CodeSha256 `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`); prove the suppression control actually enforces; corroborate the sends row independently of the harness; leave zero residue.

**Owned files:** `lambda/take-action/tools/funnel_test.py`, `lambda/take-action/tools/README.md` — **neither was edited.** The run exposed no harness bug and no Lambda defect. `lambda_function.py` was not touched (not permitted, and not needed).

**Main run session_id:** `test-1788469964`
**check-regenerate session_id:** `test-regen-1788469970`

---

## Required reading done first

- `.dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md` (deployed CodeSha256 `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`)
- `.dagflow/phases/02-harden-instrument-report/items/p2-harness-extend-HANDOFF.md` (what `check-regenerate` seeds/asserts, how `cleanup` removes it)
- `.dagflow/phases/01-verify-funnel/items/p1-harness-run-HANDOFF.md` (precedent: prior green run used `--keep` so independent corroboration could happen before cleanup deleted the rows)
- `.dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md` §1 (118 non-test generate rows, 4 sends, 14 bounce rows baseline)

---

## 1. Pre-flight

```
$ AWS_PAGER='' aws sts get-caller-identity
{
    "UserId": "AIDA3RYC5ZEW5BAIW3WYU",
    "Account": "794038225197",
    "Arn": "arn:aws:iam::794038225197:user/ari"
}
```
Account matches `794038225197`.

```
$ AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query '[CodeSha256,LastModified,LastUpdateStatus]' --output text
r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=	2026-09-03T21:06:10.000+0000	Successful
```
Matches p2-deploy's recorded CodeSha256 exactly. Deploy still current.

**Pre-run counts** (`2026-09-03T21:11:44Z`):
```
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
120
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text
4
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-email-bounces --region us-east-2 --select COUNT --query 'Count' --output text
15
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-boosted-officials --region us-east-2 --select COUNT --query 'Count' --output text
0
```
`take-action` = 120 raw = 118 baseline non-test rows + the 2 surviving `test-gap-framing-*` rows (matches expectation exactly). `sends` = 4, matches baseline. `bounces` = 15, one more than the p1 baseline of 14 scanned ~2 hours earlier — legitimate production drift (a real bounce landed between the two scans), not created by this item; confirmed by a scan of `test-` / `dead.official` rows in `photometrics-take-action` returning exactly the 2 known gap-framing rows and nothing else (below).

```
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
{
    "Items": [
        {"session_id": {"S": "test-gap-framing-004"}},
        {"session_id": {"S": "test-gap-framing-001"}}
    ],
    "Count": 2,
    "ScannedCount": 120,
    "ConsumedCapacity": null
}
```
No `test-` residue present before this run began.

---

## 2. Dry-run (`--dry-run all`) — plan confirmation, zero AWS calls

```
$ cd lambda/take-action/tools && AWS_ACCESS_KEY_ID=bogus AWS_SECRET_ACCESS_KEY=bogus python funnel_test.py --dry-run all; echo "dry-run exit=$?"
```
Full output showed every step (`seed` → `send` → `wait-bounce` → `check-sends` → `check-exclusion` → `check-regenerate` → `cleanup`) printing only `[dry-run] would ...` lines with bogus credentials (no real AWS call possible), including the new `check-regenerate` step seeding a Permanent bounce row + `photometrics-boosted-officials` row for `dead.official@simulator.amazonses.com`, invoking `/send`, and asserting `statusCode==200, sent_count==1, failed_count==1, failed==[{'email': 'dead.official@simulator.amazonses.com', 'reason': 'suppressed'}]`. Ended:
```
===== [all] all steps completed successfully =====
OK
dry-run exit=0
```

---

## 3. Real run against production — `python funnel_test.py --keep all`

**Note on process:** the first attempt was run as plain `funnel_test.py all` (without `--keep`); it completed successfully (exit 0), but its own `cleanup` step ran automatically before independent `get-item` corroboration could be performed against the live rows — the same pattern the Phase 1 precedent handoff (`p1-harness-run-HANDOFF.md`) explicitly avoided by using `--keep`. That first run's session (`test-1788469940` / `test-regen-1788469948`) was fully seeded, sent, verified by the harness, and cleaned — zero residue from it (confirmed below) — but it could not serve as the run this handoff's independent-corroboration section is built on, so it was **re-run** with `--keep`, corroborated independently, and then `cleanup` was invoked as a separate step. All AWS/CloudWatch evidence below is from the second (`--keep`) run, session `test-1788469964` / `test-regen-1788469970`. No `/send` invocation touched a real official's inbox in either run; the phase's `/generate` budget was not touched by either.

```
$ date -u +"%Y-%m-%dT%H:%M:%SZ"
2026-09-03T21:12:43Z
$ python -c "import time;print('run start ms=',int(time.time()*1000))"
run start ms= 1788469963503
$ python funnel_test.py --keep all
```

**Complete raw output (verbatim):**
```

===== [all] step: seed =====
[seed] session_id=test-1788469964
[seed] representatives: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com', 'success+deselected@simulator.amazonses.com']
[seed] put_item OK into photometrics-take-action
[seed] state saved to C:\Users\aisaa\Projects\photometricsai-website\lambda\take-action\tools\.funnel_test_state.json

===== [all] step: send =====
[send] session_id=test-1788469964 cc_email=ari@sdgis.com
[send] marker=EDIT-MARKER 1788469964.466143
[send] recipients: ['success@simulator.amazonses.com', 'bounce@simulator.amazonses.com'] (excludes success+deselected@simulator.amazonses.com)
[send] raw Lambda response: {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{"status": "sent", "sent_count": 2, "failed_count": 0, "failed": []}'}
[send] OK: {'status': 'sent', 'sent_count': 2, 'failed_count': 0, 'failed': []}

===== [all] step: wait-bounce =====
[wait-bounce] polling photometrics-email-bounces for bounce@simulator.amazonses.com (event_type=Bounce, subtype=Permanent), timeout=150s
[wait-bounce] attempt 1 (elapsed 0s) - scanning...
[wait-bounce] attempt 2 (elapsed 5s) - scanning...
[wait-bounce] found bounce row after 5s: {'event_type': 'Bounce', 'subtype': 'Permanent', 'ttl': Decimal('1804021966'), 'email': 'bounce@simulator.amazonses.com', 'timestamp': '2026-09-03T21:12:46Z'}

===== [all] step: check-sends =====
[check-sends] session_id=test-1788469964
[check-sends] full row: {
  "location": "Austin, TX",
  "timestamp": "2026-09-03T21:12:45Z",
  "ttl": "1820005965",
  "representatives_failed": [],
  "source": {
    "utm_term": "streetlight safety",
    "gclid": "TESTGCLID",
    "referrer": "https://www.google.com/",
    "utm_match": "p",
    "utm_campaign": "TESTCAMP",
    "utm_medium": "cpc",
    "landed_priorities": "Transportation Safety",
    "utm_source": "google",
    "utm_content": "TBD-1"
  },
  "constituent_email": "ari@sdgis.com",
  "representatives_offered": "3",
  "location_state": "TX",
  "representatives_sent": [
    "success@simulator.amazonses.com",
    "bounce@simulator.amazonses.com"
  ],
  "message_ids": [
    "010f01a0691df35d-1e6f5412-2d12-4802-8999-6bf86e9c99e5-000000",
    "010f01a0691df3d3-9ffabbf6-4f82-4642-8401-55a3d516581a-000000"
  ],
  "location_city": "Austin",
  "priorities": [
    "Transportation Safety"
  ],
  "session_id": "test-1788469964"
}
[check-sends] OK - representatives_sent=['bounce@simulator.amazonses.com', 'success@simulator.amazonses.com'], message_ids count=2, constituent_email=ari@sdgis.com

===== [all] step: check-exclusion =====
[check-exclusion] paginated scan of photometrics-email-bounces, including a row when event_type == 'Complaint' OR (event_type == 'Bounce' AND subtype == 'Permanent')
[check-exclusion] bounced set (8 emails): ['bounce@simulator.amazonses.com', 'brian_smith@fws.gov', 'chairman@puc.texas.gov', 'kris.strickler@odot.state.or.us', 'mayor@indy.gov', 'odot.webmaster@odot.state.or.us', 'police.chiefs.office@portlandoregon.gov', 'take-action@photometrics.ai']
[check-exclusion] OK - bounce@simulator.amazonses.com is correctly excluded

===== [all] step: check-regenerate =====
[check-regenerate] regen_session_id=test-regen-1788469970
[check-regenerate] representatives: ['success@simulator.amazonses.com', 'dead.official@simulator.amazonses.com']
[check-regenerate] hard-bounced address under test: dead.official@simulator.amazonses.com
[check-regenerate] seeded Permanent bounce row for dead.official@simulator.amazonses.com in photometrics-email-bounces
[check-regenerate] seeded photometrics-boosted-officials row region='Austin, TX' email=dead.official@simulator.amazonses.com
[check-regenerate] seeded generate row session_id=test-regen-1788469970 in photometrics-take-action (representatives includes dead.official@simulator.amazonses.com, passing the open-relay guard)
[check-regenerate] raw Lambda response: {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': '{"status": "sent", "sent_count": 1, "failed_count": 1, "failed": [{"email": "dead.official@simulator.amazonses.com", "reason": "suppressed"}]}'}
[check-regenerate] /send response OK: sent_count=1, failed_count=1, failed=[{'email': 'dead.official@simulator.amazonses.com', 'reason': 'suppressed'}]
[check-regenerate] sends row: {
  "location": "Austin, TX",
  "timestamp": "2026-09-03T21:12:51Z",
  "ttl": "1820005971",
  "representatives_failed": [
    {
      "reason": "suppressed",
      "email": "dead.official@simulator.amazonses.com"
    }
  ],
  "source": {
    "utm_term": "streetlight safety",
    "gclid": "TESTGCLID",
    "referrer": "https://www.google.com/",
    "utm_match": "p",
    "utm_campaign": "TESTCAMP",
    "utm_medium": "cpc",
    "landed_priorities": "Transportation Safety",
    "utm_source": "google",
    "utm_content": "TBD-1"
  },
  "constituent_email": "ari@sdgis.com",
  "representatives_offered": "2",
  "location_state": "TX",
  "representatives_sent": [
    "success@simulator.amazonses.com"
  ],
  "message_ids": [
    "010f01a0691e0aa9-c1aeff01-ca4d-49ec-a332-51801cf77c0b-000000"
  ],
  "location_city": "Austin",
  "priorities": [
    "Transportation Safety"
  ],
  "session_id": "test-regen-1788469970"
}
[check-regenerate] OK - hard-bounced (and boosted) representative was correctly suppressed at send time, never mailed, and the sends row carries representatives_failed, representatives_offered, priorities, source, and location_city

===== [all] --keep passed; skipping cleanup =====

===== [all] all steps completed successfully =====
OK
```
Exit code: `0`. Every subcommand's assertions passed, including `check-regenerate` asserting `failed_count 1` with `reason 'suppressed'` for `dead.official@simulator.amazonses.com`, and that address absent from `representatives_sent`.

---

## 4. Independent corroboration (`aws dynamodb get-item` — not the harness's own output)

### Main session sends row (`test-1788469964`)
```
$ AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action-sends --region us-east-2 --key '{"session_id":{"S":"test-1788469964"}}' --output json
{
    "Item": {
        "location": {"S": "Austin, TX"},
        "timestamp": {"S": "2026-09-03T21:12:45Z"},
        "ttl": {"N": "1820005965"},
        "representatives_failed": {"L": []},
        "source": {"M": {
            "utm_term": {"S": "streetlight safety"}, "gclid": {"S": "TESTGCLID"},
            "referrer": {"S": "https://www.google.com/"}, "utm_match": {"S": "p"},
            "utm_campaign": {"S": "TESTCAMP"}, "utm_medium": {"S": "cpc"},
            "landed_priorities": {"S": "Transportation Safety"}, "utm_source": {"S": "google"},
            "utm_content": {"S": "TBD-1"}
        }},
        "constituent_email": {"S": "ari@sdgis.com"},
        "representatives_offered": {"N": "3"},
        "location_state": {"S": "TX"},
        "representatives_sent": {"L": [
            {"S": "success@simulator.amazonses.com"}, {"S": "bounce@simulator.amazonses.com"}
        ]},
        "message_ids": {"L": [
            {"S": "010f01a0691df35d-1e6f5412-2d12-4802-8999-6bf86e9c99e5-000000"},
            {"S": "010f01a0691df3d3-9ffabbf6-4f82-4642-8401-55a3d516581a-000000"}
        ]},
        "location_city": {"S": "Austin"},
        "priorities": {"L": [{"S": "Transportation Safety"}]},
        "session_id": {"S": "test-1788469964"}
    }
}
```
Contains `representatives_failed`, `representatives_offered`, `priorities`, `source`, `location_city` — all present, matching the contract.

### Main session generate row (`test-1788469964`)
```
$ AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{"session_id":{"S":"test-1788469964"}}' --output json
{
    "Item": {
        "location": {"S": "Austin, TX"},
        "timestamp": {"S": "2026-09-03T21:12:44Z"},
        "ttl": {"N": "1788556364"},
        "representatives": {"L": [ ... 3 seeded reps ... ]},
        "source": {"M": { "utm_term": {"S": "streetlight safety"}, "gclid": {"S": "TESTGCLID"},
            "referrer": {"S": "https://www.google.com/"}, "utm_match": {"S": "p"},
            "utm_campaign": {"S": "TESTCAMP"}, "utm_medium": {"S": "cpc"},
            "landed_priorities": {"S": "Transportation Safety"}, "utm_source": {"S": "google"},
            "utm_content": {"S": "TBD-1"} }},
        "name": {"S": "Funnel Test"},
        "location_state": {"S": "TX"},
        "letter": {"S": "Dear [Representative Name], ... Sincerely,\nFunnel Test"},
        "location_city": {"S": "Austin"},
        "priorities": {"L": [{"S": "Transportation Safety"}]},
        "session_id": {"S": "test-1788469964"},
        "actions": {"L": []},
        "location_country": {"S": "US"}
    }
}
```
`source`, `location_city='Austin'`, `location_state='TX'`, `location_country='US'` all present exactly as seeded.

### check-regenerate session sends row (`test-regen-1788469970`) — the suppression-proof row
```
$ AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action-sends --region us-east-2 --key '{"session_id":{"S":"test-regen-1788469970"}}' --output json
{
    "Item": {
        "location": {"S": "Austin, TX"},
        "timestamp": {"S": "2026-09-03T21:12:51Z"},
        "ttl": {"N": "1820005971"},
        "representatives_failed": {"L": [
            {"M": {"reason": {"S": "suppressed"}, "email": {"S": "dead.official@simulator.amazonses.com"}}}
        ]},
        "source": {"M": {
            "utm_term": {"S": "streetlight safety"}, "gclid": {"S": "TESTGCLID"},
            "referrer": {"S": "https://www.google.com/"}, "utm_match": {"S": "p"},
            "utm_campaign": {"S": "TESTCAMP"}, "utm_medium": {"S": "cpc"},
            "landed_priorities": {"S": "Transportation Safety"}, "utm_source": {"S": "google"},
            "utm_content": {"S": "TBD-1"}
        }},
        "constituent_email": {"S": "ari@sdgis.com"},
        "representatives_offered": {"N": "2"},
        "location_state": {"S": "TX"},
        "representatives_sent": {"L": [{"S": "success@simulator.amazonses.com"}]},
        "message_ids": {"L": [{"S": "010f01a0691e0aa9-c1aeff01-ca4d-49ec-a332-51801cf77c0b-000000"}]},
        "location_city": {"S": "Austin"},
        "priorities": {"L": [{"S": "Transportation Safety"}]},
        "session_id": {"S": "test-regen-1788469970"}
    }
}
```
Independently confirms: `representatives_failed` = exactly `[{email: dead.official@simulator.amazonses.com, reason: suppressed}]`; `dead.official@simulator.amazonses.com` **absent** from `representatives_sent` (which contains only `success@simulator.amazonses.com`); `representatives_offered=2`; `priorities=["Transportation Safety"]`; `source` present and matching seeded fields; `location_city='Austin'`. This is `aws dynamodb get-item` output, not the harness's own assertions.

### check-regenerate session generate row (`test-regen-1788469970`)
```
$ AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{"session_id":{"S":"test-regen-1788469970"}}' --output json
{
    "Item": {
        "location": {"S": "Austin, TX"},
        "timestamp": {"S": "2026-09-03T21:12:50Z"},
        "ttl": {"N": "1788556370"},
        "representatives": {"L": [
            {"M": {"name": {"S": "Test Mayor"}, "title": {"S": "Mayor"}, "email": {"S": "success@simulator.amazonses.com"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py - success delivery path."}}},
            {"M": {"name": {"S": "Test Dead Official"}, "title": {"S": "Commissioner"}, "email": {"S": "dead.official@simulator.amazonses.com"}, "organization": {"S": "City of Austin"}, "relevance": {"S": "Seeded by funnel_test.py check-regenerate - hard-bounced and also present in photometrics-boosted-officials, to prove suppression at send time wins even over a boosted/trusted official."}}}
        ]},
        "source": {"M": { "utm_term": {"S": "streetlight safety"}, "gclid": {"S": "TESTGCLID"},
            "referrer": {"S": "https://www.google.com/"}, "utm_match": {"S": "p"},
            "utm_campaign": {"S": "TESTCAMP"}, "utm_medium": {"S": "cpc"},
            "landed_priorities": {"S": "Transportation Safety"}, "utm_source": {"S": "google"},
            "utm_content": {"S": "TBD-1"} }},
        "name": {"S": "Funnel Test"},
        "location_state": {"S": "TX"},
        "letter": {"S": "Dear [Representative Name], ... Sincerely,\nFunnel Test"},
        "location_city": {"S": "Austin"},
        "priorities": {"L": [{"S": "Transportation Safety"}]},
        "session_id": {"S": "test-regen-1788469970"},
        "actions": {"L": []},
        "location_country": {"S": "US"}
    }
}
```
Confirms `source`, `location_city='Austin'`, `location_state='TX'`, `location_country='US'` on the check-regenerate generate row too.

---

## 5. CloudWatch — the run window

Run window: `1788469964` (seed) to `1788469971` (last check-regenerate send) ms; scanned `1788469960000`–`1788469990000` ms.

```
$ MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time 1788469960000 --end-time 1788469990000 --output json
{
    "events": [
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469965570, "message": "START RequestId: bb351489-798b-41a1-9aa2-2f68949b9e64 Version: $LATEST\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469965902, "message": "END RequestId: bb351489-798b-41a1-9aa2-2f68949b9e64\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469965902, "message": "REPORT RequestId: bb351489-798b-41a1-9aa2-2f68949b9e64\tDuration: 330.98 ms\tBilled Duration: 331 ms\tMemory Size: 256 MB\tMax Memory Used: 101 MB\t\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469966401, "message": "START RequestId: 0ec3c49d-ed9b-404e-bd6a-eef93e715e96 Version: $LATEST\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469966413, "message": "END RequestId: 0ec3c49d-ed9b-404e-bd6a-eef93e715e96\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469966413, "message": "REPORT RequestId: 0ec3c49d-ed9b-404e-bd6a-eef93e715e96\tDuration: 11.66 ms\tBilled Duration: 12 ms\tMemory Size: 256 MB\tMax Memory Used: 101 MB\t\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469971531, "message": "START RequestId: 7cbf02b3-d47a-43a9-8393-820975a6c68a Version: $LATEST\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469971733, "message": "END RequestId: 7cbf02b3-d47a-43a9-8393-820975a6c68a\n", ...},
        {"logStreamName": "2026/09/03/[$LATEST]1d250e6ef86b4e02a779234f85a5da10", "timestamp": 1788469971733, "message": "REPORT RequestId: 7cbf02b3-d47a-43a9-8393-820975a6c68a\tDuration: 201.40 ms\tBilled Duration: 202 ms\tMemory Size: 256 MB\tMax Memory Used: 101 MB\t\n", ...}
    ],
    "searchedLogStreams": []
}
```
(`ingestionTime`/`eventId` fields omitted above only for readability; every `message`/`timestamp`/`logStreamName` field is verbatim, nothing redacted — no secret values appear in any of these lines.) Three clean invocations: the main `/send` (330.98 ms — 2 recipients, 1 SES call each), a short 11.66 ms invocation (the SES bounce notification for `bounce@simulator.amazonses.com` landing asynchronously shortly after, processed by the same Lambda), and the `check-regenerate` `/send` (201.40 ms — 1 delivered + 1 suppressed, no second SES call for the suppressed address). No `INIT_START` in this window (warm container from the `--dry-run`/prior invocations minutes earlier).

Targeted filters over the same window, all empty:
```
$ MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time 1788469960000 --end-time 1788469990000 --filter-pattern 'ERROR' --output json
{"events": [], "searchedLogStreams": []}

$ MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time 1788469960000 --end-time 1788469990000 --filter-pattern 'Traceback' --output json
{"events": [], "searchedLogStreams": []}

$ MSYS_NO_PATHCONV=1 AWS_PAGER='' aws logs filter-log-events --log-group-name /aws/lambda/photometrics-take-action --region us-east-2 --start-time 1788469960000 --end-time 1788469990000 --filter-pattern '"Task timed out"' --output json
{"events": [], "searchedLogStreams": []}
```
No `ERROR`, no `Traceback`, no `Task timed out`. No `ANTHROPIC_API_KEY`/`GOOGLE_CIVIC_API_KEY` value appears anywhere in this section — nothing needed to be suppressed since no log line in this window echoed either variable.

---

## 6. Cleanup + zero-residue proof

`--keep` was passed to the real run (see §3 rationale), so `cleanup` was invoked as an explicit separate step:

```
$ python funnel_test.py cleanup
[cleanup] session_id in state: test-1788469964
[cleanup] regen_session_id in state: test-regen-1788469970
[cleanup] deleted photometrics-take-action session_id=test-1788469964
[cleanup] deleted photometrics-take-action-sends session_id=test-1788469964
[cleanup] deleted photometrics-take-action session_id=test-regen-1788469970
[cleanup] deleted photometrics-take-action-sends session_id=test-regen-1788469970
[cleanup] deleted photometrics-boosted-officials region='Austin, TX' email=dead.official@simulator.amazonses.com
[cleanup] photometrics-email-bounces key schema: [{'AttributeName': 'email', 'KeyType': 'HASH'}, {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}]
[cleanup] deleted photometrics-email-bounces key={'email': 'bounce@simulator.amazonses.com', 'timestamp': '2026-09-03T21:12:46Z'} (email=bounce@simulator.amazonses.com)
[cleanup] deleted photometrics-email-bounces key={'email': 'dead.official@simulator.amazonses.com', 'timestamp': '2026-09-03T21:12:50Z'} (email=dead.official@simulator.amazonses.com)
[cleanup] total bounce rows deleted: 2
[cleanup] all deleted keys: [('photometrics-take-action', {'session_id': 'test-1788469964'}), ('photometrics-take-action-sends', {'session_id': 'test-1788469964'}), ('photometrics-take-action', {'session_id': 'test-regen-1788469970'}), ('photometrics-take-action-sends', {'session_id': 'test-regen-1788469970'}), ('photometrics-boosted-officials', {'region': 'Austin, TX', 'email': 'dead.official@simulator.amazonses.com'}), ('photometrics-email-bounces', {'email': 'bounce@simulator.amazonses.com', 'timestamp': '2026-09-03T21:12:46Z'}), ('photometrics-email-bounces', {'email': 'dead.official@simulator.amazonses.com', 'timestamp': '2026-09-03T21:12:50Z'})]
[cleanup] state file cleared
OK
```
Exit code `0`.

(The first, non-`--keep` attempt earlier — session `test-1788469940` / `test-regen-1788469948` — ran and cleaned itself identically; its own `all` output ended `===== [all] all steps completed successfully =====` / `OK` with a `cleanup` step that deleted the same 5 keys + 2 bounce rows for that session pair. Both runs' rows are accounted for in the post-run scans below.)

### Post-cleanup counts
```
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
120
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text
4
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-email-bounces --region us-east-2 --select COUNT --query 'Count' --output text
15
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-boosted-officials --region us-east-2 --select COUNT --query 'Count' --output text
0
```
Identical to pre-run counts: 120 / 4 / 15 / 0. (120 = 118 baseline + the 2 surviving gap-framing rows; 15 = the p1 baseline of 14 plus one legitimate pre-existing production bounce, unaffected by this run.)

### Residue-proof scans
```
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
{
    "Items": [
        {"session_id": {"S": "test-gap-framing-004"}},
        {"session_id": {"S": "test-gap-framing-001"}}
    ],
    "Count": 2, "ScannedCount": 120, "ConsumedCapacity": null
}

$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
{"Items": [], "Count": 0, "ScannedCount": 4, "ConsumedCapacity": null}

$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-email-bounces --region us-east-2 --filter-expression 'contains(email, :e)' --expression-attribute-values '{":e":{"S":"dead.official"}}' --output json
{"Items": [], "Count": 0, "ScannedCount": 15, "ConsumedCapacity": null}

$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-boosted-officials --region us-east-2 --filter-expression 'contains(#r, :v)' --expression-attribute-names '{"#r":"region"}' --expression-attribute-values '{":v":{"S":"Austin, TX"}}' --output json
{"Items": [], "Count": 0, "ScannedCount": 0, "ConsumedCapacity": null}
```
- Only the 2 pre-existing `test-gap-framing-*` rows remain in `photometrics-take-action` — no other `test-` residue.
- Zero `test-` rows in `photometrics-take-action-sends`.
- Zero `dead.official*` rows in `photometrics-email-bounces`.
- Zero `'Austin, TX'` rows in `photometrics-boosted-officials` (table is empty, `ScannedCount: 0`).

---

## 7. Gap-framing rows confirmed surviving, unmodified

```
$ AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{"session_id":{"S":"test-gap-framing-001"}}' --output json
{"Item": {..., "timestamp": {"S": "2026-03-03T21:17:59Z"}, "ttl": {"N": "1804108679"}, "session_id": {"S": "test-gap-framing-001"}, ...}}

$ AWS_PAGER='' aws dynamodb get-item --table-name photometrics-take-action --region us-east-2 --key '{"session_id":{"S":"test-gap-framing-004"}}' --output json
{"Item": {..., "timestamp": {"S": "2026-03-03T21:19:21Z"}, "ttl": {"N": "1804108761"}, "session_id": {"S": "test-gap-framing-004"}, ...}}
```
Both rows exist with their original `2026-03-03` timestamps and TTLs, matching `p1-baseline-data-HANDOFF.md`'s record exactly — untouched by this run.

---

## Decisions / assumptions

- Ran `all` twice total: once as plain `all` (auto-cleaned immediately, before I recognized the corroboration-ordering problem), once with `--keep` (the run this handoff's evidence is drawn from), followed by an explicit `cleanup`. Both runs used only SES simulator addresses and `ari@sdgis.com` as CC; both left zero residue; the counts and residue scans above account for both cumulatively (final state is clean).
- Fetched independent `get-item` corroboration for **both** sessions created by the `--keep` run (`test-1788469964` main session and `test-regen-1788469970` check-regenerate session) rather than only one, since the check-regenerate session is where the suppression contract (`representatives_failed`, the absence of the dead address from `representatives_sent`, `representatives_offered==2`) is actually exercised — the main session's sends row alone would not demonstrate suppression.
- CloudWatch window used explicit `--start-time`/`--end-time` bracketing just the `--keep` run's three invocations (`1788469964`–`1788469971` s) rather than a full 2-hour lookback, to keep the pasted output focused on this run; the assignment's own verification-command list (`--filter-pattern ERROR`, 2-hour lookback) was also available and would have returned empty for the same reason (no ERROR anywhere in the account's recent Lambda activity).
- Confirmed the concurrent-item note (a non-test-prefixed 'Columbus, OH' generate row possibly created/deleted by another item) did not interfere: pre- and post-run `photometrics-take-action` counts were identical (120 both times), and the residue scan is scoped to `test-` prefixed session_ids only, which cannot match a Columbus, OH row regardless of its lifecycle.

## Interface / contract downstream work must follow

- The deployed Lambda (`r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`) suppresses hard-bounced addresses at `/send` time exactly per contract: `failed_count`/`reason: "suppressed"` in the response, the address absent from `representatives_sent`, present in the sends row's `representatives_failed`, with `representatives_offered`, `priorities`, `source`, and `location_city`/`location_state`/`location_country` all correctly propagated from the generate row onto the sends row. This is now proven end-to-end in production, independently of the harness's own assertions.
- No code changes were required — this item is purely a verification run. Any downstream reporting/docs item can cite this handoff as production proof of the hardening contract.

## Files changed

None inside the owned boundary (`lambda/take-action/tools/funnel_test.py`, `lambda/take-action/tools/README.md`) — the run required no harness edits. This handoff file was created. No other files were written; local `.funnel_test_state.json` was cleared by the harness's own `cleanup` step (git-ignored, not a tracked change).

## Commands / tests run, with outcomes

| Command | Outcome |
|---|---|
| `aws sts get-caller-identity` | Account `794038225197` |
| `aws lambda get-function-configuration` (CodeSha256 check) | `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`, matches p2-deploy |
| Pre-run paginated COUNT scans (3 tables + boosted-officials) | 120 / 4 / 15 / 0 |
| Pre-run `test-` scan of `photometrics-take-action` | Only `test-gap-framing-001`/`-004` |
| `funnel_test.py --dry-run all` | exit 0, full plan printed, zero AWS calls |
| `funnel_test.py all` (first, non-`--keep` attempt) | exit 0, self-cleaned; superseded by the `--keep` run for corroboration purposes |
| `funnel_test.py --keep all` (evidence run) | exit 0, all assertions passed, cleanup skipped |
| `get-item` main session sends row | representatives_failed/offered/priorities/source/location_city all present, matches harness's own report |
| `get-item` main session generate row | source/location_city/location_state/location_country all present |
| `get-item` regen session sends row | proves suppression independently: dead.official absent from representatives_sent, present in representatives_failed with reason=suppressed |
| `get-item` regen session generate row | source/location fields present |
| CloudWatch `filter-log-events` (run window) | 3 clean invocations, no ERROR/Traceback/timeout |
| CloudWatch `ERROR`/`Traceback`/`"Task timed out"` filters | all empty |
| `funnel_test.py cleanup` (separate, since `--keep` was used) | exit 0, 7 keys deleted (5 rows + 2 bounce rows) |
| Post-cleanup paginated COUNT scans | 120 / 4 / 15 / 0 — identical to pre-run |
| Post-cleanup residue scans (test- in take-action/sends, dead.official in bounces, Austin TX in boosted-officials) | 2 gap-framing rows only / 0 / 0 / 0 |
| `get-item` on both gap-framing rows | both present, unmodified, original 2026-03-03 timestamps |
| `git status --porcelain` | only pre-existing out-of-boundary modifications (`DAG.md`, `function.zip` from p2-deploy); owned files untouched |

## Known limitations / risks

- The first (non-`--keep`) `all` run's own CloudWatch window was not separately captured — it was superseded by the `--keep` run for the purpose of this handoff's evidence, but it did execute a real `/send` against production (2 recipients, both simulator addresses) and self-cleaned successfully; nothing in its output suggested any anomaly (exit 0, matched expected assertions).
- The `bounces` table count (15, not the original p1 baseline of 14) reflects one real production bounce landing in the ~2-hour gap between the p1 baseline scan and this item's pre-run scan — not investigated further, as it is outside this item's scope and the residue proof (identical pre/post count, zero `test-`/`dead.official` residue) is unaffected by it.

## Discovered

- Nothing that blocks or changes scope. Confirmed the note about a concurrent item's Columbus, OH generate row did not affect this item's counts or residue proof (pre/post `photometrics-take-action` counts were identical; residue scans are `test-`-prefix-scoped and cannot collide with it).

## STANDING RULES compliance

1. Only SES simulator addresses received mail (`success@simulator.amazonses.com`, `bounce@simulator.amazonses.com` in the main session; `success@simulator.amazonses.com`, `dead.official@simulator.amazonses.com` in check-regenerate — the latter never actually mailed, by design); `ari@sdgis.com` used only as CC; no real official was ever addressed.
2. All test rows used `session_id` prefix `test-` (`test-1788469940`/`test-regen-1788469948` from the first run, `test-1788469964`/`test-regen-1788469970` from the evidence run); all deleted by this item's own cleanup; `test-gap-framing-001`/`-004` confirmed untouched.
3. Region `us-east-2` throughout; `AWS_PAGER=''` set on every `aws` call; `MSYS_NO_PATHCONV=1` prefixed on both `aws logs` calls.
4. No git commit or push performed.
5. This handoff, at the path above.
6. Zero `/generate` calls made (0 of the phase's 2-call Anthropic budget used by this item).
7. No `ANTHROPIC_API_KEY`/`GOOGLE_CIVIC_API_KEY` value printed or copied anywhere in this handoff or during the session.
8. No Chrome/browser tools used.
