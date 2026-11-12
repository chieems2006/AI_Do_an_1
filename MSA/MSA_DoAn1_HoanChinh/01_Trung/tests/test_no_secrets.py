"""Không có API key trong folder (mẫu key Google bắt đầu bằng 'AIza' hoặc tiền tố khoá tạm của môi trường)."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATTERNS = [re.compile("AI" + "za[0-9A-Za-z_-]{20,}"), re.compile("A" + r"Q\.")]


def test_no_api_key_in_files():
    hits = []
    for dp, _, fs in os.walk(ROOT):
        if "__pycache__" in dp or ".pytest_cache" in dp:
            continue
        for f in fs:
            p = os.path.join(dp, f)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if any(rx.search(txt) for rx in PATTERNS):
                hits.append(p)
    assert hits == []
