# repo: scripts/build_category_map.py
"""US_49 – Sinh data/category_map.csv từ NHÃN THẬT của các nguồn + đo độ phủ map + áp taxonomy lên catalog.

Chạy:  PYTHONPATH=src python scripts/build_category_map.py
Đầu ra:
  data/category_map.csv                 – bảng map nhãn nguồn -> (product_type, sub_category, action)
  data/catalog_fpi_taxonomy_v1.parquet  – catalog_fpi với sub_category chính thức (không sửa shared_data)
  data/vimrhp_taxonomy_v1.csv           – product_id, title, vimrhp_subcategory, product_type, sub_category, action, rule_id
  results/taxonomy_coverage.json        – độ phủ map (đo thật)
"""
from __future__ import annotations

import collections
import glob
import json
import os
import sys

import pandas as pd
import pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from msa.data.taxonomy import DOC_MAPS, FPI_ARTICLE, map_fpi, map_vimrhp  # noqa: E402

SHARED = os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data")
RAW_FPI = (os.environ.get("MSA_RAW_DIR", "/home/claude/realdata") + "/fpi/data/*.parquet")


def load_fpi_raw() -> pd.DataFrame:
    fs = sorted(glob.glob(RAW_FPI))
    cols = ["id", "masterCategory", "subCategory", "articleType", "productDisplayName"]
    return pd.concat([pq.read_table(f, columns=cols).to_pandas() for f in fs], ignore_index=True)


