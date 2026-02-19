import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def main_module():
    module_path = Path(__file__).resolve().parents[1] / "__main__.py"
    spec = importlib.util.spec_from_file_location("errol_main", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load __main__.py for testing.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
