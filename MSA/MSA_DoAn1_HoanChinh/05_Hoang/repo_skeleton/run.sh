#!/usr/bin/env bash
# Chạy demo bằng 1 lệnh: ./run.sh  (tự kiểm môi trường, tạo dữ liệu nếu thiếu, bật API)
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] && { set -a; . ./.env; set +a; }
python scripts/check_env.py
[ -f data/processed/catalog_v1.parquet ] || make data
[ -f results/cache/clip_b32_catalog.npy ] || make index
cd src && exec uvicorn msa.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
