---
title: "How to Use the Phase Calculator"
seo_title: "Phase Calculator Guide: Determine If Streetlights Were On at Any Time and Location"
description: "Step-by-step guide to the free Phase Calculator tool. Upload a CSV of times and locations. Get back the sun's exact position and whether streetlights were on, for every row."
tags:
  - tools
  - transportation-safety
  - data
date: 2026-08-11
---

## The problem

Crime prevention and transportation safety are often cited as reasons to make lighting improvements. Sight is the primary sense drivers, pedestrians, cyclists, and others rely on to navigate roads, streets, highways, bike lanes, crosswalks, and sidewalks safely. Whether the sun or a streetlight was providing visibility at a given moment is central to understanding whether visibility is an underlying factor in crash and crime data. We can't control the sun. We can control street lighting. Finding the patterns in that data can point to lighting improvements that would reduce the frequency and severity of crashes and crime. While there are strong opinions on both sides, the research is inconclusive and conflicting. See here<sup><a href="#fn1" id="fnref1">1</a></sup> and here<sup><a href="#fn2" id="fnref2">2</a></sup> for our favorite examples.

Today, the answer to whether street lighting was providing visibility at the time of an event (often a crime or a crash) is usually a guess. A common tactic is an arbitrary cutoff, like considering after 7 PM to be dark. Another is to check the time of the event against a seasonal, monthly, or daily sunset table. Neither tactic is precise enough. Streetlights begin to provide visibility at the beginning of nautical dusk, when the sun is 6° below the horizon. In San Diego, this time shifts from 5:09 PM on November 27th to 8:29 PM on June 18th. A swing of 3 hours and 21 minutes is simply too wide a range to classify these events accurately.

Much of the research on crashes and crime "in darkness" runs on exactly these kinds of inaccurate guesses. Often events land in the wrong category, and the conclusions drawn from that data are less dependable.

Crash reports have a worse version of the same problem. They follow the Model Minimum Uniform Crash Criteria (MMUCC)<sup><a href="#fn3" id="fnref3">3</a></sup>, which feeds Fatality Analysis Reporting System (FARS) data<sup><a href="#fn4" id="fnref4">4</a></sup>. Officers choose a lighting condition from Daylight, Dawn, Dusk, Dark-Lighted, Dark-Not Lighted, Dark-Unknown Lighting, or Unknown<sup><a href="#fn5" id="fnref5">5</a></sup>. That choice gets made hours after the initial response, from memory. The result regularly misclassifies crashes: daytime crashes logged as dark, dusk and dawn crashes logged as either day or night.

## How the Phase Calculator fixes this problem

