# p2-docs — Handoff

**Status:** done
**Scope:** Document the Take Action Lambda's operational shape and data contract in the website repo's `CLAUDE.md`, and bring the campaign doc's `Funnel verification` section up to current reality.
**Files owned/edited:** `C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md`, `C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md` (not a git repo; edited in place). No other file touched. No commit/push made.

---

## Required reading done first

All predecessor handoffs listed in the prompt (`p2-deploy`, `p2-harness-run`, `p2-report-tool`, `p2-frontend-source`) plus every handoff in the assignment's own `REQUIRED READING` list (`p2-exclusion-hardening`, `p2-source-and-location`, `p2-unit-tests-run`, `p2-deploy-script`, `p2-harness-extend`, `p1-sender-mailbox`, `p1-docs`) were read in full before writing anything. Also read, per the task briefing: `.dagflow/phases/02-harden-instrument-report/decisions/lead-ads-ga4-actions.md` and `.dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md`. To confirm the sender-mailbox fix (asserted in the prompt as "the sender mailbox fix" citing `p1-sender-mailbox-HANDOFF.md`, which is itself only `needs_human_decision`), I additionally read `.dagflow/OPEN-QUESTIONS.md` and `.dagflow/phases/02-harden-instrument-report/PHASE.md`, which record the actual resolution (see claim table below).

## Canonical outputs

