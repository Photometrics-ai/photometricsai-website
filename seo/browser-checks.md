# Browser add-on: photometrics.ai

Part 3 of the site-seo-routine skill, for photometrics.ai only. Uses Claude in Chrome. Load all
the browser tools in one ToolSearch call (tabs_context, tabs_create, navigate, computer,
get_page_text, find, javascript_tool, browser_batch). Make a fresh tab per tool, and close
your tabs at the end. Don't ask Ari to check anything manually, except the Glyphex sign-in below.

## A. Glyphex (on-site analytics)

1. Open `https://glyphex.io/app/sites`. The dashboard lives under `/app/sites`; `/dashboard`
   and `/app` 404.
2. If it bounces to the sign-in page, stop and ask Ari to sign in. He uses the **email
   link, not Google**. The link has to be opened in the same Chrome profile the extension
   controls, or the session won't reach the automation tabs. Once he says he's signed in, open
   a **new** tab at `https://glyphex.io/app/sites` (the old tab may still show the sign-in page).
3. Click the photometrics.ai site card and `get_page_text` the dashboard (default window: last
   30 days).
4. Write one paragraph, not a data dump: visitors, organic-search trend vs GA4 (say which one is
   more trustworthy), referral and AI-assistant traffic, rising/falling pages, rage clicks
   (page + selector), and country anomalies.

## B. Ahrefs Webmaster Tools (backlinks)

1. Start at `https://app.ahrefs.com/dashboard` (project "Photometrics", id 9679405). Record
   Health Score, DR and Referring domains from the project card.
2. Click the Referring domains number. It opens Site Explorer → Referring domains sorted by DR
   for the project. Use sidebar links, not hand-built URLs; those reset filters.
3. **Count real vs spam across ALL pages.** The UI caps at 50 rows (a `limit=500` URL resets to
   50), so page through `offset=0,50,100,…` on the same URL. After each page loads, run a
   `javascript_tool` snippet that waits ~5s, then parses the table rows (`tr` → `td` innerText;
   column 1 = domain with a trailing " SPAM" tag, column 2 = DR, second-to-last = First seen)
   and appends them to `localStorage`. Batch several navigate+JS pairs per `browser_batch`.
   `javascript_tool` output truncates around 1000 chars, so read long lists back 35 domains per call.
4. Report:
   - total, spam and real counts;
   - spam first seen since the last report date (the New/Lost filters are locked on the free plan);
   - every real referring domain with its DR;
   - any newly targeted URL.
5. **Disavow file.** If the spam set grew, regenerate `seo/disavow-photometrics.ai-YYYY-MM-DD.txt`:
   - all Ahrefs-flagged spam domains plus anything carried over from the previous disavow file;
   - Google format, `domain:` lines;
   - a header listing the real domains deliberately excluded.

   Tell Ari it needs a manual upload in the GSC Disavow tool for `sc-domain:photometrics.ai`.
   An upload replaces the old file, so always upload the full list.
6. Sidebar → *Pages → Best by links*: report the top 5 pages by referring domains.

## C. Ubersuggest (one competitor)

1. The free plan allows 3 searches/day, and every domain overview costs one. Spend at most 2.
   Never search our own terms.
2. Pick the next competitor from the `photometrics-ai-competitive-intel` skill's
   Category-to-Company table that recent reports haven't checked.
   - Confirm the real domain first (Gradis is `gradis.io`, not `.eu`).
   - Already checked: Ubicquia (09-18), Schréder `schreder.com` (10-02).
3. Open `https://app.neilpatel.com/en/traffic-analyzer/overview?domain=<domain>&lang=en&locId=2840`
   and `get_page_text`. It works unregistered for 1 search if the session has expired.
4. Record DA, organic keywords, organic traffic, backlinks, top keywords, top pages and overlap
   with our terms.

## D. Google SERP check (one topic)

1. Take the next topic from the last report's Rotation state. Open
   `https://www.google.com/search?q=<topic>&hl=en&gl=us` and `get_page_text`.
2. Capture the top 8 organic results, PAA questions, "People also search for" terms and any AI
   Overview citations. Note when the SERP is ambiguous (mixed meanings).

## Rotation state to carry in the report

Competitor checked and the next one, SERP topic used and the next one.
