# US_10 – Tổng hợp nguồn & đánh giá tính chính thống (Sheet 1, Mục C và E)

| Mục | Nội dung |
|---|---|
| Mã US | US_10 (Owner: Tuấn Đạt, Support: Trung) – Sprint 1, 2.0 pt |
| Mục tiêu | Bảng nguồn: URL, tổ chức, năm, loại, license, số lượng THẬT đã lấy, dùng cho nhóm nào, mức tin cậy |
| Đầu ra | Mục C (bảng nguồn) + Mục E (thang 5 mức + chấm từng nguồn) |
| Tiêu chí nghiệm thu | Mọi nguồn đều có URL, license và mức tin cậy |
| Trạng thái | **Hoàn thành** cho các nguồn đã dùng; license có nhãn `[cần xác minh]` phải được Trung/Tuấn Đạt mở trang gốc đọc lại trước khi nộp |

## Tóm tắt 5 dòng
1. Bảng 12 nguồn, mỗi nguồn có URL, tổ chức/năm, license, mức tin cậy (thang 5 mức ở Mục E).
2. Đã dùng thật 2 nguồn: Fashion Product Images (mức 2) và ViMRHP (mức 1, có paper NLDB 2025).
3. Các nguồn dự phòng (Amazon Reviews 2023, ABO, Clothing Dataset CC0, DeepFashion) chưa dùng vì bị chặn hoặc cần xin quyền.
4. License nào chưa đọc văn bản gốc được gắn `[cần xác minh]` – phải đọc lại trước khi nộp.
5. Số ViMRHP: 428 SP nạp vào kho (bỏ đồng hồ), trong đó 361 SP thuộc 4 nhóm (QUYET_DINH mục G2).
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Số lượng lấy từ `/home/claude/work/shared_data/stats.json` (dữ liệu `shared_data v1`, `prep_shared_data.py` seed 42) và
`results/clean_report.json` (sau làm sạch). Xoá hàng "VÍ DỤ" của sheet trước khi dán bảng này.

## Mục E – Thang đánh giá tính chính thống (giữ của sheet, thêm tiêu chí chấm)

| Mức | Định nghĩa | Tiêu chí kiểm |
|---|---|---|
| 1 – Học thuật / chính thức | Tổ chức nghiên cứu/công ty công bố kèm paper + license rõ | Có paper (arXiv/hội nghị) **và** file license |
| 2 – Cộng đồng có kiểm duyệt | Dataset trên Kaggle/HF; tin cậy phụ thuộc người đăng + nguồn gốc gốc | Truy được nguồn gốc gốc; license ghi trên trang |
| 3 – Công khai từ sàn TMĐT | Dữ liệu thật nhưng ToS sàn hạn chế | Ghi ngày lấy, robots/ToS |
| 4 – Nhóm tự tạo | Nhóm kiểm soát, phải ghi cách tạo | Có `origin`, người tạo, quy trình |
| 5 – Không rõ nguồn | Không biết ai tạo, không license | **Không dùng** |

## Mục C – Bảng nguồn (số liệu thật)

