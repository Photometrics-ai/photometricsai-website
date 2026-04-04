---
title: "Calculating the Value of Street Light Optimization for Transportation Safety (2 of 7)"
description: "Street lighting optimization reduces crash-related municipal costs by $7.82 per light per year. Original FARS analysis shows fatal crashes spike at the darkness transition. BCA of 1.56 on transportation safety alone."
tags:
  - transportation-safety
  - municipalities
  - optimization
date: 2026-04-03
seo_title: "Calculating the Value of Street Light Optimization for Transportation Safety ($7.82/light/year) | Photometrics AI"
canonical: "https://www.photometrics.ai/insights/transportation-safety/"
---

*Our streets and highways are not safe because the lighting industry uses typical/representative layouts, not the actual layouts of our streets to direct light. The transition to LED saved money by providing more lumens per watt, but it didn't lead to better lighting. Most cities simply swapped fixtures one-for-one without rethinking what the right light is, where it should go, or when it should be on. This series explores the quantifiable financial benefits of getting it right. Transportation safety is the second of seven components we'll cover. Together, these benefits outweigh the costs by 10x.*

## Nighttime Roads Are Getting More Dangerous, Not Less

The nighttime fatality rate on U.S. roadways is three times the daytime rate, despite only 25% of vehicle miles traveled occurring at night.<sup><a href="#fn1" id="fnref1">1</a></sup> For pedestrians, the disparity is worse: 77% of pedestrian fatalities occur after dark.<sup><a href="#fn2" id="fnref2">2</a></sup>

An analysis of 2024 FARS data shows that fatal crashes spike at the exact moment of the evening darkness transition, and that peak tracks sunset through the seasons, shifting earlier in winter and later in summer. The highlighted bands mark the earliest and latest times streetlights turn on and off at the US population-weighted centroid.<sup><a href="#fn4" id="fnref4">4</a></sup><sup><a href="#fn9" id="fnref9">9</a></sup>

<iframe src="/insights/transportation-safety/fars_analysis.html" class="chart-embed" scrolling="no" style="width:100%; height:820px; border:none; background:#0D1117; overflow:hidden;"></iframe>

The numbers are alarming on their own. But the trend is more alarming: between 2010 and 2023, nighttime pedestrian fatalities nearly doubled, rising 84% from 3,030 to 5,578, while daytime pedestrian fatalities rose 28%.<sup><a href="#fn2" id="fnref2b">2</a></sup> Pedestrian deaths now account for 18% of all U.S. traffic fatalities, up from 12% in 2009.<sup><a href="#fn2" id="fnref2c">2</a></sup> Nearly 90% of the increase in U.S. pedestrian fatalities since 2009 occurred in darkness.<sup><a href="#fn3" id="fnref3">3</a></sup> The proportion of pedestrian fatalities occurring in darkness has risen steadily since the late 1970s, from approximately 63% in the early 1980s to over 76% today.<sup><a href="#fn3" id="fnref3b">3</a></sup>

An analysis of FARS data from 2001 to 2024, with each crash classified by actual solar phase at its location, reveals a diverging trend: in-vehicle nighttime fatalities have declined over two decades as vehicle safety technology improved, while non-motorist nighttime fatalities have nearly doubled over the same period.<sup><a href="#fn4" id="fnref4b">4</a></sup>

<iframe src="/insights/transportation-safety/nighttime_analysis.html" class="chart-embed" scrolling="no" style="width:100%; height:660px; border:none; background:#0D1117; overflow:hidden;"></iframe>

This worsening trend coincides with the largest street lighting replacement program in history. Cities across the country swapped millions of fixtures from high-pressure sodium to LED. The hardware improved. The safety outcomes did not. When Pacific Northwest National Laboratory (PNNL) studied whether LED conversions in the Philadelphia region improved crash outcomes, they found no statistically significant difference between municipalities that had converted and those that had not.<sup><a href="#fn5" id="fnref5">5</a></sup> Hardware requiring less maintenance with brighter light is not the same as better lighting.

