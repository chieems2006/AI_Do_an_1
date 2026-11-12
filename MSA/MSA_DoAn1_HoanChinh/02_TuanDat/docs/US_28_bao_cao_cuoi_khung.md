# US_28 – Khung báo cáo cuối Đồ án 1 (report_final) + demo_script

| Mục | Nội dung |
|---|---|
| Mã US | US_28 (Owner: Tuấn Đạt, Support: Trung) – Sprint 3, 5.0 pt |
| Mục tiêu | Tổng hợp kết quả benchmark, cải tiến trước/sau, hạn chế, hướng phát triển để nộp & bảo vệ |
| Đầu ra | `report_final.docx` (dựng từ khung này ở N20) + `docs/kich_ban_video_du_phong.md` (demo_script) |
| Tiêu chí nghiệm thu | **Mọi con số trong báo cáo truy ngược được về file kết quả** |
| Trạng thái | **Khung sẵn** – đã điền các số đo thật hiện có (phần dữ liệu, LLM); phần visual/RAG/cải tiến chờ Khoa, Chiến, Hoàng, Trung |

Quy ước: mỗi số có cột **Nguồn** = đường dẫn file + khoá JSON/cột. Ô chưa có số ghi `CHƯA ĐO`. Dữ liệu: `shared_data v1 (prep_shared_data.py seed 42)`.
Đường dẫn dưới đây tương đối theo folder `stage1/02_TuanDat/` (khi gộp repo đổi sang `results/…` của repo chung).

## Chương 1. Giới thiệu & phạm vi (Trung)
Bài toán, 5 luồng (ảnh, hỏi đáp, tìm, so sánh, trò chuyện/fallback Gemini), 4 nhóm SP, ràng buộc 3 tuần/5 người/không ngân sách.

## Chương 2. Dữ liệu (Tuấn Đạt, Khoa)
| Nội dung | Số liệu | Nguồn |
|---|---|---|
| Phương pháp thu thập (9 phương pháp, chọn 3) | bảng | `docs/US_04_phuong_phap_thu_thap.md` |
| Catalog FPI ban đầu / sau làm sạch | 4.593 / 4.385 SP | `results/clean_report.json` → `before.n`, `after.n` |
| Theo nhóm sau làm sạch | giày 1.400, quần áo 2.000, phụ kiện 700, mũ 285 | `clean_report.json` → `after.by_type` |
| Ảnh lỗi | 0/4.593 (0%) | `clean_report.json` → `images.bad_rate` |
| Ảnh trùng MD5 / SP xoá do trùng | 20 / 21 | `exact_md5_duplicates`, `dedupe.removed_duplicates` |
| Cặp pHash ≤ 4 (toàn catalog) | 3.937 (phần lớn là SP khác nhau – ảnh 60×80) | `phash_pairs_global_by_threshold["4"]`, `results/figures/dup_pairs_d4.png` |
| Nhãn sửa theo tiêu đề | cap→beanie 18, cap→wide_brim 6, wide_brim→beanie 3 | `title_refined` |
| Thiếu giá / mô tả / rating | 100% / 100% / 100% | `missing_rate` |
| ViMRHP trong phạm vi | 428 SP, 9.403 review, 262 spam lọc | `results/product_review_summary.json` → `_meta` |
| Bảng nguồn + mức tin cậy | bảng | `docs/US_10_bang_nguon_va_tinh_chinh_thong.md` |
| EDA (Mục D) | CHƯA ĐO trong folder này | Khoa (US_09) |
| Ảnh truy vấn ngoài đời | CHƯA ĐO (0 ảnh) | `docs/US_11_huong_dan_tap_anh_ngoai_doi.md` |

## Chương 3. Kiến trúc hệ thống (Trung, Hoàng)
Sơ đồ router → công cụ nội bộ → Gemini tầng 2; hợp đồng response 5.2; LLM Gateway (cache, retry, ngắt mạch 429).