1. `CLAUDE.md` — new `## Take Action Lambda (lambda/take-action/)` section, appended after the existing "Sun Phase Tools" section (end of file). Covers: function/region/account/role/source path; routing (`/generate`, `/send`, `/track`, `/flag`, SNS bounce branch); the 9 environment variable **names** (no values); the 5 DynamoDB tables with key schemas; SES config set → SNS → Lambda bounce wiring, including the sender-self-bounce skip; `deploy.sh` usage and the currently deployed `CodeSha256`; `pytest` invocation and the no-moto/monkeypatched-clients fact; the harness subcommands and simulator-only rule; the report tool and `adgroups.json` placeholder-id caveat; and the full data contract (generate row `source`/location fields, sends row copied fields + `representatives_failed` reasons, frontend `/generate` `source` payload, the 3 new GA4 params).
2. `take-action-campaign.md` — the `## Funnel verification (2026-09-03)` section was rewritten to describe current state: the hard exclusion filter is live in production (citing `CodeSha256` `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=`), the sender mailbox is fixed and its suppression was cleared, campaign attribution + normalized location are now captured on every generate row and copied to sends rows (with the frontend commit's live-in-production status), and the report tool exists with the command to run it. The pre-existing "Keyword eligibility" paragraph and the intro/table format were kept, updated only where the underlying facts changed (two "needs attention" paragraphs — sender-mailbox bug, exclusion gap — became "current state" paragraphs; two new paragraphs added for attribution capture and the report tool; the closing "Test harness" paragraph was updated to mention `check-regenerate`). No dated changelog/diff entries were appended; the section still reads as a description of current reality, matching `p1-docs`'s established voice.

## Before/after of the campaign doc's Funnel verification section

**Before** (as left by `p1-docs`, Phase 01): intro paragraph + 7-row pass/partial table + 3 prose paragraphs ("The sender-mailbox bug" — open issue; "The exclusion gap" — open issue; "Keyword eligibility" — open issue) + "Test harness" paragraph.

**After:** intro paragraph (updated to mention hardening/attribution) + 8-row pass/partial table (added a row for hard-bounced/flagged suppression, replacing the old exclusion-gap framing; added a row for attribution/location capture) + 5 prose paragraphs ("The sender mailbox" — now describes it as fixed; "Exclusion enforcement" — now describes it as closed; "Campaign attribution, live" — new; "Attribution report" — new; "Keyword eligibility" — unchanged, still open, exact wording preserved except the closing sentence was tightened to "Ari wants to review the list before anything is applied" to match `OPEN-QUESTIONS.md`'s actual current status rather than the flatter "is a decision for Ari") + "Test harness" paragraph (updated to mention `check-regenerate` and the attribution/location seed fields).

Full before text is reproducible from git history of `p1-docs-HANDOFF.md`'s "Canonical output" block; full after text is in the file itself (see verification output below) and not re-pasted here for length — every sentence is sourced in the claim table below.

## Claim-by-claim source table

### CLAUDE.md

| Claim | Source handoff |
|---|---|
| Function `photometrics-take-action`, region `us-east-2`, account `794038225197`, role `photometrics-take-action-lambda-role` | `p2-deploy-HANDOFF.md` (deploy output JSON: `FunctionArn`, `Role`) |
| Source `lambda/take-action/lambda_function.py`, single file | `p2-deploy-HANDOFF.md` (zip namelist `['lambda_function.py']`), `p2-exclusion-hardening-HANDOFF.md`/`p2-source-and-location-HANDOFF.md` (both edit only this file) |
| Routing: `/generate`, `/send`, `/track`, `/flag`, SNS bounce branch | Assignment's own WHAT TO WRITE item A (routing suffixes as given); `/generate` and `/send` behavior corroborated by `p2-exclusion-hardening-HANDOFF.md`/`p2-source-and-location-HANDOFF.md`/`p2-live-generate-check-HANDOFF.md`; `/flag` corroborated by `p2-exclusion-hardening-HANDOFF.md`'s diff (`handle_flag`); SNS branch corroborated by `p2-exclusion-hardening-HANDOFF.md` item 4 (`record_bounce_event`) |
| 9 env var names | `p2-deploy-HANDOFF.md` (deploy output's `Environment.Variables` keys, values redacted there and not repeated here) |
| 5 DynamoDB tables + key schemas | `photometrics-take-action`/`-sends`: `p2-harness-run-HANDOFF.md` (`get-item --key session_id`); `photometrics-email-bounces` (email+timestamp): `p2-exclusion-hardening-HANDOFF.md` (`get_bounced_emails`/`record_bounce_event`), `p2-harness-run-HANDOFF.md` (cleanup's `describe-table`-derived key use); `photometrics-flagged-officials`: `p2-exclusion-hardening-HANDOFF.md` (`get_flagged_emails`); `photometrics-boosted-officials` (region+email): `p2-harness-extend-HANDOFF.md` (raw `describe-table` output) |
| SNS bounce wiring + sender-self-bounce skip | `p2-exclusion-hardening-HANDOFF.md` item 4 and its diff (`record_bounce_event`'s `sender_email_lower` check, exact log line) |
| `deploy.sh` usage, `--dry-run`, zip-fallback, CodeSha256 verification | `p2-deploy-script-HANDOFF.md` (full script text + commands run) |
| Deployed `CodeSha256` `r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=` | `p2-deploy-HANDOFF.md`; re-confirmed live by this item (`aws lambda get-function-configuration --query CodeSha256` — see Verification below) |
| `pytest lambda/take-action/tests -q`, 20 tests, no moto, monkeypatched clients | `p2-unit-tests-run-HANDOFF.md` (20 passed, `FakeDynamoDB`/`FakeSES` design) |
| Harness subcommands, simulator-only rule, `check-regenerate` | `p2-harness-extend-HANDOFF.md` (`--help` output), `p2-harness-run-HANDOFF.md` (live run output) |
| Report tool + `adgroups.json` placeholder caveat | `p2-report-tool-HANDOFF.md` (tool description, `adgroups.json` `_note` field) |
| Generate-row `source` keys + location fields | `p2-source-and-location-HANDOFF.md` (`SOURCE_KEYS`, `normalized_location`); live-verified by `p2-live-generate-check-HANDOFF.md` |
| Sends-row copied fields + `representatives_failed` reasons | `p2-exclusion-hardening-HANDOFF.md` (`log_send` diff, `{"suppressed","ses_error"}`); live-verified by `p2-harness-run-HANDOFF.md`'s `check-regenerate` `get-item` output |
| Frontend `/generate` `source` payload, `sessionStorage['ta_source']` | `p2-frontend-source-HANDOFF.md` |
| Frontend commit `ac10a0b` live via Amplify job 164 | `.dagflow/phases/02-harden-instrument-report/decisions/lead-ads-ga4-actions.md` ("Frontend deploy" section) — task briefing explicitly authorized stating this as fact, citing this file |
| GA4 params `landed_priorities`, `utm_content`, `preselected` | `p2-frontend-source-HANDOFF.md` (all 5 `gtagEvent` call sites) |

### take-action-campaign.md (Funnel verification section)

| Claim | Source handoff |
|---|---|
| Pre-existing pass rows (managed send, deselect, letter-edit-honored, SES-bounce-to-table, `?priorities=` preselect, GA4 partial) | `p1-docs-HANDOFF.md` (unchanged from Phase 01, reproduced verbatim) |
| Hard-bounced/flagged address refused as a hard filter (new row) | `p2-exclusion-hardening-HANDOFF.md` (`filter_excluded`, suppression block); live-verified by `p2-harness-run-HANDOFF.md`'s `check-regenerate` step (`sent_count=1, failed_count=1, failed=[{"email":"dead.official@...","reason":"suppressed"}]`, independently corroborated via `get-item`) |
| Deployed `CodeSha256` cited alongside that row | `p2-deploy-HANDOFF.md`; re-confirmed live (see Verification below) |
| Attribution/location captured on every generate row (new row) | `p2-source-and-location-HANDOFF.md` (implementation); `p2-live-generate-check-HANDOFF.md` (live proof: `source.utm_content`, `location_city='Columbus'`, `location_state='OH'`, `location_country='US'`) |
| Sender mailbox fixed, suppression cleared | `.dagflow/OPEN-QUESTIONS.md` ("Sender mailbox take-action@photometrics.ai hard-bounces" entry — "Status: answered... Lead cleared the SES suppression entry and sent a test message... on 2026-09-03"); `.dagflow/phases/02-harden-instrument-report/PHASE.md` Entry Criteria ("Sender mailbox take-action@photometrics.ai confirmed working, SES suppression cleared (2026-09-03)" — checked `[x]`); root-cause/original-bug description carried over from `p1-sender-mailbox-HANDOFF.md`/`p1-docs-HANDOFF.md` |
| Self-bounce no longer recorded | `p2-exclusion-hardening-HANDOFF.md` item 4 (same fact as CLAUDE.md's SNS section) |
| Exclusion now hard-enforced (closing the old "exclusion gap") | `p2-exclusion-hardening-HANDOFF.md` (`handle_generate`'s pre-`call_claude` filter, `handle_send`'s suppression block) |
| Frontend commit `ac10a0b` capturing attribution, live via Amplify job 164 | `.dagflow/phases/02-harden-instrument-report/decisions/lead-ads-ga4-actions.md` — explicitly authorized as statable fact per the task briefing |
| GA4 custom dimensions registered (`priorities`, `location_entered`, `method`) vs. not yet registered (`landed_priorities`, `utm_content`, `preselected`, `representatives_count` metric) | `.dagflow/phases/02-harden-instrument-report/decisions/lead-ads-ga4-actions.md` ("GA4 property 529600118 — custom definitions (PARTIAL...)" section) |
| Report tool command + `adgroups.json` placeholder caveat + Final URL suffix already applied | `p2-report-tool-HANDOFF.md`; Final URL suffix text from `.dagflow/phases/02-harden-instrument-report/decisions/lead-ads-ga4-actions.md` ("Google Ads campaign 24212880671 — Final URL suffix" section) |
| Keyword eligibility paragraph (unchanged facts) | `p1-docs-HANDOFF.md` / `p1-keyword-research-HANDOFF.md` (carried over verbatim except the closing sentence, retuned to match `.dagflow/OPEN-QUESTIONS.md`'s current "Ari wants to review the list first" status) |
| Test harness paragraph update (`check-regenerate`, seeded attribution/location fields) | `p2-harness-extend-HANDOFF.md`, `p2-harness-run-HANDOFF.md` |

No claim in either file lacks a source above. No secret value appears in either file (grep-verified, see below).

---

## Verification commands run, with outcomes

```
$ cd C:/Users/aisaa/Projects/photometricsai-website && git status --porcelain
 M .dagflow/phases/02-harden-instrument-report/DAG.md
 M .dagflow/phases/02-harden-instrument-report/decisions/lead-ads-ga4-actions.md
 M CLAUDE.md
 M lambda/take-action/function.zip
?? .dagflow/phases/02-harden-instrument-report/items/p2-deploy-HANDOFF.md
?? .dagflow/phases/02-harden-instrument-report/items/p2-harness-run-HANDOFF.md
?? .dagflow/phases/02-harden-instrument-report/items/p2-live-generate-check-HANDOFF.md
```
Only `CLAUDE.md` is modified within this item's owned boundary. `DAG.md`, `lead-ads-ga4-actions.md`, `lambda/take-action/function.zip`, and the three untracked handoff files are other items'/the lead's prior work (all read, none touched, by this item) — consistent with the phase's `git status --porcelain` showing "only CLAUDE.md (plus .dagflow)" per the DEFINITION OF DONE.

```
$ cd C:/Users/aisaa/Projects/photometricsai-website && git diff --stat -- CLAUDE.md
 CLAUDE.md | 74 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 74 insertions(+)
```
Pure addition — no existing line in `CLAUDE.md` was touched. Full diff is the "Take Action Lambda" section reproduced under Canonical outputs above (not re-pasted here for length; the file itself is the record).

```
$ grep -n -A5 'Take Action Lambda' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md | head -60
216:## Take Action Lambda (`lambda/take-action/`)
217-
218-Backend for the citizen-advocacy tool at `/take-action/` — a visitor picks a street-lighting priority, the Lambda finds their local officials and drafts a letter, and can send it to those officials on the visitor's behalf. The Google Ads campaign that drives traffic here is tracked outside this repo, in the separate `Ads` repo's `google/take-action-campaign.md`.
219-
220-- **Function:** `photometrics-take-action`
221-- **Region:** `us-east-2`
```

```
$ grep -n 'photometrics-take-action\|deploy.sh\|funnel_test.py\|report.py\|representatives_failed\|location_city\|preselected' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md
```
→ all required terms present (function name, `deploy.sh` usage lines, `funnel_test.py`, `report.py`, `representatives_failed`, `location_city`, `preselected` — full match list in the tool output above).

```
$ grep -rn -E 'sk-ant|AIza|AKIA|[A-Za-z0-9_-]{35,}' C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md' || echo 'no secret-shaped strings'
no secret-shaped strings
```

```
$ grep -n -A30 'Funnel verification' 'C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md'
```
→ full updated section printed (lines 106-131), matching the Canonical outputs description above.

```
$ AWS_PAGER='' aws lambda get-function-configuration --function-name photometrics-take-action --region us-east-2 --query CodeSha256 --output text
r0qEhgANZ9AsaCU9a7XRMtEDlgJQNB40hIPd5IbKMbE=
```
Matches the `CodeSha256` cited in both files exactly.

---

## Decisions / assumptions

- Placed the new CLAUDE.md section at the very end of the file (after "Sun Phase Tools"), as its own top-level `##` section, matching the file's existing pattern of one major `##` section per subsystem (Civil Lighting Design Newsletter, Sun Phase Tools) with `###` subheadings and tables/code-blocks inside.
- The campaign doc's "Keyword eligibility" paragraph and the earlier sections (TL;DR, campaign structure, full history) were left completely untouched — out of this item's ownership boundary (only the "Funnel verification" section was to be updated) and no fact in them changed.
- Confirmed the sender-mailbox fix via `.dagflow/OPEN-QUESTIONS.md` and `PHASE.md` rather than `p1-sender-mailbox-HANDOFF.md` alone, since that handoff by itself only documents the *investigation* (status `needs_human_decision`) — the actual fix (Ari confirmed the alias, lead cleared the SES suppression entry and sent a successful test message) is recorded in those two files, both read as part of this item's research even though `OPEN-QUESTIONS.md`/`PHASE.md` weren't in the assignment's explicit `REQUIRED READING` list. This is a factual necessity, not scope creep — the assignment's own WHAT TO WRITE instruction requires stating the sender mailbox is fixed, and the cited `p1-sender-mailbox-HANDOFF.md` alone does not support that claim.
- Kept the pre-existing 7 pass/partial table rows verbatim (Phase 01's language), only adding two new rows and updating none of the old ones, since none of the underlying facts they describe changed.
- Did not delete or restructure the "Suggested next check-ins" or "Reference" sections — out of scope (only "Funnel verification" was to be updated), and nothing in the assignment asked for changes there.

## Interface / contract downstream work must follow

None — this is a pure documentation item. No code, config, or interface changed.

## Known limitations / risks

- The GA4 custom-dimension registration status (`priorities`/`location_entered`/`method` registered; `landed_priorities`/`utm_content`/`preselected`/`representatives_count` not yet) is a snapshot as of `lead-ads-ga4-actions.md`'s last update (2026-09-03 ~21:15 UTC) — if the lead registers the remaining dimensions after this item's cutoff, this doc will read stale until someone updates it. Flagged as an accepted limitation, not fixed here (this item's scope is "current state as of the sources available now").
- The campaign doc's "Attribution report" paragraph states every `source.utm_content` value in production is still a `TBD-*` placeholder or absent — this was true as of `p2-report-tool-HANDOFF.md`'s production run (2026-09-03) and remains true regardless of the Final URL suffix now being applied, since that suffix only affects *future* clicks, not the 118 historical rows already in the table.

## Discovered

- Nothing new that blocks or changes scope. The one non-trivial finding — that `p1-sender-mailbox-HANDOFF.md` alone doesn't support the "sender mailbox is fixed" claim the assignment requires — was resolved by reading `.dagflow/OPEN-QUESTIONS.md` and `PHASE.md`, both of which record the actual fix and were consistent with each other.

## Files changed

- `C:/Users/aisaa/Projects/photometricsai-website/CLAUDE.md` — new "Take Action Lambda" section appended (pure addition, +74 lines, 0 deletions).
- `C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md` — "Funnel verification" section rewritten in place (not a git repo; no diff stat available, before/after described above).
- `C:/Users/aisaa/Projects/photometricsai-website/.dagflow/phases/02-harden-instrument-report/items/p2-docs-HANDOFF.md` — this file (created).
- No other file was created, edited, or deleted by this item.

## STANDING RULES compliance

1. No email sent, no simulator address used — this item made no AWS write calls and no `/send`/`/generate` invocation.
2. No DynamoDB rows created — nothing to clean up.
3. Region `us-east-2`, `AWS_PAGER=''` set on the one read-only `aws lambda get-function-configuration` call in this item.
4. No git commit or push performed.
5. This handoff, at the path above.
6. Zero `/generate` calls made (0 of the phase's budget used by this item).
7. `ANTHROPIC_API_KEY`/`GOOGLE_CIVIC_API_KEY` values never printed or referenced — only their names appear in either owned file.
8. No Chrome/browser tools used.
