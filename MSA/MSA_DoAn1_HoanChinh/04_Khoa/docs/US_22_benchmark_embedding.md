# US_22 – Benchmark embedding ảnh (≥ 5 phiên bản)

| Mục | Nội dung |
|---|---|
| Mã US | US_22 (Owner: Khoa, Support: Hoàng) – Sprint 2, 8.0 pt |
| Mục tiêu | Chọn model embedding ảnh dựa trên số liệu thật |
| Đầu ra | `src/scripts/bench_image_embed.py` (mỗi model 1 tiến trình, embed theo khối có thể chạy tiếp khi bị ngắt), `results/bench_image_embed.{csv,json}`, `results/bench/<model>.json` (cấu hình + phần cứng + số đo), `results/per_query/<model>.csv`, `results/errors_<model>.{md,png}`, `results/tau_v_analysis.json`, cache `cache/<model>_*.npy`; bảng tổng hợp `results/tables.md` |
| Tiêu chí nghiệm thu | Cùng tiền xử lý ✔ (pad vuông nền trắng → resize bicubic → mean/std của model), cùng FAISS `IndexFlatIP` ✔, cùng K ✔; latency đo 60 lần (20 ảnh × 3 lượt), lấy median ✔; Recall@5 theo nhóm + CTE@5 ✔; có/không type gate ✔ (cho mọi model, không chỉ 2 model dẫn đầu) |
| Trạng thái | **Hoàn thành ≥ 5 model đo THẬT** (danh sách ở Bảng A). Model chưa chạy được do thời gian CPU ghi rõ ở mục 4. |

## Tóm tắt 5 dòng
1. Benchmark thật 5 model trên cùng 360 truy vấn test, cùng tiền xử lý, cùng FAISS IndexFlatIP, latency median 60 lần đo.
2. Macro Recall@5: DINOv2-S 0,846 > SigLIP 0,833 > FashionCLIP 0,829 > CLIP B/32 0,721 > ResNet-50 0,704.
3. Bảng F (US_25) xếp **DINOv2-S hạng 1 (4,83/5)**, FashionCLIP hạng 3 → kết luận chọn FashionCLIP trước đây cần nhóm xét lại (`00_Chung/QUYET_DINH_CAN_CHOT.md` mục E).
4. τ_v = 0,25 không loại được ảnh ngoài phạm vi nào với cả 5 model → τ_v phải theo model (mục C); R@5 theo kiểu biến đổi: `results/recall_by_transform.csv`.
5. Loại số liệu: [Thật–tổng hợp]; latency trên máy dùng chung có nhiễu.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Cấu hình chung: dữ liệu `shared_data v1 (prep_shared_data.py seed 42)`, catalog 4.593 ảnh FPI 60×80, eval `eval/eval_visual.csv` (split **test**: 240 instance + 120 category; 60 OOD riêng), seed 42, CPU 2 luồng, fp32. Lệnh tái lập: `python src/scripts/bench_image_embed.py --model <id>` rồi `--aggregate`; bảng: `python src/scripts/make_tables.py`.

## 1. Kết quả chính (đo thật)

<!-- BANG_A_RESULTS -->
Phần cứng: Intel(R) Xeon(R) Processor @ 2.10GHz – 2 CPU, torch 2.15.0+cu132 (2 luồng), fp32; máy dùng chung (latency có nhiễu). Split test của `eval/eval_visual.csv`; nguồn số: `results/bench/<model>.json`, `results/bench_image_embed.csv`.

**Bảng A (chính)**