Sanders et al. found that roadway design and operations are significantly associated with the likelihood of a pedestrian fatality occurring in darkness versus daylight: speed limits, number of lanes, roadway type, and presence of traffic control. These factors are all worse at night because they are negatively affected by a lack of visibility.<sup><a href="#fn3" id="fnref3c">3</a></sup> The Federal Highway Administration classifies street lighting as a Proven Safety Countermeasure, with research showing 28-42% crash reductions from proper illumination.<sup><a href="#fn1" id="fnref1b">1</a></sup> The research consensus is clear: improved lighting quality reduces both the frequency and severity of nighttime crashes. Better lighting can turn a fatality into a property-damage-only incident, a severe injury into a near miss.

## A Problem to Solve

We know where people die. We know lighting prevents it. We know exactly how much light a crosswalk needs. IES RP-8-25 specifies 20-34 lux of vertical illuminance depending on context. Vertical illuminance is light on the face and body of a pedestrian, which is what a driver needs to see a person in time to stop. The standard exists. The science is settled. And yet we cannot get light in crosswalks.

The reason is the practice itself. Typical lighting layouts use 10-20 generic templates for an entire city. They space fixtures at uniform intervals based on road classification, without ever looking at precisely where the crosswalks, curves are, bike lanes and transit stops are relative to lighting levels. They don't overlay these critical locations with photometric data on a citywide map. They don't check whether a pedestrian standing in a crosswalk at 9 PM is visible to an approaching driver. The practice is structurally incapable of delivering light to the places where people are most vulnerable, because it never considers where those places are. The typical layout approach works for fast food restaurants with 1000 stores, but only 4 standard layouts. It does not work for our streets and roads. They are simply too diverse to boil down to a few cookie-cutter solutions.

People are dying and being severely injured at known, mapped, marked locations. Crosswalks that the city painted, signed, and signaled. The lighting design never looked at a map. That is not a technology gap. It is a practice failure. And it is quantifiable.

## The Calculation

We start with the total economic cost of motor vehicle crashes in the United States and isolate the portion that municipalities bear, that occurs in darkness, and that lighting quality can address.

**Inputs:**

| Input | Value | Source |
|-------|-------|--------|
| Total crash costs (2019) | $339.809 billion | NHTSA, Table 15-5<sup><a href="#fn6">6</a></sup> |
| State/local government share | $10.948 billion (3.22% of the total) | NHTSA, Table 15-5<sup><a href="#fn6">6</a></sup> |
| US streetlights | 26.5 million | DOE |
| Darkness crash share | 50% | FHWA<sup><a href="#fn1">1</a></sup> |
| Improvement from optimization | 3% | Conservative estimate (see below) |
| Inflation, 2019→2025 | 26.1% | BLS CPI (CUUR0000SA0)<sup><a href="#fn7">7</a></sup> |

Importantly, the NHTSA study isolates the cost borne by local governments; police, fire, emergency medical services, victim assistance, coroner services, incident management, and roadside infrastructure damage.<sup><a href="#fn6" id="fnref6">6</a></sup> These costs do not include the much larger costs (~30x) borne by individuals, health and auto insurance and other entities. The numbers herein are limited to direct costs to State and Local governments. A reduction in crashes is a reduction in municipal expenditure.

We use 50% for darkness crashes because FHWA finds that the number of fatal crashes occurring in daylight is about the same as those occurring in darkness.<sup><a href="#fn1">1</a></sup> This is conservative. For pedestrian crashes specifically, 77% occur after dark.<sup><a href="#fn2">2</a></sup>

**The math:**

State/local crash costs per streetlight:
$10.948B ÷ 26.5M = **$413.13 per light**

Darkness-related portion (50%):
$413.13 × 0.50 = **$206.57**

Improvement from better lighting management (3%):
$206.57 × 0.03 = **$6.20** (2019 dollars)

Inflation adjustment to 2025 dollars (26.1%):
$6.20 × 1.261 = **$7.82 per light per year**

For a city with 20,000 streetlights, that is $156,400 per year in reduced crash-related municipal costs. This value is separate from the utility system benefits covered in [Part 1](/insights/utility-cost-avoidance/), and separate from the other benefits of optimized lighting: crime reduction, extended luminaire life, and lower maintenance costs.

