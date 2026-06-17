---
title: "How Street Lighting's Lowest-Liability Guesses Result in Overlighting"
seo_title: "Why Street Lighting Overlights: The Lowest-Liability Guess Problem"
description: "Street lighting design assumptions aren't best guesses, they're lowest-liability guesses, and every one biases toward more light. Five stacking factors add up to 50 to 150 percent overlight on every street."
tags:
  - optimization
  - controls
  - dark-sky
  - standards
date: 2026-06-17
---

The science of light is rooted in hard and fast, unbreakable rules of physics. Light travels in straight lines at exactly 299792458 m⋅s−1 (AKA the speed of light). Light loses intensity at the inverse square law. Light's wavelengths are clearly defined. Einstein's E=mc² is built on light's immutable characteristics.

Every one of these laws describes an idealized world. The speed of light is exact in a vacuum. Light slows in air and bends through glass. The inverse square law is exact for a point source in empty space. The standards inherit those idealizations and quietly add more. A fresh fixture. A clean lens. A road in total darkness. A meter that sees light the way the human eye does. No real street provides any of these conditions. Each one is a place where the real world departs from the ideal, and every departure is knowable.

Despite this precision, the lighting designers, scientists, and others involved in predicting the performance of light fail spectacularly at predicting the amount of light that falls on a patch of asphalt or the side of a pedestrian in a crosswalk. The physics is not what fails them. Each gap between the ideal and the real is a place where the designer has to supply a number, and the failure is in the number they choose. The content below covers some of the factors we are missing, what the industry's current "best" practices are, and what they could be.

Lighting designers make a series of assumptions. The assumptions are not best guesses. They are lowest-liability guesses. The distinction matters because the two move in opposite directions. A best guess is centered. A lowest-liability guess is conservative and biased toward the assumption which would be hardest to sue over. In street lighting, that bias is always toward more light. In all cases discussed below, the lowest-liability assumption as a "best practice" means baking in a margin, which is overlighting.

Often this approach manifests by assuming zero for a variable we know is not zero. The result is delivering more light. Each of these assumptions stack and multiply impact.

Let's start this analysis with our goals. We light for human eyes, not light meters. Lighting standards are written for a driver or pedestrian. The first three variables below are ones a light meter can capture. The last two are variables it cannot. All of them should be accounted for properly.

## 1) Lumen depreciation

Every luminaire produces less light as it ages. The current practice is to apply a maintenance factor at design, typically around 0.8 to 0.85. The luminaire is installed bright enough that even after years of predicted decay it will still meet target at end of service life. The lowest liability assumption is to bake the worst-case decay into day one and stop there.

The best-guess approach acknowledges that the luminaire produces 100% on day one and depreciates along a known exponential curve from there. This tactic made sense in a pre-controls world. Today, controls make a static worst-case install obsolete. Controls should dim the luminaire to target on day one and gradually increase drive as the luminaire ages, with compensation modeled against cumulative drive current and operating temperature. Following the lowest-liability assumption instead of the best guess overlights by roughly 18-25% on day one, declining toward zero as the luminaire approaches end of life.

## 2) Dirt depreciation

Luminaires accumulate dirt between cleanings. The current practice is to apply a luminaire dirt depreciation factor, typically 0.7 to 0.9 depending on environment, which installs the luminaire 11-43% above target to compensate for predicted dirt accumulation. The cleaning truck rarely arrives on schedule. In many jurisdictions it doesn't arrive at all. The lowest-liability assumption uses the worst-case factor for the environment and assumes the cleaning will happen as scheduled.

The best-guess approach would account for the type of environment the light is in (coastal, mountain, highway, residential) and trigger cleaning based on when the luminaire stops meeting standards, not the calendar. Cleaning becomes a measured intervention that buys more operating time in compliance. When the marginal cleaning cost exceeds replacement cost, replace the luminaire. Field data also shows dirt warps intensity distribution, not just total output, so even a correct scalar would mislocate where the light lands. Following the lowest-liability assumption instead of the best guess overlights by 11-43% at the start of each cleaning cycle, including day 1.

