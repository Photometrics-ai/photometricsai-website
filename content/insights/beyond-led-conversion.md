---
title: "The LED conversion is over. What comes next?"
description: "The economic engine that powered fifteen years of street lighting upgrades is running out of fuel. The next phase of value is not in the hardware. It is in how the hardware is operated."
tags:
  - energy
  - optimization
  - controls
---

The street lighting industry ran on one pitch for fifteen years: replace high-pressure sodium with LED. Same light, lower energy bills. Utility rebates bought down the upfront cost. ESCO financing eliminated capital outlays. Energy savings provided the payback. It was a clean, repeatable economic engine and it worked brilliantly.

That engine is stalling.

## The math doesn't work anymore

Early LED deployments are approaching end of life. The luminaires installed in 2012 and 2015 are coming due for replacement. Municipalities now face a problem the industry has not confronted at scale: replacing LEDs with LEDs.

The economics of the first conversion were powered by the enormous energy delta between a 250-watt sodium fixture and a 90-watt LED. That delta financed everything. Rebate programs were designed around it. ESCO contracts depended on it. The entire financial model assumed you were replacing something inefficient with something efficient.

When you are swapping one LED for another, there is no massive delta to finance against. The new fixture might be 10-15% more efficient than the one it replaces. That is not enough to fund the project through energy savings alone. The rebate programs were not designed for this. The ESCO model needs a bill reduction large enough to generate payback within the contract term. LED-to-LED rarely delivers that.

If the only thing a new fixture offers is slightly better efficiency, the sale is a hard one to make.

## Efficiency is not effectiveness

The LED conversion optimized for the wrong variable. It made every fixture more efficient at doing the same thing it had always done: produce a fixed amount of light from dusk to dawn, regardless of what is happening on the street below.

A 2012 sodium fixture running at 250 watts all night and a 2025 LED running at 90 watts all night are doing the same job. The newer one does it with less electricity. That is efficiency. But neither fixture adjusts to weather, responds to traffic, dims for bird migration, brightens for a special event, or reduces output when the street is empty at 3 AM.

The question the industry stopped asking after the LED conversion: does the lighting actually serve the community well? Not cheaply. Well.

Pedestrian crashes spike during dark conditions. Three out of four pedestrian fatalities happen at night. The lights that are on during those crashes were designed for a generic worst-case scenario, not for the actual conditions at that location at that moment. A crosswalk at an unlit intersection. A bus stop before dawn. A residential street where the lights are as bright at 3 AM as they are at 9 PM, but the crosswalk two blocks away is underlit because the typical layout didn't account for the geometry.

Efficiency did not fix these problems. It made them cheaper to ignore.

## Where the value is now

Roughly 15% of the world's streetlights operate on networked lighting controls. Nodes installed. CMS running. The infrastructure to operate lights dynamically exists.

Most of these systems run at full power, all night, with a crude time-based dim at midnight. Not because the controls cannot do more, but because nobody has done the photometric engineering to tell them what to do.

This is where the next phase of value lives. Not in replacing the luminaire, but in making the luminaire perform differently under different conditions. Software that calculates the optimal output for each fixture based on its actual geometry, the lighting standard that applies, and the conditions at that moment.

The savings come from two mechanisms. First, precision design eliminates the over-illumination baked into every typical layout. When a lighting engineer designs for a generic road type, they design for the worst location within that type. Every location that is not the worst case is overlit. Per-luminaire optimization identifies and removes that excess, fixture by fixture. Second, time-of-night dimming reduces output further during hours when traffic volumes and pedestrian activity are lower, while maintaining the lighting standard required for those conditions.

These are not marginal gains. Combined, they produce meaningful energy savings on top of infrastructure that has already been converted to LED. And because the optimization is software-only, it requires no hardware, no field crews, no capital investment in fixtures.

## Better lighting, not just less lighting

This is easy to misunderstand, so it is worth being direct: optimization is not blanket dimming. It is not reducing every light by 30% and hoping for the best.

It is photometric engineering. Every luminaire has a known photometric distribution, described in its IES file. Every pole has a known height, arm length, setback, and orientation. Every road segment has a width, a classification, and a lighting standard that applies to it. IES RP-8-25 in the United States. EN 13201 in Europe. These standards define exactly how much light should fall on the roadway, the sidewalk, and the crosswalk under specific conditions.

The calculation is straightforward in principle: given these fixtures at these locations, what dimming level produces the illuminance the standard requires? Account for beam overlap between neighboring fixtures. Account for the actual geometry, not a generic cross-section. Account for the fact that the intersection with 30-foot pole spacing responds differently to dimming than the one with 45-foot spacing, even though both were assigned the same typical layout.

The problem has never been that this calculation is difficult. It is that it takes too long. A single photometric calculation for one road segment might take a lighting engineer an hour. A city with 50,000 fixtures has thousands of segments. Designing one lighting scenario for the full network could take months. Designing ten scenarios for different conditions — late night, rain, events, migration — is not feasible by hand.

This is the bottleneck that has kept networked lighting controls running as time clocks. The hardware can switch between scenarios in seconds. The photometric design for those scenarios takes weeks or months. Controls respond at the speed of software. Design has been moving at the speed of spreadsheets.

When that calculation runs in minutes instead of months, the constraint disappears. Every fixture gets its own dimming level, computed to meet the applicable standard for the conditions in effect. Not overlit to cover the worst case. Not underlit because someone guessed at a blanket percentage. Aligned with the standard, precisely, at every location.

The result is not dimmer streets. It is streets that meet the standard without the excess that typical layouts overbuild. In many cases, the lighting is more uniform after optimization than before, because the per-luminaire calculation maintains uniformity ratios that blanket dimming degrades.

## Capability is the new economic engine

The LED conversion sold efficiency. The next sale has to sell capability.

What does that mean in practice? A city's streetlights respond to weather conditions. When rain reduces road surface visibility, the lighting adjusts. When a sporting event ends and crowds hit the streets, the lighting is ready. When BirdCast forecasts a major migration night, residential areas dim while main roads stay lit. When the grid operator calls for demand reduction, the lighting system participates. When a crosswalk has a history of nighttime crashes, it gets targeted illumination during the hours the data says crashes cluster.

None of this requires new luminaires. It requires intelligence applied to the luminaires already in the ground.

For contractors and distributors facing the LED-to-LED replacement conversation, this changes the pitch. You are not selling a fixture swap with marginal efficiency gains. You are selling smarter infrastructure that delivers measurable results year after year. The value does not depreciate with the hardware. It compounds as more data, more scenarios, and more integrations come online.

For municipalities facing tight budgets and aging LED stock, this changes the calculus. The most cost-effective investment is not replacing fixtures that still work. It is making those fixtures perform better through software.

## The infrastructure is already there

The poles are in the ground. The LEDs are installed. The controls are deployed. The only thing missing is the intelligence to operate them well.

Fifteen years ago, the industry looked at sodium fixtures and said: we can do better. The answer was LED. Today, the industry is looking at LED fixtures running on time clocks and the same question applies. The answer is not another fixture. It is optimization.
