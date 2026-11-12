# US_25 – So sánh & chọn phiên bản bằng bảng chấm điểm có trọng số (Sheet 3, Bảng F)

| Mục | Nội dung |
|---|---|
| Mã US | US_25 (Owner: Trung, Support: Khoa) – Sprint 2, 3.0 pt |
| Mục tiêu | Quyết định chọn model embedding ảnh minh bạch, bảo vệ được trước thầy |
| Đầu ra | `src/scoring/weighted_scoring.py` (+ `tests/test_scoring.py`), `scripts/run_scoring_from_khoa.py`, kết quả `results/bench_image_embed_from_khoa.csv`, `results/weighted_scoring.md/.json`, `results/weighted_scoring_sensitivity.json`, `results/weighted_scoring_scenario_B.json` |
| Tiêu chí nghiệm thu | Mỗi điểm số có số liệu thực nghiệm đi kèm |
| Trạng thái | **ĐẠT** (cập nhật bởi Tác nhân 2, 05/11/2026): đã chạy trên **5 model đo thật** của Khoa. 4/6 tiêu chí từ số đo; License và Dễ tích hợp là điểm định tính (ghi rõ) |

## Tóm tắt 5 dòng
1. Chấm 5 model embedding ảnh (Khoa đo thật trên 360 truy vấn test, catalog 4.593 SP) theo 6 tiêu chí có trọng số, thang 1–5.
2. **Kết quả: DINOv2-S 4,83 > SigLIP B/16 3,98 ≈ FashionCLIP 3,96 > CLIP B/32 2,99 > ResNet-50 2,40.**
3. Hạng 1 **không đổi** khi thay từng trọng số ±0,05 (12/12 cấu hình) và cả khi thêm tiêu chí "tầng category" vốn có lợi cho FashionCLIP.
4. Vì vậy lựa chọn tạm FashionCLIP trong README của Khoa **không được Bảng F ủng hộ** → đề xuất đổi model chính sang DINOv2-S, chốt lại khi có ảnh ngoài đời (`00_Chung/QUYET_DINH_CAN_CHOT.md` mục E).
5. Loại số liệu: [Thật–tổng hợp] – đo thật, nhưng truy vấn instance là ảnh catalog bị biến đổi, chưa có ảnh người dùng; License/Tích hợp là điểm định tính `[cần xác minh trên model card]`.

## 1. Phương pháp (giải thích dễ hiểu)
Mỗi tiêu chí được quy về thang 1–5 bằng **chuẩn hoá min-max giữa các ứng viên**: model tốt nhất ở độ đo đó được 5, kém nhất được 1, còn lại nội suy tuyến tính.
Ví dụ Tốc độ: SigLIP nhúng 1 ảnh nhanh nhất (190 ms) → 5; ResNet-50 chậm nhất (1.603 ms) → 1; FashionCLIP 294 ms → 1 + 4·(1.603 − 294)/(1.603 − 190) = 4,71.
Tổng = Σ (trọng số × điểm tiêu chí). Vì là so sánh **tương đối**, thêm/bớt ứng viên thì điểm thay đổi → luôn ghi danh sách ứng viên cùng bảng.

| Tiêu chí | Trọng số | Độ đo (trọng số con) – cột trong `04_Khoa/results/bench_image_embed.csv` | Chiều |
|---|---|---|---|
| Độ chính xác | 0,35 | macro Recall@5 test (0,5) ← `test_macro_R@5`; MRR@10 (0,3) ← `test_MRR@10`; CTE@5 (0,2) ← `test_CTE@5` | ↑ ↑ ↓ |
| Tốc độ | 0,15 | nhúng 1 ảnh truy vấn, batch 1, median 60 lần (ms) ← `query_embed_ms_median_bs1` | ↓ |
| Tài nguyên | 0,15 | RAM đỉnh (GB) ← `peak_rss_mb`/1024 (0,5); trọng số fp32 (MB) ← `weights_fp32_total_mb` (0,5) | ↓ ↓ |
| Phù hợp miền | 0,15 | Recall@5 của **nhóm yếu nhất** trong 4 nhóm ← min(`test_R@5_<nhóm>`) | ↑ |
| License | 0,10 | điểm định tính 1–5 (bảng `QUAL` trong script) | ↑ |
| Dễ tích hợp | 0,10 | điểm định tính 1–5 (có sẵn trong open_clip/transformers, chạy CPU) | ↑ |

Thuật ngữ (Recall@5, MRR, CTE@5…): `00_Chung/THUAT_NGU.md`.

Lệnh tái lập (từ `01_Trung/`): `PYTHONPATH=src python scripts/run_scoring_from_khoa.py` (mặc định đọc `../04_Khoa/results/bench_image_embed.csv`; đổi file bằng `--csv`).

## 2. Số liệu đầu vào (đo thật – Khoa, split test, shared_data v1 seed 42, CPU 2 luồng dùng chung)
| Model | macro R@5 | MRR@10 | CTE@5 | Nhúng 1 ảnh (ms) | RAM đỉnh (GB) | Trọng số fp32 (MB) | R@5 nhóm yếu nhất | License* | Tích hợp* |
|---|---|---|---|---|---|---|---|---|---|
| dinov2_s | 0,846 | 0,791 | 0,043 | 288,8 | 1,41 | 88 | 0,833 | 5 | 4 |
| siglip_b16 | 0,833 | 0,760 | 0,055 | 190,0 | 2,37 | 813 | 0,783 (mũ) | 5 | 4 |
| fashionclip | 0,829 | 0,757 | 0,062 | 294,2 | 1,56 | 605 | 0,733 (giày) | 4 | 4 |
| clip_b32 | 0,721 | 0,660 | 0,076 | 428,3 | 1,98 | 605 | 0,683 | 5 | 5 |
| resnet50 | 0,704 | 0,644 | 0,138 | 1.602,9 | 1,33 | 94 | 0,617 (giày) | 5 | 5 |

