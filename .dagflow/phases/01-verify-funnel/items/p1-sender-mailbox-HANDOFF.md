# p1-sender-mailbox — HANDOFF

**Kind:** investigation (read-only against AWS; no changes made)
**Status:** needs_human_decision
**Region:** us-east-2, `AWS_PAGER=''` on every call.

## Summary

`take-action@photometrics.ai` is Bcc'd on every outgoing Take Action letter
(`lambda/take-action/lambda_function.py`, `handle_send()`, ~line 1031:
`"BccAddresses": [SES_SENDER_EMAIL]`) and is also the `FromEmailAddress`
local part (~line 1027). The address is confirmed hard-bouncing on every
send and is currently sitting on the SES account-level suppression list
with reason `BOUNCE`. SES only has the **domain** `photometrics.ai`
verified for sending — there is no separate identity verification for the
specific mailbox, and SES identity verification never proves an inbox
exists. This is consistent with (but does not, from the CLI alone, prove)
the working theory: the mailbox does not exist in Google Workspace, so the
Bcc copy has nowhere to be delivered and bounces on every single send.
Only Ari can confirm this in Google Workspace admin (see Option A).

No AWS resource, Lambda configuration, SES suppression entry, or Google
Workspace object was modified by this investigation.

## Evidence

### 1. `aws sesv2 get-suppressed-destination --email-address take-action@photometrics.ai --region us-east-2`

Not a NotFoundException — the address **is** on the suppression list:

```json
{
    "SuppressedDestination": {
        "EmailAddress": "take-action@photometrics.ai",
        "Reason": "BOUNCE",
        "LastUpdateTime": "2026-09-01T20:06:11.728000-07:00",
        "Attributes": {
            "MessageId": "010f01a06014ccd1-73709d8c-3c72-40d0-8089-312e52f8f918-000000",
            "FeedbackId": "010f01a06014cf6c-296b091f-306b-491e-b1c4-fffc4a35fa21-000000"
        }
    }
}
```

### 2. `aws sesv2 list-suppressed-destinations --region us-east-2`

8 suppressed destinations total. `take-action@photometrics.ai` is one of
them (reason BOUNCE, last updated 2026-09-01T20:06:11-07:00). Full list:

```json
{
    "SuppressedDestinationSummaries": [
        {"EmailAddress": "chairman@puc.texas.gov", "Reason": "BOUNCE", "LastUpdateTime": "2026-09-02T10:35:13.378000-07:00"},
        {"EmailAddress": "phase1-test@photometrics.ai", "Reason": "BOUNCE", "LastUpdateTime": "2026-08-25T11:15:21.685000-07:00"},
        {"EmailAddress": "take-action@photometrics.ai", "Reason": "BOUNCE", "LastUpdateTime": "2026-09-01T20:06:11.728000-07:00"},
        {"EmailAddress": "brian_smith@fws.gov", "Reason": "BOUNCE", "LastUpdateTime": "2026-09-01T20:50:25.085000-07:00"},
        {"EmailAddress": "police.chiefs.office@portlandoregon.gov", "Reason": "BOUNCE", "LastUpdateTime": "2026-09-02T10:08:34.281000-07:00"},
        {"EmailAddress": "mayor@indy.gov", "Reason": "BOUNCE", "LastUpdateTime": "2026-09-01T20:49:04.843000-07:00"},
        {"EmailAddress": "kris.strickler@odot.state.or.us", "Reason": "BOUNCE", "LastUpdateTime": "2026-09-02T10:08:34.498000-07:00"},
        {"EmailAddress": "odot.webmaster@odot.state.or.us", "Reason": "BOUNCE", "LastUpdateTime": "2026-09-01T22:10:52.603000-07:00"}
    ]
}
```

(Note: `phase1-test@photometrics.ai` is also present — pre-existing state
from a prior test send, not created by this item. Not touched here.)

### 3. `aws sesv2 list-email-identities --region us-east-2`

Only the **domain** `photometrics.ai` is a verified SES identity — there is
no separate identity for the address `take-action@photometrics.ai`:

```json
{
    "EmailIdentities": [
        {
            "IdentityType": "DOMAIN",
            "IdentityName": "photometrics.ai",
            "SendingEnabled": true,
            "VerificationStatus": "SUCCESS"
        }
    ]
}
```

