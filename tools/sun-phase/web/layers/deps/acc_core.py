"""
ACC Core - avoided-cost value of a street light under the CPUC 2026 Avoided Cost Calculator.

Port of the prototype valuation (analysis folder scripts/03_acc_value.py, see tools/acc-value/README.md);
tools/acc-value/tests reproduces the prototype's outputs exactly.

Everything is put on one UTC minute grid covering the ACC year:
    2018-01-01 08:00 UTC (= 00:00 PST) to 2019-01-01 08:00 UTC, 525,600 minutes = 8,760 ACC hours.
ACC hour k (PST all year, hour-beginning) = UTC minutes [k*60, k*60+60) on this grid.

Schedules per light (-6 deg nautical dawn/dusk from twilight_core, 2018 calendar):
    baseline (photocell): on pc_on_offset_min before dusk, off pc_off_offset_min after dawn, 100% power
    controlled:           on at dusk, off at dawn; power = 1 - dim_pct/100,
                          except 1-5 AM local clock (America/Los_Angeles) = 1 - deep_dim_pct/100
Value = sum over hours of saved kWh x ACC $/MWh / 1000, split into
    trim = energy from hours the photocell is on but the controlled light is off (full power)
    dim  = energy reduction while both are on
and into summer/winter by the ACC model's own per-utility TOU seasons.
The value is linear in kW, so it is computed per 1 kW and scaled.
"""

import json
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytz
from timezonefinder import TimezoneFinder

from twilight_core import calculate_nautical_times

DATA_DIR = Path(__file__).resolve().parent / 'acc_data'
YEAR = 2018                                   # the 2026 ACC is built on the 2018 calendar
T0 = datetime(2018, 1, 1, 8, tzinfo=pytz.UTC)  # 2018-01-01 00:00 PST
N_HOURS = 8760
N_MIN = N_HOURS * 60
LOCAL_TZ = 'America/Los_Angeles'
DEEP_START_H, DEEP_END_H = 1, 5               # deep-dim window, local clock
SF_BOX = (37.70, 37.84, -122.53, -122.35)     # San Francisco (Climate Zone 3A per ACC docs)
INVALID = {'SCE_CZ05', 'PGE_CZ06', 'SDGE_CZ06', 'SDGE_CZ08'}  # combos the ACC model doesn't offer
IOU = {'PGE': 'PG&E', 'SCE': 'SCE', 'SDGE': 'SDG&E'}

DEFAULTS = {'fixture_count': 1, 'dim_pct': 25, 'deep_dim_pct': 50,
            'pc_on_offset_min': 30, 'pc_off_offset_min': 30}

# Statuses for lights that get no value (dropped from the output)
OUTSIDE = 'outside_acc_area'          # not inside any utility/climate-zone polygon
NO_ZONE = 'no_acc_zone'               # inside a POU / non-ACC utility territory
INVALID_COMBO = 'combo_not_in_acc_model'

RESULT_FIELDS = ['acc_iou', 'acc_cz', 'hrs_base', 'hrs_ctrl', 'kwh_base', 'kwh_ctrl', 'kwh_trim',
                 'kwh_dim', 'kwh_saved', 'pct_saved', 'acc_base', 'acc_trim', 'acc_dim', 'acc_value',
                 'acc_value_summer', 'acc_value_winter']


# ---------------------------------------------------------------- static data

@lru_cache(maxsize=None)
def load_prices():
    """{(iou, cz): (8760, n_components) $/MWh}, component names, {iou: (8760,) bool summer}."""
    d = np.load(DATA_DIR / 'acc2026_prices.npz')
    prices = {tuple(c.split('|')): d['prices'][i] for i, c in enumerate(d['combos'])}
    summer = {iou: d['summer'][i] for i, iou in enumerate(d['season_ious'])}
    return prices, list(d['components']), summer


@lru_cache(maxsize=None)
def load_meta():
    return json.loads((DATA_DIR / 'acc2026_meta.json').read_text())


@lru_cache(maxsize=None)
def load_zones():
    d = dict(np.load(DATA_DIR / 'acc2026_zones.npz'))
    rs, coords = d['ring_start'], d['coords']
    edges = {}  # polygon index -> (x1, y1, x2, y2) over all its rings (even-odd handles holes)
    for r, p in enumerate(d['ring_poly']):
        xy = coords[rs[r]:rs[r + 1]]
        e = (xy[:-1, 0], xy[:-1, 1], xy[1:, 0], xy[1:, 1])
        edges.setdefault(int(p), []).append(e)
    edges = {p: tuple(np.concatenate(parts) for parts in zip(*es)) for p, es in edges.items()}
    utils = [str(u) for u in d['utilities']]
    poly_util = [utils[i] for i in d['poly_util']]
    return [str(c) for c in d['zone_codes']], d['poly_zone'], poly_util, d['poly_bbox'], edges


