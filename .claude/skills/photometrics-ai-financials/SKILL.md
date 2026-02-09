---
name: photometrics-ai-financials
description: Financial model, value calculations, and verified numbers for Photometrics AI. Use when Ari needs help with ROI calculations, proposal budgets, value per light figures, utility cost avoidance, pricing, energy savings math, or any quantitative claims. Triggers on dollar amounts, per-light values, energy savings, market size, pilot pricing, or requests to verify/source a number.
---

# Photometrics AI Financials

**Purpose:** Single source of truth for all financial calculations, quantitative claims, and their derivations.

**Core principle:** Never state a number as fact unless it has verified logic and sources documented here.

---

## Quick Reference: Key Numbers

| Metric | Value | Status |
|--------|-------|--------|
| Municipal value | $51.09/light/year | 🔶 DERIVED |
| Utility cost avoidance | $10.18/light/year | ✅ VERIFIED |
| Combined system value | $61.27/light/year | 🔶 DERIVED |
| Energy savings | 35% (25% eve/pre-dawn + 50% 1-5AM) | 🔶 DERIVED |
| DR revenue (CA) | $2.02/light/year | 🔶 DERIVED |
| Peak reduction | 14-28 kW per 1,000 lights | 🔶 DERIVED |
| Pricing | $3-12/light/year | — |
| ROI timeline | <12 months | 🔶 DERIVED |

**Status Key:**
- ✅ VERIFIED — Backed by cited source
- 🔶 DERIVED — Calculated from verified inputs
- ⚠️ ESTIMATE — Interpolated or approximated
- 🔴 PLACEHOLDER — Needs source; do not cite as fact

---

## Unknown ≠ Zero: Defending Value Estimates

### The Principle

The absence of a precise number does not mean the value is $0. It means the value is somewhere between $0 and some upper bound. An estimate rooted in published studies and documented methodology is almost certainly closer to the real number than zero.

Someone who dismisses a value category is not being conservative. They are implicitly claiming the value is $0 — and that claim requires the same justification as any other.

### Why This Matters

The financial model above contains values at every level of the status system. Skeptical stakeholders — PEs, utility program managers, municipal finance directors — sometimes dismiss categories they can't directly measure or capture. The implicit logic: *"I can't quantify this precisely, so I'll treat it as zero."*

This is analytically wrong. Consider the components of the $51.09/light/year municipal value:

| Component | Value | A skeptic who dismisses this claims... |
|-----------|-------|---------------------------------------|
| Maintenance savings | $4.90 | Reduced thermal stress has zero effect on failure rates |
| Luminaire life extension | $15.76 | Lower operating temperatures don't extend LED life |
| Energy savings | $9.78 | Dimming streetlights saves zero energy |
| Crime reduction | $10.81 | Street lighting has zero relationship to crime |
| Traffic safety | $7.82 | Lighting quality has zero effect on crash rates |
| DR revenue | $2.02 | Grid flexibility from 1 MW of controllable load is worthless |

Each of these dismissals contradicts published research. The question is never "Is this value exactly $10.81?" — it's "Is this value closer to $10.81 or to $0?" When the estimate is built from BJS expenditure data, LAPD crime records, and peer-reviewed methodology, the answer is clear.

### How This Connects to the Status System

| Status | What it means | What a skeptic must argue to dismiss it |
|--------|--------------|----------------------------------------|
| ✅ VERIFIED | Directly sourced from authoritative data | The source is wrong |
| 🔶 DERIVED | Calculated from verified inputs using documented logic | The methodology is wrong AND the real value is $0 |
| ⚠️ ESTIMATE | Interpolated or approximated with stated uncertainty | The approximation is not just imprecise but entirely baseless |
| 🔴 PLACEHOLDER | Needs source — we don't cite these as fact | (Correct to question; we already flag these) |

The status system isn't a weakness to apologize for. DERIVED and ESTIMATE values are honest about their methodology — which makes them more defensible than unstated assumptions of zero.

### The Stakeholder Capture Problem

A common dismissal: *"The municipality can't capture that savings directly."* This confuses value capture with value existence.

Example: A city with unmetered street lighting can't see energy savings on a utility bill. A skeptic concludes the savings don't exist. But the energy reduction is physical — fewer kilowatt-hours consumed, lower thermal stress on components, reduced grid load. The value accrues somewhere: the utility sees lower demand, the grid sees reduced congestion, the luminaires last longer, the atmosphere absorbs less carbon. Inability to invoice for a benefit is not evidence the benefit is zero.