Domain-level verification (DKIM/DNS) authorizes SES to send *as*
`anything@photometrics.ai` — it says nothing about whether a real inbox
exists at that address in Google Workspace.

### 4. `aws sesv2 get-account --region us-east-2`

Account-level auto-suppression is active for both BOUNCE and COMPLAINT,
which is why one hard bounce is enough to land an address on the
suppression list and block all future sends to it:

```json
{
    "DedicatedIpAutoWarmupEnabled": true,
    "EnforcementStatus": "HEALTHY",
    "ProductionAccessEnabled": true,
    "SendQuota": {"Max24HourSend": 50000.0, "MaxSendRate": 14.0, "SentLast24Hours": 4.0},
    "SendingEnabled": true,
    "SuppressionAttributes": {"SuppressedReasons": ["BOUNCE", "COMPLAINT"]},
    "Details": {
        "MailType": "TRANSACTIONAL",
        "WebsiteURL": "https://www.photometrics.ai",
        "ContactLanguage": "EN",
        "UseCaseDescription": "Photometrics AI is a SaaS platform for municipal street lighting optimization and networked lighting control. We send two kinds of transactional email, both single, individually-triggered messages -- never bulk or scheduled campaigns: (1) account verification codes and password reset links via Amazon Cognito to users who register at beta.photometrics.ai, and (2) citizen-initiated advocacy letters from our public tool at www.photometrics.ai/take-action/. There, a member of the public enters their location and a short set of lighting-related concerns, and we send one letter on their behalf to local, county, or state government officials (never to private individuals) about street lighting policy. Recipient emails are identified immediately before send via a web search that resolves current staff directories and .gov contact pages, and the same recipient list is echoed back to the sender for review before sending. The sender is CC'd and set as Reply-To on every message, so any reply from the official goes directly to them, not to us. Each session can send at most once. Volume is low and citizen-driven, not marketing.",
        "ReviewDetails": {"Status": "GRANTED"}
    }
}
```

### 5. `photometrics-email-bounces` scan, filtered to `email = take-action@photometrics.ai`

`aws dynamodb scan --table-name photometrics-email-bounces --region us-east-2 --filter-expression "email = :e" --expression-attribute-values '{":e":{"S":"take-action@photometrics.ai"}}'`

**7 rows** (assignment briefing said 6 — the count has grown by one since
that briefing was written; a 7th bounce landed at 2026-09-03T19:11:51Z,
consistent with an ongoing, still-live problem, not a fixed one). Every
row is `event_type=Bounce`, `subtype=Permanent` — a hard bounce every
time, no exceptions:

| email | event_type | subtype | timestamp |
|---|---|---|---|
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T03:06:11Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T03:48:59Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T04:27:41Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T05:10:51Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T05:10:52Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T17:08:33Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-03T19:11:51Z |

(Table scan: `Count: 7, ScannedCount: 15` — 15 total bounce rows in the
table, 7 of them for this address.)

### 6. Git history of the sender address in `lambda/take-action/lambda_function.py`

`git log -S "advocacy@photometrics.ai" --oneline -- lambda/take-action/lambda_function.py`
→ **no output** — `advocacy@photometrics.ai` has never appeared in this
file's history at all (added or removed).

`git log -S "SES_SENDER_EMAIL" --oneline -- lambda/take-action/lambda_function.py`
→ one commit:
```
8a1be58 Add managed SES send to Take Action letters, with bounce-based official exclusion
```
That is the commit that introduced `SES_SENDER_EMAIL` (and the current
default `take-action@photometrics.ai`) in the first place; no later
commit ever touched it. So **no alternative sender address was ever
used** — `take-action@photometrics.ai` has been the sender since managed
SES sending was added, and it has never been anything else.

Current code (unchanged):
```
34:SES_SENDER_EMAIL = os.environ.get("SES_SENDER_EMAIL", "take-action@photometrics.ai")
1027:            "FromEmailAddress": f'"{sender_name}" <{SES_SENDER_EMAIL}>',
1031:                "BccAddresses": [SES_SENDER_EMAIL],
```

### 7. `aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2` — Environment.Variables

Full deployed map (secrets redacted per instructions):

