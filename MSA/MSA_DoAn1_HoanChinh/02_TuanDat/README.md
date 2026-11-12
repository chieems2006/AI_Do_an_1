# 02_TuanDat – Dữ liệu, benchmark LLM, UI demo, kiểm thử, báo cáo cuối

Thành viên: **Tuấn Đạt** (vai do tác nhân AI thực hiện, lượt 04–05/11/2026). Dữ liệu: `shared_data v1 (prep_shared_data.py seed 42)`.
Mọi số dưới đây là **đo thật** và trỏ về file; ô không đo được ghi `CHƯA ĐO`. Không có API key trong folder (kiểm `grep -rn "AQ\." .` rỗng).

## 0. Đối chiếu yêu cầu kế hoạch (Tác nhân 2 – 05/11/2026)

Tuấn Đạt là Owner của **10 US** (Backlog). Kết luận: **Đạt 3 · Một phần 5 · Chưa đạt 2** (US_11 cần người thật chụp ảnh; US_28 thuộc Sprint 3).

| US | Đầu ra yêu cầu (DOCS) | File đầu ra | Tiêu chí nghiệm thu (TEST) | Kết quả | Bằng chứng / lý do |
|---|---|---|---|---|---|
| US_04 | Sheet 1 – Mục B | `docs/US_04_phuong_phap_thu_thap.md` | ≥ 6 phương pháp, mỗi cái đủ ưu/nhược/chi phí/pháp lý + Chọn/Không chọn có lý do | **Đạt** | 9 phương pháp, chọn 3; lý do gắn ràng buộc R1–R6 và bằng chứng thật (Tiki 403, Kaggle chặn, quota Gemini) |
| US_08 | `03_clean.py` + báo cáo trước/sau | `src/scripts/03_clean.py`, `results/clean_report.{json,md}`, `docs/US_08_quy_trinh_lam_sach.md` | Ảnh lỗi < 1 %; không còn ảnh trùng; 100 % có category; nhãn sai ≤ 5 % trên mẫu 100 SP/nhóm; không nhóm nào dưới quota | **Một phần** | Đạt: ảnh lỗi 0 %, 100 % có category, xoá 21 SP trùng MD5. Chưa: **mũ 285 < 300**; 122 cặp pHash "review" chưa người xem; kiểm nhãn 400 dòng mới là so tiêu đề tự động (1/100 lệch ở mũ), chưa người thật. Luật tiêu đề của Đạt đúng cho 7 SP mũ nhưng **gán sai 3 đôi boot** thành heel_flat/sneaker (Tác nhân 2 xem ảnh – QUYET_DINH mục A) |
| US_10 | Sheet 1 – Mục C, E | `docs/US_10_bang_nguon_va_tinh_chinh_thong.md` | Mọi nguồn có URL, license, mức tin cậy | **Đạt** | 12 nguồn đủ 3 cột; license nào chưa đọc văn bản gốc gắn `[cần xác minh]` |
| US_11 | `data/eval/visual_queries/` + CSV ground truth | `docs/US_11_huong_dan_tap_anh_ngoai_doi.md`, `eval/visual_queries_ground_truth_template.csv`, `src/scripts/check_visual_queries.py` | ≥ 80 ảnh; mỗi ảnh ≥ 1 SP đúng do 2 người xác nhận; đủ phân bổ từng nhóm | **Chưa đạt** | 0 ảnh – cần người thật chụp và gán nhãn; đã có hướng dẫn + template + script kiểm |
| US_24 | Bảng D (cột kết quả) + Bảng D2 | `src/scripts/bench_llm.py`, `docs/US_24_benchmark_llm.md`, `results/bench_llm_*.jsonl`, `results/bench_llm_summary.json` | Cùng prompt, cùng context, temperature cố định; có log; Gemini đủ số liệu cho cả 2 vai trò | **Một phần** | Đạt: 3 model cùng prompt/context, log jsonl từng câu. Chưa: vai trò router chỉ 14 câu (eval_router có 78); `gemini-3.5-flash` CHƯA ĐO (hết quota – đo trên flash-lite) |
| US_28 | report_final.docx + demo_script.md | `docs/US_28_bao_cao_cuoi_khung.md`, `docs/kich_ban_video_du_phong.md` | Mọi con số truy ngược được về file kết quả | **Chưa đạt** (Sprint 3 – đúng tiến độ) | Mới có khung; các số đã điền đều có cột nguồn |
| US_31 | Component card kết quả | `app/components.py` | Đúng 100 % trường trên 20 SP thử | **Đạt** | 20/20 SP thật đủ 5 trường (`tests/test_components_app.py`). Trên bản A2 test này **skip** vì không đóng gói `results/catalog_clean.parquet` – chạy `03_clean.py` để sinh lại |
| US_36 | `product_review_summary.json` | `src/scripts/summarize_reviews.py`, `results/product_review_summary.json`, `results/us36_kiem_tay_20sp.csv` | Kiểm tay 20 SP: không có thông tin bịa | **Một phần** | Bản baseline (trích từ khoá, có comment_id) không thể sinh ý ngoài review. Bản LLM: **3/93 ý không có trong review (3/20 SP)** → bản LLM chưa đạt; kiểm do tác nhân AI, chưa người thật |
| US_43 | `app.py` | `app/app.py`, `app/mock_api.py` | Chạy local 1 lệnh; đủ 4 luồng ảnh/hỏi đáp/tìm/so sánh | **Một phần** | 1 lệnh + 4 luồng chạy qua **API giả lập**; chưa nối API thật của Hoàng. Đã thêm nhãn "Thông báo hệ thống" cho `source="fallback"` (Tác nhân 2) |
| US_46 | test_report.md | `docs/US_46_test_plan.md`, `docs/test_report.md` | Không còn bug nghiêm trọng khi feature freeze | **Một phần** (Sprint 3) | 20 kịch bản; 4 kịch bản có test tự động pass; chưa chạy tích hợp |