## Why 3%

The 3% improvement assumption is the one number in this calculation that is not sourced from federal data. It deserves scrutiny.

The FHWA's 28-42% crash reduction figures measure the effect of adding lighting where there was none.<sup><a href="#fn1">1</a></sup> We are not adding lighting. We are optimizing existing lighting, so the right light reaches the places where and when crashes happen. This is the key in reducing the severity of a crash.

The most relevant research comes from NCHRP Project 5-19 ("Review of the Safety Benefits and Other Effects of Roadway Lighting"), conducted by the Lighting Research Center at Rensselaer Polytechnic Institute for the Transportation Research Board. Using crash data from Michigan and Minnesota, Harwood et al. found an accident modification factor (AMF) of 0.96 for arterial roadway segments that already have lighting, meaning a 4% reduction in total crashes attributable to lighting quality on roads that are already lit.<sup><a href="#fn8" id="fnref8">8</a></sup> Our 3% is below that.

Transportation safety is largely choreographed. Crosswalks are painted. Turns are signed. Bike lanes are striped. The infrastructure tells people where to walk and drive. The locations that need light are known and mapped. This is unlike crime, where participants in the activity do not follow societal rules. A 3% improvement assumes only that verifying whether light reaches those locations, and adjusting when it doesn't, produces a measurable improvement over never checking at all.

## How This Fits the Transportation Safety Framework

Transportation safety investments are funded through federal programs including Safe Streets and Roads for All (SS4A) and the Highway Safety Improvement Program (HSIP). To be eligible, projects must demonstrate that benefits exceed costs. A benefit-cost analysis (BCA) above 1.0 is considered economically justified by FHWA.

At $5/light/year over 10 years, a 20,000-light city invests $1 million. The transportation safety benefit alone is $1.56 million. That is a BCA of 1.56 on a single value component, before counting the other six components in the model. Many projects have been funded at lower BCAs.

Photometrics AI requires no hardware, no installation crews, and no capital budget. Benefits begin in weeks, not months or years. SS4A explicitly identifies street lighting plans, adaptive lighting, and pilot programs for technological advancements as eligible activities. FHWA classifies lighting as a Proven Safety Countermeasure. For cities working to improve transportation safety through their Vision Zero or safety action plans, lighting optimization is a fundable, low-risk investment with measurable returns.

---

<div class="footnotes">

1. <span id="fn1"></span><a href="https://highways.dot.gov/sites/fhwa.dot.gov/files/Lighting_508_0.pdf">FHWA Proven Safety Countermeasures: Lighting</a> (FHWA-SA-21-050) (<a href="https://claude-sources.s3.us-west-2.amazonaws.com/public/fhwa-proven-safety-countermeasures-lighting.pdf">archived copy</a>). Nighttime fatality rate is 3× daytime rate; only 25% of VMT occurs at night. Crash reduction factors: 28% highways, 33-38% intersections, 42% pedestrian crashes at intersections. <a href="#fnref1">↩︎</a>

2. <span id="fn2"></span><a href="https://www.ghsa.org/sites/default/files/2025-07/Pedestrian%20Traffic%20Fatalities%20by%20State%20-%202024%20Data%20-%207.10.25.pdf">GHSA Pedestrian Traffic Fatalities by State: 2024 Preliminary Data</a> (Governors Highway Safety Association, July 2025) (<a href="https://claude-sources.s3.us-west-2.amazonaws.com/public/ghsa-pedestrian-fatalities-2024-data.pdf">archived copy</a>). Analysis of 2023 FARS data: 77% of pedestrian fatalities occur after dark; fatal pedestrian crashes at night rose 84% from 2010 to 2023; pedestrians account for 18% of all traffic deaths. <a href="#fnref2">↩︎</a>

