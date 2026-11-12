# US_19 – Khảo sát các phiên bản embedding ảnh (Sheet 3 – Bảng A)

| Mục | Nội dung |
|---|---|
| Mã US | US_19 (Owner: Khoa, Support: Hoàng) – Sprint 1, 3.0 pt |
| Mục tiêu | Chọn danh sách ứng viên có cơ sở để benchmark (US_22) |
| Đầu ra | Bảng A (thông tin) + cột kết quả lấy từ benchmark thật; registry code `src/msa/embed/image_embedders.py` |
| Tiêu chí nghiệm thu | ≥ 6 phiên bản, mỗi phiên bản có lý do đưa vào so sánh ✔ (11 phiên bản; 8 đã nạp thử được, **5 đã benchmark thật**) |
| Trạng thái | **Hoàn thành**. Thông tin năm/tổ chức/dữ liệu/license tổng hợp từ paper & model card đã biết – mục không chắc gắn `[cần xác minh]`. Số chiều và số tham số của 8 model đã nạp thử là **đo thật** khi nạp model (`results/prefetch_models.json`). |

## Tóm tắt 5 dòng
1. Khảo sát 8 model embedding ảnh (ResNet-50, CLIP B/32, CLIP B/16, OpenCLIP LAION-2B, SigLIP B/16, FashionCLIP, Marqo-FashionSigLIP, DINOv2-S): năm, kiến trúc, số chiều, điểm mạnh/yếu.
2. Mỗi model có lý do đưa vào so sánh (baseline, đa phương thức, chuyên thời trang, tự giám sát).
3. 5/8 đã benchmark thật ở US_22; 3 model còn lại CHƯA ĐO do thời gian CPU.
4. Kết quả xếp hạng có trọng số ở US_25: DINOv2-S hạng 1.
5. Thông số công khai (năm, số chiều) gắn `[cần xác minh]` khi chưa đối chiếu model card.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## A. Thông tin phiên bản

Cột "Dim" và "Tham số visual" của các dòng **đã chạy** là đo thật (đếm `numel()` của nhánh ảnh); các dòng chưa chạy lấy theo tài liệu công bố.