| Nguồn | URL | Tổ chức / năm | Loại | Mức (E) | License / điều khoản | SP lấy | Ảnh | Review | Ngôn ngữ | Dùng cho | Đặc điểm & vấn đề chất lượng (đo thật) | Phụ trách |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fashion Product Images (small) – mirror HF | https://huggingface.co/datasets/ashraq/fashion-product-images-small ; gốc: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset | Param Aggarwal (Kaggle, ~2019, dữ liệu Myntra); mirror: ashraq (HF) | Public dataset | **2** (cộng đồng; dữ liệu gốc là catalog Myntra) | `[cần xác minh]` – trang Kaggle cần đọc Data Card; bản mirror HF không ghi license rõ. Chỉ dùng học thuật, không phát hành lại ảnh | 4.593 (từ 44.072 dòng gốc) → **4.385 sau làm sạch** | 4.593 (1 ảnh/SP) | 0 | EN | Catalog + visual search 4 nhóm | Ảnh **60×80 px** 100% (4.556 RGB, 37 grayscale); 0 ảnh lỗi; 20 cặp ảnh trùng MD5; pHash va chạm nhiều giữa SP khác nhau; "Caps" lẫn 18 beanie, "Hat" là beanie/fedora; thiếu giá, size, mô tả, review; brand bị cắt 1 từ ("Red Tape" → "Red") | Hoàng / Tuấn Đạt |
| ViMRHP – Vietnamese Multimodal Review Helpfulness Prediction | https://huggingface.co/datasets/trucmtnguyen/ViMRHP ; paper arXiv 2505.07416 | Nguyen và cộng sự, NLDB 2025 (dữ liệu Shopee VN 2023–2024) | Public dataset (học thuật) | **1** | **CC BY-NC-ND 4.0** (phi thương mại, không phát hành bản phái sinh) – theo trang HF/paper `[cần xác minh lại bản chính thức]` | 509 (428 trong phạm vi, bỏ 81 Đồng hồ) | 0 tải được (URL ảnh susercontent bị chặn) | 11.009 (9.403 thuộc 428 SP) | VI | Product QA, tóm tắt review (US_36), benchmark LLM (US_24) | Review ngắn (TB 146 ký tự, trung vị 132); rating lệch mạnh (5★ = 10.284/11.009 = 93,4%); **262 review spam/quảng cáo** bị lọc (luật regex, `product_review_summary.json`); teencode/không dấu; không có giá/size/mô tả; "PhuKienNu" lẫn khuyên tai, kẹp tóc | Chiến / Tuấn Đạt |
| Amazon Reviews 2023 | https://amazon-reviews-2023.github.io ; HF `McAuley-Lab/Amazon-Reviews-2023` | McAuley Lab (UCSD), 2024 – Hou và cộng sự, arXiv 2403.03952 | Public dataset (học thuật) | 1 | Điều khoản dùng cho nghiên cứu `[cần xác minh]` | 0 (chưa dùng) | 0 | 0 | EN | Dự phòng: bù mũ (lọc "Hats & Caps"), có giá USD | Chưa tải – ưu tiên nếu nhóm cần đủ quota mũ 300 | Hoàng |
| Amazon Berkeley Objects (ABO) | https://amazon-berkeley-objects.s3.amazonaws.com/index.html | Amazon + UC Berkeley, CVPR 2022 (Collins và cộng sự) | Public dataset | 1 | CC BY-NC 4.0 (license công bố của ABO; Tác nhân 3 bỏ nhãn cần xác minh theo đối chiếu chéo, chưa mở lại trang gốc) | 0 | 0 | 0 | EN (đa ngôn ngữ metadata) | Không dùng | Chủ yếu đồ gia dụng/nội thất; S3 bị chặn từ môi trường | – |
| Clothing Dataset (A. Grigorev) | https://github.com/alexeygrigorev/clothing-dataset | Alexey Grigorev, 2020 | Public dataset | 2 | **CC0** (theo README) `[cần xác minh]` | 0 (chưa dùng) | 0 | 0 | – | Dự phòng: ảnh đời thực + Hat (bù mũ, query ngoài đời) | ~5.000 ảnh, 20 lớp; không giá/mô tả | Hoàng |
| DeepFashion (CUHK MMLab) | https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html | Liu và cộng sự, CVPR 2016 | Public dataset (xin quyền) | 1 | Phi thương mại, phải ký thoả thuận `[cần xác minh]` | 0 | 0 | 0 | EN | Không dùng ở Đồ án 1 | Chỉ quần áo; chưa xin quyền | – |
| CAMEO / ViEcom-Rec (NTCIR-19) | Trang nhiệm vụ NTCIR-19 `[cần xác minh URL]` | NTCIR, 2025–2026 | Dataset cuộc thi | 2–3 | Theo điều khoản đăng ký cuộc thi `[cần xác minh]` | 0 | 0 | 0 | VI | Ghi nhận cho Đồ án 2 | Cần đăng ký tham gia | – |
| Shopee product listings (Zenodo) | Zenodo `[cần xác minh DOI]` | Không rõ | Dataset nhỏ | 3 | Theo trang Zenodo | 0 (loại) | 0 | 0 | VI | Loại | Chỉ ~30 dòng → không đủ dùng | – |
| Crawl Tiki | https://tiki.vn | – | Crawl | 3 | ToS Tiki | 0 | 0 | 0 | VI | Loại ở lượt này | **HTTP 403 với IP cloud** | – |
| Ảnh tự chụp (US_11) | `data/eval/visual_queries/` | Nhóm MSA, 11/2026 | Tự tạo | 4 | Xin phép người chụp/người trong ảnh | – | **CHƯA ĐO** (mục tiêu 80–100) | – | – | Tập test ngoài đời | Chưa có | Tuấn Đạt + Chiến |
| Bộ câu benchmark LLM (36 câu) | `eval/bench_qa.jsonl` | Tác nhân AI (vai Tuấn Đạt), 05/11/2026, từ review ViMRHP thật | Tự tạo | 4 | Kế thừa CC BY-NC-ND của ViMRHP (chỉ nội bộ) | 36 SP | – | 216 review làm ngữ cảnh | VI | Benchmark LLM (US_24) | `origin=tac_nhan_AI_viet_tay_tu_review_that`, **chưa có người thật duyệt** | Tuấn Đạt |
| eval_router (78 câu) | `03_Chien/eval/eval_router.jsonl` (bản chụp `eval/eval_router_snapshot_from_Chien.jsonl`, sha256 b6cf9600…) | Tác nhân AI (vai Chiến), 11/2026 | Tự tạo | 4 | Nội bộ | 78 câu | – | – | VI | Router/Fallback (Bảng D2) | `origin=viet_tay_tac_nhan`, annotator trống | Chiến |
| **TỔNG đã dùng thật** | | | | | | **4.385 SP catalog + 428 SP review** | **4.593 ảnh** | **9.403 review trong phạm vi** | | | | |

Ghi chú: Số SP FPI ban đầu theo nhóm (shared_data v1): footwear 1.400 / clothing 2.200 / accessory 700 / headwear 293.
Sau làm sạch: footwear 1.400 / clothing 2.000 / accessory 700 / headwear 285 (**thiếu 15 so với quota 300**).
