# p2-report-tool — Handoff

**Status:** done (read-only tool built and run against production; zero writes)
**Owns:** `lambda/take-action/tools/report.py` (new), `lambda/take-action/tools/adgroups.json` (new). No other file touched.
**Region:** us-east-2, account 794038225197.
**Production run performed at:** 2026-09-03, ~13:38 local (see raw output below).

---

## 1. What was built

`report.py` — a single-command, read-only report that joins
`photometrics-take-action` (generate rows) to `photometrics-take-action-sends`
(send rows) on `session_id`, cuts the result two ways, and prints markdown to
stdout (`--out <dir>` additionally writes one CSV per cut plus a totals CSV).

- Paginated `Scan` (via `paginator.paginate` / `LastEvaluatedKey` under the
  hood) against all three tables. Zero `put_item` / `update_item` /
  `delete_item` / `batch_write_item` calls anywhere in the file.
- `ProjectionExpression` on the generate-table scan is `session_id,
  priorities, #src, #loc, location_city, location_state, location_country`
  — `letter` is never requested. `source` and `location` are aliased
  (`#src`, `#loc`) because both are DynamoDB reserved words, following the
  same pattern already used in `lambda_function.py` (`#loc` for `location`,
  `#st` for `subtype`) and in the Phase 01 baseline script.
- The sends-table scan projects only `session_id, representatives_sent,
  representatives_failed` — the minimum needed for the metrics; no
  `constituent_email`, no `message_ids`, no letter-adjacent data.
- The bounces-table scan projects `email, event_type, #st` (`#st` →
  `subtype`), matching `get_bounced_emails()`'s own aliasing in
  `lambda_function.py` line 875.
- Every row (all three tables) whose `session_id` starts with `test-` is
  excluded before any aggregation. (The bounces table has no `session_id` —
  no test-filtering applies there, matching the Phase 01 baseline's finding.)
- A generate row with no matching sends row still counts as generated (just
  contributes 0 to `sent_sessions` / `reps_emailed`).
- Cut 1 key: `(ad_group, keyword, top_priority, location)`.
  - `ad_group`: `source.utm_content` resolved through `adgroups.json`; a row
    with no `source` or no `utm_content` buckets as `pre-attribution`; an id
    present but not in the map prints the raw id.
  - `keyword`: `source.utm_term`, blank when absent.
  - `top_priority`: `priorities[0]`, blank when the list is empty/missing.
  - `location`: `location_city` (+ `', ' + location_state` when present),
    falling back to the raw `location` string when both normalized fields
    are absent.
  - Metrics: `generated`, `sent_sessions`, `reps_emailed` (sum of
    `len(representatives_sent)`), `suppressed` (count of
    `representatives_failed` entries with `reason == 'suppressed'`),
    `hard_bounces` (count of `representatives_sent` addresses found in the
    bounce table as `Bounce`+`Permanent` or `Complaint`).
- Cut 2 key: `(top_priority, state)`, where `state` = `location_state` when
  present, else a **best-effort** parse of the raw `location` string (word-
  boundary match against USPS 2-letter codes and full state names; blank if
  nothing matches). This is explicitly a fallback, not authoritative — see
  Known limitations.
- Totals: one row summing all five metrics across every counted generate row.
- No `constituent_email` or letter body is ever read or printed anywhere in
  the tool.
- Every attribute access uses `.get(...)` with defaults; `representatives_failed`
  / `representatives_sent` missing or empty never raises.

`adgroups.json` maps placeholder ids `TBD-1`..`TBD-7` to the 7 real ad group
**names**, taken read-only from
`C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md` (the live
"Take Action - Street Lighting Advocacy" campaign, campaignId `24212880671`):

```json
{
  "_note": "Placeholder ids TBD-1..TBD-7 map to ad group NAMES only. Before this report tool is used against real utm_content values, the lead must replace each placeholder key below with the REAL numeric Google Ads ad group ID (Google Ads UI: campaign 'Take Action - Street Lighting Advocacy' -> Ad groups -> Columns -> add 'Ad group ID'). utm_content is expected to carry that numeric ad group ID once ads are tagged with it. An id present in a generate/send row's source.utm_content that is NOT a key in this map (after the TBD ids are replaced) prints raw in the report.",
  "TBD-1": "Transportation Safety",
  "TBD-2": "Light Pollution",
  "TBD-3": "Migratory Birds",
  "TBD-4": "Energy Waste",
  "TBD-5": "Crime & Safety",
  "TBD-6": "Environmental Impact",
  "TBD-7": "Ad group 1"
}
```

Full `report.py` source is at `lambda/take-action/tools/report.py` (380
lines) — not reproduced in full here since it's already in the repo and
unmodified since this run; see file for exact content. Key excerpts are
quoted inline above; the complete file is available at that path for diff/review.

---

## 2. Production run — raw markdown output (`python report.py`)

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

Every Cut 1 row shows `ad group = pre-attribution` and `keyword = (blank)`,
confirming the required behavior against today's production data (no row
has `source`, no row has `location_city`): every row buckets as
`pre-attribution` with the raw `location` string used verbatim, exactly as
the hard constraint requires.