**Mâu thuẫn liên quan:** mũ 285 là **con số chuẩn** của nhóm (QUYET_DINH mục A); UI đã xử lý `source="fallback"` (mục D – trước đây hiện nhầm "Từ dữ liệu cửa hàng"); token Gemini của Bảng D tính trên "100 câu QA", không so trực tiếp với số "100 lượt hội thoại" của Trung (mục F).

## 1. Truy vết US → file → trạng thái → số liệu thật → việc còn lại (bản của thành viên)

| US | Đầu ra chính | Trạng thái | Số liệu THẬT (file) | Việc còn lại (người thật/dữ liệu thật) |
|---|---|---|---|---|
| US_04 | `docs/US_04_phuong_phap_thu_thap.md` | Hoàn thành | 9 phương pháp, chọn 3; bằng chứng: Tiki 403, Kaggle chặn → mirror HF, ảnh Shopee chặn, quota Gemini 20/ngày | Dán vào Sheet 1 Mục B |
| US_08 | `src/scripts/03_clean.py`, `data/category_map.csv`, `docs/US_08_quy_trinh_lam_sach.md`, `results/catalog_clean.parquet` | Hoàn thành (chạy thật) – 2 tiêu chí mở | 4.593 → **4.385 SP**; ảnh lỗi 0%; 20 trùng MD5, xoá 21; 3.937 cặp pHash ≤ 4 phần lớn là SP khác nhau; 27 nhãn mũ sửa theo tiêu đề (beanie 21, wide_brim 6); mũ 285 < 300 (`results/clean_report.json`) | 2 người kiểm `results/label_check_sample.csv` (400 dòng) + 122 cặp `review` trong `dup_pairs.csv`; bổ sung nguồn mũ; Trung chốt lá `heel_flat`/`beanie` |
| US_10 | `docs/US_10_bang_nguon_va_tinh_chinh_thong.md` | Hoàn thành (license có `[cần xác minh]`) | 12 nguồn, đã dùng 4.385 SP catalog + 428 SP/9.403 review ViMRHP | Đọc lại license gốc FPI/ABO/Amazon |
| US_11 | `docs/US_11_huong_dan_tap_anh_ngoai_doi.md`, `eval/visual_queries_ground_truth_template.csv`, `src/scripts/check_visual_queries.py` | Khung sẵn – cần dữ liệu thật | Số ảnh: **CHƯA ĐO (0)** | Nhóm chụp 80–100 ảnh, 2 người gán nhãn, chạy script kiểm |
| US_24 | `src/scripts/bench_llm.py`, `src/msa_td/gemini_client.py`, `eval/bench_qa.jsonl`, `docs/US_24_benchmark_llm.md` | Một phần (3 model đo thật) | Flash-Lite faithfulness 0,939 / halluc. 0,111 / từ chối đúng 7/7; Gemma 4 26B (API) 0,992 / 0,031 / 6/6; Qwen2.5-0.5B 0,255 / 0,333 / 1/3; Router Flash-Lite acc 0,857 (14 câu), p95 0,9 s (`results/bench_llm_summary.json`, `bench_llm_common_subset.json`) | `gemini-3.5-flash` CHƯA ĐO (hết quota); router đủ 78 câu; người chấm lại judge; đơn giá đã xác minh |
| US_28 | `docs/US_28_bao_cao_cuoi_khung.md`, `docs/kich_ban_video_du_phong.md` | Khung sẵn | Đã điền số chương Dữ liệu + LLM kèm nguồn | Ghép số visual/RAG/cải tiến; dựng `report_final.docx`; quay video N20 |
| US_31 | `app/components.py` | Hoàn thành | Test 20 SP thật: 20/20 đủ 5 trường ảnh/tên/giá/điểm/link (`tests/test_components_app.py`) | Kiểm lại với response API thật (có giá) |
| US_36 | `src/scripts/summarize_reviews.py`, `results/product_review_summary.json`, `docs/US_36_tom_tat_review.md` | Hoàn thành (kiểm tay bởi tác nhân) | Baseline 428 SP, lọc 262 review spam; LLM 20 SP: **3/93 ý không có trong review** (3/20 SP) (`results/us36_kiem_tay_20sp.csv`) | 1 người thật kiểm lại 20 SP |
| US_43 | `app/app.py`, `app/mock_api.py` | Hoàn thành ở chế độ mock | Khởi động 1 lệnh, smoke test HTTP 200 (Gradio 6.31.0); 4 luồng + chat qua mock có test | Nối API thật của Hoàng (`MSA_API_URL`) |
| US_46 | `docs/US_46_test_plan.md`, `docs/test_report.md` | Khung sẵn | 20 kịch bản; T15/T16/T17/T20 đã có test tự động pass | Chạy tích hợp N19, ghi bug |

