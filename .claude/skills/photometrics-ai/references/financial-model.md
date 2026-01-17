# Financial Model & Methodology

## Summary: Value Per Streetlight Per Year

| Stakeholder | Total Value | Components |
|-------------|-------------|------------|
| **Municipal (SLOO)** | **$61.81** | Asset management + Quality of life |
| **Utility Cost Avoidance** | **$15.48** | ACC-based (energy, capacity, GHG, T&D, losses) |
| **Combined System Value** | **$77.29** | Municipal + Utility |

All values are **Direct, Quantifiable, and Financial** — they show up in budgets, backed by studies and concrete methodologies.

---

## Definitions

**"Direct"** = Benefits go straight to Street Light Owners and Operators (SLOOs), not to other organizations or individuals

**"Quantifiable"** = Measurable using reliable data from nationwide studies (or representative states/cities when national data unavailable)

**"Financial"** = Shows up in a SLOO's budget

**"SLOO"** = Street Light Owners and Operators (cities, counties, state highway departments, IOUs, municipal utilities, cooperatives)

---

## Core Assumption: 40% Energy Savings

Photometrics AI delivers 40% total system energy savings through two mechanisms:

1. **25% through precision design optimization** — Applied dusk-to-dawn. Per-luminaire dimming based on actual geometry, overlapping beam spreads, and Target Lighting Layers. Average operating level: 75% power.

2. **15% through early morning dimming** — Applied 1AM-6AM (~5 hours/night, ~1,826 hours/year). As vehicle miles traveled and pedestrian activity decline, applicable lighting standards decrease. Additional ~34% dimming during these hours in low-speed, low-crime residential areas.

Combined effect: 60% average power (40% savings).

---

## Asset Management Benefits: $42.71/light/year

### Maintenance Savings: $14.00/light/year

**Assumptions:**
- $35/year baseline maintenance cost per streetlight
- L70 life rating: 65,000 hours
- Operating hours: 4,100 hours/year
- 40% energy savings (60% average power)

**Logic:** Reducing power lowers thermal stress, extending LED lifespan by 67%. A 65,000-hour luminaire at 4,100 hrs/year lasts 15.85 years normally. At 60% power, lifespan extends to 26.46 years. Same maintenance cost spread over more years = lower annual cost.

**Calculation:**
```
Baseline annual maintenance: $35
At 60% power: $35 × 0.60 = $21.00
Savings: $35 - $21 = $14.00/light/year
```

---

### Extension of Luminaire Life: $18.05/light/year

**Assumptions:**
- L70 life rating: 100,000 hours
- Total replacement cost: $1,100 (LED $100 + installation $1,000)
- Operating hours: 4,100 hours/year
- 40% energy savings (60% average power)

**Logic:** Lower operating power reduces thermal stress, extending lifespan from 100,000 to 166,667 hours. Spreading $1,100 replacement cost over longer period reduces annualized cost.

**Calculation:**
```
Baseline lifespan: 100,000 / 4,100 = 24.39 years
Annualized cost baseline: $1,100 / 24.39 = $45.11/year

Extended lifespan: 166,667 / 4,100 = 40.65 years
Annualized cost extended: $1,100 / 40.65 = $27.06/year

Savings: $45.11 - $27.06 = $18.05/light/year
```

---

### Energy Savings: $10.66/light/year

**Assumptions:**
- Average LED wattage: 50W
- Operating hours: 4,100 hours/year
- Electric rate: $0.13/kWh (national average)
- Energy savings: 40%

**Calculation:**
```
Baseline annual energy cost: (50W / 1000) × 4,100 hrs × $0.13 = $26.65/year
Savings at 40%: $26.65 × 0.40 = $10.66/light/year
```

**Scaling example:** 3,000 streetlights = ~$32,000 annual savings

---

## Quality of Life Benefits: $19.10/light/year

### Demand Side Management: $2.39/light/year

Based on California's Capacity Bidding Program (CBP) and Emergency Load Reduction Program (ELRP).

**Assumptions (Stockton example, scaled per light):**
- 20,000 streetlights
- Average wattage: 50W
- DR reduction capability: 75% (dimming to 25% during events)
- Event availability: 46.8% (4,100 operating hours ÷ 8,766 annual hours)
- CBP: 20 non-emergency events/year, 3 hours each
- ELRP: 5 emergency events/year, 3 hours each
- CBP Capacity Payment: $100/kW/year
- CBP Energy Payment: $0.10/kWh
- ELRP Payment: $2.00/kWh