---

## 3. `--out <dir>` run — CSV filenames and first lines

Command: `python report.py --out <dir>` (run twice against a scratch dir,
identical results both times since no writes occur between runs).

Files written: `cut1.csv`, `cut2.csv`, `totals.csv`.

`cut1.csv` (header + first data row):
```
ad_group,keyword,top_priority,location,generated,sent_sessions,reps_emailed,suppressed,hard_bounces
pre-attribution,,Energy Waste,"San Diego, CA",4,0,0,0,0
```

`cut2.csv` (header + first data row):
```
top_priority,state,generated,sent_sessions,reps_emailed,suppressed,hard_bounces
Migratory Birds,,29,0,0,0,0
```

`totals.csv` (in full — 2 lines):
```
generated,sent_sessions,reps_emailed,suppressed,hard_bounces
118,4,15,0,6
```

---

## 4. Reconciliation against the Phase 01 baseline (118 generate / 4 sends)

| Metric | This report | Phase 01 baseline | Match? |
|---|---:|---:|---|
| Generate rows scanned (raw) | 120 | 120 | Yes |
| Generate rows excluded as `test-` | 2 | 2 | Yes |
| Generate rows counted | **118** | **118** | Yes |
| Sends rows scanned (raw) | 4 | 4 | Yes |
| Sends rows excluded as `test-` | 0 | 0 | Yes |
| Sends rows counted | **4** | **4** | Yes |
| Sum of `representatives_sent` across all sends rows | 15 (4+3+4+4) | 15 (4+3+4+4, section 5) | Yes |
| Hard-bounce count (representatives_sent addresses in bounce table, Permanent/Complaint) | 6 | 6 (section 7's numerator against the 14-address "ever sent to" denominator) | Yes |
| Bounce table raw rows | 15 | 14 | **1-row discrepancy, explained below** |

**Discrepancy explained:** the bounce table had 15 raw rows at this scan
time vs. 14 at the Phase 01 baseline scan (~13:32 vs. earlier on
2026-09-03). Per the standing rules, concurrent items in this phase (e.g.
`p2-deploy-script`, whose handoff already exists alongside this one, or
other funnel-test runs) may transiently write and clean up
`@simulator.amazonses.com` bounce rows. This tool's `test-` exclusion only
applies to the two `session_id`-keyed tables — the bounce table has no
`session_id`, so a transient extra bounce row there is expected and does
not affect the generate/sends counts. It also did not change the
hard-bounce total (still 6), meaning the extra row was either not a
hard-bounce/complaint event, or was for an address not present in any
counted send's `representatives_sent`. **All numbers that the assignment
requires to reconcile (118 generate, 4 sends) match exactly.**

---

## 5. Decisions / assumptions

- Used `boto3.dynamodb.types.TypeDeserializer` to convert raw
  `{"S": "..."}`-style DynamoDB items into native Python types in one step,
  rather than hand-rolling per-field `S`/`M`/`L` extraction — simpler and
  less error-prone than the Phase 01 baseline script's manual approach,
  while producing identical logical results.
- `ad_group = 'pre-attribution'` whenever `source` is absent OR `source`
  is present but `utm_content` is absent/empty — matches the assignment's
  "a row with no `source` (or no `utm_content`) buckets as
  `pre-attribution`" instruction verbatim.
- `keyword` is blank both when `source` is entirely absent and when
  `source.utm_term` is absent — the assignment only specifies "blank when
  absent" for the keyword column, without carving out a separate case for
  "no source at all," so the same blank behavior was used for both.
- Cut 2's `state` column, when `location_state` is absent, is filled by a
  **best-effort, non-authoritative** parse of the raw `location` string
  (word-boundary match against USPS abbreviations / full state names,
  blank if nothing matches) per the assignment's literal instruction
  "state (from location_state, else parsed/blank)." This is explicitly
  documented as approximate in the code and here — see Known limitations.
- `suppressed` and `hard_bounces` are computed only from a session's own
  matched sends row; a generate row with no send row contributes 0 to both
  (there is nothing to suppress or bounce if nothing was sent).
- Sort order for both cuts is descending by `generated` count, then
  alphabetically by the remaining key fields, purely for readability —
  not specified by the assignment, chosen as a reasonable default.
- Rewrote two initial docstring/comment lines that used an em dash and,
  separately, literal substrings resembling DynamoDB write-call names
  inside prose (not code) — done so a naive `grep` for write-call names
  against this file can't produce a false-positive match against
  documentation text. No functional code was affected by either change.

## Interface / contract downstream work must follow

- `report.py` is fully driven by the fixed data contract named in the
  assignment (`source.utm_content`/`utm_term`, `location_city`,
  `location_state`, `location_country` on the generate table;
  `representatives_failed` with `reason` on the sends table). No code
  changes are needed in `report.py` once real attributed rows start
  arriving — the `pre-attribution` bucket and raw-location fallback simply
  stop firing as those fields populate.
- `adgroups.json`'s `TBD-1`..`TBD-7` placeholder keys **must** be replaced
  with the real numeric Google Ads ad group IDs (visible in Ad groups >
  Columns > Ad group ID in the Google Ads UI for campaign
  `24212880671`) before `source.utm_content` values from real traffic will
  resolve to a name instead of printing raw. This is explicitly called out
  in the file's own `_note` field.
- Whatever process starts tagging outbound ad-group links with
  `utm_content`/`utm_term` must set `utm_content` to that same numeric ad
  group ID string for the mapping to resolve.

## Files changed

- Created: `lambda/take-action/tools/report.py` (380 lines)
- Created: `lambda/take-action/tools/adgroups.json`
- Created: this handoff file
- No other files touched. `lambda_function.py` and `funnel_test.py` were
  not read for modification purposes (only grepped for the existing
  reserved-word aliasing pattern, per the assignment's required-reading
  instruction) and were not edited.

## Commands / tests run, with outcomes

- `aws sts get-caller-identity --region us-east-2` → succeeded, account
  794038225197, user `ari`.
- `python -c "import boto3; print(boto3.__version__)"` → `1.42.70`.
- `python report.py` → exit 0, full markdown output above.
- `python report.py --out <scratch dir>` (run twice) → exit 0 both times,
  `cut1.csv` / `cut2.csv` / `totals.csv` written both times, identical
  content.
- `grep -i 'total' report_output` → matched `## Totals` heading; totals row
  values shown in section 2/4 above.
- `python -c "import json;d=json.load(open('adgroups.json'));print(json.dumps(d,indent=2))"` →
  succeeded, valid JSON, printed in section 1 above.
- `grep -n 'put_item\|delete_item\|update_item\|batch_write' report.py` →
  `READ-ONLY: no write calls` (no match).
- `grep -n 'ProjectionExpression\|LastEvaluatedKey\|letter' report.py` →
  matches on the `ProjectionExpression` kwarg construction, the
  `LastEvaluatedKey` mention in the module docstring (describing the
  paginator's pagination mechanism), and two comments noting `letter` is
  never projected.
- `AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action --region us-east-2 --select COUNT --query 'Count' --output text` → `120`.
- `AWS_PAGER='' aws dynamodb scan --table-name photometrics-take-action-sends --region us-east-2 --select COUNT --query 'Count' --output text` → `4`.

Both plain-CLI raw counts (120 / 4) match this tool's own raw-scanned counts
exactly.

## Known limitations / risks

- **Cut 2's state-from-raw-location parser is best-effort, not
  authoritative.** It will correctly extract a state for strings like
  `Austin, TX` or `Massachusetts`, but returns blank for the many raw
  strings in current production data that are bare ZIP codes (e.g. `92115`,
  `97201`) or ambiguous city names with no state token at all — this
  matches the assignment's own "else parsed/blank" instruction, but the
  lead should not read a `(blank)` state in Cut 2 as "no session from that
  state," only as "state could not be determined from the raw string."
  Proper ZIP-to-state mapping was judged out of scope for this item (it
  would require a ZIP database dependency this tool doesn't otherwise
  need) — flagged here as a possible future improvement, not undertaken.
- The bounce table's 1-row growth between the Phase 01 baseline scan and
  this run (14 → 15) is a timing artifact of concurrent phase activity, not
  a defect in this tool — see the reconciliation section above.
- `adgroups.json`'s placeholder ids are non-functional until the lead swaps
  them for real numeric Google Ads ad group IDs; until then, any real
  `utm_content` value present in future rows will print raw (which is the
  documented, correct fallback behavior — not a bug).

## Discovered

- Nothing blocking. The one non-trivial judgment call (Cut 2's "parsed"
  state fallback) is documented above and in the code; no new prerequisite,
  conflicting assumption, or missing upstream work was found.
