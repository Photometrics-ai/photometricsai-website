"""
Build the static data the ACC Value Lambda ships with (in the sun-phase deps layer):

    acc_data/acc2026_prices.npz   hourly $/MWh, 22 utility/zone combos x 8,760 h x 11 components,
                                  plus a per-utility summer flag per hour (ACC TOU seasons)
    acc_data/acc2026_zones.npz    ACC zone polygons in WGS84 lon/lat, flattened rings
    acc_data/acc2026_meta.json    settings, time basis, season dates, source hashes

Inputs (analysis folder, see README.md):
    acc/acc2026_hourly_PST.csv                  from scripts/02_extract_acc.py (Excel-driven)
    acc/acc2026_settings.json                   settings recorded by 02_extract_acc.py
    ACC_2026/2026-acc-electric-model-v1a.xlsb   'Losses' sheet TOU periods (seasons)
    Intersection_exp_reporoject_elim.gpkg       ACC zone polygons, attribute ACC_ZONE

Usage:
    python tools/acc-value/build_data.py [ANALYSIS_DIR]
"""
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from pyxlsb import convert_date, open_workbook
from shapely.geometry import Polygon

DEFAULT_ANALYSIS = Path(r"C:\Users\aisaa\Downloads\UtilityClimateZones")
OUT = Path(__file__).resolve().parents[1] / "sun-phase" / "web" / "layers" / "deps" / "acc_data"

COMPONENTS = ["ghg_cap_invest", "ghg_adder", "air_quality", "energy", "gen_capacity", "transmission",
              "distribution", "ancillary", "losses", "methane", "total"]
