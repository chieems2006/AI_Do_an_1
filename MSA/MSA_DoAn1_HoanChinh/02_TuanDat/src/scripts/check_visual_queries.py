# repo: scripts/check_visual_queries.py
"""US_11 – Kiểm tra tập ảnh truy vấn 'ngoài đời' + CSV ground truth trước khi dùng cho eval_visual.

Tiêu chí (Backlog US_11): ≥ 80 ảnh; mỗi ảnh có ≥ 1 sản phẩm đúng được 2 người xác nhận (agreed = yes);
quota tối thiểu giày 25 / quần áo 25 / mũ 15 / phụ kiện 15; có ảnh người mặc nhiều món.

    python src/scripts/check_visual_queries.py --csv data/eval/visual_queries/ground_truth.csv \
        --image-root . --catalog results/catalog_clean.parquet
Mã thoát 0 = đạt, 1 = còn lỗi (in danh sách lỗi + bảng thống kê).
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REQUIRED = ["query_id", "file", "product_type", "scenario", "gt_product_ids", "annotator_1", "annotator_2", "agreed"]
SCENARIOS = {"studio_khac_goc", "tu_chup", "chup_man_hinh", "nen_phuc_tap", "nguoi_mac_nhieu_mon"}
TYPES = {"footwear", "clothing", "headwear", "accessory"}
QUOTA = {"footwear": 25, "clothing": 25, "headwear": 15, "accessory": 15}
MIN_TOTAL = 80
YES = {"yes", "y", "1", "true", "có", "co", "x"}


def check(df: pd.DataFrame, image_root: Path | None = None, catalog_ids: set[str] | None = None,
          min_total: int = MIN_TOTAL, quota: dict[str, int] | None = None) -> dict:
    """Trả dict{ok, errors, stats}. Không sửa dữ liệu."""
    quota = quota or QUOTA
    errors: list[str] = []
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return {"ok": False, "errors": [f"thiếu cột: {missing}"], "stats": {}}
    df = df.fillna("")
    df = df[~df["note"].astype(str).str.contains("VÍ DỤ")] if "note" in df else df
    dup = df.query_id[df.query_id.duplicated()].tolist()
    if dup:
        errors.append(f"query_id trùng: {dup}")
    for r in df.itertuples():
        if r.product_type not in TYPES:
            errors.append(f"{r.query_id}: product_type '{r.product_type}' không hợp lệ")
        if r.scenario not in SCENARIOS:
            errors.append(f"{r.query_id}: scenario '{r.scenario}' không hợp lệ")
        gts = [g.strip() for g in str(r.gt_product_ids).split("|") if g.strip()]
        if not gts:
            errors.append(f"{r.query_id}: chưa có gt_product_ids")
        if catalog_ids is not None:
            bad = [g for g in gts if g not in catalog_ids]
            if bad:
                errors.append(f"{r.query_id}: gt không có trong catalog: {bad}")
        if not str(r.annotator_1).strip() or not str(r.annotator_2).strip():
            errors.append(f"{r.query_id}: thiếu người gán nhãn thứ 2 (cần 2 người)")
        elif str(r.annotator_1).strip().lower() == str(r.annotator_2).strip().lower():
            errors.append(f"{r.query_id}: annotator_1 trùng annotator_2")
        if str(r.agreed).strip().lower() not in YES:
            errors.append(f"{r.query_id}: chưa được 2 người thống nhất (agreed)")
        if image_root is not None and not (image_root / str(r.file)).exists():
            errors.append(f"{r.query_id}: không thấy file ảnh {r.file}")
    by_type = Counter(df.product_type)
    for t, q in quota.items():
        if by_type.get(t, 0) < q:
            errors.append(f"nhóm {t}: {by_type.get(t, 0)} < quota {q}")
    if len(df) < min_total:
        errors.append(f"tổng {len(df)} ảnh < {min_total}")
    if "nguoi_mac_nhieu_mon" not in set(df.scenario):
        errors.append("chưa có ảnh người mặc nhiều món (scenario nguoi_mac_nhieu_mon)")
    stats = {"n": int(len(df)), "by_type": dict(by_type), "by_scenario": dict(Counter(df.scenario)),
             "agreed": int(sum(str(a).strip().lower() in YES for a in df.agreed))}
    return {"ok": not errors, "errors": errors, "stats": stats}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--image-root", default=None)
    ap.add_argument("--catalog", default=None)
    a = ap.parse_args()
    df = pd.read_csv(a.csv, dtype=str)
    ids = set(pd.read_parquet(a.catalog, columns=["product_id"]).product_id) if a.catalog else None
    res = check(df, Path(a.image_root) if a.image_root else None, ids)
    print(res["stats"])
    for e in res["errors"]:
        print("LỖI:", e)
    print("ĐẠT" if res["ok"] else f"CHƯA ĐẠT ({len(res['errors'])} lỗi)")
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