# ---------------------------------------------------------------- zones

def _inside(px, py, edges, block=2_000_000):
    """Even-odd ray cast of points against one polygon's edges."""
    x1, y1, x2, y2 = edges
    inside = np.zeros(len(px), dtype=bool)
    step = max(1, block // max(1, len(px)))
    for i in range(0, len(x1), step):
        a, b, c, d = x1[i:i + step, None], y1[i:i + step, None], x2[i:i + step, None], y2[i:i + step, None]
        crosses = (b > py) != (d > py)
        with np.errstate(divide='ignore', invalid='ignore'):
            xint = (c - a) * (py - b) / (d - b) + a
        inside ^= (np.count_nonzero(crosses & (px < xint), axis=0) % 2).astype(bool)
    return inside


def zone_at(lat, lon):
    """ACC_ZONE per point and a note on overlapping territories.

    Returns (zones, notes): zones[i] is e.g. 'PGE_CZ12', '' inside a utility with no ACC zone (POU,
    PacifiCorp, ...), or None outside every polygon. The CEC territory layer overlaps (wholesale/water
    entities are already excluded at build time); where an ACC zone polygon overlaps a non-ACC utility,
    the ACC zone wins and notes[i] names the other utility. Ties between ACC polygons go to the first.
    """
    lat, lon = np.asarray(lat, dtype=np.float64), np.asarray(lon, dtype=np.float64)
    codes, poly_zone, poly_util, bbox, edges = load_zones()
    hits = [[] for _ in range(len(lat))]
    for p in range(len(poly_zone)):
        x0, y0, x1, y1 = bbox[p]
        cand = np.flatnonzero((lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1))
        if len(cand):
            for i in cand[_inside(lon[cand], lat[cand], edges[p])]:
                hits[i].append(p)
    zones = np.full(len(lat), None, dtype=object)
    notes = np.full(len(lat), '', dtype=object)
    for i, hs in enumerate(hits):
        if not hs:
            continue
        acc = [p for p in hs if poly_zone[p] >= 0]
        if acc:
            zones[i] = codes[poly_zone[acc[0]]]
            others = sorted({poly_util[p] for p in hs if poly_zone[p] < 0})
            if others:
                notes[i] = 'overlaps ' + '; '.join(others)
        else:
            zones[i] = ''
    return zones, notes


def acc_zone_key(acc_zone, lat, lon):
    """ACC_ZONE + location -> (status, iou, cz). status is 'ok' or a drop reason."""
    if acc_zone is None:
        return OUTSIDE, None, None
    if not acc_zone:
        return NO_ZONE, None, None
    if acc_zone in INVALID:
        return INVALID_COMBO, None, None
    iou, cz = acc_zone.split('_CZ')
    cz = f'CZ{int(cz)}'
    if cz == 'CZ3':
        in_sf = SF_BOX[0] <= lat <= SF_BOX[1] and SF_BOX[2] <= lon <= SF_BOX[3]
        cz = 'CZ3A' if in_sf else 'CZ3B'
    return 'ok', IOU[iou], cz


# ---------------------------------------------------------------- schedules

_tf = None


def _minute(dt):
    return int((dt - T0) // timedelta(minutes=1))


def twilight_minutes(lat, lon):
    """Nautical dawn and dusk for each 2018 date as integer minutes from T0 (UTC grid).

    Uses twilight_core (identical to the twilight_times.py CLI). Returns (dawn, dusk) int arrays,
    or None if any date has no -6 deg crossing (never in California).
    """
    global _tf
    if _tf is None:
        _tf = TimezoneFinder()
    tz = pytz.timezone(_tf.timezone_at(lat=lat, lng=lon))
    dawn, dusk = [], []
    d = date(YEAR, 1, 1)
    while d.year == YEAR:
        k, w, _, _ = calculate_nautical_times(lat, lon, d, tz)
        if not (k and w):
            return None
        dusk.append(_minute(k.astimezone(pytz.UTC)))
        dawn.append(_minute(w.astimezone(pytz.UTC)))
        d += timedelta(days=1)
    return np.array(dawn), np.array(dusk)


def minute_mask(starts, ends):
    """Boolean minute mask for [start, end) intervals, clipped to the ACC year."""
    d = np.zeros(N_MIN + 1, dtype=np.int32)
    s, e = np.clip(starts, 0, N_MIN), np.clip(ends, 0, N_MIN)
    keep = e > s
    np.add.at(d, s[keep], 1)
    np.add.at(d, e[keep], -1)
    return np.cumsum(d)[:N_MIN] > 0


def night_intervals(dawn, dusk, on_early=0, off_late=0):
    """Lit intervals: open night before first dawn, dusk(d)->dawn(d+1), last dusk->end.
    Offsets are whole minutes (the grid resolution); fractional inputs are rounded."""
    on_early, off_late = int(round(on_early)), int(round(off_late))
    starts = np.concatenate([[-10**9], dusk - on_early])
    ends = np.concatenate([dawn + off_late, [10**9]])
    return starts, ends


@lru_cache(maxsize=None)
def deep_window_mask():
    """1-5 AM local clock each night. On the fall-back date 1 AM occurs twice; the controller
    starts at the first (daylight-time) 1 AM, so that window is 5 elapsed hours. On the
    spring-forward date it is 3 elapsed hours."""
    tz = pytz.timezone(LOCAL_TZ)
    starts, ends = [], []
    d = date(2017, 12, 31)
    while d <= date(2019, 1, 1):
        for h, out in ((DEEP_START_H, starts), (DEEP_END_H, ends)):
            local = tz.localize(datetime(d.year, d.month, d.day, h), is_dst=True)
            out.append(_minute(local.astimezone(pytz.UTC)))
        d += timedelta(days=1)
    m = minute_mask(np.array(starts), np.array(ends))
    m.flags.writeable = False
    return m


def _hourly(m):
    """Fraction of each ACC hour (mean over its 60 minutes)."""
    return m.reshape(N_HOURS, 60).mean(axis=1)


# ---------------------------------------------------------------- valuation

def value_per_kw(dawn, dusk, iou, cz, dim_pct, deep_dim_pct, pc_on_offset_min, pc_off_offset_min):
    """Value of a 1 kW light. Returns (fields, component $ dict); kW-proportional fields scale linearly."""
    prices, components, summer = load_prices()
    pr = prices[(iou, cz)] / 1000                                 # $/kWh, (8760, n_components)
    total = pr[:, components.index('total')]
    ctrl = minute_mask(*night_intervals(dawn, dusk))
    base = minute_mask(*night_intervals(dawn, dusk, pc_on_offset_min, pc_off_offset_min))
    lvl = np.where(deep_window_mask(), 1 - deep_dim_pct / 100, 1 - dim_pct / 100)

    b_h = _hourly(base.astype(float))
    c_h = _hourly(ctrl.astype(float))
    trim_h = _hourly((base & ~ctrl).astype(float))                # kWh per hour at 1 kW
    dim_h = _hourly(ctrl * (1 - lvl))
    saved_h = trim_h + dim_h
    s = summer[iou]

    f = dict(hrs_base=b_h.sum(), hrs_ctrl=c_h.sum(),
             kwh_base=b_h.sum(), kwh_ctrl=_hourly(ctrl * lvl).sum(),
             kwh_trim=trim_h.sum(), kwh_dim=dim_h.sum(),
             acc_base=(b_h * total).sum(), acc_trim=(trim_h * total).sum(), acc_dim=(dim_h * total).sum(),
             acc_value_summer=(saved_h * total)[s].sum(), acc_value_winter=(saved_h * total)[~s].sum())
    comp = dict(zip(components, saved_h @ pr))
    return f, comp


KW_FIELDS = ['kwh_base', 'kwh_ctrl', 'kwh_trim', 'kwh_dim', 'acc_base', 'acc_trim', 'acc_dim',
             'acc_value_summer', 'acc_value_winter']


def scale(per_kw, kw, iou, cz):
    """Per-kW fields -> one light's output fields (RESULT_FIELDS order)."""
    r = {k: (v * kw if k in KW_FIELDS else v) for k, v in per_kw.items()}
    r['kwh_saved'] = r['kwh_trim'] + r['kwh_dim']
    r['pct_saved'] = 100 * r['kwh_saved'] / r['kwh_base'] if r['kwh_base'] else 0.0
    r['acc_value'] = r['acc_trim'] + r['acc_dim']
    r['acc_iou'], r['acc_cz'] = iou, cz
    return {k: r[k] for k in RESULT_FIELDS}


def value_light(lat, lon, baseline_w, acc_zone=None, **settings):
    """Value one light end to end (zone lookup, twilight, schedules). For tests and small jobs.

    Returns (status, fields, components). fields/components are None unless status == 'ok'.
    """
    s = {**DEFAULTS, **{k: v for k, v in settings.items() if v is not None}}
    if acc_zone is None:
        acc_zone = zone_at([lat], [lon])[0][0]
    status, iou, cz = acc_zone_key(acc_zone, lat, lon)
    if status != 'ok':
        return status, None, None
    tw = twilight_minutes(lat, lon)
    per_kw, comp = value_per_kw(*tw, iou, cz, s['dim_pct'], s['deep_dim_pct'],
                                s['pc_on_offset_min'], s['pc_off_offset_min'])
    kw = baseline_w / 1000 * s['fixture_count']
    return status, scale(per_kw, kw, iou, cz), {k: v * kw for k, v in comp.items()}
