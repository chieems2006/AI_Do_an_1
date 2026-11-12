# repo: scripts/01b_download_clothing_hats.py
"""US_48 – Mở rộng dữ liệu QUẦN ÁO + MŨ (Owner: Hoàng, Support: Tuấn Đạt).

Chạy thật: Fashion Product Images small + ViMRHP (ThoiTrangNam/Nu, lọc theo từ khoá tên SP).
Tuỳ chọn --amazon-lines N: đọc luồng N dòng đầu meta Amazon Reviews 2023 Clothing_Shoes_and_Jewelry qua HF
để đếm số SP mũ (headwear) có thể bổ sung (chỉ metadata + URL ảnh; ảnh m.media-amazon.com bị chặn ở môi trường này).
Đầu ra: data/processed/public_clothing_headwear.parquet (+ ảnh), data/counts_public_clothing_headwear.json,
        data/amazon_probe.json (nếu chạy probe), data/processed/amazon_meta_probe.parquet (metadata-only, không vào index).

Lệnh: python src/scripts/01b_download_clothing_hats.py --check-repro --amazon-lines 20000
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from msa.data import converters as C, pipeline  # noqa: E402


def amazon_probe(n_lines: int, out_dir: Path) -> dict:
    """Đếm SP theo product_type/sub_category trong N dòng đầu meta Amazon 2023 (đọc luồng)."""
    t0 = time.time()
    rows, by_main, n, skipped = [], collections.Counter(), 0, collections.Counter()
    for d in C.stream_jsonl_http(C.AMAZON_HF_META_URL, n_lines):
        n += 1
        by_main[d.get("main_category")] += 1
        rec = C.amazon_meta_to_schema(d)
        if rec is None:
            skipped["no_map_or_excluded"] += 1
            continue
        rows.append(rec)
    df = pd.DataFrame(rows, columns=C.SCHEMA_FIELDS).drop_duplicates("product_id")
    if len(df):
        C.write_catalog(df, out_dir / "processed" / "amazon_meta_probe.parquet")
    hw = df[df.product_type == "headwear"]
    rep = {"source": C.AMAZON_SOURCE, "file": C.AMAZON_HF_META_URL, "lines_read": n, "mapped_products": int(len(df)),
           "by_type": df.product_type.value_counts().to_dict() if len(df) else {},
           "by_sub": {f"{a}/{b}": int(k) for (a, b), k in df.groupby(["product_type", "sub_category"]).size().items()} if len(df) else {},
           "headwear_products": int(len(hw)), "headwear_with_price": int(hw.price.notna().sum()) if len(hw) else 0,
           "headwear_with_image_url": int(hw.specs.map(lambda s: bool(s["image_urls"])).sum()) if len(hw) else 0,
           "main_category_top": dict(by_main.most_common(8)), "skipped": dict(skipped),
           "headwear_examples": hw.title.head(5).tolist(), "elapsed_s": round(time.time() - t0, 1),
           "note": "Ảnh Amazon (m.media-amazon.com) bị proxy chặn trong môi trường này → chưa có ảnh local; "
                   "chỉ dùng được cho text search/QA hoặc tải ảnh trên máy thật."}
    (out_dir / "amazon_probe.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    C.append_sources_log(out_dir / "sources_log.json", {**C.AMAZON_SOURCE, "used_for": "probe mũ/quần áo (metadata-only)",
                                                        "lines_read": n})
    return rep


if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("s01", Path(__file__).with_name("01_download_public.py"))
    s01 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s01)
    argv = sys.argv[1:]
    n_amz = 0
    if "--amazon-lines" in argv:
        i = argv.index("--amazon-lines")
        n_amz = int(argv[i + 1])
        del argv[i:i + 2]
    args = s01.parse_args(argv)
    rep = pipeline.run("public_clothing_headwear", {"clothing", "headwear"}, args)
    out = {k: rep[k] for k in ("counts", "schema_errors", "catalog_sha256", "n_images", "elapsed_s")}
    if "repro_check" in rep:
        out["repro_check"] = rep["repro_check"]
    if n_amz:
        out["amazon_probe"] = {k: v for k, v in amazon_probe(n_amz, Path(args.out_dir)).items() if k != "source"}
    print(json.dumps(out, ensure_ascii=False, indent=1))
