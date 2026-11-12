#!/usr/bin/env bash
# Chạy benchmark tuần tự từng model (mỗi model 1 tiến trình), log ở logs/bench_<model>.log
cd "$(dirname "$0")/../.."
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
MODELS=${MODELS:-"clip_b32 resnet50 dinov2_s fashionclip siglip_b16 clip_b16 marqo_fashionsiglip openclip_b32_laion2b"}
for m in $MODELS; do
  if [ -f results/bench/$m.json ] && grep -q '"status": "ok"' results/bench/$m.json; then echo "skip $m (đã có)"; continue; fi
  echo "=== $m $(date -Is)"; python src/scripts/bench_image_embed.py --model $m > logs/bench_$m.log 2>&1; tail -2 logs/bench_$m.log
done
python src/scripts/bench_image_embed.py --aggregate
echo "DONE $(date -Is)"
