# repo: scripts/validate_catalog.py
"""US_05 – Validate dữ liệu thật với product.schema.json; ghi results/schema_validation.json + ví dụ thật mỗi product_type.

Chạy:  PYTHONPATH=src python scripts/validate_catalog.py   (sau build_category_map.py)
"""
from __future__ import annotations

import collections
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "src"))  # + package msa chung
from msa.data.schema_adapters import fpi_row_to_record, validate_records, vimrhp_to_record  # noqa: E402

SHARED = os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data")
EXAMPLE_IDS = {"footwear": "fpi_21744", "clothing": "fpi_9465", "headwear": "fpi_40767", "accessory": "fpi_7108"}


def _summ(ok: int, bad: int, errs: list) -> dict:
    kinds = collections.Counter(m.split(":")[0] + ": " + m.split(":", 1)[1].strip()[:60] for _, m in errs)
    return dict(valid=ok, invalid=bad, total=ok + bad, valid_pct=round(100 * ok / max(ok + bad, 1), 2),
                error_kinds=dict(kinds.most_common(10)), first_errors=errs[:5])


def main() -> None:
    out: dict = {}
    # 1) catalog_fpi gốc (nhãn TẠM của Tác nhân 1)
    raw = pd.read_parquet(f"{SHARED}/catalog_fpi.parquet")
    recs = [fpi_row_to_record(r) for r in raw.to_dict("records")]
    out["catalog_fpi_goc"] = _summ(*validate_records(recs))
    # 2) catalog sau taxonomy v1, chỉ phần in-scope (action=keep|unknown)
    cat = pd.read_parquet(os.path.join(ROOT, "data", "catalog_fpi_taxonomy_v1.parquet"))
    inscope = cat[cat.taxonomy_action != "exclude"]
    recs2 = [fpi_row_to_record(r) for r in inscope.to_dict("records")]
    out["catalog_fpi_taxonomy_v1_inscope"] = _summ(*validate_records(recs2))
    out["catalog_fpi_taxonomy_v1_inscope"]["excluded_out_of_scope"] = int((cat.taxonomy_action == "exclude").sum())
    # 3) ViMRHP in-scope
    prods = [json.loads(line) for line in open(f"{SHARED}/vimrhp_fashion_products.jsonl", encoding="utf-8")]
    vrecs = [vimrhp_to_record(p) for p in prods]
    vin = [r for r in vrecs if r["product_type"] != "out_of_scope"]
    out["vimrhp_inscope"] = _summ(*validate_records(vin))
    out["vimrhp_inscope"]["excluded_out_of_scope"] = len(vrecs) - len(vin)
    # Ví dụ thật mỗi product_type
    ex_dir = os.path.join(ROOT, "src", "schema", "examples")
    os.makedirs(ex_dir, exist_ok=True)
    by_id = {r["product_id"]: r for r in recs2}
    for pt, pid in EXAMPLE_IDS.items():
        json.dump(by_id[pid], open(os.path.join(ex_dir, f"fpi_{pt}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    seen = set()
    for r in vin:
        if r["product_type"] not in seen and r["sub_category"] != "unknown":
            seen.add(r["product_type"])
            r2 = dict(r, reviews=r["reviews"][:2])  # rút gọn review trong ví dụ
            json.dump(r2, open(os.path.join(ex_dir, f"vimrhp_{r['product_type']}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out["config"] = dict(schema="src/schema/product.schema.json (draft 2020-12)", validator="jsonschema Draft202012Validator",
                         data_version="shared_data v1 (prep_shared_data.py seed 42)")
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "results", "schema_validation.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("first_errors",)} for k, v in out.items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