**Calculation:**
```
Committed capacity: 20,000 × 50W × 75% × 46.8% = 351 kW

CBP Capacity Payment: 351 kW × $100/kW/year = $35,100/year
CBP Energy Payment: 750 kW × 3 hrs × 20 events × 46.8% × $0.10 = $2,106/year
ELRP Payment: 750 kW × 3 hrs × 5 events × 46.8% × $2.00 = $10,530/year

Total: $35,100 + $2,106 + $10,530 = $47,736/year
Per light: $47,736 / 20,000 = $2.39/light/year
```

**Note:** DR revenue accrues to whoever owns the lights. If utility-owned, the utility receives this value. If municipally-owned, the city receives payments from the utility.

---

### Crime Reduction: $10.81/light/year

**Assumptions:**
- State/local government spending on police, judicial, corrections (2017): $246.7B
- US streetlights: 26.5 million
- Crimes occurring at night: 45%
- Crimes influenced by street lighting: 20%
- Crime reduction from Photometrics AI: 1% (conservative)
- Inflation since 2017: 29%

**Logic:** Only count outdoor nighttime crimes that lighting can influence (excludes fraud, daytime offenses). Conservative 1% reduction assumption.

**Calculation:**
```
Crime cost per streetlight: $246.7B / 26.5M = $9,309/light
Nighttime outdoor crimes: $9,309 × 0.45 × 0.20 = $837.90/light
1% reduction: $837.90 × 0.01 = $8.38/light
Inflation adjusted: $8.38 × 1.29 = $10.81/light/year
```

**Source:** Bureau of Justice Statistics, Justice Expenditure and Employment Extracts 2017

---

### Reduction in Traffic Incidents: $5.90/light/year

**Assumptions:**
- Motor vehicle crash costs to state/local govt (2019): $10.948B
- US streetlights: 26.5 million
- Crashes in darkness: 50%
- Safety improvement from better lighting: 3%

**Logic:** Local governments bear 3.22% of total crash costs ($339.8B) for police, fire, EMS, victim assistance, incident management, roadside furniture damage.

**FHWA Proven Safety Countermeasures — lighting can reduce crashes:**
- 42% for nighttime injury pedestrian crashes at intersections
- 33-38% for nighttime crashes at rural/urban intersections
- 28% for nighttime injury crashes on rural/urban highways

---

## Utility Cost Avoidance: $15.48/light/year

Calculated using the **California Public Utilities Commission's 2024 Avoided Cost Calculator (ACC)** Electric Model v1b, configured for Southern California Edison Climate Zone 10 under the Total Resource Cost test with a 20-year levelization period.

### ACC Methodology

The ACC produces hourly avoided costs that incorporate **all utility cost components**:
- Generation energy
- Generation capacity
- Transmission capacity
- Distribution capacity
- GHG compliance (cap-and-trade + GHG adder with rebalancing)
- Ancillary services
- System losses

### Streetlight Load Profile

For a streetlight operating 4,100 hours annually from dusk to dawn:
- Evening hours (dusk to midnight): ~50% of operating hours, avoided costs average ~$275/MWh
- Overnight hours (midnight to dawn): ~50% of operating hours, avoided costs average ~$150/MWh
- Load-weighted blended avoided cost: ~$212/MWh

### Calculation at 40% Savings

| Component | kWh Saved | ACC Rate | Annual Value |
|-----------|-----------|----------|--------------|
| 25% design optimization (all hours) | 51.25 kWh | $0.212/kWh | $10.87 |
| 15% early morning (1AM-6AM only) | 30.75 kWh | $0.15/kWh | $4.61 |
| **Total (40%)** | **82 kWh** | | **$15.48/light/year** |

**Note:** This is California-specific. Other jurisdictions may have different avoided cost values or no equivalent methodology.

---

## National Energy Impact

**Base assumptions:**
- Average streetlight wattage: 50W
- Operating hours per day: 11.4 hours
- Days per year: 365.25
- US streetlights: 60,000,000
- Average US household annual consumption: 10,715 kWh
- Energy savings: 40%

**Calculation:**
```
a. Annual consumption per streetlight: 50W × 11.4 hrs × 365.25 days / 1000 = 208.19 kWh
b. Total US consumption: 208.19 kWh × 60,000,000 = 12,491.4 GWh
c. Savings at 40%: 12,491.4 GWh × 0.40 = 4,996.56 GWh
d. Equivalent homes: 4,996,560,000 kWh / 10,715 kWh/household = 466,296 homes
```

**Standard phrasing:** "Photometrics AI saves an average of 40% energy on the 60 million streetlights in the US, equivalent to 4,997 GWh annually or the energy consumption of approximately 466,000 homes."

---

## Customer Calculator Approach

For any customer, replace these generic assumptions with actual values:

| Input | Generic Value | Customer Value |
|-------|---------------|----------------|
| Number of streetlights | — | _____ |
| Average wattage | 50W | _____ |
| Electric rate ($/kWh) | $0.13 | _____ |
| Annual maintenance cost/light | $35 | _____ |
| Luminaire + install cost | $1,100 | _____ |
| L70 rating (hours) | 100,000 | _____ |
| Operating hours/year | 4,100 | _____ |

---

## ROI Summary

| Metric | Value |
|--------|-------|
| Value delivered | $61.81/light/year (municipal) |
| Pricing | $3-12/light/year |
| ROI | **<12 months** |
| 50,000-light city annual savings | **$3.1M+** |

Compare to LED retrofits: years to payback, capital-intensive, hardware required.

---

## Direct Unquantifiable Financial Benefits

These are real but harder to assign dollar values:

**Strategic Funding Opportunities**
- SS4A (Safe Streets For All)
- SMART grants
- DOE EECBG and GRIP programs
- DOJ Byrne JAG and COPS grants
- Photometrics AI strengthens grant applications with data-driven evidence

**Liability Reduction**
- Demonstrate purposeful, optimized lighting management
- Respond quickly to ROW changes (new crosswalks, bike lanes)
- Stronger legal position than "grouped standards" or "hasn't been reviewed"

**Resource Optimization**
- Automate routine tasks
- Free lighting professionals for complex/creative work

**Community & Economic Vibrancy**
- NYC nightlife: $35B annually, 300,000 jobs
- 1% increase = $350M economic activity = $31M tax revenue
- $124/streetlight/year in additional tax receipts (NYC example)

**Policy Alignment**
- Vision Zero
- Climate Action Plans
- DarkSky Recognized Codes and Statutes
- Local outdoor lighting ordinances

**Real Estate Value**
- 1-3% property value increase from perceived safety improvements
- 100,000 properties × $300,000 avg × 1% = $300M value increase

---

## Source Documentation

For detailed methodology, exact citations, or defense of calculations, see `references/sources/`:

| File | Content | Key Search Terms |
|------|---------|------------------|
| `nhtsa-crash-costs-2019.pdf` | Motor vehicle crash economic costs | "state and local", "police", "$339.8 billion", "government" |
| `fhwa-lighting-safety-countermeasure.pdf` | FHWA Proven Safety Countermeasures - Lighting | "42%", "33-38%", "28%", "pedestrian", "intersection" |
| `cpuc-acc-documentation-2024.pdf` | California Avoided Cost Calculator methodology | "hourly avoided cost", "generation capacity", "T&D", "PCAF" |
| `us-patent-9894736b2-tll.pdf` | Target Lighting Layer patent (US9894736B2) | "geographic setpoint", "substantive performance", "illumination" |

**When to read these files:**
- Grant reviewer challenges crash reduction methodology → Read FHWA doc
- Need exact citation for $339.8B crash cost → Read NHTSA doc  
- Defending ACC calculation approach → Read CPUC doc
- Patent claims or technical IP questions → Read TLL patent

**Do not load these files** for routine proposals or general questions—the summary data in this file is sufficient.

---

## Quick Reference Citations

**Crash Reduction (FHWA-SA-21-050):**
- 42% reduction for nighttime injury pedestrian crashes at intersections
- 33-38% reduction for nighttime crashes at rural and urban intersections
- 28% reduction for nighttime injury crashes on rural and urban highways
- Source: Elvik, R. and Vaa, T., "Handbook of Road Safety Measures." Oxford, United Kingdom, Elsevier, (2004).

**Crash Costs (NHTSA 2019):**
- Total economic cost: $339.8 billion (2019)
- State/local government share: 3.22% (~$10.948B)
- Includes: police, fire, EMS, victim assistance, incident management

**Avoided Costs (CPUC 2024 ACC):**
- All-inclusive hourly rates bundle: energy, generation capacity, T&D capacity, GHG, ancillary services, losses
- Capacity allocated via Peak Capacity Allocation Factor (PCAF) method
- SCE Climate Zone 10, TRC test, 20-year levelization

**Patent (US9894736B2):**
- Granted: February 13, 2018
- Title: Methods for optimizing street lighting performance using geographic setpoint layers
- Assignee: Target Lighting Layers technology

---

## Additional Sources (Not in /sources/)

- Bureau of Justice Statistics: Justice expenditure extracts 2017
- DOE: 26.5M US streetlights (conservative; 60M used for national impact)
- PG&E: 4,100 operating hours/year
- EIA: National average electric rate $0.13/kWh
- California CBP and ELRP program documentation
- OSRAM: LED thermal stress / lifespan relationship
- Clean Energy Ministerium: Street lighting = 1-3% of electricity demand
