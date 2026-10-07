"""Gate 2: acc_core reproduces the prototype (scripts 01 + 03) and holds its invariants."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest
import pytz

import acc_core
from conftest import expected, inputs, twilight_fixture, twilight_for

NUM = ['hrs_base', 'hrs_ctrl', 'kwh_base', 'kwh_ctrl', 'kwh_trim', 'kwh_dim', 'kwh_saved', 'pct_saved',
       'acc_base', 'acc_trim', 'acc_dim', 'acc_value']
SETTINGS = ['dim_pct', 'deep_dim_pct', 'pc_on_offset_min', 'pc_off_offset_min']


def _minutes(ts):
    return ((pd.to_datetime(ts, utc=True) - pd.Timestamp(acc_core.T0)) // pd.Timedelta('1min')).to_numpy()


def _tw(p):
    return twilight_for(p.REF_ID, p.latitude, p.longitude)


def test_twilight_matches_prototype_all_points():
    tw = twilight_fixture().sort_values(['REF_ID', 'date'])
    bad = []
    for p in inputs().itertuples():
        t = tw[tw.REF_ID == p.REF_ID]
        dawn, dusk = _tw(p)
        if not (np.array_equal(dawn, _minutes(t.dawn_utc)) and np.array_equal(dusk, _minutes(t.dusk_utc))):
            bad.append(p.REF_ID)
    assert not bad, bad[:10]


def _value(p, zone=None, **over):
    """Value one fixture point using the cached twilight; zone defaults to the prototype's ACC_ZONE."""
    s = {k: getattr(p, k) for k in SETTINGS}
    s.update({k: v for k, v in over.items() if k in SETTINGS})
    zone = p.ACC_ZONE if zone is None and isinstance(p.ACC_ZONE, str) else (zone or '')
    status, iou, cz = acc_core.acc_zone_key(zone, p.latitude, p.longitude)
    if status != 'ok':
        return status, None
    per_kw, comp = acc_core.value_per_kw(*_tw(p), iou, cz, **s)
    kw = over.get('baseline_w', p.baseline_w) / 1000 * over.get('fixture_count', p.fixture_count)
    return status, (acc_core.scale(per_kw, kw, iou, cz), {k: v * kw for k, v in comp.items()})


def test_values_match_prototype():
    exp = expected().set_index('REF_ID')
    n_ok = 0
    for p in inputs().itertuples():
        e = exp.loc[p.REF_ID]
        status, out = _value(p)
        assert status == e.acc_status, (p.REF_ID, status, e.acc_status)
        if status != 'ok':
            continue
        r, _ = out
        assert (r['acc_iou'], r['acc_cz']) == (e.acc_iou, e.acc_cz), p.REF_ID
        for k in NUM:
            # the fixture is rounded to 4 dp; allow a half-unit (plus float noise) for exact .5 ties
            assert abs(r[k] - e[k]) <= 5e-5 + 1e-9, (p.REF_ID, k, r[k], e[k])
        n_ok += 1
    assert n_ok == 210


def test_benchmarks():
    results = [_value(p) for p in inputs().itertuples()]
    vals = [out[0]['acc_value'] for status, out in results if status == 'ok']
    assert (round(min(vals), 2), round(float(np.median(vals)), 2), round(max(vals), 2)) == (14.79, 15.03, 15.44)


def _point(ref_id):
    return next(p for p in inputs().itertuples() if p.REF_ID == ref_id)