Nguồn: `results/bench_image_embed_from_khoa.csv` (bản đã đổi tên cột). \* điểm định tính do Trung đề xuất, nhóm thống nhất lại ở buổi chấm N12.
Lưu ý latency: CLIP B/32 và FashionCLIP **cùng kiến trúc** ViT-B/32 nhưng đo ra 428 ms vs 294 ms → chênh lệch do máy dùng chung, không phải do model. Tiêu chí Tốc độ vì vậy có nhiễu; độ nhạy bên dưới cho thấy nhiễu này không đổi hạng 1.

## 3. Bảng F (đầu ra thật của script)
| Hạng | Ứng viên | Độ chính xác (0,35) | Tốc độ (0,15) | Tài nguyên (0,15) | Phù hợp miền (0,15) | License (0,10) | Dễ tích hợp (0,10) | **Tổng (thang 5)** |
|---|---|---|---|---|---|---|---|---|
| 1 | dinov2_s | 5,00 | 4,72 | 4,83 | 5,00 | 5,00 | 4,00 | **4,83** |
| 2 | siglip_b16 | 4,47 | 5,00 | 1,00 | 4,08 | 5,00 | 4,00 | **3,98** |
| 3 | fashionclip | 4,33 | 4,71 | 3,13 | 3,15 | 4,00 | 4,00 | **3,96** |
| 4 | clip_b32 | 1,89 | 4,33 | 2,33 | 2,23 | 5,00 | 5,00 | 2,99 |
| 5 | resnet50 | 1,00 | 1,00 | 4,98 | 1,00 | 5,00 | 5,00 | 2,40 |

### 3.1 Kiểm tra độ nhạy (đã làm – trước đây ghi ở "việc còn lại")
- Đổi **từng** trọng số ±0,05 (phần chênh chia đều cho 5 tiêu chí còn lại) → 12 cấu hình: DINOv2-S hạng 1 ở **12/12**; SigLIP và FashionCLIP đổi chỗ hạng 2–3 ở 4/12 cấu hình (giảm Tốc độ, tăng Tài nguyên, giảm Phù hợp miền, giảm License). File: `results/weighted_scoring_sensitivity.json`.
- **Kịch bản B** (đề xuất, chưa chốt): tách 0,10 từ Độ chính xác sang tiêu chí mới "Tầng category" (cat Hit@5 + cat P@5 – tìm SP khác cùng loại/màu, điểm mạnh của FashionCLIP): DINOv2-S **4,48** > FashionCLIP 4,03 > SigLIP 3,96 > CLIP B/32 3,10 > ResNet-50 2,47. File: `results/weighted_scoring_scenario_B.json`.

### 3.2 Bằng chứng bổ sung không nằm trong trọng số
| Điểm | DINOv2-S | SigLIP B/16 | FashionCLIP | Nguồn |
|---|---|---|---|---|
| R@5 truy vấn **đổi nền** (gần ảnh người dùng nhất, n=32) | 0,812 | **0,906** | 0,656 | `04_Khoa/results/recall_by_transform.csv` |
| R@5 truy vấn **nhiều biến đổi** (n=36) | **0,750** | **0,750** | 0,667 | như trên |
| Có text tower (type gate zero-shot, tìm bằng chữ) | Không | Có | Có | `04_Khoa/results/bench_image_embed.csv` (`has_text`) |
| CTE@5 tốt nhất đạt được | 0,043 (không gate) | 0,044 (gate zero-shot) | 0,044 (gate zero-shot) | `04_Khoa/docs/US_22_benchmark_embedding.md` §2 |
| cat P@5 (tầng category) | 0,307 | 0,355 | **0,378** | như trên |

## 4. Kết luận đề xuất
- Theo Bảng F đã thống nhất từ đầu: **chọn DINOv2-S** (ổn định qua mọi kiểm tra độ nhạy). Ứng viên dự phòng: **SigLIP B/16** (có text tower, bền nền lạ nhất, nhưng tốn RAM nhất).
- FashionCLIP chỉ hơn ở tầng category (cat P@5) và đã có index + cải tiến đo sẵn; nếu nhóm vẫn dùng FashionCLIP cho demo thì báo cáo phải ghi rõ "chọn khác Bảng F" và lý do.
- **Chốt cuối** khi có ≥ 80 ảnh ngoài đời (US_11): chạy lại DINOv2-S / SigLIP / FashionCLIP, cập nhật cột Độ chính xác, chạy lại script này.
- Người chốt: Trung + Khoa (buổi N12). Chi tiết phương án: `00_Chung/QUYET_DINH_CAN_CHOT.md` mục E.

## 5. Việc còn lại
1. Họp N12 thống nhất điểm License/Tích hợp (đọc model card: DINOv2 Apache-2.0, SigLIP Apache-2.0, FashionCLIP MIT – `[cần xác minh]`).
2. Thêm cột "R@5 ảnh ngoài đời" vào tiêu chí Độ chính xác khi US_11 có ảnh.
3. Ứng viên CLIP B/16, OpenCLIP LAION-2B, Marqo-FashionSigLIP: CHƯA ĐO (Khoa) – có thì chạy lại script, không cần sửa code.
