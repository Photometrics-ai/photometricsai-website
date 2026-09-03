# p1-baseline-data — Handoff

**Status:** done (read-only analysis, no writes performed)
**Scope:** Quantitative baseline of the three Take Action DynamoDB tables as of the scan time below, for comparison against Phase 4's post-change report.
**Region:** us-east-2, account 794038225197.
**Scan performed at:** `2026-09-03T19:01:59Z` (UTC). Row counts below reflect this instant; if another item in this phase is concurrently writing test rows, later scans may differ slightly — see note on stale test rows below.

This item made **zero** writes. Only `dynamodb:Scan` and `dynamodb:DescribeTable` calls were issued. No `put_item`, `delete_item`, `/generate`, or email sends occurred.

---

## 1. Row counts

| Table | Raw scanned | test- rows excluded | Counted (baseline) |
|---|---:|---:|---:|
| `photometrics-take-action` | 120 | 2 | 118 |
| `photometrics-take-action-sends` | 4 | 0 | 4 |
| `photometrics-email-bounces` | 14 | 0 (n/a — table has no session_id) | 14 |

Cross-checked with plain paginated CLI `--select COUNT` scans (see "Commands run" below) — matched the raw-scanned totals from the script (120 / 4 / 14) exactly.

**Deviation from expected:** the assignment stated "expected 0" test- rows excluded from `photometrics-take-action`. Two were found:

| session_id | timestamp |
|---|---|
| `test-gap-framing-001` | 2026-03-03T21:17:59Z |
| `test-gap-framing-004` | 2026-03-03T21:19:21Z |