def _median_point():
    """The ok point whose acc_value is the median (PG&E CZ2 in the prototype)."""
    exp = expected()
    ok = exp[exp.acc_status == 'ok'].sort_values('acc_value')
    return _point(int(ok.REF_ID.iloc[len(ok) // 2]))


def test_jul15_hour_alignment():
    """Jul 15 in Los Angeles-area time: dusk 21:22 PDT = 20:22 PST -> controlled on 0.63 of the 20:00 PST
    hour; photocell on 19:52 PST -> 0.13 of the 19:00 hour; deep dim covers 00:00-04:00 PST."""
    p = _median_point()
    dawn, dusk = _tw(p)
    k = (datetime(2018, 7, 15) - datetime(2018, 1, 1)).days * 24  # 00:00 PST Jul 15
    d = dusk[195] - k * 60                                          # minutes after 00:00 PST Jul 15
    ctrl = acc_core.minute_mask(*acc_core.night_intervals(dawn, dusk)).reshape(8760, 60).mean(axis=1)
    base = acc_core.minute_mask(*acc_core.night_intervals(dawn, dusk, 30, 30)).reshape(8760, 60).mean(axis=1)
    # generic alignment: the controlled hour fraction equals the minutes after dusk in that PST hour
    h = d // 60
    assert ctrl[k + h] == pytest.approx((60 - d % 60) / 60)
    assert base[k + (d - 30) // 60] == pytest.approx((60 - (d - 30) % 60) / 60)
    deep = acc_core.deep_window_mask().reshape(8760, 60).mean(axis=1)
    jul = deep[k + 24:k + 48]  # night of Jul 15->16, 00:00-23:00 PST Jul 16
    assert list(np.flatnonzero(jul)) == [0, 1, 2, 3] and (jul[:4] == 1).all()
    print(f'REF_ID {p.REF_ID}: Jul 15 dusk {d // 60:02d}:{d % 60:02d} PST')


def test_jul15_handoff_example():
    """Find the prototype point whose Jul 15 dusk is 20:22 PST and check the handoff numbers."""
    k = (datetime(2018, 7, 15) - datetime(2018, 1, 1)).days * 24 * 60
    for p in inputs().itertuples():
        dawn, dusk = _tw(p)
        if dusk[195] - k == 20 * 60 + 22:
            ctrl = acc_core.minute_mask(*acc_core.night_intervals(dawn, dusk)).reshape(8760, 60).mean(axis=1)
            base = acc_core.minute_mask(*acc_core.night_intervals(dawn, dusk, 30, 30)).reshape(8760, 60).mean(axis=1)
            assert round(ctrl[k // 60 + 20], 2) == 0.63 and round(base[k // 60 + 19], 2) == 0.13
            return
    pytest.fail('no point with Jul 15 dusk at 20:22 PST')


@pytest.mark.parametrize('day,hours', [('2018-03-11', 3), ('2018-11-04', 5), ('2018-07-15', 4)])
def test_deep_window_dst(day, hours):
    tz = pytz.timezone('America/Los_Angeles')
    start = tz.localize(datetime.fromisoformat(day + 'T01:00'), is_dst=True).astimezone(pytz.UTC)
    m = acc_core.deep_window_mask()
    i = acc_core._minute(start)
    assert m[i] and not m[i - 1]
    run = np.argmin(m[i:])  # minutes until the window closes
    assert run == hours * 60


def test_invariants():
    p = _median_point()
    _, (r, comp) = _value(p)
    assert r['acc_trim'] + r['acc_dim'] == pytest.approx(r['acc_value'])
    assert r['acc_value_summer'] + r['acc_value_winter'] == pytest.approx(r['acc_value'])
    assert r['kwh_base'] == pytest.approx(r['kwh_ctrl'] + r['kwh_saved'])
    assert comp['total'] == pytest.approx(r['acc_value'])
    assert sum(v for k, v in comp.items() if k != 'total') == pytest.approx(r['acc_value'])

    _, (r2, _) = _value(p, baseline_w=2 * p.baseline_w)
    _, (r3, _) = _value(p, fixture_count=2 * p.fixture_count)
    for k in ('acc_value', 'acc_trim', 'acc_dim', 'kwh_saved', 'acc_value_summer'):
        assert r2[k] == pytest.approx(2 * r[k]) and r3[k] == pytest.approx(2 * r[k])
    assert r2['hrs_base'] == r['hrs_base'] and r2['pct_saved'] == pytest.approx(r['pct_saved'])

    _, (nodim, _) = _value(p, dim_pct=0, deep_dim_pct=0)
    assert nodim['acc_dim'] == 0 and nodim['kwh_dim'] == 0
    assert nodim['acc_trim'] == pytest.approx(r['acc_trim'])
    _, (nooff, _) = _value(p, pc_on_offset_min=0, pc_off_offset_min=0)
    assert nooff['acc_trim'] == 0 and nooff['acc_dim'] == pytest.approx(r['acc_dim'])


def test_season_split_independent():
    """Recompute the summer share from script-03-style hourly vectors and calendar dates from the
    metadata (not the stored per-hour flags)."""
    meta = acc_core.load_meta()['seasons']
    prices, components, _ = acc_core.load_prices()
    ts = pd.Timestamp('2018-01-01') + pd.to_timedelta(np.arange(8760), unit='h')
    md = ts.strftime('%m-%d')
    for p in inputs().itertuples():
        status, out = _value(p)
        if status != 'ok':
            continue
        r, _ = out
        dawn, dusk = _tw(p)
        ctrl = acc_core.minute_mask(*acc_core.night_intervals(dawn, dusk))
        base = acc_core.minute_mask(*acc_core.night_intervals(dawn, dusk, p.pc_on_offset_min, p.pc_off_offset_min))
        lvl = np.where(acc_core.deep_window_mask(), 1 - p.deep_dim_pct / 100, 1 - p.dim_pct / 100)
        kw = p.baseline_w / 1000 * p.fixture_count
        hourly = lambda m: m.reshape(8760, 60).mean(axis=1)
        saved = hourly((base & ~ctrl).astype(float)) * kw + hourly(ctrl * (1 - lvl)) * kw
        price = prices[(r['acc_iou'], r['acc_cz'])][:, components.index('total')] / 1000
        s = meta[r['acc_iou']]
        summer = (md >= s['summer_start']) & (md <= s['summer_end'])
        assert r['acc_value_summer'] == pytest.approx((saved * price)[summer].sum(), abs=1e-9), p.REF_ID
        assert r['acc_value_winter'] == pytest.approx((saved * price)[~summer].sum(), abs=1e-9), p.REF_ID


def test_zone_key_rules():
    assert acc_core.acc_zone_key(None, 37, -120)[0] == acc_core.OUTSIDE
    assert acc_core.acc_zone_key('', 37, -120)[0] == acc_core.NO_ZONE
    assert acc_core.acc_zone_key('SCE_CZ05', 34, -119)[0] == acc_core.INVALID_COMBO
    assert acc_core.acc_zone_key('PGE_CZ03', 37.78, -122.42) == ('ok', 'PG&E', 'CZ3A')
    assert acc_core.acc_zone_key('PGE_CZ03', 37.80, -122.27) == ('ok', 'PG&E', 'CZ3B')
    assert acc_core.acc_zone_key('SDGE_CZ07', 32.7, -117.1) == ('ok', 'SDG&E', 'CZ7')


def test_value_light_end_to_end_sf():
    """San Francisco: PG&E wins over the CCSF (Hetch Hetchy) overlap, CZ3A via the SF box."""
    z, n = acc_core.zone_at([37.7793], [-122.4193])
    assert z[0] == 'PGE_CZ03' and 'San Francisco' in n[0]
    status, r, _ = acc_core.value_light(37.7793, -122.4193, 50)
    assert status == 'ok' and r['acc_cz'] == 'CZ3A' and r['acc_value'] > 0
