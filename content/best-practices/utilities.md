---
title: "Best Practices for Utilities"
linkTitle: "Utilities"
subtitle: "Your streetlights are already grid assets.<br>They just don't know it yet."
description: "How utilities can unlock energy savings, demand response revenue, and grid flexibility from existing street lighting infrastructure using Photometrics AI's precision optimization."
keywords: ["duck curve street lighting", "LED victory lap", "avoided cost lighting", "street lighting demand response"]
lastmod: 2026-03-29
---

## The Overlooked Asset

If you manage demand-side resources for a utility, you already know the challenge: finding controllable load that's large enough to matter, dispatchable on short notice, and available during peak hours. Preferably in areas that are resource constrained. Street lighting checks every box, and almost nobody is using it. Across the world, millions of streetlights run at full power from dusk to dawn, every night, regardless of conditions.

Globally, street lighting accounts for **1–3% of electricity demand during operating hours**.[^1] That's not a rounding error. It's a massive, untapped demand-side resource hiding in plain sight. The streetlight effect in reverse.[^2]

<h2 style="border-top: none; padding-top: 0;">Darkness on the Grid</h2>

Darkness is no longer downtime for the electric grid. It's the most challenging part of the day. In 2024, solar generated over 10% of the world's electricity.[^3] In solar-rich places like California, solar alone accounts for over a fifth of the state's power mix, and clean energy overall exceeds 60%.[^4] By 2030, the IEA projects wind and solar PV will supply nearly 30% of global electricity, roughly double today's level.[^5] The march to adopt solar isn't slowing down.

At the same time, the adoption of electric vehicles and data centers is moving more electric consumption to the hours between dusk and dawn. Traditionally, this window gave the grid time to relax. Not anymore. Combine these trends with aging infrastructure and climate-driven wildfire risk, and the picture is clear: nighttime grid stress is growing, not shrinking.

