# ACC Street Light Value

Avoided-cost value of each street light under the **CPUC 2026 Avoided Cost Calculator (ACC) Electric Model v1a** (D.26-09-007): the avoided utility-system cost (TRC perspective, single-year 2026 values, all components) of the energy saved when a photocell-controlled light is replaced by a networked, dimmed schedule. This is an avoided cost to the utility system, not a bill saving to the light's owner.

The hosted tool is the "ACC Value" tab on photometrics.ai/tools. The math lives in `tools/sun-phase/web/layers/deps/acc_core.py` (Lambda layer); this folder holds the data build, fixtures and tests.

## Method

- **Twilight:** −6° nautical dusk/dawn for every 2018 date (the 2026 ACC is built on a 2018 calendar), from `twilight_core.py` (identical to the `twilight_times.py` CLI), minute precision, converted to UTC.
- **Baseline (photocell):** on 30 min before dusk, off 30 min after dawn, full power.
- **Controlled (Photometrics AI):** dusk to dawn at 75% power, and 50% power from 1 to 5 AM local clock (America/Los_Angeles; 3 elapsed hours on the spring-forward night, 5 on fall-back).
- The schedule is fixed (`acc_core.DEFAULTS`, one fixture per row): the tool values Photometrics AI's schedule, so uploads supply only location and wattage, and the API ignores any schedule columns or settings a client sends. `acc_core.value_light()` still takes the settings as arguments, for analysis.
- **ACC hours:** treated as PST (UTC−8) all year, hour-beginning: ACC hour *k* = UTC [2018-01-01 08:00 + *k* h, +1 h). The ACC documentation does not state a time zone; this is an assumption (see methodology text on the tool page).
- **Value** = Σ_k saved kWh(k) × ACC total $/MWh(k) / 1000, split into `acc_trim` (photocell on, controlled off) and `acc_dim` (dimming while on), and into summer/winter by the ACC model's own per-utility TOU seasons (`Losses` sheet): PG&E May 1–Oct 31, SCE Jun 1–Sep 30, SDG&E May 1–Sep 30.
- **Zone:** point-in-polygon against the ACC zone polygons (CEC utility territories ∩ CEC building climate zones, `ACC_ZONE` = `<IOU>_CZ<nn>`).
  - Water/wholesale entities (Metropolitan Water District, PWRPA, Eastside Power Authority) are excluded from the lookup; they overlap retail utilities but don't serve street lighting.
  - Where an IOU zone overlaps a retail POU (e.g. PG&E and CCSF Hetch Hetchy in San Francisco, PG&E and Modesto ID), the IOU wins and `acc_note` names the POU.
  - CZ3 is split 3A (San Francisco box: lat 37.70–37.84, lon −122.53 to −122.35) / 3B (elsewhere); the ACC publishes no boundary.
  - Lights outside PG&E/SCE/SDG&E, or in a utility/zone combination the model doesn't offer (SCE CZ5, PG&E CZ6, SDG&E CZ6, SDG&E CZ8), get no value and are dropped from the output (counted by reason).

## Files

| Path | What |
|---|---|
| `build_data.py` | Builds `layers/deps/acc_data/` (prices npz, zones npz, meta json) from the analysis folder |
| `make_fixtures.py` | Copies the prototype's reference outputs into `tests/fixtures/` |
| `tests/` | Gate tests: data vs sources, PIP vs a geopandas reference, values vs the prototype, invariants |

The analysis folder (outside the repo, default `C:\Users\aisaa\Downloads\UtilityClimateZones`, override with `ACC_ANALYSIS_DIR`) holds the ACC model, the polygons, and the prototype scripts `01_twilight_points.py`, `02_extract_acc.py` (drives Excel), `03_acc_value.py`.

```bash
python -m pytest tools/acc-value/tests -q    # ~2 min; analysis-folder tests skip if it's absent
```

## Performance (measured 2026-10-07)

- Twilight is the cost: ~144 ms per unique location locally (pure-Python root finding, 365 days), plus ~34 ms per valuation.
- Twilight is cached per lat/lon rounded to **3 dp (~110 m)**. On the 210 prototype points this changes `acc_value` by at most $0.00087 (4 dp: $0.00006; 2 dp: $0.00298, and one value changes at the cent), so no value changes at the cent.
- Lambda (2,048 MB): a worst-case 1,000-row chunk with every light at a unique location takes ~229 s. With 1,000-row chunks and Map concurrency 25, a worst-case 50,000-row file (49,961 unique locations) finished end to end in 7 min 57 s. Real inventories share 110 m cells and run faster.
- Limit: 50,000 rows per file.

## Refreshing for a new ACC release

1. Download the new electric model `.xlsb` into the analysis folder and update `02_extract_acc.py` (file name, valid combos, cell addresses if the layout changed). Run it (needs Excel).
2. Rerun `01_twilight_points.py` if the ACC calendar year changed (and update `YEAR`/`T0` in `acc_core.py`), then `03_acc_value.py`.
3. `python tools/acc-value/build_data.py` and `python tools/acc-value/make_fixtures.py`.
4. Update the expected numbers in `tests/test_data.py` (IOU means, seasons) and `tests/test_core.py` (benchmarks), run the tests.
5. Deploy the SAM stack (`tools/sun-phase/web`), then update the tool page's version labels.

If the ACC authors confirm a different time basis than PST, change `T0`/the hour mapping in `acc_core.py` and in `03_acc_value.py`, then refresh fixtures.
