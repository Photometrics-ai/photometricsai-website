"""
Test setup: put tools/sun-phase on sys.path (the CLI/GUI modules import each
other as top-level modules) and expose the Lambda layer's twilight_core.
"""

import importlib.util
import sys
from pathlib import Path

SUN_PHASE_DIR = Path(__file__).resolve().parent.parent
LAYER_DIR = SUN_PHASE_DIR / 'web' / 'layers' / 'deps'

sys.path.insert(0, str(SUN_PHASE_DIR))


def load_layer_module(name):
    """Load a module from the Lambda layer by path, under a distinct name."""
    spec = importlib.util.spec_from_file_location(f'layer_{name}', LAYER_DIR / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