| Model | R@1 | R@5 | R@10 | MRR@10 | NDCG@10 | Macro R@5 | CTE@5 | cat Hit@5 | cat P@5 | Embed truy vấn ms (median / p95, bs=1) | Embed catalog ms/ảnh (bs=32) | FAISS search ms (median) | RSS sau nạp (MB) | Peak RSS (MB) | Trọng số visual fp32 (MB) | Index (MB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| resnet50 | 0.604 | 0.704 | 0.738 | 0.644 | 0.666 | 0.704 | 0.138 | 0.667 | 0.332 | 1602.9 / 3666.0 | 282.9 | 1.555 | 933 | 1357 | 94 | 37.6 |
| clip_b32 | 0.621 | 0.721 | 0.746 | 0.660 | 0.680 | 0.721 | 0.076 | 0.700 | 0.353 | 428.3 / 2900.9 | 148.6 | 0.341 | 1523 | 2024 | 351 | 9.4 |
| clip_b16 | CHƯA ĐO | | | | | | | | | | | | | | | |
| openclip_b32_laion2b | CHƯA ĐO | | | | | | | | | | | | | | | |
| siglip_b16 | 0.704 | 0.833 | 0.887 | 0.760 | 0.790 | 0.833 | 0.055 | 0.767 | 0.355 | 190.0 / 213.8 | 204.9 | 0.549 | 1750 | 2431 | 372 | 14.1 |
| fashionclip | 0.704 | 0.829 | 0.871 | 0.757 | 0.784 | 0.829 | 0.062 | 0.767 | 0.378 | 294.2 / 390.1 | 168.9 | 0.441 | 1270 | 1597 | 351 | 9.4 |
| marqo_fashionsiglip | CHƯA ĐO | | | | | | | | | | | | | | | |
| dinov2_s | 0.750 | 0.846 | 0.883 | 0.791 | 0.813 | 0.846 | 0.043 | 0.692 | 0.307 | 288.8 / 1923.7 | 172.2 | 0.282 | 972 | 1446 | 88 | 7.0 |

**Bảng A2 (theo nhóm)**

| Model | R@5 giày | R@5 quần áo | R@5 mũ | R@5 phụ kiện | Macro R@5 | CTE@5 | R@5 (hard_cross_type) | CTE@5 (hard) | cat P@5 giày | cat P@5 quần áo | cat P@5 mũ | cat P@5 phụ kiện | cat SubP@5 | R@5 ảnh ngoài đời |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| resnet50 | 0.617 | 0.683 | 0.733 | 0.783 | 0.704 | 0.138 | 0.906 | 0.177 | 0.287 | 0.240 | 0.393 | 0.407 | 0.925 | CHƯA ĐO |
| clip_b32 | 0.683 | 0.817 | 0.700 | 0.683 | 0.721 | 0.076 | 0.906 | 0.109 | 0.347 | 0.253 | 0.307 | 0.507 | 0.937 | CHƯA ĐO |
| siglip_b16 | 0.833 | 0.867 | 0.783 | 0.850 | 0.833 | 0.055 | 0.906 | 0.091 | 0.333 | 0.233 | 0.373 | 0.480 | 0.968 | CHƯA ĐO |
| fashionclip | 0.733 | 0.833 | 0.883 | 0.867 | 0.829 | 0.062 | 0.981 | 0.079 | 0.380 | 0.267 | 0.393 | 0.473 | 0.962 | CHƯA ĐO |
| dinov2_s | 0.833 | 0.867 | 0.833 | 0.850 | 0.846 | 0.043 | 0.943 | 0.060 | 0.347 | 0.173 | 0.353 | 0.353 | 0.948 | CHƯA ĐO |
<!-- /BANG_A_RESULTS -->

Định nghĩa cột: R@K/MRR@10/NDCG@10/Macro R@5/CTE@5 trên tầng instance; `cat Hit@5`, `cat P@5` trên tầng category (SP khác, cùng articleType+màu). Latency "Embed truy vấn" = 1 ảnh, batch 1, gồm tiền xử lý; "Embed catalog" = tổng thời gian embed khối / số ảnh (batch 32).

## 2. Type gate I19 (có/không gate, split test)

<!-- GATE_RESULTS -->
| Model | Gate | Độ chính xác gate (test) | τ chọn trên val | R@5 trước → sau | Macro R@5 trước → sau | CTE@5 trước → sau | R@5 hard trước → sau | cat P@5 trước → sau | cat CTE@5 trước → sau |
|---|---|---|---|---|---|---|---|---|---|
| resnet50 | centroid | 0.886 | 0.9 | 0.704 → 0.679 | 0.704 → 0.679 | 0.138 → 0.119 | 0.906 → 0.792 | 0.332 → 0.330 | 0.010 → 0.018 |
| clip_b32 | zeroshot | 0.961 | 0.9 | 0.721 → 0.717 | 0.721 → 0.717 | 0.076 → 0.068 | 0.906 → 0.887 | 0.353 → 0.353 | 0.015 → 0.017 |
| clip_b32 | centroid | 0.872 | 0.9 | 0.721 → 0.717 | 0.721 → 0.717 | 0.076 → 0.072 | 0.906 → 0.887 | 0.353 → 0.353 | 0.015 → 0.015 |
| siglip_b16 | zeroshot | 0.972 | 0.9 | 0.833 → 0.829 | 0.833 → 0.829 | 0.055 → 0.044 | 0.906 → 0.887 | 0.355 → 0.355 | 0.000 → 0.000 |
| siglip_b16 | centroid | 0.936 | 0.9 | 0.833 → 0.829 | 0.833 → 0.829 | 0.055 → 0.052 | 0.906 → 0.887 | 0.355 → 0.355 | 0.000 → 0.000 |
| fashionclip | zeroshot | 0.956 | 0.9 | 0.829 → 0.821 | 0.829 → 0.821 | 0.062 → 0.044 | 0.981 → 0.943 | 0.378 → 0.378 | 0.002 → 0.000 |
| fashionclip | centroid | 0.917 | 0.9 | 0.829 → 0.821 | 0.829 → 0.821 | 0.062 → 0.058 | 0.981 → 0.943 | 0.378 → 0.378 | 0.002 → 0.008 |
| dinov2_s | centroid | 0.914 | 0.9 | 0.846 → 0.796 | 0.846 → 0.796 | 0.043 → 0.083 | 0.943 → 0.830 | 0.307 → 0.307 | 0.005 → 0.005 |
<!-- /GATE_RESULTS -->

## 3. Ngưỡng τ_v và ảnh ngoài phạm vi

<!-- OOD_RESULTS -->
| Model | top-1 cos instance (p05/p50) | top-1 cos category (p05/p50) | top-1 cos OOD (p50/p95) | AUROC category vs OOD | τ_v (p05 val) | Giữ in-scope (test) | Loại OOD (test) | Loại OOD @ τ_v=0,25 | Giữ in-scope @ 0,25 |
|---|---|---|---|---|---|---|---|---|---|
| resnet50 | 0.537/0.835 | 0.742/0.866 | 0.519/0.647 | 1.000 | 0.690 | 0.983 | 1.000 | 0.000 | 1.000 |
| clip_b32 | 0.826/0.934 | 0.885/0.938 | 0.804/0.839 | 1.000 | 0.875 | 0.992 | 1.000 | 0.000 | 1.000 |
| siglip_b16 | 0.784/0.898 | 0.829/0.894 | 0.669/0.743 | 1.000 | 0.809 | 0.967 | 1.000 | 0.000 | 1.000 |
| fashionclip | 0.615/0.874 | 0.795/0.869 | 0.600/0.676 | 1.000 | 0.776 | 0.983 | 1.000 | 0.000 | 1.000 |
| dinov2_s | 0.575/0.869 | 0.756/0.893 | 0.386/0.534 | 1.000 | 0.733 | 0.958 | 1.000 | 0.000 | 1.000 |
<!-- /OOD_RESULTS -->

Phân tích thêm (`results/tau_v_analysis.json`, `src/scripts/tau_v_analysis.py`): ngưỡng mặc định **τ_v = 0,25 của thiết kế chung không loại được ảnh ngoài phạm vi nào (0 %) với mọi model** vì cosine top-1 của ảnh đồng hồ/mỹ phẩm vẫn ≥ 0,39–0,80 tuỳ model. Với FashionCLIP, chọn τ_v = max(top-1 của OOD val) + 0,01 = **0,704** → trên test loại 100 % OOD, giữ 100 % truy vấn category và 84,2 % truy vấn instance (các truy vấn bị loại chủ yếu là biến đổi `background`/`lowres_jpeg`). **Đề xuất Trung/Hoàng đổi τ_v theo model** (giá trị nằm trong `indexes/<model>/config.json`).

## 4. Nhận xét

1. **Thứ hạng tầng instance (macro R@5, test)**: DINOv2-S (0,846) > SigLIP B/16 (0,833) > FashionCLIP (0,829) > CLIP B/32 (0,721) > ResNet-50 (0,704). Chênh giữa 3 model đầu ≤ 1,7 điểm, **dưới ngưỡng 5 điểm** mà Sheet 3 đặt ra để coi là khác biệt đáng kể (với 60 truy vấn/nhóm, mỗi truy vấn = 1,7 điểm).
2. **Tầng category (SP khác cùng loại + màu)**: FashionCLIP tốt nhất (cat Hit@5 0,767, P@5 0,378), SigLIP sát sau (0,767 / 0,355) – DINOv2 kém hơn rõ (0,692 / 0,307). Tức là DINOv2 giỏi "tìm lại đúng ảnh bị biến dạng" (tương đồng hình dáng/kết cấu), còn FashionCLIP giỏi "tìm SP tương tự về ngữ nghĩa" – đúng hơn với nhu cầu mua sắm khi SP người dùng chụp *không có sẵn* trong catalog.
3. **Fine-tune miền thắng CLIP gốc rõ** (FashionCLIP vs CLIP B/32, cùng kiến trúc ViT-B/32): +10,8 điểm macro R@5, ở **mọi nhóm** (giày 0,683→0,733; quần áo 0,817→0,833; mũ 0,700→0,883; phụ kiện 0,683→0,867). Giả thuyết "lợi thế co lại ở mũ/phụ kiện" **không đúng** trên dữ liệu này. Lưu ý rò rỉ: FashionCLIP/Marqo có thể đã thấy dữ liệu cùng nguồn Kaggle (US_19) → số có thể lạc quan.
4. **ResNet-50** có CTE@5 cao nhất (0,138, gần gấp đôi CLIP) – xác nhận vai trò baseline; embed cũng chậm nhất trên CPU dùng chung.
5. **Điểm yếu chung theo kiểu biến đổi** (`results/errors_<model>.md`): với FashionCLIP, R@5 = 1,0 cho crop/xoay/lật/đổi màu, nhưng chỉ **0,656 (nền khác), 0,667 (tổ hợp), 0,500 (ảnh nén/độ phân giải thấp)**; CLIP B/32 còn tệ hơn (0,344 / 0,389 / 0,417). SigLIP B/16 bền hơn hẳn với nền khác (**0,906**) và tổ hợp (0,750) nhưng sụp ở ảnh nén/độ phân giải thấp (**0,278**). Đây chính là các điều kiện của ảnh người dùng → kỳ vọng số trên ảnh ngoài đời thấp hơn bảng trên, và thứ hạng FashionCLIP/SigLIP có thể đảo khi đo ảnh thật.
6. **Type gate** zero-shot đúng ~95–96 % (FashionCLIP, CLIP B/32) nhưng lọc cứng không tăng Recall trên ảnh studio; chi tiết ở US_45.
7. **Latency**: search FAISS Flat < 1 ms cho 4.593 vector; chi phí nằm ở embed ảnh (vài trăm ms/ảnh trên 2 CPU dùng chung, p95 dao động mạnh do tải nền của 4 tác nhân khác). Số latency chỉ dùng để so sánh tương đối giữa các model.

## 5. Đề xuất chọn model (đầu vào cho US_25 – bảng chấm điểm có trọng số của Trung)
- **Chọn FashionCLIP** làm model chung cho demo (tạm thời): macro R@5 kém DINOv2 1,7 điểm và SigLIP 0,4 điểm (không đáng kể) nhưng cao nhất ở tầng category (P@5 0,378), có text tower (type gate zero-shot I19, tìm bằng chữ tiếng Anh), 512 chiều (index 9,4 MB, RSS sau nạp 1.270 MB so với 1.750 MB của SigLIP).
- **SigLIP B/16 là ứng viên thay thế mạnh**: CTE@5 thấp hơn (0,055), bền với nền khác (0,906 vs 0,656) – nếu ảnh ngoài đời chủ yếu là "đặt trên nền khác" thì nên chuyển sang SigLIP. Quyết định cuối chờ số trên ảnh ngoài đời.
- DINOv2-S giữ làm phương án thuần ảnh/ensemble nếu đo trên ảnh ngoài đời cho thấy instance quan trọng hơn.
- Không dựng 2 index song song (chênh < 5 điểm).

## 6. Hạn chế & việc còn lại
- Truy vấn là ảnh studio 60×80 biến đổi tổng hợp → cột "R@5 ảnh ngoài đời" **CHƯA ĐO** (thiếu 80–100 ảnh nhóm tự chụp).
- Model chưa chạy (thời gian CPU trên máy 2 CPU dùng chung, máy khởi động lại 2 lần giữa chừng): xem các dòng `CHƯA ĐO` trong Bảng A; chạy tiếp bằng `python src/scripts/bench_image_embed.py --model <id>` (embed theo khối, tự chạy tiếp từ khối đã lưu).
- ViT-L/14, SigLIP 2, M-CLIP không chạy theo ràng buộc máy/phạm vi (US_19).
- bf16 autocast đã thử trên CLIP B/16 (32 ảnh): không nhanh hơn fp32 khi máy đang tải (`results/bf16_probe.json`) → giữ fp32.
