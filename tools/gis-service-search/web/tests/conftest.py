import importlib.util
import os
import sys

SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "lambdas", "shared")
LAMBDAS_DIR = os.path.join(os.path.dirname(__file__), "..", "lambdas")

sys.path.insert(0, os.path.abspath(SHARED_DIR))


def load_handler(lambda_dir_name):
    path = os.path.join(LAMBDAS_DIR, lambda_dir_name, "handler.py")
    spec = importlib.util.spec_from_file_location(f"{lambda_dir_name}_handler_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