When a stakeholder says "we can't capture that," the correct response is to identify *who does* capture it and whether it still supports the business case. Value that accrues to a different stakeholder is still value — and often still motivates the decision.

### When to Invoke This Principle

- A stakeholder dismisses quality-of-life values (crime, traffic safety) as "soft"
- Someone treats DERIVED or ESTIMATE values as equivalent to PLACEHOLDER
- A PE or engineer rejects ROI because one component can't be directly metered
- A reviewer says "you can't prove the exact number" as grounds for using zero
- Anyone frames the choice as "perfectly measured or worthless"

### Response Framing

When challenged, the structure is:

1. **Acknowledge the uncertainty.** "You're right that $10.81 is an estimate, not a measurement."
2. **Reject the false alternative.** "But the alternative isn't a better number — it's an implicit claim that the value is $0."
3. **Show the methodology.** "Our estimate uses [source], [methodology], [conservative assumptions]. Here's the derivation."
4. **Shift the burden.** "If you believe the value is closer to $0 than to $10.81, what's the basis for that?"
5. **Offer the range.** "Even if you halve every estimate in the model, the ROI is still under 12 months."

---

## Operating Hours: Two Numbers for Two Purposes

Street lights operate dusk-to-dawn, but different calculations require different hour values:

| Value | Use For | Source |
|-------|---------|--------|
| **4,100 hrs/year** | Rate calculations, cost savings, utility billing | PG&E LS-2 tariff (regulatory) |
| **4,165 hrs/year** | Actual energy consumed, CO2 emissions, national impact | Astronomical (11.4 hrs × 365.25 days) |

**Why the difference?**
- **4,100 hours** is the regulatory value embedded in utility tariffs. When calculating dollar savings from reduced consumption, use this number because it matches how utilities bill.
- **4,165 hours** is the astronomical reality of dusk-to-dawn operation. When calculating actual energy consumed or CO2 avoided, use this number because it reflects physics.

**In practice:**
- Energy cost savings: Use 4,100 hrs → 205 kWh/light/year
- National energy impact / CO2: Use 4,165 hrs → 208 kWh/light/year

---

## Reference Files

### ⚠️ CRITICAL: Always Check Numbers Audit First

**Before citing ANY number, read [Numbers Audit](references/numbers-audit.md).**

Each number shows: the claim, derivation logic, source citations, and verification status.

---

- **[Numbers Audit](references/numbers-audit.md)** — Derivation logic and sources for ALL quantitative claims
- **[Financial Model](references/financial-model.md)** — Full methodology for $51.09 municipal + $10.18 utility calculations

---

## Source Documents

Source PDFs and images are in `references/sources/`:

| File | Content |
|------|---------|
| `ledsmaster-street-light-costs.pdf` | LED-specific maintenance costs ($20-$50/yr) |
| `cps-lighting-street-light-costs-2024.pdf` | General street light costs (secondary source) |
| `osram-led-reliability-lifetime-2013.pdf` | OSRAM "Reliability and Lifetime of LEDs" — thermal/Arrhenius |
| `pge-ls2-streetlight-tariff-2026.pdf` | PG&E LS-2 tariff — authoritative 4,100 hours/year source |
| `eia-electric-power-monthly-oct2025.pdf` | EIA national electric rates — $0.1363/kWh source |
| `cpuc-acc-documentation-2024.pdf` | California Avoided Cost Calculator methodology |
| `nhtsa-crash-costs-2019.pdf` | NHTSA crash costs — Table 15-5: $10.948B state/local (3.22%) |
| `fhwa-lighting-safety-countermeasure.pdf` | FHWA crash reduction: 28-42% from lighting |
| `datam-connected-streetlight-market-2026.pdf` | 30% CAGR market growth (Jan 2026) |
| `gis_analysis/streetlight_estimation_results.json` | CA IOU territory totals and utility-owned counts |
| `Lighting the Way for Next-Generation Streetlight Efficiency _ Energized by Edison.pdf` | SCE utility-owned: 450,000 lights (primary source) |
| `sce-cbp-tariff-2024.pdf` | SCE Capacity Bidding Program — $79/kW/year |
| `cpuc-elrp-program-2024.pdf` | CPUC Emergency Load Reduction Program — $2/kWh |
| `streetlighting-demand-response-stockton-ca.pdf` | DR methodology and calculation example |
| `bjs-justice-expenditures-employment-2017.pdf` | BJS $246.7B state/local crime spending (Table 1) |
| `lapd-crime-data-2010-2019-open-data-portal.pdf` | LAPD 2.13M crime records — empirical verification |