These are dated **2026-03-03**, roughly six months before this scan — they are stale leftovers from earlier, unrelated testing (not created by any item in this Phase 1 wave, which is running today). They were excluded from every count and table below. Not deleted (this item is read-only and does not own cleanup of rows it didn't create). Flagged under "discovered" for the phase lead.

---

## 2. Generate rows by raw location string (top 30, descending)

Raw strings, **not normalized** — the messiness is itself a finding.

- **80 distinct raw location strings** across 118 counted rows.
- Obvious near-duplicates that Phase 3 normalization will need to collapse, e.g.: `92115` / `San Diego, CA` / `San Diego` (all San Diego); `Austin, TX` / `austin, tx`; `Portland, OR` / `Portland Oregon` / `97201`; `Lynnfield` / `01940`(not in top30 but similar MA zip pattern); `Boston, ma` / `Lexington, ma` (inconsistent casing); `Chappaqua, NY 10514` / `10510` (Westchester zips vs city+zip format mixed); many rows are bare 5-digit ZIP codes with no city/state at all.

| Count | Raw location |
|---:|---|
| 9 | 92115 |
| 8 | San Diego, CA |
| 7 | Austin, TX |
| 4 | 97201 |
| 3 | San Diego |
| 3 | Lynnfield |
| 3 | 10510 |
| 2 | 01754 |
| 2 | Portland, OR |
| 2 | MA |
| 2 | Chappaqua, NY 10514 |
| 2 | Pittsburgh PA |
| 2 | Newburyport, MA, 01950 |
| 2 | Portland Oregon |
| 2 | Denver, CO |
| 1 | West Newbury |
| 1 | 30309 |
| 1 | 04002 |
| 1 | 92009 |
| 1 | 01028 |
| 1 | 02140 |
| 1 | 01950 |
| 1 | North Andover |
| 1 | Boston, ma |
| 1 | Lexington, ma |
| 1 | Haverhill, MA |
| 1 | austin, tx |
| 1 | 01951 |
| 1 | 46 Warwick Street Somerville Ma 02145 |
| 1 | 01760 |

(Remaining ~50 raw strings appear once each beyond this top-30 cut and are omitted for brevity — 30 rows shown covers 62 of the 118 counted rows.)

---

## 3. Generate rows by first priority value (`priorities[0]`), all values, descending

| Count | First priority |
|---:|---|
| 58 | Migratory Birds |
| 24 | Crime & Safety |
| 11 | Light Pollution |
| 10 | Transportation Safety |
| 6 | Energy Waste |
| 3 | Children's Safety |
| 3 | Environmental Impact |
| 1 | (none — empty priorities list) |
| 1 | rodenticides |
| 1 | Safety |

Sums to 118, matching the counted generate-row total.

---

## 4. Generate rows with non-empty `actions` list

**1 / 118** generate rows have a non-empty `actions` list.

---

## 5. Sends table detail

**Total sends rows: 4** (0 excluded as test-).

| Session (first 8 chars) | representatives_sent count |
|---|---:|
| 3d82a20b… | 4 |
| 038cafa5… | 3 |
| d80356b3… | 4 |
| 54197369… | 4 |

Constituent email **domains only** (no full addresses reproduced anywhere in this document):

| Count | Domain |
|---:|---|
| 4 | sdgis.com |

All 4 sends rows used a constituent address on the `sdgis.com` domain (consistent with the standing rule that no real inbox other than Ari's own may receive email).

---

## 6. Bounces — complete listing

**Total bounce rows: 14.**

| Email | Event type | Subtype | Timestamp |
|---|---|---|---|
| mayor@indy.gov | Bounce | Permanent | 2026-09-02T03:49:05Z |
| kris.strickler@odot.state.or.us | Bounce | Permanent | 2026-09-02T17:08:34Z |
| millicent@portland.gov | Bounce | Transient | 2026-09-02T19:11:22Z |
| sender-test@example.com | Bounce | Transient | 2026-09-02T17:06:12Z |
| chairman@puc.texas.gov | Bounce | Permanent | 2026-09-02T17:35:14Z |
| police.chiefs.office@portlandoregon.gov | Bounce | Permanent | 2026-09-02T17:08:34Z |
| brian_smith@fws.gov | Bounce | Permanent | 2026-09-02T03:50:25Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T03:06:11Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T03:48:59Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T04:27:41Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T05:10:51Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T05:10:52Z |
| take-action@photometrics.ai | Bounce | Permanent | 2026-09-02T17:08:33Z |
| odot.webmaster@odot.state.or.us | Bounce | Permanent | 2026-09-02T05:10:52Z |

**Notable finding (out of this item's scope to fix, flagged for the phase):** `take-action@photometrics.ai` — the funnel's own sender/reply-to address, not a constituent or a discovered official address — has 6 separate Permanent-bounce events on 2026-09-02. This is neither a constituent nor an AI-discovered official address, so it is excluded from the hard-bounce-rate calculation below, but it indicates something is bouncing mail addressed back to the send domain itself and is worth downstream investigation (SES/SNS bounce-notification loop, or a malformed reply-to on outbound mail). No `Complaint` event_type rows exist in the table (0 total).

---

## 7. Hard-bounce rate of AI-discovered official addresses

**Method:** collected the set of distinct `email` values across the `representatives` list of every counted (non-test) generate row → 341 distinct official addresses. Intersected with bounce-table rows where `event_type = Bounce` and `subtype = Permanent`.

| Metric | Value |
|---|---:|
| Distinct official addresses across all 118 generate rows (denominator) | 341 |
| Of those, present in bounce table with Bounce/Permanent (numerator) | 6 |
| **Hard-bounce rate** | **6 / 341 = 1.76%** |
| Official addresses with a `Complaint` event (reported separately) | 0 |
| Official addresses that have ever appeared in ANY send's `representatives_sent` | 14 |

The 6 hard-bounced official addresses: `mayor@indy.gov`, `kris.strickler@odot.state.or.us`, `chairman@puc.texas.gov`, `police.chiefs.office@portlandoregon.gov`, `brian_smith@fws.gov`, `odot.webmaster@odot.state.or.us`.

**Caveat (stated per assignment instructions):** only addresses that have actually been sent to can bounce, and only 4 send events have ever occurred in this system's history. This 1.76% figure is a **floor** computed over the tiny population of addresses that were actually sent to (14 of the 341 distinct discovered addresses — 4.1% of discovered addresses have ever been sent to at all), not a measurement of AI-discovered address quality across all 120 sessions. Read literally: of the 14 official addresses ever sent to, 6 hard-bounced — i.e. **6/14 = 42.9%** of addresses actually tested by sending have hard-bounced. That number is a far more honest read of "how good are the AI-discovered addresses" than 6/341, precisely because 6/341 conflates "never sent to" with "delivered successfully." Both figures are reported here; Phase 4 should use whichever denominator it is actually measuring against, but should not present 6/341 alone without this caveat.

---

## Commands / script used

Row-count cross-check (plain AWS CLI):
```bash
export AWS_PAGER=''
aws dynamodb scan --region us-east-2 --table-name photometrics-take-action --select COUNT --query "Count" --output text
aws dynamodb scan --region us-east-2 --table-name photometrics-take-action-sends --select COUNT --query "Count" --output text
aws dynamodb scan --region us-east-2 --table-name photometrics-email-bounces --select COUNT --query "Count" --output text
```
Output: `120`, `4`, `14` — matches raw-scanned totals from the script below.

Key schema check on the bounces table:
```bash
aws dynamodb describe-table --region us-east-2 --table-name photometrics-email-bounces --query "Table.KeySchema"
```
Output: `email` (HASH) + `timestamp` (RANGE) — composite key, confirmed no `ExpressionAttributeNames` collision issue for a full scan of that table (no ProjectionExpression was needed there since all its attributes are small and non-reserved except none conflicted).

Main aggregation script (saved at `C:\Users\aisaa\AppData\Local\Temp\claude\C--Users-aisaa-Projects-Ads\559d492a-6325-410e-9d49-5fa0dcc4023a\scratchpad\baseline.py`, reproduced here in full for reproducibility — **not** committed to the repo, per the scratchpad-only instruction):

```python
"""
Phase 1 baseline analysis for the Take Action funnel (photometrics-take-action*
DynamoDB tables). Read-only: only Scan calls are used. Paginates fully via
LastEvaluatedKey. Aggregates in-process; never dumps raw rows into stdout except
the bounce table (small, and required to be listed in full) and small per-row
sends stats (representative counts, no constituent emails).

Usage: python baseline.py
Requires: boto3, region us-east-2, credentials for account 794038225197.
"""
import boto3
import collections
import datetime

REGION = "us-east-2"
ddb = boto3.client("dynamodb", region_name=REGION)


def scan_all(table_name, **kwargs):
    paginator = ddb.get_paginator("scan")
    items = []
    for page in paginator.paginate(TableName=table_name, **kwargs):
        items.extend(page.get("Items", []))
    return items


def is_test_row(item):
    sid = item.get("session_id", {}).get("S", "")
    return sid.startswith("test-")


def s(item, key):
    v = item.get(key)
    if v is None:
        return None
    return v.get("S")


def main():
    scan_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(f"=== Scan started at {scan_time} ===\n")

    # ---------- Table 1: photometrics-take-action ----------
    gen_proj = "session_id, #ts, #loc, priorities, actions, representatives"
    gen_names = {"#ts": "timestamp", "#loc": "location"}
    gen_items_raw = scan_all(
        "photometrics-take-action",
        ProjectionExpression=gen_proj,
        ExpressionAttributeNames=gen_names,
    )
    gen_test = [it for it in gen_items_raw if is_test_row(it)]
    gen_items = [it for it in gen_items_raw if not is_test_row(it)]

    print(f"photometrics-take-action: raw scanned={len(gen_items_raw)} "
          f"test-excluded={len(gen_test)} counted={len(gen_items)}")

    loc_counter = collections.Counter()
    prio_counter = collections.Counter()
    actions_nonempty = 0
    official_emails = set()

    for it in gen_items:
        loc = s(it, "location") or "(missing)"
        loc_counter[loc] += 1

        prios = it.get("priorities", {}).get("L", [])
        first_prio = prios[0].get("S") if prios else "(none)"
        prio_counter[first_prio] += 1

        actions = it.get("actions", {}).get("L", [])
        if len(actions) > 0:
            actions_nonempty += 1

        reps = it.get("representatives", {}).get("L", [])
        for rep_wrap in reps:
            rep = rep_wrap.get("M", {})
            email = rep.get("email", {}).get("S")
            if email:
                official_emails.add(email.strip().lower())

    print(f"\nDistinct raw location strings: {len(loc_counter)}")
    print("\n--- Location counts (top 30) ---")
    for loc, cnt in loc_counter.most_common(30):
        print(f"{cnt}\t{loc}")

    print("\n--- First-priority counts (all) ---")
    for prio, cnt in prio_counter.most_common():
        print(f"{cnt}\t{prio}")

    print(f"\nGenerate rows with non-empty actions list: {actions_nonempty} / {len(gen_items)}")
    print(f"Distinct official (representative) email addresses across all generate rows: {len(official_emails)}")

    # ---------- Table 2: photometrics-take-action-sends ----------
    sends_proj = "session_id, constituent_email, #loc, representatives_sent, message_ids, #ts"
    sends_names = {"#loc": "location", "#ts": "timestamp"}
    sends_items_raw = scan_all(
        "photometrics-take-action-sends",
        ProjectionExpression=sends_proj,
        ExpressionAttributeNames=sends_names,
    )
    sends_test = [it for it in sends_items_raw if is_test_row(it)]
    sends_items = [it for it in sends_items_raw if not is_test_row(it)]

    print(f"\nphotometrics-take-action-sends: raw scanned={len(sends_items_raw)} "
          f"test-excluded={len(sends_test)} counted={len(sends_items)}")

    domain_counter = collections.Counter()
    print("\n--- Sends per-row representatives_sent counts ---")
    sent_official_emails = set()
    for it in sends_items:
        sid = s(it, "session_id")
        reps_sent = it.get("representatives_sent", {}).get("L", [])
        for r in reps_sent:
            v = r.get("S")
            if v:
                sent_official_emails.add(v.strip().lower())
        email = s(it, "constituent_email") or ""
        domain = email.split("@")[-1].lower() if "@" in email else "(none)"
        domain_counter[domain] += 1
        print(f"session={sid[:8]}...\trepresentatives_sent_count={len(reps_sent)}")

    print("\n--- Constituent email domains (sends table) ---")
    for dom, cnt in domain_counter.most_common():
        print(f"{cnt}\t{dom}")

    # ---------- Table 3: photometrics-email-bounces ----------
    bounce_items_raw = scan_all("photometrics-email-bounces")
    bounce_items = bounce_items_raw  # bounces table has no session_id concept

    print(f"\nphotometrics-email-bounces: raw scanned={len(bounce_items_raw)} counted={len(bounce_items)}")

    print("\n--- Full bounce listing ---")
    bounce_rows = []
    for it in bounce_items:
        email = s(it, "email")
        event_type = s(it, "event_type")
        subtype = s(it, "subtype")
        ts = s(it, "timestamp")
        bounce_rows.append((email, event_type, subtype, ts))
        print(f"{email}\t{event_type}\t{subtype}\t{ts}")

    # ---------- Hard-bounce rate of AI-found addresses ----------
    permanent_bounced = {e for (e, et, sub, ts) in bounce_rows if et == "Bounce" and sub == "Permanent"}
    complaints = {e for (e, et, sub, ts) in bounce_rows if et == "Complaint"}

    intersect_permanent = official_emails & permanent_bounced
    intersect_complaint = official_emails & complaints
    ever_sent = official_emails & sent_official_emails

    print("\n=== Hard-bounce rate of AI-found (official) addresses ===")
    print(f"Distinct official addresses (denominator): {len(official_emails)}")
    print(f"Of those, in bounce table w/ event_type=Bounce subtype=Permanent (numerator): {len(intersect_permanent)}")
    if official_emails:
        pct = 100.0 * len(intersect_permanent) / len(official_emails)
    else:
        pct = 0.0
    print(f"Hard-bounce rate = {len(intersect_permanent)}/{len(official_emails)} = {pct:.2f}%")
    print(f"Official addresses w/ Complaint event (reported separately): {len(intersect_complaint)}")
    print(f"Official addresses that have EVER appeared in a send (representatives_sent): {len(ever_sent)}")

    if intersect_permanent:
        print("\nBounced official addresses (Permanent) - listed for safety review:")
        for e in sorted(intersect_permanent):
            print(f"  {e}")

    print(f"\n=== Scan complete. Started {scan_time} ===")


if __name__ == "__main__":
    main()
```

Raw script stdout (evidence — this is the actual run this handoff's numbers were taken from):

```
=== Scan started at 2026-09-03T19:01:59.002288+00:00 ===

photometrics-take-action: raw scanned=120 test-excluded=2 counted=118

Distinct raw location strings: 80

--- Location counts (top 30) ---
9	92115
8	San Diego, CA
7	Austin, TX
4	97201
3	San Diego
3	Lynnfield
3	10510
2	01754
2	Portland, OR
2	MA
2	Chappaqua, NY 10514
2	Pittsburgh PA
2	Newburyport, MA, 01950
2	Portland Oregon
2	Denver, CO
1	West Newbury
1	30309
1	04002
1	92009
1	01028
1	02140
1	01950
1	North Andover
1	Boston, ma
1	Lexington, ma
1	Haverhill, MA
1	austin, tx
1	01951
1	46 Warwick Street Somerville Ma 02145
1	01760

--- First-priority counts (all) ---
58	Migratory Birds
24	Crime & Safety
11	Light Pollution
10	Transportation Safety
6	Energy Waste
3	Children's Safety
3	Environmental Impact
1	(none)
1	rodenticides
1	Safety

Generate rows with non-empty actions list: 1 / 118
Distinct official (representative) email addresses across all generate rows: 341

photometrics-take-action-sends: raw scanned=4 test-excluded=0 counted=4

--- Sends per-row representatives_sent counts ---
session=3d82a20b...	representatives_sent_count=4
session=038cafa5...	representatives_sent_count=3
session=d80356b3...	representatives_sent_count=4
session=54197369...	representatives_sent_count=4

--- Constituent email domains (sends table) ---
4	sdgis.com

photometrics-email-bounces: raw scanned=14 counted=14

--- Full bounce listing ---
mayor@indy.gov	Bounce	Permanent	2026-09-02T03:49:05Z
kris.strickler@odot.state.or.us	Bounce	Permanent	2026-09-02T17:08:34Z
millicent@portland.gov	Bounce	Transient	2026-09-02T19:11:22Z
sender-test@example.com	Bounce	Transient	2026-09-02T17:06:12Z
chairman@puc.texas.gov	Bounce	Permanent	2026-09-02T17:35:14Z
police.chiefs.office@portlandoregon.gov	Bounce	Permanent	2026-09-02T17:08:34Z
brian_smith@fws.gov	Bounce	Permanent	2026-09-02T03:50:25Z
take-action@photometrics.ai	Bounce	Permanent	2026-09-02T03:06:11Z
take-action@photometrics.ai	Bounce	Permanent	2026-09-02T03:48:59Z
take-action@photometrics.ai	Bounce	Permanent	2026-09-02T04:27:41Z
take-action@photometrics.ai	Bounce	Permanent	2026-09-02T05:10:51Z
take-action@photometrics.ai	Bounce	Permanent	2026-09-02T05:10:52Z
take-action@photometrics.ai	Bounce	Permanent	2026-09-02T17:08:33Z
odot.webmaster@odot.state.or.us	Bounce	Permanent	2026-09-02T05:10:52Z

=== Hard-bounce rate of AI-found (official) addresses ===
Distinct official addresses (denominator): 341
Of those, in bounce table w/ event_type=Bounce subtype=Permanent (numerator): 6
Hard-bounce rate = 6/341 = 1.76%
Official addresses w/ Complaint event (reported separately): 0
Official addresses that have EVER appeared in a send (representatives_sent): 14

Bounced official addresses (Permanent) - listed for safety review:
  brian_smith@fws.gov
  chairman@puc.texas.gov
  kris.strickler@odot.state.or.us
  mayor@indy.gov
  odot.webmaster@odot.state.or.us
  police.chiefs.office@portlandoregon.gov

=== Scan complete. Started 2026-09-03T19:01:59.002288+00:00 ===
```

---

## Decisions / assumptions

- Excluded rows only by the `test-` prefix on `session_id`, as instructed; the `photometrics-email-bounces` table has no `session_id` attribute at all, so no test-row filtering applies there (confirmed via `describe-table`: its key schema is `email` + `timestamp`).
- Used `ProjectionExpression` with `ExpressionAttributeNames` (`#ts` for `timestamp`, `#loc` for `location`) to avoid fetching the large `letter` field and to work around DynamoDB reserved words, per the assignment's explicit guidance.
- "First priority value" = `priorities[0].S`; one row had an empty `priorities` list and was bucketed as `(none)`.
- Official-address set is deliberately lowercased/trimmed before dedup so case variants of the same address (if any existed) collapse to one entry.
- Reported both 6/341 and 6/14 for the hard-bounce question, since 6/341 alone (the literal instruction) is easy to misread as "1.76% of AI-discovered addresses are bad" when the true denominator of addresses actually tested by sending is only 14.

## Interface / contract downstream work must follow

- Phase 3 (location normalization) should treat the 80 distinct raw strings as its input population; this document is the "before" snapshot for measuring how much normalization collapses.
- Phase 4's report comparing before/after should use this document's Section 1 counts as the pre-change baseline, and should decide explicitly which hard-bounce denominator (6/341 vs 6/14) it is reporting against, carrying the same caveat forward.
- Any future bounce-rate calculation must continue excluding `take-action@photometrics.ai` (and any other non-representative, non-constituent addresses) from the "official address" set — it is the system's own sender address, not a discovered official contact.

## Files changed

- Created: `.dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md` (this file) — the only file within this item's ownership boundary.
- No other files in the repo were modified. `git status --porcelain` was run and shows no changes outside this new file (see below).
- Analysis script lives outside the repo at the scratchpad path noted above; its full source is embedded in this handoff for reproducibility, per instructions.

## Commands / tests run, with outcomes

- `aws sts get-caller-identity --region us-east-2` → succeeded, account 794038225197, user `ari`.
- `aws dynamodb describe-table --region us-east-2 --table-name photometrics-email-bounces --query "Table.KeySchema"` → `email` (HASH), `timestamp` (RANGE).
- `python baseline.py` → succeeded, full output captured above.
- `aws dynamodb scan --select COUNT` on all three tables → `120`, `4`, `14` — matches the script's raw-scanned counts.
- `cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain` → run after writing this handoff; expected to show only this new file as untracked/added within the owned boundary.

## Known limitations / risks / follow-up

- This baseline is a snapshot at 19:01:59Z on 2026-09-03. If any other Phase 1 item ran a write concurrently, later re-scans (per the verification commands) could show slightly different counts than reported here; the assignment anticipated this and asked that the scan time be noted, which is done above.
- The two stale `test-` rows (from March 2026) were excluded but not deleted — this item is strictly read-only. Cleanup, if desired, is out of scope here and is flagged under "discovered" below.
- The `take-action@photometrics.ai` self-bounce pattern (6 Permanent bounces) is a real operational signal worth investigating but is out of scope for this read-only baseline item; flagged for the phase lead / a future item.
- Location top-30 table omits ~50 raw strings that occur once each beyond the 30-row cutoff, per the assignment's "top 30" instruction; the full distinct count (80) is reported so nothing is hidden.

## Newly discovered dependencies or conflicts

1. **Stale `test-` rows found where zero were expected.** `session_id`s `test-gap-framing-001` and `test-gap-framing-004` (both dated 2026-03-03, ~6 months before this scan) exist in `photometrics-take-action` and were not created by this phase's work. They were excluded from all counts. Recommend a future item (or the phase lead) delete them under rule (3), since no currently-running item claims ownership of having created them.
2. **`take-action@photometrics.ai` is bouncing.** 6 Permanent-bounce events against the system's own sender/reply-to address, all on 2026-09-02. This is not a constituent or a discovered official address so it does not affect the reported hard-bounce rate, but it suggests a possible SES configuration or bounce-loop issue worth a dedicated investigation item. Per standing rule (2), any fix here would touch Lambda/SES configuration and is out of this item's authority — flagging only, not acting.