3. <span id="fn3"></span><a href="https://doi.org/10.1016/j.tranpol.2022.02.010">Sanders, R.L., Schneider, R.J., & Proulx, F.R. (2022). "Pedestrian fatalities in darkness: What do we know, and what can be done?"</a> <em>Transport Policy</em>, 120, 23-39 (<a href="https://claude-sources.s3.us-west-2.amazonaws.com/public/sanders-schneider-proulx-pedestrian-fatalities-darkness-2022.pdf">archived copy</a>). Nearly 90% of the increase in pedestrian fatalities since 2009 occurred in darkness; proportion in darkness rising from ~63% in the early 1980s to 76%+; roadway design and operations significantly associated with darkness fatalities. <a href="#fnref3">↩︎</a>

4. <span id="fn4"></span>Photometrics AI analysis of NHTSA FARS data (2001-2024). Each crash classified by actual solar position at crash latitude, longitude, date, and time using the <a href="https://tools.photometrics.ai/#phase">Photometrics AI Phase Calculator</a>. Night defined as sun elevation below −12° (astronomical twilight or darker), not crude clock-time proxy. Fatal crash peaks track sunset through the seasons; non-motorist nighttime fatalities nearly doubled from 2001 to 2024 while motorist nighttime fatalities declined. <a href="#fnref4">↩︎</a>

5. <span id="fn5"></span><a href="https://journals.sagepub.com/doi/10.1177/036063252005000808">Kinzey, B. & Tuenge, J.R. (2020). "Can LED Lighting Improve Roadway Safety?"</a> <em>LD+A</em>, 50(8) (<a href="https://www.energy.gov/sites/prod/files/2020/08/f77/ssl-LDandA-aug20.pdf">PDF</a>). PNNL partnered with DVRPC to study LED conversions across 60+ municipalities in the Philadelphia region. DOE reports no statistically significant difference in vehicle crashes between converted and non-converted municipalities. <a href="#fnref5">↩︎</a>

6. <span id="fn6"></span><a href="https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813403">NHTSA, "The Economic and Societal Impact of Motor Vehicle Crashes, 2019"</a> (DOT HS 813 403) (<a href="https://claude-sources.s3.us-west-2.amazonaws.com/public/nhtsa-crash-costs-2019.pdf">archived copy</a>). Table 15-5: State/local government share of crash costs is $10.948B (3.22% of $339.809B total). <a href="#fnref6">↩︎</a>

7. <span id="fn7"></span><a href="https://data.bls.gov/timeseries/CUUR0000SA0">BLS Consumer Price Index — All Urban Consumers</a> (Series CUUR0000SA0). December 2019: 256.974; December 2025: 324.054; inflation factor: 26.1%. <a href="#fnref7">↩︎</a>

8. <span id="fn8"></span><a href="https://onlinepubs.trb.org/onlinepubs/nchrp/docs/nchrp05-19_litreview.pdf">NCHRP Project 5-19: Review of the Safety Benefits and Other Effects of Roadway Lighting</a> (Rea, Bullough, Fay, Brons, Van Derlofske, Donnell; Lighting Research Center, Rensselaer Polytechnic Institute, 2009) (<a href="https://claude-sources.s3.us-west-2.amazonaws.com/public/nchrp-5-19-roadway-lighting-safety-2009.pdf">archived copy</a>). AMF of 0.96 (4% crash reduction) for arterial segments with existing lighting, using Michigan and Minnesota crash data. <a href="#fnref8">↩︎</a>

9. <span id="fn9"></span><a href="https://www.census.gov/geographies/reference-files/time-series/geo/centers-population.html">US Census Bureau Mean Center of Population, 2020</a> (36.7456°N, 93.4712°W; Hartville, MO). Streetlights turn on at −6° sun elevation (end of civil dusk) and off at −6° ascending (end of nautical dawn). <a href="#fnref9">↩︎</a>

</div>

<script>
window.addEventListener('message', function(e) {
  if (e.data && e.data.iframeHeight) {
    document.querySelectorAll('iframe.chart-embed').forEach(function(f) {
      if (e.data.src.indexOf(f.getAttribute('src').split('/').pop()) !== -1) {
        f.style.height = e.data.iframeHeight + 'px';
      }
    });
  }
});
</script>
