# p1-keyword-research — HANDOFF

Status: **needs_human_decision** (this is the expected, successful outcome for this item — a recommendation for Ari to approve, not a failure).

Note: a `p1-keyword-research-HANDOFF.md` already existed in this directory from an earlier pass that used only "Get search volume and forecasts" (no "Discover new keywords"). This version supersedes it — it re-verifies the same 4 ineligible keywords, and additionally runs "Discover new keywords" as the assignment instructed, which surfaced better candidates than the earlier pass found, particularly for Crime & Safety (the earlier pass reported "no good candidate found" for that group; this pass found two with real volume).

## What this item did

Read-only investigation in Google Ads Keyword Planner (account `673-574-9140`, "Photometrics AI Ads", owned by `ari@sdgis.com`) to find phrase-match, citizen-language keyword candidates that can replace the four keywords in campaign `24212880671` ("Take Action - Street Lighting Advocacy") currently flagged **"Not eligible: Low search volume."** No keyword, ad group, campaign, or setting in Google Ads was added, edited, paused, or removed. A Keyword Planner "plan" (planId `1436720453`) was created as a scratchpad, which is expected and does not touch the live campaign — plans are Keyword Planner's own sandbox and are separate from any campaign's saved keyword list.

## Procedure

1. Read `C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md` in full first (the only durable source file for this item).
2. Opened Google Ads in its own browser tab (`mcp__claude-in-chrome`, tab created via `tabs_create_mcp` per instructions) → Tools → Planning → Keyword Planner.
3. **"Get search volume and forecasts"**: priced 16 keywords (United States, All languages, Google search network, trailing-12-month window Aug 2025–Jul 2026) — the 4 current ineligible keywords plus 12 citizen-language hypotheses across all 4 affected ad groups.
4. **"Discover new keywords"**: ran two rounds (United States, English, Google) —
   - Round A, seeded with `bird safe outdoor lighting`, `migratory birds lights out`, `birds and glass windows` → 24 keyword ideas returned.
   - Round B, seeded with `environmental impact street lighting`, `reduce crime streetlights`, `streetlight energy savings` → 6 keyword ideas returned (confirms this is a genuinely low-volume corner of the keyword space — Google itself struggled to suggest anything beyond a handful of ideas for these three seeds combined).
5. Read every row's Avg. monthly searches, Three month change, YoY change, and Competition directly from the Keyword Planner grid via the accessibility tree (paged/scrolled through all rows).
6. Opened the live campaign's Keywords tab read-only (Campaigns → Take Action - Street Lighting Advocacy → Keywords) and confirmed the keyword set is unchanged (see "Verification" below). No "Add keywords," "Save to plan" into the live campaign, "Create campaign," "Apply all" (on the "Add new keywords" recommendation card that Google surfaced), or any account-modifying control was clicked anywhere in this session.

### Data-quality note

Keyword Planner suppresses Avg. monthly searches (shows "–" in "Saved keywords"/"Get search volume" view) for a keyword already present in the account ("In Account" badge) — it shows the account's live stats instead of a forecast, and the live stats for these keywords are 0 (they've never served an impression, consistent with "Not eligible"). In the "Discover new keywords" view, the same 4 keywords instead showed as **"0 – 10"** avg. monthly searches under "Keywords you provided" — i.e. Keyword Planner's own generation-side estimate for these phrases really is at or near the floor of its measurable range, which corroborates (rather than just re-states) the account's ineligibility flag.

## Results table

