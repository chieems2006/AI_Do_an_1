import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for p in [ROOT / "src", ROOT / "src" / "scripts", ROOT / "app", ROOT / "eval"]:
    sys.path.insert(0, str(p))


def pytest_configure(config):
    config.addinivalue_line("markers", "live: gọi Gemini thật (bỏ qua mặc định, chạy bằng -m live)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("-m") and "live" in config.getoption("-m"):
        return
    skip = pytest.mark.skip(reason="test live – chạy bằng: pytest -m live (cần GEMINI_API_KEY/MSA_ENV_FILE)")
    for it in items:
        if "live" in it.keywords:
            it.add_marker(skip)
