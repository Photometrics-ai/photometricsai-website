# p1-browser-ui-check — HANDOFF

## Status: done (executed by the lead, not a subagent — see "Why the lead ran this")

## Why the lead ran this
Two subagent attempts failed for environmental reasons, not product reasons: the Chrome MCP tab group is shared by the whole session, so the lead's and subagents' tabs evicted each other ("tab-group contention", see the FAILED handoff text preserved in git history of this file / the run journal wf_476b0072-728). The lead ran the item in its own tab after stopping the scheduler. Recorded in CHANGELOG.md.

## What was verified (live production page, tab 1137267000, 2026-09-03 ~19:45–20:00 UTC)

| Step | Result | Evidence |
|---|---|---|
| Open `/take-action/?priorities=Transportation%20Safety&gclid=TEST` | PASS | JS: `aria-checked=true` card = ["Transportation Safety"]; Card 2 message = "Nearly half of all traffic fatalities happen at night on just 25% of the driving…" (Transportation Safety copy, generic subtitle hidden) |
| Enter location "Austin, TX" and name "UI Test" | PASS | form_input set both; JS read back both values |
| Click Generate → representatives + letter | PASS | After ~30s: 4 reps returned, letter 2704 chars, Send button label "Send to 4 Representatives" |
| Uncheck one rep ("Include in send") | PASS | transportation@austintexas.gov checkbox → false; Send label → "Send to 3 Representatives" |
| Edit letter textarea | PASS | Appended "UI-EDIT-MARKER 2026-09-03: this sentence was added by hand before sending."; textarea value tail confirms. Screenshot: `p1-browser-ui-check-letter-edited.jpg` (same dir) |
| Send | NOT CLICKED (by design) | No row added to photometrics-take-action-sends (count stayed 4) |
| GA4 `take_action_submit` observed | **NOT OBSERVED from this browser** | See GA4 section |

Representatives returned for Austin, TX / Transportation Safety (session 66099731-08d3-4aac-a501-a094f2f40d3a):
- Kirk Watson — Mayor — kirk.watson@austintexas.gov
- Austin Transportation and Public Works Department — Department Head — transportation@austintexas.gov
- Thomas J. Gleeson — Chairman — thomas.gleeson@puc.texas.gov
- Tucker Ferguson — District Engineer — tucker.ferguson@txdot.gov

Anecdotal but notable: `chairman@puc.texas.gov` (hard-bounced 2026-09-02, in the exclusion set) was NOT suggested; a named address at the same agency was. Consistent with the prompt-level exclusion working in this instance. Not proof it always works (Phase 2 adds the hard filter).

## /generate calls made: 2 (phase budget was 2; harness-run made 0)
An earlier click while the tab was in a hidden/zero-size Chrome window silently fired one generate (session b47c8dc6-8b9c-44cc-b990-72f523813316, 19:47:42Z, reps: mayor@austintexas.gov, transportation@austintexas.gov, txdot.trafficsafety@txdot.gov, publicworks@austintexas.gov). Second was the visible run (66099731…, 19:49:17Z). Note the two runs for the same input returned different rep sets — the officials search is non-deterministic.

## Cleanup
Both rows deleted with `aws dynamodb delete-item`. Post-delete counts: photometrics-take-action 120, photometrics-take-action-sends 4 (baseline restored). Today's remaining generate rows (real users): 0.

## GA4 findings (important for Phase 3)
- From this machine's Chrome, gtag.js loads (googletagmanager.com 200), `window.gtag` exists, and hits are emitted to `analytics.google.com/g/collect` with the correct params (`en=take_action_submit&ep.priorities=Transportation%20Safety&ep.location_entered=…` captured in the network log).
- GA4 Realtime received the **page_view** hits from this browser (count rose 1→2→3 with each reload) but **none** of the custom events fired from this browser: the real `take_action_submit` from the generate, nor test events `lead_gtag_test_1`, `take_action_submit` (debug_mode), `lead_fetch_debug`, `lead_beacon_debug`. DebugView showed 0 debug events over the window.
- The Chrome MCP network monitor labels these POSTs 503, but a direct `fetch()` to the same URL from page context returns 204, and `curl` from this machine reaches real Google servers (411 on empty POST). The 503 label is not trustworthy evidence on its own; the DebugView/Realtime absence is.
- GA4 property has NO developer-traffic filter (Data filters: only "Internal Traffic", state Testing), so debug_mode events are not being filtered out by configuration.
- Real users' custom events DO arrive: the 28-day event list includes `take_action_submit`, `send_intent_clicked`, `csp_verify_*`, `manual_debug_test`; 8 key events in the last 7 days; and Acquisition shows 8 sessions from google / cpc (the new campaign) in the last 7 days.
- Conclusion: this is a local-environment anomaly on Ari's machine/browser, the same one seen in the 2026-09-02 investigation ("DebugView events never appeared… despite dataLayer growing"). **Phase 3's GA4 verification must be done from a different device (phone on cellular with Tag Assistant worked on 2026-09-02) or via GA4's Events report the next day, not from this Chrome.**
- Side finding: `insights_article_view` fires on the Take Action page (and, per the 7-day report, on almost every page: 416 vs 424 page_views). It is not defined under `layouts/`; source is elsewhere (static JS or Glyphex tracker). Worth a look in Phase 3 since it pollutes event counts.

## Environment notes for future browser items
- Subagents and the lead share one Chrome tab group; run browser items from the lead or run them strictly one at a time with no lead browser activity.
- A tab created while Chrome's window is minimized reports `innerWidth 0` / `visibilityState hidden`; clicks don't land and screenshots fail with "0 width". `resize_window` did not fix it; creating a fresh tab did.
- `computer type` did not enter text into these inputs; `form_input` did.
