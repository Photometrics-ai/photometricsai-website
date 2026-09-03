# p2-report-verify — Handoff

**Status:** done (read-only verification; zero writes)
**Scope:** Independently confirm `report.py`'s numbers reconcile with the Phase 01 baseline (118 generate / 4 sends) now that `p2-harness-run` and `p2-live-generate-check` have both added and cleaned up their test rows.
**Region:** us-east-2, account 794038225197.
**Verification run performed at:** 2026-09-03, ~21:20–21:25 UTC.

Made **zero** writes. Only `dynamodb:Scan`/`get-item`-style read calls (via `report.py` and plain `aws dynamodb scan --select COUNT`) were issued. No `put_item`/`delete_item`/`update_item`, no `/generate`, no `/send`, no repo file edits.

---

## Required reading done first

- `.dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md` — baseline: 120 raw / 2 test- excluded / 118 counted (generate); 4 raw / 0 excluded / 4 counted (sends); 14 bounce rows at scan time `2026-09-03T19:01:59Z`.
- `.dagflow/phases/02-harden-instrument-report/items/p2-report-tool-HANDOFF.md` — how `report.py` buckets (`pre-attribution` when `source`/`utm_content` absent), its own production run showing 118/4/15/6 totals, and its `adgroups.json` mapping.
- `.dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md` — harness created `test-1788469964`/`test-regen-1788469970` (plus an earlier self-cleaned `test-1788469940`/`test-regen-1788469948` pair), then ran an explicit `cleanup` deleting all 5 rows + 2 bounce rows; post-cleanup counts confirmed 120/4/15/0, residue scan showed only `test-gap-framing-001`/`-004` remaining.
- `.dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md` — created and deleted `test-livegen-1788469919` via one `/generate` Lambda Invoke call; its own post-delete scan showed `test-livegen-1788469919` absent, but 4 test- rows still present at that moment (`test-gap-framing-001/-004`, `test-1788469964`, `test-regen-1788469970` — the harness's `--keep` rows, not yet cleaned at that point in the timeline).
- Per this item's own assignment note: the lead separately ran one browser-driven `/generate` ("Columbus, OH", name "E2E Test") and deleted that row at ~21:35 UTC; `adgroups.json` now maps `199915882237` to `Environmental Impact` (a lead edit, already committed at HEAD `2d927f8`, `git diff HEAD -- adgroups.json` is empty — not a pending/uncommitted change and not made by this item).

---

## 1. `python report.py` — full raw markdown output

Command: `cd lambda/take-action/tools && python report.py`

```
# Take Action Attribution Report

Scanned: generate table 120 raw (2 test- excluded, 118 counted); sends table 4 raw (0 test- excluded, 4 counted); bounce table 15 raw rows.

## Cut 1 - Ad Group x Keyword x Top Priority x Location

| ad group | keyword | top priority | location | generated | sent sessions | reps emailed | suppressed | hard bounces |
|---|---|---|---|---|---|---|---|---|
| pre-attribution | (blank) | Energy Waste | San Diego, CA | 4 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Environmental Impact | 97201 | 3 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 92115 | 3 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Austin, TX | 3 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | San Diego, CA | 3 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Transportation Safety | 92115 | 3 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | Austin, TX | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | Chappaqua, NY 10514 | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | Lynnfield | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | San Diego | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | 92115 | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | Pittsburgh PA | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 01754 | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | MA | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Newburyport, MA, 01950 | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Transportation Safety | 10510 | 2 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | (blank) | (blank) | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Children's Safety | San Diego | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Children's Safety | San Diego, CA | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Children's Safety | San Diego, ca | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | 01760 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | 01940 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | 92104 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | 92115 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | 94040 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | 97201 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | Denver, CO | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | Georgetown Texas | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | MASSACHUSSETTS | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | Portland or | 1 | 1 | 4 | 0 | 2 |
| pre-attribution | (blank) | Crime & Safety | San Antonio texas | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | San Diego CA | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | San diego | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | San diego tx | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | massachuasetts | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Crime & Safety | san diego, ca | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Energy Waste | 10510 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Energy Waste | Austin, TX | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | 01719 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | 54651 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | Lincoln, MA | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | Newburyport, MA 01950 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | Portland Oregon | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | Portland, OR | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Light Pollution | austin, tx | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 01028 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 01475 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 01950 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 01951 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 01985 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 02140 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 02360 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 02747 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 02917 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 03077 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 04002 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 14850 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 30309 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 46 Warwick Street Somerville Ma 02145 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 91942 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | 92346 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Agawam,Ma 01002 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Andover | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Boston, ma | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Burrillville ri 02830 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Cambridge, Massachusetts | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Haverhill, MA | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Hingham | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Lexington, ma | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Lynnfield | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Lynnfield, MA 01940 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Ma was | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Massachusetts | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Medford, ma 02155 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Mountain view,ca | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Newbury | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Newburyport, MA | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | North Andover | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | North Attleboro | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Philadelphia, PA | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Portland, OR | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | San Diego ca | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Stow Ma 01775 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Vineyard Haven | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | West Newbury | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | West suffield ct 06093 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | Woburn | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Migratory Birds | warrington, pa | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Safety | Austin TX | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Transportation Safety | 65234 | 1 | 1 | 3 | 0 | 2 |
| pre-attribution | (blank) | Transportation Safety | 92009 | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Transportation Safety | Austin, TX | 1 | 1 | 4 | 0 | 1 |
| pre-attribution | (blank) | Transportation Safety | Denver, CO | 1 | 0 | 0 | 0 | 0 |
| pre-attribution | (blank) | Transportation Safety | Portland Oregon | 1 | 1 | 4 | 0 | 1 |
| pre-attribution | (blank) | rodenticides | 46 Warwick st somerville ma | 1 | 0 | 0 | 0 | 0 |

## Cut 2 - Top Priority x State

| top priority | state | generated | sent sessions | reps emailed | suppressed | hard bounces |
|---|---|---|---|---|---|---|
| Migratory Birds | (blank) | 29 | 0 | 0 | 0 | 0 |
| Migratory Birds | MA | 16 | 0 | 0 | 0 | 0 |
| Crime & Safety | (blank) | 13 | 0 | 0 | 0 | 0 |
| Transportation Safety | (blank) | 7 | 1 | 3 | 0 | 2 |
| Crime & Safety | TX | 5 | 0 | 0 | 0 | 0 |
| Migratory Birds | CA | 5 | 0 | 0 | 0 | 0 |
| Energy Waste | CA | 4 | 0 | 0 | 0 | 0 |
| Light Pollution | (blank) | 4 | 0 | 0 | 0 | 0 |
| Environmental Impact | (blank) | 3 | 0 | 0 | 0 | 0 |
| Migratory Birds | TX | 3 | 0 | 0 | 0 | 0 |
| Children's Safety | CA | 2 | 0 | 0 | 0 | 0 |
| Crime & Safety | CA | 2 | 0 | 0 | 0 | 0 |
| Crime & Safety | NY | 2 | 0 | 0 | 0 | 0 |
| Light Pollution | MA | 2 | 0 | 0 | 0 | 0 |
| Light Pollution | OR | 2 | 0 | 0 | 0 | 0 |
| Light Pollution | PA | 2 | 0 | 0 | 0 | 0 |
| Migratory Birds | PA | 2 | 0 | 0 | 0 | 0 |
| (blank) | (blank) | 1 | 0 | 0 | 0 | 0 |
| Children's Safety | (blank) | 1 | 0 | 0 | 0 | 0 |
| Crime & Safety | CO | 1 | 0 | 0 | 0 | 0 |
| Crime & Safety | OR | 1 | 1 | 4 | 0 | 2 |
| Energy Waste | (blank) | 1 | 0 | 0 | 0 | 0 |
| Energy Waste | TX | 1 | 0 | 0 | 0 | 0 |
| Light Pollution | TX | 1 | 0 | 0 | 0 | 0 |
| Migratory Birds | CT | 1 | 0 | 0 | 0 | 0 |
| Migratory Birds | OR | 1 | 0 | 0 | 0 | 0 |
| Migratory Birds | RI | 1 | 0 | 0 | 0 | 0 |
| Safety | TX | 1 | 0 | 0 | 0 | 0 |
| Transportation Safety | CO | 1 | 0 | 0 | 0 | 0 |
| Transportation Safety | OR | 1 | 1 | 4 | 0 | 1 |
| Transportation Safety | TX | 1 | 1 | 4 | 0 | 1 |
| rodenticides | MA | 1 | 0 | 0 | 0 | 0 |

## Totals

| generated | sent sessions | reps emailed | suppressed | hard bounces |
|---|---|---|---|---|
| 118 | 4 | 15 | 0 | 6 |
```

Every Cut 1 row shows `ad group = pre-attribution`, `keyword = (blank)` — see section 5 for the independent CLI corroboration of why.

---

## 2. `python report.py --out <dir>` — CSV row-count reconciliation

Command: `python report.py --out "<scratch>/rptverify"` then per-file line counts.

```
CSV files written to <scratch>/rptverify
cut1.csv: 96 lines
cut2.csv: 33 lines
totals.csv: 2 lines
```

Markdown-vs-CSV row-count reconciliation (data rows only, header excluded):

| Cut | Markdown data rows | CSV lines (incl. header) | CSV data rows | Match? |
|---|---:|---:|---:|---|
| Cut 1 | 95 | 96 | 95 | Yes |
| Cut 2 | 32 | 33 | 32 | Yes |
| Totals | 1 | 2 | 1 | Yes |

Content spot-check (identical values, not just counts):
- `totals.csv`: `generated,sent_sessions,reps_emailed,suppressed,hard_bounces` / `118,4,15,0,6` — exact match to the markdown Totals row.
- `cut1.csv` first data row: `pre-attribution,,Energy Waste,"San Diego, CA",4,0,0,0,0` — exact match to the markdown Cut 1 first row.
- `cut1.csv` last data row: `pre-attribution,,rodenticides,46 Warwick st somerville ma,1,0,0,0,0` — exact match to the markdown Cut 1 last row.
- `cut2.csv` first data row: `Migratory Birds,,29,0,0,0,0` — exact match to the markdown Cut 2 first row.

---

## 3. AWS CLI corroboration (independent of `report.py`)

### Paginated `--select COUNT` scans

```
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text
120
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text
4
```

### `test-` prefix scans (both tables)

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

$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --filter-expression 'begins_with(session_id, :p)' --expression-attribute-values '{":p":{"S":"test-"}}' --projection-expression 'session_id' --output json
{
    "Items": [],
    "Count": 0,
    "ScannedCount": 4,
    "ConsumedCapacity": null
}
```

Only `test-gap-framing-001`/`-004` (the pre-existing 2026-03 rows) remain in `photometrics-take-action`; zero `test-` rows in `photometrics-take-action-sends`. This confirms both `p2-harness-run`'s (`test-1788469964`/`test-regen-1788469970`, plus the earlier self-cleaned `test-1788469940`/`test-regen-1788469948`) and `p2-live-generate-check`'s (`test-livegen-1788469919`) rows are gone, and confirms the lead's own browser-driven `/generate` row (name "E2E Test", non-`test-`-prefixed session_id, deleted ~21:35 UTC per this item's assignment note) left no `test-`-prefixed residue either — consistent with it never having been `test-`-prefixed in the first place.

### `source`/`source.utm_content` presence scan (independent corroboration of the pre-attribution claim, not run by `report.py` itself)

```
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'attribute_exists(#src)' --expression-attribute-names '{"#src":"source"}' --output json --query 'Count'
0
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --filter-expression 'attribute_exists(#src.utm_content)' --expression-attribute-names '{"#src":"source"}' --output json --query 'Count'
0
```

Zero of the 120 raw rows currently in `photometrics-take-action` have a `source` attribute at all (raw CLI scan, not `report.py`'s own logic) — independently confirming every row must bucket as `pre-attribution` (satisfying acceptance criterion 4) and explaining why `keyword` is blank on every Cut 1 row too.

### Bounce table (informational — not in the acceptance criteria's reconciliation, but load-bearing for the `hard_bounces` total)

```
$ AWS_PAGER='' aws dynamodb scan --table-name photometrics-email-bounces --region us-east-2 --select COUNT --query 'Count' --output text
15
```

---

## 4. Reconciliation table

| Metric | Phase 01 baseline (19:01:59Z) | `report.py` (this run) | AWS CLI (this run) | Match? |
|---|---:|---:|---:|---|
| Generate rows raw scanned | 120 | 120 | 120 | Yes |
| Generate rows excluded (`test-`) | 2 | 2 | 2 (only `test-gap-framing-001/-004` found in the `test-` scan) | Yes |
| **Generate rows counted** | **118** | **118** | 120 − 2 = 118 | **Yes** |
| Sends rows raw scanned | 4 | 4 | 4 | Yes |
| Sends rows excluded (`test-`) | 0 | 0 | 0 (`test-` scan on sends table returned empty) | Yes |
| **Sends rows counted** | **4** | **4** | 4 − 0 = 4 | **Yes** |
| Sum of `representatives_sent` (reps emailed) | 15 (4+3+4+4, baseline §5) | 15 | not independently re-derived this run (p2-report-tool's handoff already cross-checked this against baseline §5; unchanged since no sends row was added/removed between that run and this one) | Yes |
| Hard-bounce count | 6 (baseline §7, against 14-address denominator) | 6 | not independently re-derived this run (same reasoning) | Yes |
| Bounce table raw rows | 14 (at 19:01:59Z) | 15 | 15 | Consistent — see below |
| Rows with `source` present | (not measured in baseline; no attributed traffic existed yet) | (bucketed as pre-attribution) | 0 / 120 | Yes — all pre-attribution |

**Verdict: PASS.** Report generated total = **118**, sends total = **4** — both equal the Phase 01 baseline exactly, with zero deviation requiring row-by-row attribution.

**Bounce-table count (15, not 14) — explained, not a discrepancy in the numbers that matter:** the assignment's acceptance criteria only require the *generate* (118) and *sends* (4) totals to reconcile; the bounce table has no `session_id` and is explicitly out of the `test-`-residue reconciliation. `p2-report-tool-HANDOFF.md` (run ~13:38 local, before the harness/live-generate runs) already observed 15 raw bounce rows and attributed the +1 over the 14 in the Phase 01 baseline to legitimate concurrent production/phase bounce activity between the two scan times (~13:32 vs. 19:01:59Z-adjacent scans — timestamps in these handoffs use two different clock references, local vs. UTC, but the ordering and the tool's own explanation are consistent). This run, after both harness and live-generate cleanup, still reads 15 — i.e. the harness's own bounce-table activity (2 seeded + 2 deleted rows, confirmed net zero in `p2-harness-run-HANDOFF.md` §6) and the live-generate check (which touched no bounce rows at all, per its own handoff) are both fully accounted for and left the bounce table exactly where `p2-report-tool` last observed it. No new, unexplained bounce-table growth occurred between that run and this one. Cause: **(a)** none — this is stable state, not residue; the harness/live-generate items' own handoffs already prove their bounce-table writes net to zero.

**Cause attribution per the assignment's (a)/(b)/(c) framework, applied to the metrics that matter (generate/sends totals):** no deviation exists to attribute — both totals matched the baseline exactly on the first read. No residue, no new production traffic drift, and no `report.py` defect were found in the two counted-row metrics.

---

## 5. 'pre-attribution' bucket coverage

Every one of the 95 Cut 1 rows shows `ad group = pre-attribution`. The independent CLI scan in section 3 (`attribute_exists(source)` → `Count: 0`) confirms this is correct: none of the 120 raw rows currently in `photometrics-take-action` carry a `source` attribute at all, so `report.py`'s bucketing rule ("`pre-attribution` when `source` is absent OR `source.utm_content` is absent") necessarily buckets all 118 counted rows there. This is consistent with `p2-harness-run` and `p2-live-generate-check` having fully cleaned up their own rows (which *did* carry a `source` map, per their handoffs) — none of that attributed test data survives in the table this report scans.

---

## Decisions / assumptions

- Did not re-run the `representatives_sent`/hard-bounce independent re-derivation from raw item data (baseline §5/§7's per-row methodology) since `p2-report-tool-HANDOFF.md` already performed and documented that exact cross-check against the same baseline, and no sends-table row has been added or removed since (confirmed by the sends-table `test-` scan returning empty and the sends COUNT staying at 4). Re-deriving it a third time would not exercise anything new; the two load-bearing counts the assignment names explicitly (118 generate / 4 sends) were independently re-verified via fresh CLI scans in this run.
- Treated the bounce-table's 14→15 raw-row difference as already explained by `p2-report-tool-HANDOFF.md` (concurrent phase activity, not test residue, not a `report.py` defect) rather than re-investigating from scratch, since this item's acceptance criteria scope the required reconciliation to the generate/sends totals and the bounce table has no `session_id` to filter test rows against in the first place.
- Confirmed (via `git diff HEAD -- lambda/take-action/tools/adgroups.json`, empty) that the `adgroups.json` edit mapping `199915882237` → `Environmental Impact` mentioned in this item's assignment note is already committed at HEAD (`2d927f8`) and not a pending/uncommitted change — nothing for this read-only item to flag as an anomaly there. It had no effect on this run's numbers since no row in the current table carries any `source.utm_content` value (section 3).

## Interface / contract downstream work must follow

- `report.py`'s numbers are now proven true against production twice, independently: once by its own author (`p2-report-tool-HANDOFF.md`) and once by this separate verification pass using different CLI queries (`attribute_exists`, plain `--select COUNT`, `test-` prefix scans) than the tool's own internal logic. Any future consumer of `report.py`'s output can cite both handoffs as evidence.
- No `report.py` defect and no residue from either `p2-harness-run` or `p2-live-generate-check` was found. The phase's reconciliation goal (118 generate / 4 sends matching the Phase 01 baseline) is achieved.

## Files changed

None inside the repo other than this handoff file. `report.py` was run twice (plain and `--out`) but performs zero writes (verified by its own author's `grep -n 'put_item\|delete_item\|update_item\|batch_write' report.py` finding no matches, re-relied-upon here rather than re-run since this item did not modify `report.py`). CSV output was written only to the scratch directory (`C:\Users\aisaa\AppData\Local\Temp\claude\C--Users-aisaa-Projects-Ads\559d492a-6325-410e-9d49-5fa0dcc4023a\scratchpad\rptverify\`), outside the repo. `git status --porcelain` before and after this item's work shows only pre-existing changes from other items (`DAG.md`, `lead-ads-ga4-actions.md`, `CLAUDE.md`, `function.zip` modified; `p2-deploy-HANDOFF.md`/`p2-harness-run-HANDOFF.md`/`p2-live-generate-check-HANDOFF.md` untracked) — none of which this item touched.

## Commands / tests run, with outcomes

| Command | Outcome |
|---|---|
| `cat lambda/take-action/tools/adgroups.json` | confirmed lead's `199915882237` → `Environmental Impact` edit is present and already committed |
| `git status --porcelain` (before) | only pre-existing out-of-scope changes, nothing from this item |
| `aws sts get-caller-identity --region us-east-2` | account `794038225197`, user `ari` |
| `python report.py` | exit 0; full markdown output above; totals 118/4/15/0/6 |
| `python report.py --out "<scratch>/rptverify"` | exit 0; `cut1.csv` (96 lines), `cut2.csv` (33 lines), `totals.csv` (2 lines) written |
| Markdown-vs-CSV row-count reconciliation (custom Python parse of both) | Cut 1: 95 md rows = 95 CSV data rows; Cut 2: 32 = 32; Totals: 1 = 1 — all match |
| `aws dynamodb scan --table-name photometrics-take-action --select COUNT` | `120` |
| `aws dynamodb scan --table-name photometrics-take-action-sends --select COUNT` | `4` |
| `aws dynamodb scan --table-name photometrics-take-action --filter-expression 'begins_with(session_id, :p)' ...` | 2 items: `test-gap-framing-004`, `test-gap-framing-001` only |
| `aws dynamodb scan --table-name photometrics-take-action-sends --filter-expression 'begins_with(session_id, :p)' ...` | 0 items |
| `aws dynamodb scan --table-name photometrics-take-action --filter-expression 'attribute_exists(#src)' ...` | `Count: 0` |
| `aws dynamodb scan --table-name photometrics-take-action --filter-expression 'attribute_exists(#src.utm_content)' ...` | `Count: 0` |
| `aws dynamodb scan --table-name photometrics-email-bounces --select COUNT` | `15` |
| `git status --porcelain` (after) | unchanged from before — this item wrote no repo files |
| `git diff HEAD -- lambda/take-action/tools/adgroups.json` | empty (lead's edit already committed, not a pending change) |

## Known limitations / risks

- The `representatives_sent`-sum (15) and hard-bounce (6) totals were not independently re-derived from raw per-row data in this run — they were cross-checked against `p2-report-tool-HANDOFF.md`'s own prior independent derivation (which matched baseline §5/§7 exactly) rather than recomputed a third time, since nothing in the sends table changed between that run and this one (see Decisions/assumptions). If a future verifier wants a third independent derivation of those two numbers specifically, it would need to re-run a `representatives_sent`/bounce-intersection script against the 4 sends rows — not done here as it was judged out of the acceptance criteria's explicit scope (which names only the 118/4 generate/sends totals as requiring reconciliation).
- The bounce table's raw count (15) does not match the Phase 01 baseline's 14 — explained above as pre-existing, already-documented drift (from `p2-report-tool-HANDOFF.md`, itself run before the harness/live-generate items), not new residue from this phase's items. Not treated as a blocking finding since the assignment's acceptance criteria do not require the bounce table to reconcile to the baseline (it has no `session_id`/test- filtering concept).

## Discovered

- Nothing blocking. No `report.py` defect found. No residue from `p2-harness-run` or `p2-live-generate-check` found (both tables' `test-` scans are clean except for the pre-existing, correctly-preserved `test-gap-framing-001`/`-004` rows). No uncommitted/pending change to `adgroups.json` was found — the lead's `199915882237` mapping edit noted in this item's assignment is already committed at HEAD.
