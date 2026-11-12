# repo: scripts/02_merge_data_v1.py
"""N5 – Gộp public (US_06 + US_48) thành Data v1, kiểm schema 100%, so khớp với shared_data/catalog_fpi.parquet.

Lệnh: python src/scripts/02_merge_data_v1.py
Đầu ra: data/processed/catalog_v1.parquet, data/counts_data_v1.json
(Phần crawl VN của Chiến – US_07 – nối thêm bằng --extra <parquet> khi có.)
"""
from __future__ import annotations
import os

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from msa.data import converters as C  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(ROOT / "data"))
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--shared", default=(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/catalog_fpi.parquet"))
    a = ap.parse_args()
    d = Path(a.data_dir) / "processed"
    parts = [C.read_catalog(d / "public_footwear_accessory.parquet"), C.read_catalog(d / "public_clothing_headwear.parquet")]
    parts += [C.read_catalog(p) for p in a.extra]
    cat = pd.concat(parts, ignore_index=True).sort_values("product_id").reset_index(drop=True)[C.SCHEMA_FIELDS]
    errs = C.validate_schema(cat)
    C.write_catalog(cat, d / "catalog_v1.parquet")
    rep = {"version": "Data v1 (public: FPI small + ViMRHP; seed 42)", "counts": C.count_table(cat), "schema_errors": errs,
           "schema_valid_100pct": not errs, "catalog_sha256": C.catalog_hash(cat)}
    if Path(a.shared).exists():
        sh = set(pd.read_parquet(a.shared, columns=["product_id"]).product_id)
        mine = set(cat[cat.source == "fashion_product_images_small"].product_id)
        rep["compare_shared_catalog_fpi"] = {"shared": len(sh), "mine_fpi": len(mine), "intersection": len(sh & mine),
                                             "identical_id_set": sh == mine}
    (Path(a.data_dir) / "counts_data_v1.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))