The [Phase Calculator](/tools/#phase) replaces a crude estimate or a guess with a calculation of exactly when streetlights begin to provide visibility. Upload a table with latitude, longitude, date, and time for any event anywhere in the world. Get back the sun's phase and whether streetlights should be on, for every row. It is free, it runs in your browser, and it handles files up to 2.5 million rows.

## What the tool calculates

For every row in your file, the Phase Calculator:

1. Finds the correct time zone from the latitude and longitude, so you don't have to supply one.
2. Calculates the sun's elevation angle at that exact place and moment.
3. Classifies the result into a twilight phase.
4. Determines whether streetlights would have been on.

The phase classification follows the same nautical-twilight threshold streetlight photocells use in the field:

| Sun elevation | Phase | Streetlights |
|---|---|---|
| Above 0° | Day | Off |
| 0° to −6° | Civil Dawn / Civil Dusk | Off |
| −6° to −12° | Nautical Dawn / Nautical Dusk | **On** 💡 |
| −12° to −18° | Astronomical Dawn / Astronomical Dusk | **On** 💡 |
| Below −18° | Night | **On** 💡 |

## How to use it

**1. Upload your CSV.**
Go to the [Phase Calculator](/tools/#phase) and drop your file in, or click browse. No sample data on hand? Two ready-to-use files are linked right on the page: a Los Angeles crime dataset and an NHTSA FARS crash dataset.

**2. Map your columns.**
Choose which columns hold latitude and longitude. Then pick a date/time format:
- **Date + Time columns** — one column for the date, one for the time (the LA Crime data layout).
- **Separate Year, Month, Day, Hour, Minute columns** — five distinct fields (the FARS layout).

The tool guesses your columns automatically from their names. Check the guesses before continuing, since a mismatched column produces wrong results silently.

**3. Process.**
Click Process. Large files are split into chunks and processed in parallel, so a multi-million-row file doesn't sit in a single slow pass. A progress indicator shows chunk-by-chunk status.

**4. Download.**
When processing finishes, download the result CSV. It contains every original column plus three new ones.

## What comes back

| Column | Meaning |
|---|---|
| `evSunElevAngle` | Sun elevation in degrees at that place and moment. Positive is above the horizon, negative is below. |
| `evPhase` | The twilight phase from the table above: Day, Civil Dawn/Dusk, Nautical Dawn/Dusk, Astronomical Dawn/Dusk, or Night. |
| `evStreetlightsOn` | `True` or `False` — whether streetlights would have been operating. |

Rows with missing or invalid coordinates, unparseable dates, or coordinates at (0, 0) are flagged with an error phase rather than dropped, so row counts still match your input file.

## Who this is for

Anyone who needs to know lighting conditions at a specific place and time, at scale, without doing it by hand:

- **Civil lighting designers** finding areas with severe crashes or high crime where a lighting change could make a difference.
- **Municipal or utility street lighting managers** prioritizing repair, maintenance, and upgrade budgets against crash and crime hotspots.
- **Crash reconstruction and transportation safety analysts** tagging FARS, state DOT, or local crash records with actual lighting conditions instead of a "dark / not dark" flag reported at the scene.
- **Personal injury and premises liability investigators** establishing whether a streetlight should have been on at the time and location of an incident.
- **Crime analysts and researchers** correlating incident data with lighting conditions across a full dataset in one pass.
- **Journalists and public policy researchers** building the kind of analysis behind our own [crash-mapping work](/insights/crashes-after-dark-map/).
- **Vision Zero and crime prevention professionals** working with city data to determine where and how street lighting improvements can make streets safer.

---

<div class="footnotes">

1. <span id="fn1"></span><a href="https://www.researchgate.net/publication/359578279_Absence_of_Street_Lighting_May_Prevent_Vehicle_Crime_but_Spatial_and_Temporal_Displacement_Remains_a_Concern">Tompson, L., Steinbach, R., Johnson, S.D., Teh, C.S., Perkins, C., Edwards, P., & Armstrong, B. (2022). "Absence of Street Lighting May Prevent Vehicle Crime, but Spatial and Temporal Displacement Remains a Concern."</a> <em>Journal of Quantitative Criminology</em>. Switching street lighting off at midnight was associated with a reduction in night-time theft from vehicles, but theft increased on adjacent streets where lighting remained unchanged, indicating displacement rather than prevention. <a href="#fnref1">↩︎</a>

2. <span id="fn2"></span><a href="https://onlinelibrary.wiley.com/doi/10.1111/1745-9133.70006">MacDonald, J., Chalfin, A., Moritz, M., Wade, B., Mendlein, A., Braga, A., & South, E.C. (2025). "Can Enhanced Street Lighting Improve Public Safety at Scale?"</a> <em>Criminology & Public Policy</em>, 25, 31–62. A citywide upgrade of 34,374 Philadelphia streetlights across 13,275 street segments was associated with a 15% decline in nighttime outdoor crime overall, including a 21% drop in gun crimes. <a href="#fnref2">↩︎</a>

3. <span id="fn3"></span><a href="https://www.nhtsa.gov/traffic-records/model-minimum-uniform-crash-criteria">National Highway Traffic Safety Administration. "Model Minimum Uniform Crash Criteria (MMUCC)."</a> <a href="#fnref3">↩︎</a>

4. <span id="fn4"></span><a href="https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars">National Highway Traffic Safety Administration. "Fatality Analysis Reporting System (FARS)."</a> <a href="#fnref4">↩︎</a>

5. <span id="fn5"></span><a href="https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813525#page=64">National Highway Traffic Safety Administration. Model Minimum Uniform Crash Criteria (MMUCC) Guideline.</a> Lists the Light Condition attribute options used in FARS and other standardized crash reporting. <a href="#fnref5">↩︎</a>

</div>