## 3) Ambient light

Photometric calculations assume the road is in total darkness. No moonlight. No storefronts. No headlights. No illuminated signage. The lowest-liability assumption is zero ambient contribution, because the designer cannot quantify ambient per location with the tools in front of them, and assuming zero is the safest defense if a lighting level is ever challenged.

The best-guess approach would build a per-location ambient baseline from measured drive data, and remove the contribution of known streetlights using photometric calculations. The lunar component would be modeled forward from phase and altitude. Controls would dim streetlights to deliver only the deficit between target and current ambient, accounting for time-of-night transitions as storefronts close and the moon sets. Following the lowest-liability assumption instead of the best guess overlights by roughly 10% from moonlight alone on a residential street under a bright moon, and substantially more in commercial and downtown areas where storefronts, signage, windows and other ambient light sources contribute.

## 4) Logarithmic perception

Human brightness perception is logarithmic. A 50% reduction in physical light is perceived as roughly a 20% reduction in brightness.<sup><a href="#fn1" id="fnref1">1</a></sup> The eye cannot reliably detect a change below approximately 15-20% in real time.<sup><a href="#fn2" id="fnref2">2</a></sup> The current practice is to ignore this entirely. The lowest-liability assumption is zero perceptual headroom, because the standards methodology calculates in photopic units that don't include perception, and accounting for it would mean deliberately delivering less light than the standard calls for.

The best-guess approach would treat the perceptual threshold as the operational dimming floor, dimming past the standards target where the visual task allows, up to the just-noticeable difference. The specific threshold is open vision-science territory; the existence of substantial perceptual headroom is not. Following the lowest-liability assumption instead of the best guess overlights by at least 20% beyond the standards target, delivered for no perceived benefit.

## 5) Spectral power distribution

RP-8's illuminance targets were largely calibrated during the high-pressure sodium era. HPS has a narrow yellow-orange spectrum. Modern LED streetlights have a broader spectrum with substantial blue content, where rod cells are sensitive. Under the mesopic conditions where streetlights operate, LED delivers more useful visual signal per photopic lumen than HPS did. The current practice is to apply HPS-era photometrics targets to LED installations without any spectral correction. The lowest-liability assumption is no adjustment when clearly whiter bluer LEDs are considered "brighter" to human eyes even though a light meter reads the same amount of light.

The best-guess approach would be to translate HPS-era photometrics targets into LED-appropriate values, using the scotopic-to-photopic ratio of the installed source against typical street adaptation luminances. Following the lowest-liability assumption instead of the best guess overlights by roughly 20%, and up to ~30%, based on S/P ratio modeling.<sup><a href="#fn3" id="fnref3">3</a></sup>

## What it adds up to

Each contribution alone is modest. They compound, stack, and multiply. The honest combined overlight, depending on which variables apply where, is somewhere in the range of 50% to 150% above target. LEDs accounted for roughly 83.55% of global street and roadway lighting market value in 2025<sup><a href="#fn4" id="fnref4">4</a></sup> and the most reliable estimate is 26.5M streetlights in the US.<sup><a href="#fn5" id="fnref5">5</a></sup>

That's before any deliberate margin the designer adds on top, because nobody got sued for an overlit street. That's before the municipality asks for brighter because brighter sounds safer to voters. That's before the utility runs everything at 100% because nobody asked them to dim.

## What should change

Lighting designers are not precluded from accounting for these variables. The fix is to overspecify luminaires and operate them at dimming levels which account for best-guess assumption for all these variables, irrespective of "free light" due to unmetered tariffs. In the same way, the practitioners currently apply an 85% maintenance factor, we should apply standards for variables like human perception and SPD changes.