## Chương 4. Khảo sát & benchmark
### 4.1 Embedding ảnh (Khoa) – Bảng A/A2: CHƯA ĐO trong folder này.
### 4.2 Text embedding cho RAG (Chiến) – Bảng C: CHƯA ĐO trong folder này.
### 4.3 LLM trả lời (Tuấn Đạt) – Bảng D
| Mô hình | n | Faithfulness | Hallucination | Từ chối đúng | Latency p50 (s) | Nguồn |
|---|---|---|---|---|---|---|
| gemini-3.5-flash-lite | 36 | 0,939 | 0,111 | 7/7 | 14,5 | `results/bench_llm_summary.json` → `qa.gemini35flashlite` |
| gemma-4-26b-a4b-it (API) | 32 | 0,992 | 0,031 | 6/6 | 13,8 | `qa.gemma4_26b_api` |
| Qwen2.5-0.5B (CPU) | 18 | 0,255 | 0,333 | 1/3 | 39,5 | `qa.qwen25_05b` |
| So sánh 18 câu chung | | | | | | `results/bench_llm_common_subset.json` |
| gemini-3.5-flash | – | CHƯA ĐO | | | | quota 429: `results/failed/` |
Ghi chú bắt buộc: điểm do LLM-judge `gemini-2.5-flash` chấm, câu hỏi do tác nhân AI viết – chưa người thật duyệt.

### 4.4 Gemini Router/Fallback – Bảng D2
| Chỉ số | Giá trị | Nguồn |
|---|---|---|
| Route accuracy (14 câu phân tầng) | 0,857 | `bench_llm_summary.json` → `router.gemini35flashlite.route_accuracy` |
| Latency p50/p95 | 0,7 / 0,9 s | idem |
| Reply bịa dữ kiện cửa hàng | 0/4 | `store_fact_flagged` |
| Token/100 lượt | 31.579 vào / 3.271 ra | `tokens_in_per_100`, `tokens_out_incl_thinking_per_100` |
| Tỉ lệ chuyển Gemini thực tế (log demo) | CHƯA ĐO | `logs/requests.jsonl` (Hoàng) |
| Chi phí/100 lượt bằng tiền | CHƯA ĐO – thiếu đơn giá đã xác minh | công thức `docs/US_24_benchmark_llm.md` mục 5 |

## Chương 5. Cải tiến trước/sau (Khoa – US_45)
| Cải tiến | Chỉ số | Trước | Sau | Nguồn |
|---|---|---|---|---|
| (vd) Khử trùng: pHash ≤ 4 → MD5 + pHash 0 + tiêu đề | SP bị xoá | 118 (bản chạy đầu, phần lớn xoá nhầm) | 21 | `docs/US_08_quy_trinh_lam_sach.md` mục 3; bản đầu không lưu file kết quả → **chỉ dùng như mô tả định tính, không đưa vào bảng số** |
| (vd) Gemini client: retry 3 lần → ngắt mạch 429 | Lời gọi lãng phí khi hết quota | 144 lời gọi/36 câu | tối đa 3 rồi dừng | `results/failed/…ALL_429.jsonl` (36 dòng × 4 lần thử) ; test `test_gemini_client_429_circuit` |
| Tóm tắt review: LLM vs baseline | ý không có trong review | LLM 3/93 | baseline 0 (theo cấu tạo) | `results/us36_kiem_tay_20sp.csv` |
| ≥ 4 cải tiến visual/RAG | | CHƯA ĐO | | Khoa |

## Chương 6. Giao diện & kiểm thử
- UI Gradio (`app/app.py`), card (`app/components.py`): test 20 SP thật hiển thị đủ 5 trường – `tests/test_components_app.py::test_20_real_products_all_fields`.
- Test plan 20 kịch bản: `docs/US_46_test_plan.md`; kết quả: `docs/test_report.md` (CHƯA CHẠY tích hợp).

## Chương 7. Hạn chế
1. Ảnh catalog 60×80 px (bản small) → giới hạn visual search và khử trùng; 2. Thiếu giá/size/mô tả 100% trong FPI; 3. Mũ 285 < 300, không có boot/bucket; 4. ViMRHP không có ảnh, license ND (không phát hành bản phái sinh); 5. Bộ đánh giá do AI viết, chưa người duyệt; 6. Quota Gemini free tier 20 request/ngày/model; 7. Máy 2 CPU dùng chung → latency nhiễu.

## Chương 8. Hướng phát triển (Đồ án 2)
Ảnh độ phân giải gốc (bản FPI full ~23 GB), crawl giá/size hợp lệ, ViEcom-Rec/DeepFashion, model LLM local ≥ 7B trên GPU, router học có giám sát từ log.

## Phụ lục – Kiểm tra truy vết trước khi nộp
`grep -nE "[0-9]+[,.][0-9]+" report_final.md` → mỗi số phải có dòng "Nguồn" tương ứng trong bảng; số không truy được → xoá hoặc ghi CHƯA ĐO.