Street lights turn on exactly when solar generation ramps down and evening demand peaks. They consume energy at the worst possible time. It is [the duck curve's blind spot](/concepts/#duck-curve).

<h2 style="border-top: none; padding-top: 0;">Avoided Costs and Demand Response</h2>

Energy conservation during evening and overnight hours saves money at the most expensive times.[^6] Yet utilities spend millions enrolling individual customers in demand response programs — smart thermostats, water heaters, EV chargers — one household at a time. Meanwhile, street lighting sits right there: on every feeder, in every service territory, many already metered, already connected.

<h2 style="border-top: none; padding-top: 0;">Two Paths to the Same Grid Asset</h2>

Roughly **50% of U.S. streetlights are utility-owned**.[^7] This ownership split plays out internationally as well.

These lights are already on the utility's books. No enrollment required. The utility can optimize and benefit from them directly. Using California's Avoided Cost Calculator (ACC) methodology,[^8] Photometrics AI calculates grid value of **$12.20/light/year** to utilities — $10.18 in avoided generation, transmission, and distribution costs plus $2.02 in demand response revenue through programs like the Capacity Bidding Program (CBP) and Emergency Load Reduction Program (ELRP).[^9] Because utility-owned lights are utility assets, the benefits of reduced maintenance and extended luminaire life also accrue directly to the utility — an additional **$20.66/light/year** in asset management value.[^10]

The other half are owned and operated by municipalities. In the U.S., street lighting is often on fixed rates, meaning municipalities have little incentive to dim. Internationally, the picture varies but is often still not truly metered. If these lights were on metered rates, municipalities would dim on their own to save money when light isn't needed, benefiting both the municipality and the utility. Currently, they have no incentive.

Utilities should engage municipalities in DR programs for their street lighting — programs like California's CBP or ELRP. While this is not as straightforward as managing your own fleet, the enrollment economics are compelling: a single contract with one municipality captures thousands of controllable endpoints. Compare that to the per-household acquisition cost of residential demand response. Municipalities are looking to cut costs while delivering excellent services. Many will opt in if it's available.

Either way, the load is controllable. The question is whether anyone is controlling it.

<h2 style="border-top: none; padding-top: 0;">The Duck Curve's Blind Spot</h2>

Street lights turn on exactly when solar generation ramps down and evening demand peaks. They consume energy at the worst possible time: evening peaks, early-morning ramps, hot summer nights when the grid is most stressed.

But here's what makes street lighting different from every other demand response resource: **geographic ubiquity**. A factory is in one place. A data center is in one place. Street lights are on *every* distribution circuit, in *every* community, in *every* resource area. They are the only dispatchable load with true geographic coverage across the entire grid.

This means street lighting can provide demand relief exactly where it's needed — not just system-wide, but at the local feeder level where constraints actually bind.

<h2 style="border-top: none; padding-top: 0;">Precision Optimization, Not Blanket Dimming</h2>

The standard approach to streetlight dimming is crude: reduce everything by some fixed percentage after midnight. It ignores the fact that a light over a six-lane intersection and a light in a residential cul-de-sac have completely different needs.

Photometrics AI calculates the **optimal output for every individual luminaire** based on its actual context: road geometry, fixture height, optic type, adjacent land use, and the overlapping beam patterns of neighboring lights. Crosswalks and major arterials stay reliably lit. Quiet residential communities where the speed limit is below 25 MPH are strategically dimmed. Cul-de-sacs can be dimmed more aggressively than through streets.

The result: **35% energy savings** compared to baseline LED on/off operation,[^11] while maintaining or improving lighting quality at every calculation point, verified against ANSI/IES RP-8 and CIE 115 standards.

These optimized parameters are delivered to existing networked lighting control (NLC) systems via API. No new hardware, no field activity. If the lights are already networked, Photometrics AI works with what's there.

Human eyes are remarkably effective at using available light. Brightness reductions below 20% are generally imperceptible, especially at night. Two lights next to each other, one at 80% and one at 100%, look identical. No one is going to notice a light dimming to 50% for a few hours a few times per year. There is enormous optimization headroom that has simply never been used. Nobody calls to complain that their streetlight dimmed from 100% to 80% at 2 AM. It's a frictionless demand response resource.

## How to Implement these Ideas with Photometrics AI

*Coming soon — practical guidance for utility program managers on defining Target Lighting Layers that align dimming strategies with grid priorities, safety standards, and demand response objectives.*

[^1]: [SEAD/Clean Energy Ministerial, "Street Lighting and Dark Skies" (2012)](https://www.cleanenergyministerial.org/content/uploads/2022/05/sead-street-lighting-factsheet-final.pdf) ([archived copy](https://claude-sources.s3.us-west-2.amazonaws.com/sead-street-lighting-factsheet-2012.pdf)). Original estimate of 1–3% of total electricity demand; LED conversion has likely reduced this, but the range remains defensible during operating hours when overall grid demand is lower.
[^2]: [The Streetlight Effect, Reversed](https://www.linkedin.com/pulse/streetlight-effect-reversed-ari-isaak-gisp-cflc-jkeac/) — Ari Isaak, Photometrics AI.
[^3]: IEA via pv magazine, ["Solar Supplied Over 10% of Global Electricity Consumption in 2024"](https://pv-magazine-usa.com/2025/04/15/solar-supplied-over-10-of-global-electricity-consumption-in-2024/) ([archived copy](https://claude-sources.s3.us-west-2.amazonaws.com/pv-magazine-solar-10-percent-global-2024.pdf)) (April 2025).
[^4]: California Energy Commission, [2024 Total System Electric Generation](https://www.energy.ca.gov/data-reports/energy-almanac/california-electricity-data/2024-total-system-electric-generation) ([archived copy](https://claude-sources.s3.us-west-2.amazonaws.com/california-energy-commission-2024-total-system-electric-generation.pdf)). Solar: 21.3% of power mix; clean energy: 62%.
[^5]: IEA, [Renewables 2025](https://www.iea.org/reports/renewables-2025/renewable-electricity) ([archived copy](https://claude-sources.s3.us-west-2.amazonaws.com/iea-renewables-2025-renewable-electricity.pdf)). Variable renewables (solar PV + wind) projected at ~27–30% of global electricity by 2030, up from 17% in 2024.
[^6]: See ["Utility Cost Avoidance: Why Nighttime Energy Savings Are Worth More Than You Think"](/insights/utility-cost-avoidance/) — Photometrics AI Insights.
[^7]: [AB 719 Assembly Bill — Bill Analysis](http://www.leginfo.ca.gov/pub/13-14/bill/asm/ab_0701-0750/ab_719_cfa_20130405_164252_asm_comm.html) ([archived copy](https://claude-sources.s3.us-west-2.amazonaws.com/AB%20719%20Assembly%20Bill%20-%20Bill%20Analysis.pdf)). See also: U.S. DOE streetlight ownership data.
[^8]: [CPUC, Avoided Cost Calculator Documentation, 2024](https://www.cpuc.ca.gov/-/media/cpuc-website/divisions/energy-division/documents/demand-side-management/acc-models-latest-version/updated-2024-acc-documentation-v1b.pdf) ([archived copy](https://claude-sources.s3.us-west-2.amazonaws.com/cpuc-acc-documentation-2024.pdf)).
[^9]: ["Calculating the Value of Street Light Optimization: Utilities"](https://www.linkedin.com/pulse/calculating-value-street-light-optimization-utilities-1-hxohc/) — Ari Isaak, Photometrics AI. California-specific; other jurisdictions require different methodology.
[^10]: Photometrics AI internal modeling. Includes $4.90/light/year maintenance reduction from lower thermal stress and $15.76/light/year luminaire life extension (50% of fleet at end-of-life; 12-to-19-year extension from reduced operating temperatures).
[^11]: Photometrics AI internal modeling — 25% savings during evening/pre-dawn periods (precision design eliminating over-illumination per RP-8 standards) plus 50% reduction from 1–5 AM (time-of-night dimming during low-traffic hours). Weighted average: 35%.