## 2. Chạy
```bash
python -m pytest -q                                   # 23 passed, 1 skipped khi có catalog_clean.parquet (bản A2: 21 passed, 3 skipped)
python src/scripts/03_clean.py                        # làm sạch thật (~9 s)
python src/scripts/summarize_reviews.py baseline      # tóm tắt review 428 SP (<1 s)
MSA_UI_MOCK=1 python app/app.py                       # UI http://localhost:7860 (bỏ MSA_UI_MOCK khi API chạy)
MSA_ENV_FILE=<file .env chứa GEMINI_API_KEY> python src/scripts/bench_llm.py summary   # các lệnh benchmark: docs/US_24
```
Kết quả pytest lần cuối (05/11/2026): **23 passed, 1 skipped** (bỏ qua `test_gemini_live_one_call`, đánh dấu `live`).
Trên bản A2 (Tác nhân 2, không đóng gói `results/catalog_clean.parquet`): **21 passed, 3 skipped** – 2 test card SP bị skip vì thiếu file nặng; chạy `python src/scripts/03_clean.py` để sinh lại.

## 3. Ngân sách Gemini & sự cố
- Đã dùng **250/250** lời gọi (`results/gemini_budget.json`), trong đó **144 lời gọi bị 429** do quota free tier `gemini-3.5-flash` = 20 request/ngày/project (key dùng chung) và client bản đầu retry 3 lần – đã sửa bằng ngắt mạch 429 (`results/failed/`).
- Phần dùng được: QA Flash-Lite 36, Gemma 4 32, router 14, tóm tắt 4 lô, judge `gemini-2.5-flash` 9 lô + vài lần thử/lỗi.
- Không còn ngân sách cho lượt này → các mục CHƯA ĐO liên quan Gemini chạy lại khi có quota.

## 4. Gợi ý cho thành viên khác
- **Hoàng (LLMGateway):** tái dùng `src/msa_td/gemini_client.py` (cache SQLite, đếm ngân sách, ngắt mạch 429, `error_detail`, hỗ trợ Gemma không nhận systemInstruction); `gemini-3.5-flash-lite` không nhận `thinkingBudget=0`.
- **Chiến (RAG):** lọc review spam trước khi chunk (`summarize_reviews.is_spam`) – lỗi hallucination của cả hai model API đều đến từ 1 review spam.
- **Trung (taxonomy):** FPI "Caps" lẫn beanie, "Hat" là beanie/fedora → cần lá `beanie`, `wide_brim`, `heel_flat`.
- **Khoa (visual):** dùng `results/catalog_clean.parquet` (4.385 SP); không dùng pHash để lọc trùng trên ảnh 60×80.
