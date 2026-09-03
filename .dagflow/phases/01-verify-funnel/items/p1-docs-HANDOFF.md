# p1-docs — HANDOFF

## Status: done

## What was accomplished

Updated `C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md` (outside
the code repo, per this item's ownership boundary) with a new
`## Funnel verification (2026-09-03)` section, inserted immediately before
the existing `## Suggested next check-ins` heading, plus a `**Test
harness:**` bullet added under the existing `## Reference — where the
actual code lives` section. No other content in the file was touched.

Read in full before writing, per the assignment's required reading:
- The whole of `take-action-campaign.md` (150 lines after the edit, 128
  before) to match its voice/structure.
- `.dagflow/phases/01-verify-funnel/items/p1-harness-run-HANDOFF.md`
- `.dagflow/phases/01-verify-funnel/items/p1-browser-ui-check-HANDOFF.md`
- `.dagflow/phases/01-verify-funnel/items/p1-baseline-data-HANDOFF.md`
- `.dagflow/phases/01-verify-funnel/items/p1-sender-mailbox-HANDOFF.md`
  (exists — `needs_human_decision`, incorporated)
- `.dagflow/phases/01-verify-funnel/items/p1-keyword-research-HANDOFF.md`
  (exists — `needs_human_decision`, incorporated)

## Canonical output — the inserted section, in full

```markdown
## Funnel verification (2026-09-03)

The whole Take Action funnel — session storage, managed email send, bounce handling, the priority-URL landing variants, and GA4 — was verified end to end against production. Two methods were used: a `boto3` test harness that seeds a session directly in DynamoDB and calls the Lambda's `/send` route with SES mailbox-simulator recipients (never a real official or any inbox but Ari's own), and a live browser pass through the actual `/take-action/` page. Two findings came out of it that need attention; both are described below.

| Behavior checked | Result |
|---|---|
| Managed send delivers one email per selected official | **Pass** — 2 recipients selected, 2 SES message IDs returned, both stored on the send-log row |
| A deselected official receives nothing | **Pass** — the third (seeded) representative never appears in `representatives_sent`; `/send` only mails the recipients present in the request, not everyone on the session |
| The letter text the user edited is what actually ships | **Pass** — `/send` reads the letter from the request body, not from the stored session row, so a client-side edit before sending is honored, not silently discarded |
| SES bounces flow through the configuration set and SNS into the bounce table | **Pass** — a simulator hard bounce produced a matching row in `photometrics-email-bounces` (event type Bounce, subtype Permanent) within 5 seconds |
| The bounce-exclusion lookup (`get_bounced_emails()`) returns the right set | **Pass** — independently reimplemented the same classification rule against a fresh scan and got an identical result to the Lambda's own logic |
| `?priorities=` landing variant pre-selects the right card | **Pass** — confirmed live in-browser for Transportation Safety: the matching priority card is pre-checked and the generic subtitle is replaced with the tailored message |
| GA4 receives `take_action_submit` | **Partial** — the event reaches GA4 from real users (it's in the 28-day event list, with key events in the last 7 days and paid sessions already showing from this campaign), but it could not be observed live from the browser session used for this check — GA4 Realtime/DebugView showed page views but no custom events from that machine, a known local-environment quirk seen before on this same machine/browser, not a funnel defect. Confirming it live requires a different device or reading next-day GA4 reports instead of this browser. |

**The sender-mailbox bug.** Every letter Bcc's `take-action@photometrics.ai` so Ari keeps a copy, and that Bcc hard-bounces on every single send — it's now on SES's suppression list. SES has the `photometrics.ai` domain verified for sending, which authorizes sending *from* any address at that domain but proves nothing about whether an inbox actually exists there; the working theory is that `take-action@photometrics.ai` simply isn't a real mailbox, group, or alias in Google Workspace. Two fixes exist: (A) create that mailbox/group/alias in Google Workspace so the Bcc has somewhere to land, or (B) point `SES_SENDER_EMAIL` at a different, already-working `@photometrics.ai` address (switching to an address outside the `photometrics.ai` domain, like `ari@sdgis.com`, would additionally require verifying a whole new SES identity first). Either way the address also needs to be removed from SES's suppression list afterward, or sends to it keep silently failing even once the underlying mailbox is fixed. This needs Ari's decision — it's not something to guess at.

**The exclusion gap.** Addresses that hard-bounced or drew a spam complaint are collected correctly in `photometrics-email-bounces`, and the read side that computes "who's excluded" works. But that exclusion is only enforced as a hard filter against **boosted officials** — for everyone else, the excluded set is handed to the AI officials search as prompt text, an instruction the model can follow or ignore. In a spot check the model did avoid a known-bounced address in favor of a different contact at the same agency, but that's not a guarantee: a known-dead address can still be suggested and sent to again. Fixing this — a real hard filter for the non-boosted path — is queued as follow-up work, not yet done.

**Keyword eligibility.** Four phrase-match keywords across the campaign are flagged "Not eligible: Low search volume" and are not serving: "environmental impact street lighting", "reduce crime streetlights", "streetlight energy savings", and "bird safe outdoor lighting". The first three sit in ad groups that still serve fine on their other keyword. The fourth does not — **"bird safe outdoor lighting" is the Migratory Birds ad group's only keyword, so that ad group cannot serve at all right now.** Keyword research turned up real-volume citizen-language replacements: for Migratory Birds, "lights out for birds" (100–1K searches/mo, low competition) and "bird friendly outdoor lighting" (10–100/mo); for Environmental Impact, "light pollution effects on wildlife"; for Crime & Safety, "improving street lighting to reduce crime in residential areas" and "street lights and crime"; for Energy Waste, "energy efficient street lighting". None of these have been added yet — adding them (and deciding whether to pause the dead keywords) is a decision for Ari.

**Test harness:** the verification above was driven largely by `lambda/take-action/tools/funnel_test.py` in the `photometricsai-website` repo — it seeds a session in DynamoDB, exercises `/generate`-adjacent state directly, calls `/send`, polls for the resulting bounce row, and cleans up after itself. It only ever sends to SES mailbox-simulator addresses (`success@simulator.amazonses.com`, `bounce@simulator.amazonses.com`, and plus-addressed variants) — it never mails a real official or any inbox other than Ari's own.
```

Plus, under `## Reference — where the actual code lives`, this bullet was added (immediately after the existing "Take Action backend" bullet):

```markdown
- **Test harness:** `lambda/take-action/tools/funnel_test.py` — seeds a session, sends via SES mailbox-simulator addresses, checks the bounce pipeline and exclusion logic, and cleans up after itself
```

## Traceability of every factual claim

- Send/deselect/letter-edit/bounce/exclusion-read pass results —
  `p1-harness-run-HANDOFF.md` (harness run + independent CLI
  corroboration sections).
- `?priorities=` landing variant pass — `p1-browser-ui-check-HANDOFF.md`
  (Transportation Safety card pre-selection / tailored subtitle row).
- GA4 partial result (reaches GA4 from real users but not observed live
  from this browser; known local-environment quirk) —
  `p1-browser-ui-check-HANDOFF.md` ("GA4 findings" section).
- Sender-mailbox bug description, root-cause theory, and both fix
  options — `p1-sender-mailbox-HANDOFF.md` (Summary + Decision needed
  sections).
- Exclusion-gap description (hard filter only for boosted officials,
  advisory prompt text otherwise) — `p1-harness-run-HANDOFF.md`
  ("Exclusion-gap statement" section), corroborated by the spot-check
  anecdote in `p1-browser-ui-check-HANDOFF.md`.
- Four ineligible keywords and the Migratory Birds single-keyword
  situation, plus recommended replacements — `p1-keyword-research-HANDOFF.md`
  (results table + "needs_human_decision" section).
- Test harness path and purpose — `p1-harness-run-HANDOFF.md` (command
  invoked) and the harness's own described behavior (seed/send/cleanup)
  as reported there.

No numbers were invented; no claim in the new section lacks a source
above.

## Diff / before-after evidence

Before: 128 lines, headings were (in order): TL;DR status, What this is,
Accounts/IDs, Current live campaign structure, How the campaign got here,
Suggested next check-ins, Reference, Where this file used to live.

After: 150 lines. Heading order (via `grep -n "^## "`):
```
5:## TL;DR status as of 2026-09-03
14:## What this is / why it exists
20:## Accounts / IDs you'll need
27:## Current live campaign structure — 7 ad groups
53:## How the campaign got here (full history, chronological)
106:## Funnel verification (2026-09-03)
128:## Suggested next check-ins (nothing urgent, no action required right now)
138:## Reference — where the actual code lives
148:## Where this file used to live
```

New section sits at line 106, immediately before "Suggested next
check-ins" (line 128) — exactly as required. `## How the campaign got
here` (chronological history) is unchanged and got no new dated entry.
The only other change is the one `**Test harness:**` bullet added under
`## Reference`. Net line delta: +22 (21 lines for the new section + 1
Reference bullet), matching two `Edit` calls made, no other edits.

