"""
Tests for the yearly twilight schedule (twilight_times.py and its mirrors).

Run from the repo root:
    python -m pytest tools/sun-phase/tests -q
"""

import csv
import importlib.util
import inspect
import io
import os
import tempfile
from functools import lru_cache

import pytest

import twilight_times
from sun_phase_paths import LAYER_DIR, SUN_PHASE_DIR, load_layer_module

YEAR = 2026

LOCATIONS = {
    'riverside': (33.95, -117.40),     # America/Los_Angeles, DST
    'hartville': (36.7456, -93.4712),  # America/Chicago, DST
    'sydney': (-33.87, 151.21),        # Australia/Sydney, southern-hemisphere DST
    'phoenix': (33.45, -112.07),       # America/Phoenix, no DST
    'anchorage': (61.2, -149.9),       # summer days with no nautical twilight (N/A rows)
}


@lru_cache(maxsize=None)
def cli_csv(name):
    """CSV text produced by the CLI's generate_yearly_report."""
    lat, lon = LOCATIONS[name]
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    try:
        twilight_times.generate_yearly_report(lat, lon, YEAR, path)
        with open(path, newline='') as f:
            return f.read()
    finally:
        os.remove(path)


def rows(csv_text):
    return list(csv.DictReader(io.StringIO(csv_text)))


def valid_rows(csv_text):
    return [r for r in rows(csv_text) if r['streetlights_off_time'] != 'N/A']


def clock_hours(hhmm):
    h, m = hhmm.split(':')
    return int(h) + int(m) / 60


@pytest.mark.parametrize('name', LOCATIONS)
def test_rows_single_day_ordering(name):
    """Each row is one calendar day: lights off < sunrise < sunset < lights on."""
    for r in valid_rows(cli_csv(name)):
        assert (r['streetlights_off_time'] < r['sunrise'] < r['sunset']
                < r['streetlights_on_time']), r


def test_riverside_dst_hours():
    """Elapsed hours on ordinary days and on both DST transition days."""
    expected = {
        '2026-01-01': ('06:27', '17:19', '6.45', '6.68', '13.13'),
        '2026-03-07': ('05:45', '18:16', '5.75', '5.73', '11.48'),
        '2026-03-08': ('06:44', '19:17', '5.73', '4.72', '10.45'),  # spring forward
        '2026-10-31': ('06:43', '18:23', '6.72', '5.62', '12.33'),
        '2026-11-01': ('05:43', '17:23', '6.72', '6.62', '13.33'),  # fall back
    }
    by_date = {r['date']: r for r in rows(cli_csv('riverside'))}
    for d, (off, on, morning, evening, total) in expected.items():
        r = by_date[d]
        assert (r['streetlights_off_time'], r['streetlights_on_time'],
                r['streetlights_on_hours_morning'], r['streetlights_on_hours_evening'],
                r['streetlights_on_hours_total']) == (off, on, morning, evening, total), d


def test_rounding_to_utc_midnight_keeps_date():
    """Hartville dusk 2026-01-25 rounds to exactly 00:00 UTC; it must stay on the 25th."""
    r = {r['date']: r for r in rows(cli_csv('hartville'))}['2026-01-25']
    assert (r['streetlights_on_time'], r['streetlights_on_hours_evening']) == ('18:00', '6.00')


@pytest.mark.parametrize('name', LOCATIONS)
def test_evening_hours_in_range(name):
    for r in valid_rows(cli_csv(name)):
        assert 0 <= float(r['streetlights_on_hours_evening']) <= 24, r
        assert 0 <= float(r['streetlights_on_hours_morning']) <= 24, r


@pytest.mark.parametrize('name', LOCATIONS)
def test_total_is_morning_plus_evening(name):
    for r in valid_rows(cli_csv(name)):
        total = float(r['streetlights_on_hours_morning']) + float(r['streetlights_on_hours_evening'])
        assert abs(float(r['streetlights_on_hours_total']) - total) <= 0.011, r


def test_phoenix_no_dst():
    """With no clock changes, elapsed hours equal clock-reading hours."""
    for r in valid_rows(cli_csv('phoenix')):
        assert r['streetlights_on_hours_morning'] == f"{clock_hours(r['streetlights_off_time']):.2f}", r
        assert r['streetlights_on_hours_evening'] == f"{24 - clock_hours(r['streetlights_on_time']):.2f}", r


@pytest.mark.parametrize('name', LOCATIONS)
def test_na_rows_all_na(name):
    for r in rows(cli_csv(name)):
        values = [v for k, v in r.items() if k != 'date']
        if 'N/A' in (r['streetlights_off_time'], r['streetlights_on_time']):
            assert all(v == 'N/A' for v in values), r


@pytest.mark.parametrize('name', ['riverside', 'anchorage'])
def test_gui_processor_matches_cli(name, tmp_path):
    from core.twilight_processor import generate_twilight_with_progress
    lat, lon = LOCATIONS[name]
    path = tmp_path / 'gui.csv'
    stats = generate_twilight_with_progress(lat, lon, YEAR, str(path), lambda *a: None)
    assert path.read_bytes() == cli_csv(name).encode()
    assert stats['total_days'] == 365
    assert stats['valid_days'] + stats['polar_days'] == 365


# ─── Lambda mirror (web/layers/deps/twilight_core.py) ───

MIRRORED = ['find_sun_elevation_time', '_utc_hour_to_local', 'calculate_nautical_times',
            'streetlight_hours', 'twilight_row']


@pytest.fixture(scope='module')
def layer_core():
    return load_layer_module('twilight_core')


@pytest.mark.parametrize('name', LOCATIONS)
def test_lambda_matches_cli(name, layer_core):
    lat, lon = LOCATIONS[name]
    assert layer_core.generate_twilight_csv(lat, lon, YEAR) == cli_csv(name)


def test_copies_in_sync(layer_core):
    for fn in MIRRORED:
        assert inspect.getsource(getattr(layer_core, fn)) == inspect.getsource(getattr(twilight_times, fn)), fn
    assert layer_core.CSV_HEADER == twilight_times.CSV_HEADER
    assert (SUN_PHASE_DIR / 'sun_utils.py').read_bytes() == (LAYER_DIR / 'sun_utils.py').read_bytes()


def test_twilight_api_handler(monkeypatch):
    monkeypatch.syspath_prepend(str(LAYER_DIR))
    spec = importlib.util.spec_from_file_location(
        'twilight_api_handler', SUN_PHASE_DIR / 'web' / 'lambdas' / 'twilight_api' / 'handler.py')
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)
    event = {'queryStringParameters': {'lat': '33.95', 'lon': '-117.40', 'year': str(YEAR)}}
    resp = handler.lambda_handler(event, None)
    assert resp['statusCode'] == 200
    assert '2026-03-08,06:44,07:13,18:48,19:17,5.73,4.72,10.45' in resp['body']
    assert '2026-11-01,05:43,06:13,16:53,17:23,6.72,6.62,13.33' in resp['body']
