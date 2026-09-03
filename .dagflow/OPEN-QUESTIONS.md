# Open Questions

Durable, cross-phase log of questions that need the user's input. The lead
appends here instead of interrupting mid-round. Only presented to the user
as a batch, when every other ready item is exhausted — never one at a time
as they arise.

## <date> — <short title>

**Question:** <the actual question, phrased so a plain answer resolves it>
**Why it matters / what's blocked:** <what work is gated on this, and why
it can't proceed with a guessed default>
**Lead's suggested default, if forced to guess:** <state one, or "none
reasonable" if the decision genuinely has no safe default>
**Status:** open | answered — <answer> (<date>)

---
## 2026-09-03 — Privacy policy disclosure for constituent email

**Question:** The Take Action send path stores the constituent's email (sends table, 1-year TTL) and CCs it on letters to officials. The privacy policy has not been updated to disclose this (open since 2026-09-02). Do you want that copy drafted as part of this effort, or handled separately?
**Why it matters / what's blocked:** Nothing in Phases 1–5 is blocked. Compliance/trust item only.
**Lead's suggested default, if forced to guess:** Handle separately after Phase 3; not in this DAG.
**Status:** open

---
## 2026-09-03 — Sender mailbox take-action@photometrics.ai hard-bounces (p1-sender-mailbox)

**Question:** Every letter BCCs `take-action@photometrics.ai` so you keep a copy, and that BCC hard-bounces every time. SES has already put the address on the account-level suppression list (reason BOUNCE, since 2026-09-01), so nothing sent to it is even attempted now. Pick one: (A) create `take-action@photometrics.ai` in Google Workspace (a Google Group with you as member is the cheapest, no license seat), then I clear the SES suppression entry; or (B) change the Lambda's `SES_SENDER_EMAIL` env var to a mailbox that already exists (which address?), and I apply it with the command in `.dagflow/phases/01-verify-funnel/items/p1-sender-mailbox-HANDOFF.md`.
**Why it matters / what's blocked:** Phase 2 entry criterion. You never receive copies today, and each send adds a bounce to your SES reputation once the suppression entry is cleared without a mailbox behind it.
**Lead's suggested default, if forced to guess:** (B) with an existing @photometrics.ai mailbox you read. Zero Workspace admin work, one env-var change, no suppression cleanup needed.
**Status:** open

---

## 2026-09-03 — Replacement keywords for the 4 ineligible ones (p1-keyword-research)

**Question:** Keyword Planner results (US, phrase match) in `.dagflow/phases/01-verify-funnel/items/p1-keyword-research-HANDOFF.md`. Approve adding: Migratory Birds → "lights out for birds" (100–1K/mo) and "bird friendly lighting" (10–100); Environmental Impact → "light pollution effects on environment" (10–100), optionally "street light too bright" (10–100, borderline fit); Energy Waste → "led streetlight conversion" (10–100). Crime & Safety: no candidate showed volume; keep "crime prevention lighting" as its only live keyword. Leave the 4 ineligible keywords in place for now.
**Why it matters / what's blocked:** Migratory Birds cannot serve at all today, and 58 of 118 real sessions chose Migratory Birds as top priority. Phase 5 is blocked on this. Applying is a Google Ads change, so it is your click or your explicit go-ahead for me to do it.
**Lead's suggested default, if forced to guess:** Add all four recommended keywords, skip "street light too bright", pause nothing yet.
**Status:** open

---
