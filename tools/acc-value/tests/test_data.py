"""Gate 1: the static data files (prices, seasons, zones) match their sources."""

import json

import numpy as np
import pandas as pd
import pytest

import acc_core
from conftest import ANALYSIS, FIXTURES, analysis, inputs

IOU_MEANS = {'PG&E': 152.20, 'SCE': 147.03, 'SDG&E': 150.93}  # single-year 2026 average total $/MWh
SEASONS = {'PG&E': ('05-01', '10-31', 4416), 'SCE': ('06-01', '09-30', 2928), 'SDG&E': ('05-01', '09-30', 3672)}
COMBOS = {
    'PG&E': ['CZ1', 'CZ2', 'CZ3A', 'CZ3B', 'CZ4', 'CZ5', 'CZ11', 'CZ12', 'CZ13', 'CZ16'],
    'SCE': ['CZ6', 'CZ8', 'CZ9', 'CZ10', 'CZ13', 'CZ14', 'CZ15', 'CZ16'],
    'SDG&E': ['CZ7', 'CZ10', 'CZ14', 'CZ15'],
}


@analysis
def test_prices_bit_identical_to_source_csv():
    prices, components, _ = acc_core.load_prices()
    src = pd.read_csv(ANALYSIS / 'acc' / 'acc2026_hourly_PST.csv', float_precision='round_trip')
    assert len(prices) == 22
    for (iou, cz), g in src.groupby(['iou', 'acc_cz']):
        g = g.sort_values('hour_index')
        assert np.array_equal(prices[(iou, cz)], g[components].to_numpy(np.float64)), (iou, cz)


def test_combo_set_and_iou_means():
    prices, components, _ = acc_core.load_prices()
    assert sorted(prices) == sorted((i, c) for i, cs in COMBOS.items() for c in cs)
    t = components.index('total')
    for (iou, cz), p in prices.items():
        assert p.shape == (8760, 11)
        assert round(p[:, t].mean(), 2) == IOU_MEANS[iou], (iou, cz, p[:, t].mean())


def test_components_sum_to_total():
    prices, components, _ = acc_core.load_prices()
    t = components.index('total')
    for k, p in prices.items():
        assert np.allclose(np.delete(p, t, axis=1).sum(axis=1), p[:, t], atol=1e-6), k


def test_seasons():
    _, _, summer = acc_core.load_prices()
    ts = pd.Timestamp('2018-01-01') + pd.to_timedelta(np.arange(8760), unit='h')
    meta = acc_core.load_meta()['seasons']
    for iou, (start, end, hours) in SEASONS.items():
        s = summer[iou]
        assert s.sum() == hours
        assert ts[s][0].strftime('%m-%d %H') == f'{start} 00' and ts[s][-1].strftime('%m-%d %H') == f'{end} 23'
        assert (np.diff(np.flatnonzero(s)) == 1).all()
        assert meta[iou] == {'summer_start': start, 'summer_end': end, 'summer_hours': hours}


def test_meta_hashes_match_fixture_manifest():
    manifest = json.loads((FIXTURES / 'manifest.json').read_text())
    srcs = acc_core.load_meta()['sources']
    for key in ('acc_model', 'acc_hourly', 'zones'):
        assert srcs[manifest[key]['file']] == manifest[key]['sha256'], key


def test_settings_recorded():
    s = acc_core.load_meta()['settings']
    assert s['cost_test'] == 'TRC' and s['start_year'] == 2026 and s['levelization_years'] == 1
    assert all(v for k, v in s['components_included'].items() if k != 'Final Air Quality Adder')


WHOLESALE = {'Metropolitan Water District of So. Cal', 'Power and Water Resource Pooling Authority',
             'Eastside Power Authority'}


def test_pip_on_zone_points():
    """Each prototype point (point-on-surface of its own polygon) resolves to its own ACC zone, or,
    when its own polygon is non-ACC and overlapped by an IOU zone, to that zone with a note."""
    pts = inputs()
    zones, notes = acc_core.zone_at(pts.latitude, pts.longitude)
    counts = {'own': 0, 'iou_over_pou': 0, 'wholesale_skipped': 0}
    for ref, util, own, z, n in zip(pts.REF_ID, pts.Utility, pts.ACC_ZONE.fillna(''), zones, notes):
        if util in WHOLESALE:
            counts['wholesale_skipped'] += 1
        elif own:
            assert z == own, (ref, util, own, z)
            counts['own'] += 1
        elif z == '':
            assert n == '', (ref, n)
            counts['own'] += 1
        else:
            assert z and util in n, (ref, util, z, n)
            counts['iou_over_pou'] += 1
    print(counts)


def _reference_lookup(lat, lon):
    """Independent implementation of the lookup rule with geopandas, in the polygons' native CRS."""
    import geopandas as gpd
    zones = gpd.read_file(ANALYSIS / 'Intersection_exp_reporoject_elim.gpkg')[['Utility', 'ACC_ZONE', 'geometry']]
    zones = zones[~zones.Utility.isin(WHOLESALE)].reset_index(drop=True)
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lon, lat), crs='EPSG:4326').to_crs(zones.crs)
    j = gpd.sjoin(pts, zones, how='left', predicate='within').sort_values('index_right', kind='stable')
    out_zone, out_note = [], []
    for i in range(len(pts)):
        rows = j.loc[[i]]
        rows = rows[rows.index_right.notna()]
        acc = rows[rows.ACC_ZONE.notna()]
        if not len(rows):
            out_zone.append(None)
            out_note.append('')
        elif len(acc):
            out_zone.append(acc.ACC_ZONE.iloc[0])
            others = sorted(set(rows[rows.ACC_ZONE.isna()].Utility))
            out_note.append('overlaps ' + '; '.join(others) if others else '')
        else:
            out_zone.append('')
            out_note.append('')
    return np.array(out_zone, dtype=object), np.array(out_note, dtype=object), pts, zones


@analysis
def test_pip_agrees_with_geopandas_reference():
    rng = np.random.default_rng(20261007)
    n = 10_000
    lon = np.concatenate([rng.uniform(-124.5, -114.1, n), inputs().longitude])
    lat = np.concatenate([rng.uniform(32.5, 42.0, n), inputs().latitude])
    want_z, want_n, pts, zones = _reference_lookup(lat, lon)
    got_z, got_n = acc_core.zone_at(lat, lon)
    mismatch = np.flatnonzero((got_z != want_z) | (got_n != want_n))
    # Any disagreement must be a boundary tie: within ~1 m of a polygon edge in the native CRS (ftUS).
    if len(mismatch):
        edges = zones.boundary.union_all()
        far = [i for i in mismatch if edges.distance(pts.geometry.iloc[i]) > 3.3]
        assert not far, [(i, got_z[i], want_z[i], got_n[i], want_n[i]) for i in far[:10]]
    print(f'PIP: {len(lat) - len(mismatch)}/{len(lat)} identical, {len(mismatch)} boundary ties; '
          f'{np.sum(want_z != None)} in a polygon, {np.sum(want_n != "")} with an overlap note')  # noqa: E711
