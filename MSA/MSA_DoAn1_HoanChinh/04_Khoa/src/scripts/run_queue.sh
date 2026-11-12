#!/usr/bin/env bash
# Hàng đợi tuần tự (1 tiến trình nặng của Khoa tại một thời điểm – tránh OOM trên máy dùng chung)
cd "$(dirname "$0")/../.."
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false
while pgrep -f "bench_image_embed.py --model" >/dev/null; do sleep 15; done
echo "=== improvements clip_b32 $(date -Is)"
for i in 1 2 3; do python src/scripts/run_improvements.py --model clip_b32 > logs/improvements_clip_b32.log 2>&1 && break; echo "improvements thử lại $i (exit $?)"; sleep 30; done
echo "improvements clip_b32 status $?"
for m in ${MODELS:-dinov2_s siglip_b16 clip_b16 openclip_b32_laion2b marqo_fashionsiglip}; do
  if [ -f results/bench/$m.json ] && grep -q '"status": "ok"' results/bench/$m.json; then echo "skip $m"; continue; fi
  for i in 1 2 3; do
    echo "=== $m $(date -Is) (lần $i)"; python src/scripts/bench_image_embed.py --model $m > logs/bench_$m.log 2>&1
    tail -2 logs/bench_$m.log | cut -c1-600
    grep -q '"status": "ok"' results/bench/$m.json 2>/dev/null && break; sleep 30
  done
done
python src/scripts/bench_image_embed.py --aggregate
echo "DONE $(date -Is)"
