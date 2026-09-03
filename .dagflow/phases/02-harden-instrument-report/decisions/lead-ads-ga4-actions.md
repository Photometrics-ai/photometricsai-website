# Lead actions outside the DAG (Google Ads / GA4) — 2026-09-03

Authorized by Ari's instruction to push forward without stopping; both changes are reversible and were approved in principle during planning.

## Google Ads campaign 24212880671 — Final URL suffix (APPLIED 2026-09-03 ~20:50 UTC)
Campaign settings → Campaign URL options → Final URL suffix:
```
utm_source=google&utm_medium=cpc&utm_campaign={campaignid}&utm_content={adgroupid}&utm_term={keyword}&utm_match={matchtype}
```
Tracking template left empty. Destination URLs unchanged (still /take-action/ with ?priorities=). Saved; the row summary now reads "Using URL tracking options".
Known ad group id so far: Environmental Impact = 199915882237 (others will appear in generate rows' `source.utm_content` once clicks arrive; the keyword in `utm_term` identifies the ad group unambiguously because each keyword belongs to exactly one ad group).

## GA4 property 529600118 — custom definitions
See the section below (appended when done).

## GA4 property 529600118 — custom definitions (PARTIAL, 2026-09-03 ~21:15 UTC)
Registered event-scoped custom dimensions: `priorities`, `location_entered`, `method` (parameter names identical to dimension names).
NOT yet registered: `landed_priorities`, `utm_content`, `preselected` (dimensions) and `representatives_count` (metric). Reason: these params have never been sent yet (frontend deploy Amplify job 164 in progress), so GA4's parameter picker has nothing to suggest, and the admin UI was resetting the dialog mid-entry from this browser. Register them once the first attributed events arrive: Admin → Data display → Custom definitions → Create custom dimension (scope Event). Also still to do: mark `send_confirmed` as a key event and import it into Google Ads as a secondary conversion.
Also observed: GA4 event `insights_article_view` fires on every page (416 vs 424 page_views in 7 days) and is not in the repo → it is a GA4-side "Create event" rule (Admin → Events → Create event). Recommend deleting or fixing its condition; not changed by the lead.

## Frontend deploy
Commit ac10a0b pushed to master 2026-09-03 20:43 UTC → Amplify job 164.