That's a different discipline than the one currently taught and practiced. It requires the field, the standards bodies that write the targets, the vision scientists who could quantify the perceptual headroom, the national labs that could characterize lumen depreciation and soiling patterns at scale, to accept that better-than-zero best guesses are progress even when they aren't yet perfect. It requires lighting designers to stop treating "I don't know precisely" as a reason to assume zero, and start treating it as a reason to use the best available estimate while pushing for the science that would tighten it.

The industry should work on approved numbers to account for these variables and should make the science around these variables a priority. Many wonder why skyglow is growing at 10%/year worldwide. Is it possible that the lowest liability designs the industry practices aren't anywhere close to precise?

There is a second standard the industry is failing, and this one it helped write. The IES, the same body behind the RP-8 targets, joined DarkSky International to publish the [Five Principles for Responsible Outdoor Lighting](https://ies.org/advocacy/light-at-night/). The third principle, Low Level, says light should be no brighter than necessary. A practice that bakes 50 to 150 percent overlight into every street it touches does not meet that principle.

The current discipline produces a known, quantifiable, defensible overlighting on every street it touches. The proposed approach produces an honest estimate that gets better over time.

Which do you think will result in the lighting outcomes humans want?

---

<div class="footnotes">

1. <span id="fn1"></span><a href="https://doi.org/10.1037/h0046162">Stevens, S.S. (1957). "On the psychophysical law."</a> <em>Psychological Review</em>, 64(3), 153-181. Brightness perception follows Stevens' power law (ψ = kI^a, with a ≈ 0.33 for an extended target viewed dark-adapted); a 50% reduction in luminance yields a perceived reduction of about 20% (0.5^0.33 ≈ 0.80). <a href="#fnref1">↩︎</a>

2. <span id="fn2"></span><a href="https://doi.org/10.1080/00994480.2004.10748422">Akashi, Y., & Neches, J. (2004). "Detectability and Acceptability of Illuminance Reduction for Load Shedding."</a> <em>Journal of the Illuminating Engineering Society</em>, 33(1), 3-13. Single-change detection studies cluster around 15-20%: roughly half of people fail to notice a 15-20% illuminance reduction while engaged in a visual task, and the point at which over half of occupants detect a reduction is about 20%. <a href="#fnref2">↩︎</a>

3. <span id="fn3"></span><a href="https://cie.co.at/publications/recommended-system-mesopic-photometry-based-visual-performance">CIE 191:2010, <em>Recommended System for Mesopic Photometry Based on Visual Performance</em></a>. Modeled with the CIE mesopic system: at the low adaptation luminances of street lighting, a higher S/P-ratio source delivers more mesopic luminance per photopic lumen, the effect concentrated in peripheral detection. Replacing HPS (S/P ≈ 0.65) with a high-CCT LED (S/P ≈ 1.6 to 2.0) raises effective luminance at equal photopic output by roughly 40-50% on a local street (~0.3 cd/m²), 20-30% on a collector (~0.6 cd/m²), and under 15% on a bright arterial (~1.0-1.2 cd/m²). Modeled estimate; magnitude depends on assumed S/P ratios and adaptation luminance. <a href="#fnref3">↩︎</a>

4. <span id="fn4"></span><a href="https://www.mordorintelligence.com/industry-reports/street-and-roadway-lighting-market">Mordor Intelligence, "Street and Roadway Lighting Market: Size, Share & Industry Analysis"</a> (updated January 16, 2026). By light source, LEDs accounted for an 83.55% share of the street and roadway lighting market size in 2025. <a href="#fnref4">↩︎</a>

5. <span id="fn5"></span>Smalley, E. (2013). "A Tour Through the Municipal Solid-State Streetlighting Consortium Resources." U.S. DOE Municipal Solid-State Street Lighting Consortium, presented at LightFair 2013, Philadelphia, April 21 & 24, 2013. Quick Facts: "Street lights in the U.S.: 26.5 million." <a href="#fnref5">↩︎</a>

</div>