```json
{
    "SEND_LOG_TABLE": "photometrics-take-action-sends",
    "BOUNCE_TABLE": "photometrics-email-bounces",
    "DYNAMODB_TABLE": "photometrics-take-action",
    "BOOSTED_TABLE": "photometrics-boosted-officials",
    "SES_CONFIGURATION_SET": "take-action-sends",
    "SES_SENDER_EMAIL": "take-action@photometrics.ai",
    "GOOGLE_CIVIC_API_KEY": "<GOOGLE_CIVIC_API_KEY_REDACTED>",
    "ANTHROPIC_API_KEY": "<ANTHROPIC_API_KEY_REDACTED>"
}
```

Confirms both open questions from the brief:
- `SES_SENDER_EMAIL` is deployed as `take-action@photometrics.ai` (the
  code default, i.e. no override is set — the env var is present but
  equals the default value).
- `SES_CONFIGURATION_SET` is deployed as `take-action-sends` (not the
  code's empty-string default — production does have this set, as
  believed).

## Decision needed (Ari)

Both options below fully eliminate the hard-bounce loop. Neither is a
"do nothing" option — one of the two must be chosen and applied by a
human (this item makes no changes).

**Shared tradeoff for both options:** the Bcc exists so Ari has a
standing copy of every letter sent on a citizen's behalf. Option A keeps
that copy landing in a `take-action@` address; Option B keeps the copy
but relocates it to a different, already-working inbox — it does not
eliminate the "Ari gets a copy" behavior, just moves where the copy goes.

### Option A — Create `take-action@photometrics.ai` as a real destination in Google Workspace

What to check/create (in Google Workspace admin, not from the CLI):
1. Log into Google Workspace admin console for the `photometrics.ai`
   domain.
2. Under Directory → Users, confirm there is no user mailbox at
   `take-action@photometrics.ai`. (Expected: none — this is the
   suspected root cause.)
3. Under Apps → Google Workspace → Gmail → Routing, or under Groups,
   check whether `take-action@photometrics.ai` exists as a **group**
   or **alias** pointing somewhere that no longer accepts mail (e.g. an
   alias to a deleted/suspended user) — that would also produce a hard
   bounce and needs to be found the same way.
4. Create one of:
   - A real mailbox/user `take-action@photometrics.ai`, or
   - A Google Group `take-action@photometrics.ai` with Ari (and/or
     other appropriate staff) as members, with "Who can post" allowing
     mail from `photometrics.ai`'s own outbound (SES sends from a
     domain identity, not from a Workspace-authenticated sender, so
     confirm the group accepts external senders / is not restricted to
     internal-only posting), or
   - An alias on an existing mailbox (e.g. alias of Ari's own Workspace
     mailbox) pointing to `take-action@photometrics.ai`.
5. No AWS or Lambda change is required for Option A — `SES_SENDER_EMAIL`
   stays `take-action@photometrics.ai`.