| Ad group | Keyword | Status (current/candidate) | Avg monthly searches (US) | Competition | 3-mo change | Citizen-language rationale |
|---|---|---|---|---|---|---|
| **Migratory Birds** | "bird safe outdoor lighting" | **Current — Not eligible: Low search volume** | 0 – 10 | — | — | Trade/industry phrasing ("bird safe," "outdoor lighting") — not how a resident or birder talks. This is the group's **only** keyword, so the entire ad group cannot serve at all right now. |
| Migratory Birds | "lights out for birds" | **Candidate — recommended #1** | **100 – 1K** | Low | −90% | Matches real citizen/advocacy language — "Lights Out" is the actual name of bird-safe-lighting programs cities run (Chicago, NYC, etc.) that residents search for, especially during migration season. Best volume-to-relevance candidate found. The −90% three-month change is very likely seasonal (spring/fall migration windows), not a genuine decline — worth re-checking in April. |
| Migratory Birds | "bird friendly outdoor lighting" | Candidate | 10 – 100 | High | 0% | Plain-language variant of the current failing keyword ("safe" → "friendly"). Real, if modest, volume where the original had none. Competition is High, unlike most candidates here — worth a modest bid. |
| Migratory Birds | "birds flying into window" | Candidate — **caution, likely off-topic** | 1K – 10K | Low | 0% | Best raw volume of anything tested for this group, but this phrase (and its siblings "bird safe glass," "prevent birds from flying into windows," "bird window protection," all 100–1K) are about **daytime window-glass collisions**, a different problem than our page's nighttime/light-pollution message. Using it risks real clicks with a mismatched landing message (hurting Quality Score and wasting spend) — do not add without adjusting ad copy/expectations, or treat as a "maybe" pending a copy test. |
| Migratory Birds | "birds flying into windows at night" | Candidate — **no volume, rejected** | – (no measurable volume) | – | – | The literal seasonal/nocturnal framing from the brief; tested and failed to return volume as its own phrase (the broader daytime phrase above did return volume, but with different intent). |
| Migratory Birds | "street light too bright my window" | Candidate — **no volume, rejected** | – (no measurable volume) | – | – | The literal "annoyed neighbor" phrasing from the brief; tested and failed — people don't appear to type this exact complaint into Google at phrase-match level. |
| **Environmental Impact** | "environmental impact street lighting" | **Current — Not eligible: Low search volume** | 0 – 10 | — | — | Environmental-report/EIS language, not citizen language. Group is not fully dead — its other keyword, "sustainable street lighting," is eligible and already serving. |
| Environmental Impact | "light pollution effects on wildlife" | **Candidate — recommended** | 10 – 100 | Low | 0% | Direct, plain-language rephrasing of what a concerned resident researching light pollution's broader harm (not just birds) would type. |
| Environmental Impact | "how streetlights affect environment" | Candidate — **no volume, rejected** | – (no measurable volume) | – | – | Tested and failed. |
| Environmental Impact | "environmentally friendly street lights" | Candidate — **no volume, rejected** | – (no measurable volume) | – | – | Tested and failed. |
| **Crime & Safety** | "reduce crime streetlights" | **Current — Not eligible: Low search volume** | 0 – 10 | — | — | Group is not fully dead — its other keyword, "crime prevention lighting," is eligible and already serving. |
| Crime & Safety | "improving street lighting to reduce crime in residential areas" | **Candidate — recommended #1** | 10 – 100 | Low | — | Long, but this is exactly the kind of long-tail phrase an engaged resident (the type who reads NextDoor and city council agendas) types when searching for advocacy angles — found via Discover, not a hand-written guess. |
| Crime & Safety | "street lights and crime" | **Candidate — recommended #2** | 10 – 100 | Low | — | Short, plain, exactly how a less-engaged searcher phrases the same question. |
| Crime & Safety | "street lights reduce crime" | Candidate — **caution, volume collapsing** | 10 – 100 | — | **−100%** (YoY also −100%) | Technically has a bucketed number, but both 3-month and YoY change show a full collapse to near-zero — treat as unreliable / likely to go ineligible itself soon. Not recommended. |
| Crime & Safety | "do streetlights reduce crime" | Candidate — **no volume, rejected** | – (no measurable volume) | – | – | Hand-written hypothesis; tested and failed. (Note: the near-identical Discover-sourced "street lights reduce crime," above, did return a bucketed number — small wording differences can cross Planner's measurability threshold.) |
| Crime & Safety | "streetlights and crime prevention" / "more streetlights safer neighborhood" | Candidates — **no volume, rejected** | – (no measurable volume) | – | – | Tested and failed. |
| **Energy Waste** | "streetlight energy savings" | **Current — Not eligible: Low search volume** | 0 – 10 | — | — | Group is not fully dead — its other keyword, "led streetlight upgrade," is eligible and already serving. |
| Energy Waste | "energy efficient street lighting" | **Candidate — recommended** | 10 – 100 | Low | 0% | Plain, real volume; close enough in register to the already-eligible "led streetlight upgrade" that some overlap is likely, but it's the only candidate tested for this group that returned measurable volume. |
| Energy Waste | "wasted energy street lights" | Candidate — **no volume, rejected** | – (no measurable volume) | – | – | Tested and failed. |

18 non-calibration keywords priced/discovered across the 4 groups (4 current + 14 candidates), plus 24 raw ideas returned by Discover Round A and 6 by Discover Round B (not all listed individually above — off-topic or duplicate ones omitted; full grid data is reproducible by re-running the same two Discover searches, which is deterministic for a fixed date range).

## needs_human_decision

**Question for Ari:** which of the candidates below should be added (phrase match) to each ad group, and should the currently-ineligible keyword in that group be paused or left as-is?

**Migratory Birds — highest priority, this group cannot serve at all today:**
1. **Add "lights out for birds"** (100–1K/mo, Low competition) — clear best option, real volume, genuine citizen/advocacy phrasing tied to an actual real-world movement name.
2. **Add "bird friendly outdoor lighting"** (10–100/mo, High competition) — smaller but real, closest sibling to the current failing keyword.
3. Optional, higher-risk 3rd add: **"birds flying into window"** (1K–10K/mo, Low) — by far the biggest volume found, but it's predominantly a daytime window-glass-collision search, not a nighttime-lighting search. Recommend testing only if ad copy/landing message is adjusted to acknowledge both angles, otherwise skip it — clicks with mismatched intent waste budget and can drag down Quality Score.
4. Recommend **keep** "bird safe outdoor lighting" rather than pause — it's the group's only keyword today, so pausing it before the replacements are confirmed to generate impressions would risk the ad group going from "1 dead keyword" to "0 keywords" (defeating the purpose of this whole exercise). Once #1 and #2 are live and showing impressions (check after a few days), pausing the dead one is safe cleanup. Keeping a zero-volume keyword costs nothing.

**Environmental Impact:**
1. **Add "light pollution effects on wildlife"** (10–100/mo, Low) — the only candidate tested that returned real volume for this group.
2. This group already serves via "sustainable street lighting" (eligible, live). Recommend **pause** "environmental impact street lighting" once the replacement is added — since the group has working coverage already, there's less downside risk to cleaning up the dead keyword right away, unlike Migratory Birds.

**Crime & Safety:**
1. **Add "improving street lighting to reduce crime in residential areas"** (10–100/mo, Low) — long-tail but genuinely how an engaged citizen-advocate searches.
2. **Add "street lights and crime"** (10–100/mo, Low) — shorter, more casual phrasing of the same intent.
3. This group already serves via "crime prevention lighting" (eligible, 10–100/mo, live). Recommend **pause** "reduce crime streetlights" once the two replacements above are added and confirmed live.
4. Note for Ari: an earlier pass at this same item (superseded by this handoff) reported "no good candidate exists" for this group, based only on hand-written hypotheses. Running Keyword Planner's "Discover new keywords" tool (as this pass did) surfaced two real candidates that the hand-written approach missed — worth remembering for any future keyword work in this niche: Discover found ideas hand-guessing didn't.

**Energy Waste:**
1. **Add "energy efficient street lighting"** (10–100/mo, Low) — real volume, though close enough to the existing eligible "led streetlight upgrade" that some search-term overlap is likely; treat as a phrase-match diversifier rather than a guaranteed independent volume source.
2. This group already serves via "led streetlight upgrade" (eligible, live). Recommend **pause** "streetlight energy savings" once the replacement is added.

**Suggested default if Ari wants one decision applied without further discussion:** add the 5 clearly-recommended candidates — lights out for birds; bird friendly outdoor lighting; light pollution effects on wildlife; improving street lighting to reduce crime in residential areas; street lights and crime; energy efficient street lighting (6 total) — as phrase match to their respective ad groups, leave all 4 currently-ineligible keywords in place for now (do not pause any yet), and revisit pause/cleanup after a few days of the new keywords showing real impressions. This is the lowest-risk path: it adds coverage everywhere without removing anything, and Migratory Birds — the fully-dead group — gets fixed either way. Skip the higher-risk "birds flying into window" addition unless Ari specifically wants to test the window-collision angle with adjusted ad copy.

## Nothing in Google Ads was changed

Confirmed by directly re-opening the live campaign's Keywords tab (Campaigns → Take Action - Street Lighting Advocacy → Keywords, read-only) after all Keyword Planner work was done. All **14** keywords present match `C:/Users/aisaa/Projects/Ads/google/take-action-campaign.md` exactly (2 Transportation Safety + 2 Light Pollution + 1 Migratory Birds + 2 Energy Waste + 2 Crime & Safety + 2 Environmental Impact + 3 "Ad group 1" = 14), with the same 4 keywords showing "Not eligible / Low search volume" and no others. Migratory Birds still shows exactly one keyword ("bird safe outdoor lighting"). A Google Ads "Add new keywords" recommendation card ("Apply all" / "View") was visible on the Keywords page — it was **not** clicked. No "Add keywords," "Save to plan" into the live campaign, "Create campaign," or any account-modifying control was clicked anywhere in this session. The only thing created was a Keyword Planner "plan" (scratchpad, planId `1436720453`), which is Keyword Planner's own sandbox, does not touch the live campaign, and is explicitly permitted by the assignment.

## Files

- This handoff: `.dagflow/phases/01-verify-funnel/items/p1-keyword-research-HANDOFF.md`
- No screenshots were saved as files this session — evidence was read directly from the page via the accessibility tree (`read_page`) and transcribed into the table above; that data is reproducible by re-running the same "Get search volume and forecasts" list and the same two "Discover new keywords" seed sets (Keyword Planner's historical data for a fixed date range is stable, so re-running returns identical numbers).

## Known limitations

- Search volume ranges (e.g. "10 – 100") are Google's bucketed ranges, not exact counts — a Keyword Planner platform limitation, not a gap in this investigation.
- "Birds flying into window" and its siblings are flagged as a real but likely-mismatched-intent option rather than a clean recommendation — a human call on whether to test it is left to Ari, not made unilaterally here.
- No `/generate` calls were made (0 of the phase's 2-call budget used by this item); no AWS resource was touched; this item's cost was entirely the read-only Keyword Planner session.