IOUS = ["PG&E", "SCE", "SDG&E"]
SUMMER_TOU = (1, 2, 3)  # Losses sheet: 1-3 Summer Peak/Shoulder/Off-Peak, 4-6 Winter
# The CEC territory layer overlaps. These entities are water/wholesale power pools that don't serve
# retail street lighting, so they are left out of the zone lookup (user decision 2026-10-07): their
# footprints (e.g. MWD covers most of San Diego/Orange County) would otherwise shadow the retail utility.
WHOLESALE = {"Metropolitan Water District of So. Cal", "Power and Water Resource Pooling Authority",
             "Eastside Power Authority"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build_prices(analysis):
    acc = pd.read_csv(analysis / "acc" / "acc2026_hourly_PST.csv", float_precision="round_trip")
    combos, arrays = [], []
    for (iou, cz), g in acc.groupby(["iou", "acc_cz"], sort=False):
        g = g.sort_values("hour_index")
        assert (g.hour_index.to_numpy() == np.arange(8760)).all(), (iou, cz)
        combos.append(f"{iou}|{cz}")
        arrays.append(g[COMPONENTS].to_numpy(dtype=np.float64))
    return np.array(combos), np.stack(arrays)


def read_seasons(xlsb):
    """Per-utility hourly TOU period from the ACC model's 'Losses' sheet -> summer flags."""
    rows = []
    with open_workbook(str(xlsb)) as wb, wb.get_sheet("Losses") as sh:
        cols = None
        for row in sh.rows():
            vals = [c.v for c in row]
            if cols is None:
                if "Timestamp" in vals:
                    t = vals.index("Timestamp")
                    assert vals[t + 1:t + 4] == IOUS, vals[t:t + 4]
                    cols = t
                continue
            ts = vals[cols] if cols < len(vals) else None
            if isinstance(ts, float) and ts > 40000:
                rows.append(vals[cols:cols + 4])
    tou = np.array(rows, dtype=np.float64)
    assert tou.shape == (8760, 4), tou.shape
    start = convert_date(tou[0, 0])
    assert start.isoformat() == "2018-01-01T00:00:00", start
    assert np.allclose(np.diff(tou[:, 0]), 1 / 24, atol=1e-6)
    summer = np.isin(tou[:, 1:].T, SUMMER_TOU)  # (3, 8760)
    return summer


def season_dates(summer):
    ts = pd.Timestamp("2018-01-01") + pd.to_timedelta(np.arange(8760), unit="h")
    out = {}
    for iou, s in zip(IOUS, summer):
        idx = np.flatnonzero(s)
        assert (np.diff(idx) == 1).all(), f"{iou} summer is not one contiguous block"
        out[iou] = {"summer_start": ts[idx[0]].strftime("%m-%d"), "summer_end": ts[idx[-1]].strftime("%m-%d"),
                    "summer_hours": int(len(idx))}
    return out


def build_zones(analysis):
    g = gpd.read_file(analysis / "Intersection_exp_reporoject_elim.gpkg")[["Utility", "ACC_ZONE", "geometry"]]
    assert WHOLESALE <= set(g.Utility), WHOLESALE - set(g.Utility)
    g = g[~g.Utility.isin(WHOLESALE)].to_crs("EPSG:4326").reset_index(drop=True)
    codes = sorted(z for z in g.ACC_ZONE.dropna().unique())
    code_index = {c: i for i, c in enumerate(codes)}
    utilities = sorted(g.Utility.unique())
    coords, ring_start, ring_poly, poly_zone, bbox = [], [], [], [], []
    n = 0
    for pi, (zone, geom) in enumerate(zip(g.ACC_ZONE, g.geometry)):
        polys = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
        for p in polys:
            for ring in [p.exterior, *p.interiors]:
                xy = np.asarray(ring.coords, dtype=np.float64)
                coords.append(xy)
                ring_start.append(n)
                ring_poly.append(pi)
                n += len(xy)
        poly_zone.append(-1 if zone is None or pd.isna(zone) else code_index[zone])
        bbox.append(geom.bounds)
    ring_start.append(n)
    return dict(zone_codes=np.array(codes), poly_zone=np.array(poly_zone, dtype=np.int16),
                utilities=np.array(utilities), poly_util=np.array([utilities.index(u) for u in g.Utility], dtype=np.int16),
                poly_bbox=np.array(bbox, dtype=np.float64), ring_start=np.array(ring_start, dtype=np.int64),
                ring_poly=np.array(ring_poly, dtype=np.int32), coords=np.concatenate(coords))


def main(analysis):
    OUT.mkdir(parents=True, exist_ok=True)
    combos, prices = build_prices(analysis)
    xlsb = analysis / "ACC_2026" / "2026-acc-electric-model-v1a.xlsb"
    summer = read_seasons(xlsb)
    np.savez_compressed(OUT / "acc2026_prices.npz", combos=combos, components=np.array(COMPONENTS),
                        prices=prices, season_ious=np.array(IOUS), summer=summer)
    np.savez_compressed(OUT / "acc2026_zones.npz", **build_zones(analysis))

    settings = json.loads((analysis / "acc" / "acc2026_settings.json").read_text())
    meta = {
        "acc_version": "CPUC 2026 ACC Electric Model v1a (D.26-09-007)",
        "settings": settings,
        "calendar_year": 2018,
        "time_basis": "PST (UTC-8) all year, hour-beginning; ACC hour k = UTC [2018-01-01 08:00 + k h, +1 h)",
        "seasons": season_dates(summer),
        "season_source": "ACC model 'Losses' sheet TOU periods (2000 vintage TOU periods); TOU 1-3 = summer",
        "zones": {"excluded_wholesale": sorted(WHOLESALE),
                  "overlap_rule": "an ACC (IOU) zone polygon wins over an overlapping non-ACC polygon; acc_note names it"},
        "sources": {p.name: sha256(p) for p in [
            xlsb, analysis / "acc" / "acc2026_hourly_PST.csv", analysis / "Intersection_exp_reporoject_elim.gpkg"]},
    }
    (OUT / "acc2026_meta.json").write_text(json.dumps(meta, indent=2, default=str) + "\n")
    print(json.dumps(meta["seasons"], indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ANALYSIS)
