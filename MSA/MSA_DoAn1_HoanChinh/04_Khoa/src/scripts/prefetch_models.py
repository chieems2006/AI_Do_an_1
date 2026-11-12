# repo: scripts/prefetch_models.py
"""Tải trước trọng số các model trong REGISTRY (chạy nền), ghi dim/params hoặc lỗi ra results/prefetch_models.json."""
import json, sys, time, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung
from msa.embed.image_embedders import get_embedder, available_models  # noqa
out = {}
names = sys.argv[1:] or available_models()
for n in names:
    t = time.time()
    try:
        e = get_embedder(n)
        out[n] = {"ok": True, **e.info(), "load_s": round(time.time() - t, 1)}
        del e
    except Exception as ex:
        out[n] = {"ok": False, "error": f"{type(ex).__name__}: {ex}"[:500], "trace": traceback.format_exc()[-1500:]}
    print(n, json.dumps({k: v for k, v in out[n].items() if k != "trace"}, ensure_ascii=False), flush=True)
    (ROOT / "results" / "prefetch_models.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
