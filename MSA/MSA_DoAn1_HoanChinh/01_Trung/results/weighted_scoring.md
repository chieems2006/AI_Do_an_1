| Hạng | Ứng viên | Độ chính xác (0.35) | Tốc độ (0.15) | Tài nguyên (0.15) | Phù hợp miền (0.15) | License (0.10) | Dễ tích hợp (0.10) | Tổng (thang 5) | Thiếu số liệu |
|---|---|---|---|---|---|---|---|---|---|
| 1 | dinov2_s | 5.00 | 4.72 | 4.83 | 5.00 | 5.00 | 4.00 | 4.83 | — |
| 2 | siglip_b16 | 4.47 | 5.00 | 1.00 | 4.08 | 5.00 | 4.00 | 3.98 | — |
| 3 | fashionclip | 4.33 | 4.71 | 3.13 | 3.15 | 4.00 | 4.00 | 3.96 | — |
| 4 | clip_b32 | 1.89 | 4.33 | 2.33 | 2.23 | 5.00 | 5.00 | 2.99 | — |
| 5 | resnet50 | 1.00 | 1.00 | 4.98 | 1.00 | 5.00 | 5.00 | 2.40 | — |

Nguồn: `../04_Khoa/results/bench_image_embed.csv` (5 model, split test eval_visual, shared_data v1 seed 42). Độ nhạy: đổi từng trọng số ±0,05 → hạng 1 vẫn là **dinov2_s** ở 12/12 cấu hình (chi tiết `results/weighted_scoring_sensitivity.json`).

### Kịch bản B (đề xuất, chưa chốt): thêm tiêu chí Tầng category 0,10, Độ chính xác instance còn 0,25

| Hạng | Ứng viên | Độ chính xác (0.25) | Tầng category (0.10) | Tốc độ (0.15) | Tài nguyên (0.15) | Phù hợp miền (0.15) | License (0.10) | Dễ tích hợp (0.10) | Tổng (thang 5) | Thiếu số liệu |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | dinov2_s | 5.00 | 1.50 | 4.72 | 4.83 | 5.00 | 5.00 | 4.00 | 4.48 | — |
| 2 | fashionclip | 4.33 | 5.00 | 4.71 | 3.13 | 3.15 | 4.00 | 4.00 | 4.03 | — |
| 3 | siglip_b16 | 4.47 | 4.35 | 5.00 | 1.00 | 4.08 | 5.00 | 4.00 | 3.96 | — |
| 4 | clip_b32 | 1.89 | 2.97 | 4.33 | 2.33 | 2.23 | 5.00 | 5.00 | 3.10 | — |
| 5 | resnet50 | 1.00 | 1.70 | 1.00 | 4.98 | 1.00 | 5.00 | 5.00 | 2.47 | — |
