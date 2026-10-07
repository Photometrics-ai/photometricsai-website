"""
Freeze the prototype's reference outputs as test fixtures.

The prototype lives outside the repo (analysis folder, see README.md):
    scripts/01_twilight_points.py  -> twilight/twilight_points_2018.csv
    scripts/03_acc_value.py        -> acc/acc2026_value_by_point.csv
Rerun those first, then this script copies the parts the tests need into tests/fixtures/.

Usage:
    python tools/acc-value/make_fixtures.py [ANALYSIS_DIR]
"""
import gzip
import hashlib
import json
import shutil
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

DEFAULT_ANALYSIS = Path(r"C:\Users\aisaa\Downloads\UtilityClimateZones")
FIXTURES = Path(__file__).resolve().parent / "tests" / "fixtures"

INPUT_COLS = ["REF_ID", "latitude", "longitude", "Utility", "ACC_ZONE", "baseline_w", "fixture_count",
              "dim_pct", "deep_dim_pct", "pc_on_offset_min", "pc_off_offset_min"]
RESULT_COLS = ["REF_ID", "hrs_base", "hrs_ctrl", "kwh_base", "kwh_ctrl", "kwh_trim", "kwh_dim",
               "kwh_saved", "pct_saved", "acc_status", "acc_iou", "acc_cz", "acc_base",
               "acc_trim", "acc_dim", "acc_value"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(analysis):
    FIXTURES.mkdir(parents=True, exist_ok=True)
    pts = gpd.read_file(analysis / "AccZone_pts.gpkg")
    pts[INPUT_COLS].sort_values("REF_ID").to_csv(FIXTURES / "inputs.csv", index=False)

    val = pd.read_csv(analysis / "acc" / "acc2026_value_by_point.csv")
    val[RESULT_COLS].sort_values("REF_ID").to_csv(FIXTURES / "expected_value_by_point.csv", index=False)

    tw = pd.read_csv(analysis / "twilight" / "twilight_points_2018.csv",
                     usecols=["REF_ID", "date", "dawn_utc", "dusk_utc"])
    with gzip.open(FIXTURES / "twilight_2018.csv.gz", "wt", newline="") as f:
        tw.to_csv(f, index=False)

    shutil.copy2(analysis / "acc" / "acc2026_settings.json", FIXTURES / "acc2026_settings.json")

    sources = {
        "acc_model": analysis / "ACC_2026" / "2026-acc-electric-model-v1a.xlsb",
        "acc_hourly": analysis / "acc" / "acc2026_hourly_PST.csv",
        "zones": analysis / "Intersection_exp_reporoject_elim.gpkg",
        "points": analysis / "AccZone_pts.gpkg",
        "twilight": analysis / "twilight" / "twilight_points_2018.csv",
        "value_by_point": analysis / "acc" / "acc2026_value_by_point.csv",
    }
    manifest = {k: {"file": p.name, "sha256": sha256(p)} for k, p in sources.items()}
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote fixtures to {FIXTURES}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ANALYSIS)