---

## Value Breakdown: Municipal ($51.09/light/year)

### Asset Management: $30.44

| Component | Value | Logic |
|-----------|-------|-------|
| Maintenance savings | $4.90 | 🔶 DERIVED — See numbers-audit.md |
| Luminaire life extension | $15.76 | 50% of lights reach EOL; 12→19 yr extension |
| Energy savings | $9.78 | 205 kWh × 35% × $0.1363/kWh |

### Quality of Life: $20.65

| Component | Value | Logic |
|-----------|-------|-------|
| DSM revenue (CA) | $2.02 | CBP ($79/kW/yr) + ELRP ($2/kWh) — verified rates |
| Crime reduction | $10.81 | 1% of lighting-influenced crime cost (conservative; LAPD analysis supports $20.85) |
| Traffic incidents | $7.82 | 3% of darkness crash costs, inflation-adjusted (NHTSA 2019 + 26.1% CPI) |

**DSM Value Attribution:** Can be categorized as municipal benefit (city receives payments), utility benefit (grid flexibility), or quality of life benefit (rate stability, blackout reduction).

---

## Value Breakdown: Utility ($10.18/light/year)

Based on CPUC 2024 ACC Electric Model v1b, Climate Zone 10 (Riverside, CA).

**Key Finding:** Nighttime hours have zero capacity value (Gen Capacity, Transmission, Distribution = $0/MWh). Overnight avoided costs are GHG + Energy only (~$130-150/MWh).

**Dimming Schedule (35% savings):**
| Period | Power Level | Savings |
|--------|-------------|---------|
| Dusk to 1 AM | 75% | 25% |
| 1 AM to 5 AM | 50% | 50% |
| 5 AM to Dawn | 75% | 25% |

**Calculation:** Hour-by-hour ACC rates × hours × dimming factor, using CZ10 twilight data.
- Fleet: 20,000 lights × 50W = 1 MW
- Annual ACC benefit: $203,699
- Per light: **$10.18/light/year**

**Sources:** 2024-ACC-Electric-Model-v1b.xlsb, AccStreetLightingAnalysis.xlsx, cz10_riverside_2026.csv

**Note:** California-specific. Other jurisdictions require different methodology.

---

## Pricing & ROI

### SaaS Pricing: $3-12/light/year

Based on:
- Deployment size (volume discounts)
- Service level (self-service vs managed)
- Feature set (basic vs full dynamic scheduling)

### ROI Calculation

```
Value delivered: $51.09/light/year
Cost: $3-12/light/year
Net benefit: $39.09-48.09/light/year
ROI: <12 months
```

**Example:** 50,000-light city
- Annual value: 50,000 × $51.09 = $2.55M
- Annual cost: 50,000 × $6/light = $300K (mid-range)
- Net savings: $2.25M/year

### Pilot Structure

| Parameter | Value |
|-----------|-------|
| Scope | 1,500 networked luminaires |
| Duration | 10-12 weeks |
| Cost | ~$25,000 USD |

---

## Market Size

### Global Streetlights

| Metric | Value | Status |
|--------|-------|--------|
| Total global (2022) | 300-320M | ✅ VERIFIED |
| Connected (Jan 2026) | ~15% penetration | ⚠️ ESTIMATE |
| Market CAGR | 30% (2024-2031) | ✅ VERIFIED |

### US Streetlights

| Metric | Value | Status |
|--------|-------|--------|
| Conservative (DOE) | 26.5M | ✅ VERIFIED |
| Higher estimate | 60M | 🔴 PLACEHOLDER |

### California Streetlights

#### Baseline: AB 719 / CPUC Data (2013)

The most defensible single source for IOU streetlight counts is the AB 719 bill analysis, which cites data provided by the CPUC to the California Legislature:

| Utility | IOU-Owned | Local Gov't-Owned | Total | Status |
|---------|-----------|-------------------|-------|--------|
| PG&E | 175,585 | 554,000 | 729,585 | ✅ VERIFIED |
| SCE | 653,209 | 115,460 | 768,669 | ✅ VERIFIED |
| SDG&E | 27,981 | 119,469 | 147,450 | ✅ VERIFIED |
| **IOU Total** | **856,775** | **788,929** | **1,645,704** | ✅ VERIFIED |

**Source:** [AB 719 Assembly Bill Analysis (April 2013)](http://www.leginfo.ca.gov/pub/13-14/bill/asm/ab_0701-0750/ab_719_cfa_20130405_164252_asm_comm.html) — data provided by the CPUC.

#### Cross-References

| Source | Claim | Date | Status |
|--------|-------|------|--------|
| [Edison "Lighting the Way"](https://energized.edison.com/stories/lighting-the-way-for-next-generation-streetlight-efficiency) | SCE owns/operates ~450,000 city streetlights | ~2024 | ✅ VERIFIED |
| [PG&E Streetlight Reporting Page](https://www.pge.com/en/contact-us/report-an-issue/report-streetlight-issue.html) | ~670,000 streetlights in PG&E territory | ~2025 | ✅ VERIFIED |
| [LA Bureau of Street Lighting](https://lalights.lacity.org/) | City of LA has ~220,000 streetlights | ~2025 | ✅ VERIFIED |
| [LA County Public Works](https://pw.lacounty.gov/tnl/streetlights/) | LA County maintains ~99,700 streetlights | ~2025 | ✅ VERIFIED |

**SCE note:** The Edison article states SCE owns ~450,000; cities own a comparable number in SCE territory. This implies ~900,000 total in SCE territory today — above the 2013 CPUC baseline of 768,669, suggesting growth and/or broader counting methodology.

**PG&E note:** PG&E's website states "nearly 670,000" total in their territory, below the 2013 CPUC figure of 729,585. This likely reflects city acquisitions of utility-owned lights (per AB 719 programs) removing lights from PG&E's tracked inventory, not a reduction in total lights.

#### Estimation Methodology: Population-Proportional Inflation

To estimate current streetlight counts from the 2013 CPUC baseline, a GIS analysis was performed (January 2026) using territory-specific population growth factors.

**Method:**
1. Spatial join of 9,129 California census tract centroids to CEC utility service territory polygons
2. Population assigned per territory using ACS 2023 5-year tract-level data
3. 2013 population estimated by deflating 2023 tract populations using county-level ACS 2013/2023 growth ratios (counties have stable boundaries across census vintages)
4. AB 719 streetlight counts inflated by each territory's population growth factor
5. Non-IOU territory lights estimated using the IOU-derived lights-per-capita ratio

**Data Sources:**
- **Utility territories:** CEC ElectricLoadServingEntities_IOU_POU (ArcGIS FeatureServer, 50 retail utilities after removing 3 non-retail overlays)
- **Census tracts:** Census TIGERweb ACS2023 boundaries (9,129 tracts)
- **Population:** ACS 2023 5-year (tract level), ACS 2013 5-year (county level for growth factors)
- **Streetlight baseline:** AB 719 Bill Analysis (April 2013), CPUC data

**Data cleaning:** Three non-retail overlay entities were removed to prevent double-counting: Power and Water Resource Pooling Authority (wholesale, overlaps PG&E), Metropolitan Water District of So. Cal (water district, overlaps LADWP), Eastside Power Authority (JPA, overlaps PG&E). After removal, 255 tracts still had dual matches (San Francisco tracts in both PG&E and Hetch Hetchy territory); these were assigned to the first match.

**Reproducibility:** Analysis script at `references/sources/gis_analysis/run_analysis.py`, results at `references/sources/gis_analysis/streetlight_estimation_results.json`.

#### GIS Analysis Results: Population by Territory

| Utility | Pop 2013 (est.) | Pop 2023 | Growth Factor |
|---------|----------------|----------|---------------|
| PG&E | 12,485,771 | 13,200,018 | 1.0572x |
| SCE | 13,173,987 | 13,581,988 | 1.0310x |
| SDG&E | 3,415,983 | 3,570,599 | 1.0453x |
| **IOU Total** | **29,075,741** | **30,352,605** | **1.0439x** |
| Non-IOU (50 munis) | 8,335,520 | 8,636,082 | 1.0361x |
| Unmatched (94 tracts) | — | 254,098 | — |
| **CA Total** | **37,659,206** | **39,242,785** | **1.0421x** |

**California population:** 39.24M (ACS 2023). Previous figure of 52.2M was incorrect.

#### Current Streetlight Estimates (🔶 DERIVED)

| Territory | 2013 CPUC Baseline | Growth | Est. ~2023 | Status |
|-----------|--------------------|--------|------------|--------|
| PG&E | 729,585 | 1.0572x | **771,321** | 🔶 DERIVED |
| SCE | 768,669 | 1.0310x | **792,475** | 🔶 DERIVED |
| SDG&E | 147,450 | 1.0453x | **154,124** | 🔶 DERIVED |
| **IOU Total** | **1,645,704** | | **1,717,920** | 🔶 DERIVED |
| **Non-IOU breakdown (not included in IOU totals):** | | | | |
| — LADWP | — | | 215,827 | ⚠️ ESTIMATE |
| — SMUD | — | | 89,170 | ⚠️ ESTIMATE |
| — Imperial Irrigation District | — | | 22,847 | ⚠️ ESTIMATE |
| — City of Anaheim | — | | 18,948 | ⚠️ ESTIMATE |
| — City of Riverside | — | | 17,245 | ⚠️ ESTIMATE |
| — 45 other munis | — | | 124,755 | ⚠️ ESTIMATE |
| **Non-IOU Subtotal** | — | | **488,792** | ⚠️ ESTIMATE |
| Unmatched areas | — | | 14,382 | ⚠️ ESTIMATE |
| **California Total** | | | **~2,221,000** | ⚠️ ESTIMATE |

**Lights-per-capita ratio (IOU):** 0.0566 (1 light per 17.7 people)

**Non-IOU estimation method:** Applied the IOU lights-per-capita ratio to non-IOU territory populations. This assumes similar streetlight density — a simplification, since urban munis (LADWP) likely have higher density and rural districts lower.

**Top non-IOU utilities (estimated lights):**

| Municipal Utility | Pop 2023 | Est. Lights | Status |
|-------------------|----------|-------------|--------|
| LADWP | 3,813,283 | 215,827 | ⚠️ ESTIMATE |
| SMUD | 1,575,469 | 89,170 | ⚠️ ESTIMATE |
| Imperial Irrigation District | 403,660 | 22,847 | ⚠️ ESTIMATE |
| City of Anaheim | 334,774 | 18,948 | ⚠️ ESTIMATE |
| City of Riverside | 304,697 | 17,245 | ⚠️ ESTIMATE |

**Validation:** LADWP estimate of ~216K matches the known ~220K from the LA Bureau of Street Lighting, supporting the lights-per-capita ratio.

#### Known Limitations

- **Population ≠ streetlights:** The assumption that streetlight density scales linearly with population is a simplification. Urban cores have more lights per capita; rural areas fewer. Highway lighting adds lights without corresponding residential population.
- **2013 baseline age:** The AB 719 data is from 2013. Since then, cities have acquired utility-owned lights (AB 719 programs), new developments have added lights, and some areas may have consolidated. Population growth is a proxy for net new infrastructure.
- **SCE gap:** The SCE estimate (~792K) is below the Edison article's implied ~900K total. This may reflect SCE territory having above-average lighting density, or the Edison figure capturing lights not in the 2013 CPUC count.
- **Non-IOU assumption:** Applying the IOU ratio to munis is approximate. Where known data exists (LADWP ~220K), it should override the estimate.

---

## National Energy Impact

**Claim:** 4,372 GWh saved annually (408,000 homes equivalent)

**Calculation:**
```
Annual kWh per light: 50W × 11.4 hrs × 365.25 = 208.19 kWh
US total (60M lights): 208.19 × 60M = 12,491 GWh
35% savings: 12,491 × 0.35 = 4,372 GWh
Homes equivalent: 4,372,000,000 ÷ 10,715 = 408,000 homes
```

**Status:** 🔶 DERIVED — Depends on 60M lights and 35% savings assumptions

---

## When to Use This Skill

**Use photometrics-financials for:**
- ROI calculations and proposal budgets
- Value per light questions
- Energy savings math
- Market size and penetration data
- Verifying any quantitative claim
- Utility cost avoidance calculations
- Pricing discussions

**Use photometrics-ai (core skill) for:**
- How the product works
- Technical architecture (TLL, optimization engine)
- Competitive positioning
- Go-to-market strategy
- Use cases and applications
