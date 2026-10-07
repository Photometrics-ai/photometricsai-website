"""
Test setup: put the sun-phase Lambda layer on sys.path (acc_core imports twilight_core from it)
and expose the fixtures and the optional analysis folder.

Run from the repo root:
    python -m pytest tools/acc-value/tests -q

Tests marked `analysis` also read the prototype's analysis folder (source CSV, polygons) and are
skipped when it isn't present; set ACC_ANALYSIS_DIR to point at it.
"""

import gzip
import os
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[3]
LAYER_DIR = REPO / 'tools' / 'sun-phase' / 'web' / 'layers' / 'deps'
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
ANALYSIS = Path(os.environ.get('ACC_ANALYSIS_DIR', r'C:\Users\aisaa\Downloads\UtilityClimateZones'))

sys.path.insert(0, str(LAYER_DIR))

analysis = pytest.mark.skipif(not ANALYSIS.exists(), reason=f'analysis folder not found: {ANALYSIS}')


@lru_cache(maxsize=None)
def inputs():
    return pd.read_csv(FIXTURES / 'inputs.csv')


@lru_cache(maxsize=None)
def expected():
    return pd.read_csv(FIXTURES / 'expected_value_by_point.csv')


@lru_cache(maxsize=None)
def twilight_fixture():
    with gzip.open(FIXTURES / 'twilight_2018.csv.gz', 'rt') as f:
        return pd.read_csv(f)


@lru_cache(maxsize=None)
def twilight_for(ref_id, lat, lon):
    import acc_core
    return acc_core.twilight_minutes(lat, lon)