| # | Phiên bản (id trong registry) | Tổ chức / Năm | Kiến trúc | Dữ liệu huấn luyện | Dim | Tham số visual | Hiểu text? | License | Điểm mạnh | Điểm yếu | Vì sao đưa vào so sánh | Đã chạy? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ResNet-50 (`resnet50`, timm `resnet50.tv2_in1k` = trọng số torchvision IMAGENET1K_V2) | Microsoft Research (He và cộng sự), CVPR 2016 | CNN 50 lớp, global avg pool | ImageNet-1K (1,28 M ảnh, nhãn) | 2048 | 23,5 M | Không | BSD-3 (torchvision) `[cần xác minh]` | Nhẹ, nhanh trên CPU, baseline kinh điển | Đặc trưng theo nhãn ImageNet, ít ngữ nghĩa thời trang; không có text → không làm type gate zero-shot | BASELINE chứng minh lợi ích mô hình ảnh–text | Có |
| 2 | CLIP ViT-B/32 (`clip_b32`, open_clip `ViT-B-32-quickgelu`/`openai`) | OpenAI (Radford và cộng sự), ICML 2021 | ViT-B, patch 32, 224 px | WIT 400 M cặp ảnh–text | 512 | 87,8 M | Có (EN) | MIT | Nhanh, zero-shot tốt, phổ biến | Patch 32 mất chi tiết nhỏ | Lựa chọn mặc định theo đề bài | Có |
| 3 | CLIP ViT-B/16 (`clip_b16`, `ViT-B-16-quickgelu`/`openai`) | OpenAI, 2021 | ViT-B, patch 16 | WIT 400 M | 512 | 86,2 M | Có (EN) | MIT | Giữ chi tiết tốt hơn B/32 | ~4× FLOPs so với B/32 | Đánh đổi chính xác – tốc độ trong cùng họ | Nạp được; **benchmark CHƯA ĐO** (thiếu thời gian CPU) |
| 4 | CLIP ViT-L/14 | OpenAI, 2021 | ViT-L, patch 14 | WIT 400 M | 768 | ~304 M (công bố) | Có | MIT | Mạnh nhất họ CLIP gốc | Quá nặng cho máy 2 CPU/7 GB dùng chung | Cận trên chất lượng | **Không** – ràng buộc máy (mục 7.1 thiết kế chung cấm ViT-L trên toàn catalog) |
| 5 | OpenCLIP ViT-B/32 LAION-2B (`openclip_b32_laion2b`, `laion2b_s34b_b79k`) | LAION / mlfoundations (Cherti và cộng sự), CVPR 2023 | ViT-B/32 | LAION-2B (EN), 34 B mẫu đã xem | 512 | 87,8 M | Có | MIT | Bản mở, dữ liệu lớn hơn CLIP gốc | Dữ liệu web lọc ít | Kiểm tra bản open-source thay CLIP gốc; cũng là gốc của FashionCLIP 2.0 `[cần xác minh]` | Nạp được; **benchmark CHƯA ĐO** |
| 6 | SigLIP B/16-224 (`siglip_b16`, open_clip `ViT-B-16-SigLIP`/`webli`) | Google (Zhai và cộng sự), ICCV 2023 | ViT-B/16, sigmoid loss | WebLI | 768 | 92,9 M | Có (EN) | Apache-2.0 | Thường tốt hơn CLIP cùng cỡ | Text tower lớn hơn (tổng 203 M tham số) | Đại diện thế hệ sau CLIP | Có |
| 7 | SigLIP 2 | Google (Tschannen và cộng sự), 2025 | ViT (nhiều cỡ), sigmoid + mục tiêu dày đặc | WebLI đa ngôn ngữ | tuỳ bản | tuỳ bản | Có (đa ngôn ngữ) | Apache-2.0 `[cần xác minh]` | Đa ngôn ngữ (có thể hỗ trợ truy vấn tiếng Việt) | Mới; cần transformers mới | Ứng viên mới nhất họ SigLIP | **Không** – để vòng sau (thời gian CPU) |
| 8 | FashionCLIP (`fashionclip`, HF `patrickjohncyh/fashion-clip`) | Farfetch / Coveo (Chia và cộng sự), Scientific Reports 2022 | CLIP ViT-B/32 fine-tune | Catalog thời trang Farfetch (~700–800 K SP) `[cần xác minh]` | 512 | 87,8 M | Có (EN) | MIT `[cần xác minh]` | Chuyên miền thời trang | Dữ liệu hàng cao cấp, lệch hàng phổ thông VN | Thử xem fine-tune miền có thắng CLIP gốc ở từng nhóm | Có |
| 9 | Marqo-FashionSigLIP (`marqo_fashionsiglip`, open_clip `hf-hub:Marqo/marqo-fashionSigLIP`) | Marqo, 2024 | ViT-B/16-SigLIP fine-tune (GCL) | Dữ liệu thời trang nhiều nguồn `[cần xác minh]` | 768 | 92,9 M | Có (EN) | Apache-2.0 `[cần xác minh]` | Tác giả công bố vượt FashionCLIP 2.0 | **Nguy cơ rò rỉ**: đánh giá của tác giả có bộ KAGL (cùng nguồn Kaggle với FPI) | Ứng viên chuyên miền thế hệ mới | Nạp được; **benchmark CHƯA ĐO** |
| 10 | DINOv2 ViT-S/14 (`dinov2_s`, HF `facebook/dinov2-small`, CLS token) | Meta AI (Oquab và cộng sự), 2023 | ViT-S/14 self-supervised | LVD-142M (không nhãn) | 384 | 22,1 M | Không | Apache-2.0 | Tương đồng hình dáng/kết cấu tốt, nhẹ | Không có text tower; không zero-shot | Ứng viên thuần ảnh – hình dáng có quan trọng hơn ngữ nghĩa? | Có |
| 11 | M-CLIP (Multilingual CLIP) | Carlsson và cộng sự, LREC 2022 | Text encoder XLM-R căn theo CLIP; nhánh ảnh = CLIP | Dữ liệu dịch máy | 512/640/768 tuỳ bản | (nhánh ảnh = CLIP) | Có (đa ngôn ngữ) | MIT `[cần xác minh]` | Truy vấn text tiếng Việt vào không gian ảnh CLIP | Không đổi gì cho ảnh→ảnh | Chỉ có ý nghĩa cho text→ảnh tiếng Việt | **Không** – ngoài phạm vi benchmark ảnh→ảnh |

Ứng viên bổ sung nên xem ở vòng sau (chưa chạy): MobileCLIP (Apple, 2024 – tối ưu cho thiết bị/CPU), EVA-CLIP (BAAI, 2023) `[cần xác minh]`.

## B. Cột kết quả (đo thật – xem chi tiết US_22)

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

## C. Nhận xét chọn ứng viên
- 5 model đã benchmark thật (ResNet-50, CLIP B/32, FashionCLIP, DINOv2-S, SigLIP B/16) trên cùng catalog 4.593 ảnh, cùng tiền xử lý, cùng FAISS `IndexFlatIP`; CLIP B/16, OpenCLIP LAION-2B, Marqo-FashionSigLIP đã nạp được nhưng chưa đủ thời gian CPU (≈ 15–25 phút/model trên máy dùng chung, máy khởi động lại 2 lần).
- Không chạy ViT-L/14, SigLIP 2, M-CLIP vì lý do nêu trong bảng (không phải vì kết quả kém).
