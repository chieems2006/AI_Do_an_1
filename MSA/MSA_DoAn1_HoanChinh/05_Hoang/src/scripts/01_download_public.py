# repo: scripts/01_download_public.py
"""US_06 – Tải & chuẩn hoá dataset công khai cho nhóm GIÀY DÉP + PHỤ KIỆN (Owner: Hoàng, Support: Tuấn Đạt).

Nguồn chạy thật: Fashion Product Images small (HF ashraq/fashion-product-images-small) + ViMRHP (HF trucmtnguyen/ViMRHP).
Quần áo + mũ: xem 01b_download_clothing_hats.py (US_48).
Đầu ra: data/processed/public_footwear_accessory.parquet, data/images/<product_id>/0.jpg,
        data/counts_public_footwear_accessory.json (bảng đếm + kiểm quota + hash), data/sources_log.json.

Lệnh: python src/scripts/01_download_public.py --raw-dir /home/claude/realdata --check-repro
      (máy mới: thêm --download để tải qua huggingface_hub; bản Kaggle gốc là tuỳ chọn, không bắt buộc)
"""
from __future__ import annotations
import os

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung
from msa.data import pipeline  # noqa: E402


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", default=os.environ.get("MSA_RAW_DIR", "/home/claude/realdata"))
    ap.add_argument("--out-dir", default=str(ROOT / "data"))
    ap.add_argument("--download", action="store_true", help="tải dữ liệu gốc qua huggingface_hub nếu chưa có")
    ap.add_argument("--no-images", action="store_true")
    ap.add_argument("--full", action="store_true", help="lấy toàn bộ dòng map được (không áp quota)")
    ap.add_argument("--check-repro", action="store_true", help="chạy lần 2 vào thư mục tạm và so hash")
    return ap.parse_args(argv)


if __name__ == "__main__":
    rep = pipeline.run("public_footwear_accessory", {"footwear", "accessory"}, parse_args())
    print(json.dumps({k: rep[k] for k in ("counts", "schema_errors", "catalog_sha256", "n_images", "elapsed_s")
                      + (("repro_check",) if "repro_check" in rep else ())}, ensure_ascii=False, indent=1))