Evidence it worked: after the fix, trigger one test send (SES mailbox
simulator recipient only, e.g. `success@simulator.amazonses.com`, per
standing rule — never a real official) and confirm:
- No new row appears in `photometrics-email-bounces` for
  `email = take-action@photometrics.ai` with a timestamp after the fix
  (re-run the scan command in Evidence #5 above and compare).
- The mailbox/group now actually receives the Bcc copy (check the
  Workspace inbox/group directly).

### Option B — Switch `SES_SENDER_EMAIL` to an existing, real mailbox

Recommended value: **`ari@sdgis.com`** — it is confirmed to be a real,
already-working inbox (it is the only non-simulator address the standing
rules for this phase permit any test email to reach), so switching to it
requires no new Workspace object and no new verification step to test.
(If Ari prefers an `@photometrics.ai` address instead — e.g. a
Workspace mailbox Ari already owns — the same command works with that
address substituted; note the SES identity/verification requirement
below covers that case too.)

**SES identity/verification prerequisite:** SES has the `photometrics.ai`
domain verified (Evidence #3), so any `...@photometrics.ai` address needs
no additional SES verification to be used as `FromEmailAddress`/Bcc — the
domain identity covers it. `ari@sdgis.com` is on a **different** domain
(`sdgis.com`), which is **not** a verified SES identity in this account —
using it as `FromEmailAddress` would fail to send (SES requires the
`From` domain, or the exact address, to be a verified identity in the
sending account). **Recommendation therefore narrows to an
`@photometrics.ai` mailbox that already exists and works** — Ari should
supply that address; if none is confirmed to already work, Option A is
the simpler fix. If Ari does want `ari@sdgis.com` specifically, it would
first need to be added and verified as its own SES identity
(`aws sesv2 create-email-identity --email-identity ari@sdgis.com --region us-east-2`,
then complete DKIM/verification) before Option B's command below would
succeed for that address — this is exactly the kind of AWS
identity/verification change item p1-sender-mailbox is not authorized to
make; it would need its own follow-up item.

Complete, copy-pasteable command (only `SES_SENDER_EMAIL` changed; every
other key preserved verbatim; **replace the two placeholder values with
the real secrets before running — do not run this with the literal
placeholder text**):

```bash
export AWS_PAGER=''
aws lambda update-function-configuration \
  --function-name photometrics-take-action \
  --region us-east-2 \
  --environment 'Variables={SEND_LOG_TABLE=photometrics-take-action-sends,BOUNCE_TABLE=photometrics-email-bounces,DYNAMODB_TABLE=photometrics-take-action,BOOSTED_TABLE=photometrics-boosted-officials,SES_CONFIGURATION_SET=take-action-sends,SES_SENDER_EMAIL=<NEW_SENDER_ADDRESS>,GOOGLE_CIVIC_API_KEY=<GOOGLE_CIVIC_API_KEY_REDACTED>,ANTHROPIC_API_KEY=<ANTHROPIC_API_KEY_REDACTED>}'
```

Substitute `<NEW_SENDER_ADDRESS>` with the chosen real mailbox (must be
`...@photometrics.ai` unless the sdgis.com domain is first verified in
SES as described above), and substitute the two secret placeholders with
the actual current values (visible in the AWS console / Lambda config,
not reproduced here). **`--environment` replaces the entire Variables
map** — any key omitted from this command would be silently deleted from
production, so this command intentionally lists every key currently
deployed (per Evidence #7).

### Suppression-list cleanup (applies to both options)

`take-action@photometrics.ai` is currently on the SES suppression list
(confirmed in Evidence #1 and #2, reason `BOUNCE`, auto-suppression is
on per Evidence #4). SES will silently refuse to send to a suppressed
address even after the underlying mailbox problem is fixed, so:

- **If Option A is chosen** (mailbox created, `SES_SENDER_EMAIL`
  unchanged): the suppression entry for `take-action@photometrics.ai`
  **must** be removed, or every send will continue to silently skip the
  Bcc (SES suppression is checked per-send regardless of why the
  original bounce happened).
- **If Option B is chosen** (sender switched away from
  `take-action@photometrics.ai`): removal is not strictly required for
  sends to keep working (the new address isn't suppressed), but removing
  it is still recommended for cleanliness / in case anything reverts to
  the old address later.

To check whether it's currently on the list: re-run Evidence command #1
(`aws sesv2 get-suppressed-destination --email-address
take-action@photometrics.ai --region us-east-2` — a `NotFoundException`
means it is not; the JSON body shown in Evidence #1 above means it is,
which is the current state).

To remove it:
```bash
export AWS_PAGER=''
aws sesv2 delete-suppressed-destination --email-address take-action@photometrics.ai --region us-east-2
```

## Files touched

- Created/overwrote: `.dagflow/phases/01-verify-funnel/items/p1-sender-mailbox-HANDOFF.md` (this file — the only file this item owns/writes).
- No other file, AWS resource, Lambda configuration, SES entry, or Google Workspace object was modified.

## Test rows created

None. This item made no writes of any kind (read-only investigation).

## Known limitations / follow-up

- Whether the mailbox genuinely doesn't exist in Google Workspace (vs.
  some other Workspace-side routing problem, e.g. a broken alias) cannot
  be confirmed from the CLI/AWS side — that's exactly why this is
  `needs_human_decision` rather than a completed fix. Option A's
  checklist walks through both possibilities.
- If Option B is chosen with a brand-new `@photometrics.ai` address that
  has never been used as a Workspace mailbox either, the same bounce
  problem would simply recur at the new address — Option B's value only
  holds if the chosen address is a mailbox Ari confirms already receives
  mail today.
- `phase1-test@photometrics.ai` was found on the suppression list during
  Evidence #2 (pre-existing, not created by this item) — flagged here for
  visibility but out of scope; not touched.
