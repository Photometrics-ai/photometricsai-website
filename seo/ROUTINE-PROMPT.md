# SEO Routine Prompt (paste into Claude Code every two weeks)

Copy everything below the line into a Claude Code session opened in this repo. Have Chrome open; Claude in Chrome will open Glyphex, Ahrefs, and Ubersuggest tabs and ask you to sign in if the sessions have expired.

Skill script quirks learned 2026-09-04: pass Windows-style paths (`C:/...`) to the skill's Python scripts, not `/c/...`; `pagespeed_check.py` needed a one-line patch (`audit_details` was never initialized) which is applied in `~/.claude/skills/seo/scripts/`.

---

Run the bi-weekly SEO check-in for photometrics.ai. Use the /seo skill for every automated step. Do not ask me to log in or check anything manually — Claude in Chrome is already signed in to Glyphex, Ahrefs Webmaster Tools, and Ubersuggest; Google Search Console and GA4 are wired through the /seo google API credentials (service account, tier 2), so pull those via the API, not the browser.

Before starting, read the most recent file in `seo/reports/` (if any) so you can distinguish NEW issues from ones already flagged, and so you can see which rotation pages were covered last time.

## Part 1 — Google data via API (/seo google)

1. `/seo google gsc` — GSC lags 2-3 days, so use explicit windows ending 3 days ago: current = last 14 full days, prior = the 14 before. The site's traffic is small, so treat any week-over-week move under about 30% as noise and say so. Pull four queries with the skill's script: `--dimensions date` over both windows (this gives the accurate totals — query-dimension rows are anonymized and undercount), `--dimensions query` per window, `--dimensions page` per window. Report clicks, impressions, CTR, average position with deltas. List new queries absent from the prior window. Flag high-impression/low-CTR pages as title/meta-rewrite candidates. Report any `beta.photometrics.ai` URLs that still show impressions.
2. `/seo google sitemaps https://photometrics.ai` — sitemap submitted, processed, no errors, discovered-URL count matches expectations.
3. `/seo google inspect` on any page that lost impressions week-over-week, plus any page published or edited since the last report (check `git log --since` on `content/`). Report index status, canonical, and last crawl date.
4. Core Web Vitals: CrUX has no field data for this origin (too little Chrome traffic), so skip `crux-history` and run `/seo google pagespeed https://photometrics.ai` for lab data on mobile and desktop. Report performance score, LCP, CLS, TBT, and the top opportunity. Compare to the previous report.
5. `/seo google ga4 --days 28` and `/seo google ga4-pages --days 28` — the GA4 script only takes `--days`, so pull 28 days and split the `daily_data` into two 14-day halves yourself. Report organic sessions per window and top landing pages. Flag any landing page whose organic traffic dropped more than 25%. Note when GA4 and GSC disagree on direction.

## Part 2 — Claude-seo site checks

6. `/seo technical https://photometrics.ai` — crawlability, indexability, security headers, mobile, JS rendering.
7. `/seo schema https://photometrics.ai` — validate JSON-LD across page types. Remember: existing FAQPage is Info priority only, never recommend HowTo.
8. `/seo sitemap https://photometrics.ai/sitemap.xml` — confirm it matches actual content pages in `content/`.
9. Run `/seo page` on the next 3 pages in this rotation (continue from where the last report left off; wrap around at the end):
   homepage, how-it-works, benefits, about, faq, tools, take-action, insights/adaptive-street-lighting, insights/beyond-led-conversion, insights/transportation-safety, insights/utility-cost-avoidance, insights/led-conversion-vs-optimization, best-practices/utilities, best-practices/birds, best-practices/public-safety, best-practices/transportation-safety, best-practices/dark-sky, press/birdcast-integration, concepts, civil-lighting-design
10. Every other run (roughly monthly): also run `/seo geo https://photometrics.ai` for AI-search readiness and `/seo audit https://photometrics.ai` for the full health score.

## Part 3 — Browser tools via Claude in Chrome

11. **Glyphex** — go to `https://glyphex.io/login`. If the sign-in page appears, stop and ask me to sign in **in that tab** (Google button; a magic link opens elsewhere and does not carry over). Then open the photometrics.ai dashboard. Note engagement patterns and anything that disagrees with the GA4 numbers from step 5. One paragraph, not a data dump.
12. **Ahrefs Webmaster Tools** — start at `https://app.ahrefs.com/dashboard` (project "Photometrics", id 9679405). Record DR, referring domains, and health score from the project card. Then use the sidebar links (not hand-built URLs, they reset the filters): *Referring domains* sorted by DR, and *Pages → Best by links*. The New/Lost history filters are locked on the free plan, so infer new domains from the First-seen column against the last report date. Separate real referring domains from Ahrefs-flagged SPAM and count each; report the spam network's size so it can be tracked run to run. Report the top 5 pages by referring domains.
13. **Ubersuggest** — the free plan allows 3 searches per day, and every domain overview costs one. Spend at most 2. Do NOT search our own terms. Pick one competitor from the photometrics-ai-competitive-intel skill's Category-to-Company table that the last report did not check, confirm its real domain from the profile before searching (Gradis is `gradis.io`, not `.eu`), and open `https://app.neilpatel.com/en/traffic-analyzer/overview?domain=<domain>&lang=en&locId=2840`. Record DA, organic keywords, organic traffic, backlinks, and top keywords. Record which competitor was checked.
14. Google SERP check — open `https://www.google.com/search?q=<topic>&hl=en&gl=us` for one target topic (rotate; take the next one from the last report's Rotation state). Capture the top 8 organic results, any People Also Ask questions if the box appears, and the "People also search for" terms as content prompts. Note if the SERP is ambiguous (mixed with unrelated meanings).

## Part 4 — Report

Write the report to `seo/reports/YYYY-MM-DD.md` (today's date) with these sections, in this order:

- **Headline numbers** — a short table: clicks, impressions, CTR, avg position, organic sessions, referring domains, each with prior-period value and delta.
- **New issues** — only things not present in the previous report. Ranked by impact.
- **Still open** — issues carried over from the previous report, one line each.
- **Resolved** — issues from the previous report that no longer reproduce.
- **Weakest pages** — from the 3 rotation pages, with scores.
- **Action items** — ranked Critical → High → Medium → Low, each with the file or page to change.
- **Content prompts** — new queries, PAA questions, competitor gaps, anything for the content to-do list in the seo-weekly-routine memory.
- **Skipped** — anything that could not be checked and why.
- **Rotation state** — the 3 pages checked this run and the next 3, the competitor checked in Ubersuggest, the SERP topic used and the next one, so the next run can continue.

Do not fix anything in this run. Summarize the report in the terminal, lead with the headline numbers and the top 3 action items, and tell me the report path. Then commit the report with `git add -A` and message `seo: routine report YYYY-MM-DD`.
