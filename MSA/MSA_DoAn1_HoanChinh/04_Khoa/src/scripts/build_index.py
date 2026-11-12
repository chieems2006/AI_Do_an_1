# repo: scripts/build_index.py
"""US_29 – Trích embedding toàn danh mục + build FAISS IndexFlatIP, đo thời gian build & truy vấn.

Ví dụ:
    python src/scripts/build_index.py --model clip_b16 --out indexes/clip_b16            # embed lại từ đầu (đo build thật)
    python src/scripts/build_index.py --model clip_b16 --out indexes/clip_b16 --reuse-cache
    python src/scripts/build_index.py --model dummy --catalog <parquet> --image-root <dir> --out /tmp/x  (test)
Kết quả: <out>/{index.faiss, embeddings.npy, meta.parquet, config.json} + results/build_index_<model>.json
Latency truy vấn đo trên ảnh đã nạp sẵn vào RAM (không tính đọc file), ≥3 lần, lấy median.
"""
from __future__ import annotations
import os

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from msa.embed.image_embedders import get_embedder, load_image, set_threads  # noqa: E402
from msa.search.visual import VisualSearcher, build_meta  # noqa: E402

SHARED = Path(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))


def build(model: str, catalog: Path, image_root: Path, out: Path, tau_v: float, gate_tau: float, reuse_cache: bool,
          n_lat: int = 30, rep: int = 3, batch: int = 32, query_csv: Path | None = None) -> dict:
    set_threads(2)
    import faiss

    out.mkdir(parents=True, exist_ok=True)
    cat = pd.read_parquet(catalog)
    meta = build_meta(cat, image_root)
    t_all = time.perf_counter()
    t = time.perf_counter(); emb = get_embedder(model); load_s = time.perf_counter() - t
    cache = ROOT / "cache" / f"{model}_catalog.npy"; cache_ids = ROOT / "cache" / f"{model}_catalog_ids.json"
    used_cache = False
    t = time.perf_counter()
    if reuse_cache and cache.exists() and json.loads(cache_ids.read_text(encoding="utf-8")) == meta.product_id.tolist():
        X = np.load(cache); used_cache = True
    else:
        X = emb.embed(meta.image.tolist(), batch_size=batch)
    embed_s = time.perf_counter() - t
    t = time.perf_counter()
    index = faiss.IndexFlatIP(X.shape[1]); index.add(np.ascontiguousarray(X, dtype=np.float32))
    faiss.write_index(index, str(out / "index.faiss")); np.save(out / "embeddings.npy", X.astype(np.float32))
    meta.to_parquet(out / "meta.parquet", index=False)
    index_s = time.perf_counter() - t
    build_total_s = time.perf_counter() - t_all
    cfg = {"model": model, "n_items": int(len(X)), "dim": int(X.shape[1]), "index": "IndexFlatIP", "tau_v": tau_v,
           "gate_tau": gate_tau, "catalog": str(catalog), "data_version": "shared_data v1 (prep_shared_data.py seed 42)", "seed": 42}
    (out / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- latency truy vấn end-to-end (embed 1 ảnh + type gate + search), ảnh nạp sẵn
    vs = VisualSearcher(emb, X, meta, tau_v=tau_v, gate_tau=gate_tau)
    if query_csv and Path(query_csv).exists():
        qs = pd.read_csv(query_csv).query_image.head(n_lat).map(lambda p: str(ROOT / p)).tolist()
    else:
        qs = meta.image.head(n_lat).tolist()
    imgs = [load_image(p) for p in qs]
    vs.query(imgs[0])  # warmup
    lat, lat_search = [], []
    for _ in range(rep):
        for im in imgs:
            t = time.perf_counter(); r = vs.query(im, k=10); lat.append((time.perf_counter() - t) * 1000)
            q = vs.embed_query(im)
            t = time.perf_counter(); vs._search_vec(q, 10, None); lat_search.append((time.perf_counter() - t) * 1000)
    res = {**cfg, "embedder_load_s": round(load_s, 2), "embed_s": round(embed_s, 2), "embed_from_cache": used_cache,
           "index_write_s": round(index_s, 3), "build_total_s": round(build_total_s, 2),
           "index_file_mb": round((out / "index.faiss").stat().st_size / 1e6, 2),
           "query_e2e_ms_median": round(statistics.median(lat), 2), "query_e2e_ms_p95": round(float(np.percentile(lat, 95)), 2),
           "search_only_ms_median": round(statistics.median(lat_search), 4), "n_latency_measurements": len(lat)}
    (ROOT / "results").mkdir(exist_ok=True)
    if model != "dummy":
        (ROOT / "results" / f"build_index_{model}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--catalog", default=str(SHARED / "catalog_fpi.parquet"))
    ap.add_argument("--image-root", default=str(SHARED))
    ap.add_argument("--out", default=None)
    ap.add_argument("--tau-v", type=float, default=0.25)
    ap.add_argument("--gate-tau", type=float, default=0.0)
    ap.add_argument("--reuse-cache", action="store_true")
    ap.add_argument("--query-csv", default=str(ROOT / "eval" / "eval_visual.csv"))
    a = ap.parse_args()
    build(a.model, Path(a.catalog), Path(a.image_root), Path(a.out or ROOT / "indexes" / a.model), a.tau_v, a.gate_tau,
          a.reuse_cache, query_csv=Path(a.query_csv))