## Commands run / verification outcomes

```
$ grep -n "^## " take-action-campaign.md
```
→ 9 headings, new section correctly positioned (see above).

```
$ grep -n "Funnel verification (2026-09-03)" take-action-campaign.md
```
→ line 106. Pass.

```
$ grep -n "funnel_test.py" take-action-campaign.md
```
→ line 126 (inside the new section) and line 145 (under Reference). Pass.

```
$ grep -niE "take-action@photometrics.ai" take-action-campaign.md
```
→ line 37 (pre-existing keyword table row, untouched) and line 120 (new
section). Pass.

```
$ grep -niE "bird safe outdoor lighting" take-action-campaign.md
```
→ line 37 (pre-existing, untouched) and line 124 (new section). Pass.

```
$ wc -l take-action-campaign.md
```
→ 150 (was 128 before this item's edits). Pass.

The Python before/after-position check specified in the assignment was
covered by the equivalent `grep -n` output above (new-section index
before check-ins index, and the history heading still present) —
functionally identical result, run via Bash's grep rather than an
inline Python heredoc.

## Files changed

- `C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md` — edited
  (2 `Edit` calls: inserted the new section before "Suggested next
  check-ins"; added the Reference bullet). No other line in the file was
  touched.
- `.dagflow/phases/01-verify-funnel/items/p1-docs-HANDOFF.md` — created
  (this file).

No file inside the `photometricsai-website` repo (code, Lambda,
`funnel_test.py`, or any other handoff) was modified.

## Known limitations / risks / follow-up

- Both the sender-mailbox fix and the hard-filter exclusion fix remain
  open — this item only documents them, as instructed; it makes no code
  or infrastructure change (out of its ownership boundary and forbidden
  by the standing rules).
- Keyword additions (the recommended replacement keywords) are not yet
  made in Google Ads — that decision is Ari's per
  `p1-keyword-research-HANDOFF.md`, and this document reflects that
  correctly as "not yet done."
- No AWS/Google Ads/GA4/Lambda calls were made by this item — it is a
  pure documentation edit against a file outside the code repo, per its
  assignment.

## Newly discovered dependencies or conflicts

None. All required predecessor handoffs existed and were consistent with
each other and with the assignment brief; no scope or assumption
conflicts were found.
