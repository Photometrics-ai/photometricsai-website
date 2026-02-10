# Source Documents Index

PDFs are hosted externally on S3. Key facts are extracted in `numbers-audit.md` and `SKILL.md`.

**S3 Bucket:** `claude-sources` (public read access)

## Financial Sources

| Source | S3 URL | Key Facts |
|--------|--------|-----------|
| CPUC ACC Documentation 2024 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/cpuc-acc-documentation-2024.pdf) | California avoided cost methodology |
| NHTSA Crash Costs 2019 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/nhtsa-crash-costs-2019.pdf) | Table 15-5: $10.948B state/local crash costs |
| BJS Justice Expenditures 2017 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/bjs-justice-expenditures-employment-2017.pdf) | Table 1: $246.7B crime spending |
| EIA Electric Power Monthly Oct 2025 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/eia-electric-power-monthly-oct2025.pdf) | Electric rates by state |

## Maintenance & Equipment

| Source | S3 URL | Key Facts |
|--------|--------|-----------|
| LEDSmaster Street Light Costs | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/ledsmaster-street-light-costs.pdf) | LED maintenance costs ($20-$50/yr) |
| CPS Lighting Costs 2024 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/cps-lighting-street-light-costs-2024.pdf) | Generic maintenance (secondary source) |
| OSRAM LED Reliability 2013 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/osram-led-reliability-lifetime-2013.pdf) | Thermal/Arrhenius relationship |

## Utility Tariffs & Programs

| Source | S3 URL | Key Facts |
|--------|--------|-----------|
| PG&E LS-2 Tariff 2026 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/pge-ls2-streetlight-tariff-2026.pdf) | 4,100 operating hours source |
| Stockton DR Streetlighting | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/streetlighting-demand-response-stockton-ca.pdf) | DR methodology example |

## Safety & Crime

| Source | S3 URL | Key Facts |
|--------|--------|-----------|
| FHWA Lighting Safety | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/fhwa-lighting-safety-countermeasure.pdf) | FHWA crash reduction: 28-42% |
| LAPD Crime Data 2010-2019 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/lapd-crime-data-2010-2019-open-data-portal.pdf) | 2.13M records: 17.1% treatable |
| Crimes While You Sleep | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/Crimes%20that%20Happen%20While%20You%20Sleep%20-%20The%20Sleep%20Judge.pdf) | Nighttime crime patterns |

## Market Data

| Source | S3 URL | Key Facts |
|--------|--------|-----------|
| LA Lights Strategic Plan 2020-2025 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/strategic_plan-compressed.pdf) | 223,000 LA streetlights |
| SCE Streetlight Efficiency | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/Lighting%20the%20Way%20for%20Next-Generation%20Streetlight%20Efficiency%20_%20Energized%20by%20Edison.pdf) | SCE utility-owned: 450,000 lights |
| DataM Connected Streetlight Market | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/datam-connected-streetlight-market-2026.pdf) | Market projections |
| Smalley Consortium LightFair 2013 | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/smalley_consortium_lightfair2013.pdf) | Consortium research |

## Regulatory

| Source | S3 URL | Key Facts |
|--------|--------|-----------|
| AB 719 Bill Analysis | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/AB%20719%20Assembly%20Bill%20-%20Bill%20Analysis.pdf) | California legislation |
| 2024 ACC Documentation v1b | [Link](https://claude-sources.s3.us-west-2.amazonaws.com/2024%20ACC%20Documentation%20v1b.pdf) | Avoided cost methodology (alternate) |

## Local Data (Not Externalized)

These files remain in `references/sources/`:
- `gis_analysis/streetlight_estimation_results.json` — CA IOU territory totals vs utility-owned