def main() -> None:
    rows: list[dict] = []
    cov: dict = {}
    # ---------------- FPI: map theo bộ ba nhãn gốc (masterCategory/subCategory/articleType)
    raw = load_fpi_raw()
    res = [map_fpi(m, s, a, t) for m, s, a, t in zip(raw.masterCategory, raw.subCategory, raw.articleType, raw.productDisplayName)]
    raw["product_type"] = [r.product_type for r in res]
    raw["sub_category"] = [r.sub_category for r in res]
    raw["action"] = [r.action for r in res]
    raw["rule_id"] = [r.rule_id for r in res]
    for (m, s, a), g in raw.groupby(["masterCategory", "subCategory", "articleType"]):
        base = map_fpi(m, s, a, "")
        refined = g[g.rule_id.str.startswith("fpi.title_")]
        note = ""
        if len(refined):
            note = "; ".join(f"{a}/{b}: {v} dòng (luật tiêu đề)" for (a, b), v in refined.groupby(["product_type", "sub_category"]).size().items())
        rows.append(dict(source="fashion_product_images", source_label=f"{m}/{s}/{a}", n_rows_source=len(g),
                         product_type=base.product_type, sub_category=base.sub_category, action=base.action,
                         rule_id=base.rule_id, title_refinement=note, verified="du_lieu_that"))
    n_labels = len(rows)
    lab = pd.DataFrame(rows)
    cov["fpi"] = dict(
        distinct_labels=n_labels,
        labels_keep=int((lab.action == "keep").sum()), labels_unknown=int((lab.action == "unknown").sum()),
        labels_exclude=int((lab.action == "exclude").sum()),
        labels_unmapped=int(lab.rule_id.str.contains("chua_co_trong_bang").sum()),
        rows_total=len(raw), rows_keep=int((raw.action == "keep").sum()), rows_unknown=int((raw.action == "unknown").sum()),
        rows_exclude=int((raw.action == "exclude").sum()),
        rows_keep_by_leaf={f"{a}/{b}": int(n) for (a, b), n in raw[raw.action == "keep"].groupby(["product_type", "sub_category"]).size().items()},
    )
    cov["fpi"]["label_coverage_pct"] = round(100 * (n_labels - cov["fpi"]["labels_unmapped"]) / n_labels, 2)

    # ---------------- catalog_fpi (4.593 SP do Tác nhân 1 chuẩn bị): áp taxonomy chính thức
    cat = pd.read_parquet(f"{SHARED}/catalog_fpi.parquet")
    parts = cat.category.str.split("/", n=2, expand=True)
    r2 = [map_fpi(m, s, a, t) for m, s, a, t in zip(parts[0], parts[1], parts[2], cat.title)]
    old = cat.product_type + "/" + cat.sub_category
    cat["product_type"] = [r.product_type for r in r2]
    cat["sub_category"] = [r.sub_category for r in r2]
    cat["taxonomy_action"] = [r.action for r in r2]
    cat["taxonomy_rule"] = [r.rule_id for r in r2]
    new = cat.product_type + "/" + cat.sub_category
    changed = collections.Counter(f"{o} -> {n}" for o, n in zip(old, new) if o != n)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    cat.to_parquet(os.path.join(ROOT, "data", "catalog_fpi_taxonomy_v1.parquet"), index=False)
    cov["catalog_fpi_v1"] = dict(
        rows=len(cat), keep=int((cat.taxonomy_action == "keep").sum()), unknown=int((cat.taxonomy_action == "unknown").sum()),
        exclude=int((cat.taxonomy_action == "exclude").sum()),
        by_type={k: int(v) for k, v in cat[cat.taxonomy_action == "keep"].product_type.value_counts().items()},
        by_leaf={f"{a}/{b}": int(n) for (a, b), n in cat.groupby(["product_type", "sub_category"]).size().items()},
        changed_vs_tam=dict(changed),
    )

    # ---------------- ViMRHP: SubCategory gốc + luật tiêu đề tiếng Việt
    prods = [json.loads(line) for line in open(f"{SHARED}/vimrhp_fashion_products.jsonl", encoding="utf-8")]
    vrows = []
    for p in prods:
        r = map_vimrhp(p["vimrhp_subcategory"], p["title"])
        vrows.append(dict(product_id=p["product_id"], title=p["title"], vimrhp_subcategory=p["vimrhp_subcategory"],
                          n_reviews=len(p["reviews"]), product_type=r.product_type, sub_category=r.sub_category,
                          action=r.action, rule_id=r.rule_id))
    vdf = pd.DataFrame(vrows)
    vdf.to_csv(os.path.join(ROOT, "data", "vimrhp_taxonomy_v1.csv"), index=False)
    for (sub, pt, leaf, act, rule), g in vdf.groupby(["vimrhp_subcategory", "product_type", "sub_category", "action", "rule_id"]):
        rows.append(dict(source="vimrhp_shopee", source_label=f"{sub} + luật:{rule}", n_rows_source=len(g), product_type=pt,
                         sub_category=leaf, action=act, rule_id=rule, title_refinement="", verified="du_lieu_that"))
    cov["vimrhp"] = dict(
        products=len(vdf), subcategories=sorted(vdf.vimrhp_subcategory.unique().tolist()),
        keep=int((vdf.action == "keep").sum()), unknown=int((vdf.action == "unknown").sum()), exclude=int((vdf.action == "exclude").sum()),
        unmatched_title_rule=int(vdf.rule_id.eq("vi.khong_khop_mau").sum()),
        by_subcat={s: {f"{a}/{b}": int(n) for (a, b), n in g.groupby(["product_type", "sub_category"]).size().items()} for s, g in vdf.groupby("vimrhp_subcategory")},
        reviews_in_scope=int(vdf[vdf.action == "keep"].n_reviews.sum()),
    )
    cov["vimrhp"]["title_rule_coverage_pct"] = round(100 * (len(vdf) - cov["vimrhp"]["unmatched_title_rule"]) / len(vdf), 2)

    # ---------------- Nguồn chưa có file: map theo tài liệu [cần xác minh]
    for src, mp in DOC_MAPS.items():
        for label, (pt, leaf, act) in mp.items():
            rows.append(dict(source=src, source_label=label, n_rows_source="", product_type=pt, sub_category=leaf, action=act,
                             rule_id="doc", title_refinement="", verified="[cần xác minh] theo tài liệu, chưa có file"))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(ROOT, "data", "category_map.csv"), index=False)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    cov["config"] = dict(data_version="shared_data v1 (prep_shared_data.py seed 42)", script="scripts/build_category_map.py",
                         fpi_articleTypes_in_table=len(FPI_ARTICLE))
    json.dump(cov, open(os.path.join(ROOT, "results", "taxonomy_coverage.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if not isinstance(vv, dict)} for k, v in cov.items()}, ensure_ascii=False, indent=1))
    print("catalog changed:", json.dumps(cov["catalog_fpi_v1"]["changed_vs_tam"], ensure_ascii=False))


if __name__ == "__main__":
    main()
