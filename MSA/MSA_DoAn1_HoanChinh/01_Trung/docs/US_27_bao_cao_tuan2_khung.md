# US_27 – Báo cáo mốc 2 tuần: trả lời 3 yêu cầu của thầy (dữ liệu, độ đo, khảo sát phiên bản)

| Mục | Nội dung |
|---|---|
| Mã US | US_27 (Owner: Trung, Support: All) – Sprint 2, 5.0 pt |
| Mục tiêu | Tổng hợp 3 yêu cầu của thầy thành `report_week2.docx` + slide 15–20 trang |
| Đầu ra | File này = **nội dung báo cáo đã có số liệu** (Tác nhân 2 viết lại 05/11/2026 từ kết quả mới nhất của 5 thành viên) + dàn ý slide |
| Tiêu chí nghiệm thu | Trả lời đủ 3 yêu cầu; mỗi kết luận có số liệu hoặc bảng |
| Trạng thái | **Một phần**: nội dung + số liệu đủ cho cả 3 yêu cầu; **chưa xuất `.docx` và slide**; mọi bộ đánh giá chưa có người thật duyệt; chưa có ảnh ngoài đời |

## Tóm tắt 5 dòng
1. **Dữ liệu:** chọn dataset public (Fashion Product Images – 4.385 SP sạch, 4 nhóm) + ViMRHP (509 SP Shopee, 11.009 review tiếng Việt) thay cho crawl sàn (Tiki chặn 403); thiếu mũ (285/300), ảnh chỉ 60×80, không có giá/size.
2. **Độ đo:** visual dùng macro Recall@5 + MRR@10 + CTE@5 + latency; RAG dùng Hit@5 + Faithfulness + Hallucination + Abstention; Agent dùng route accuracy, TSR, unsupported-store-fact; không dùng ROUGE/BLEU.
3. **Khảo sát ảnh:** 5 model đo thật; Bảng F xếp **DINOv2-S hạng 1 (4,83/5)**, macro R@5 0,846 (trên truy vấn tổng hợp).
4. **Khảo sát RAG/LLM:** Hybrid BM25 + e5-small tốt nhất (Hit@5 test 0,895); Gemini 3.5 Flash-Lite đủ tốt cho trả lời (faithfulness 0,94 – LLM chấm) và rẻ token nhất trong 2 model API.
5. **Chưa đạt / hạn chế:** router 0,878 < 0,90; chưa có 80–100 ảnh ngoài đời; nhãn đánh giá chưa người duyệt; quota Gemini free tier 20 request/ngày/model.

Quy ước: mỗi bảng ghi loại số liệu theo `00_Chung/THUAT_NGU.md` mục 1 – [Thật–thật], [Thật–tổng hợp], [LLM chấm], [Tác nhân kiểm], [Chưa người duyệt]. Data version: `shared_data v1 (prep_shared_data.py seed 42)`.

---

## Yêu cầu 1 – Thu thập dữ liệu

### 1.1 Phương pháp và lý do chọn / không chọn (chi tiết: `02_TuanDat/docs/US_04_phuong_phap_thu_thap.md`)
| Phương pháp | Quyết định | Lý do chính (bằng chứng thật) |
|---|---|---|
| Dataset public (HF/Kaggle/học thuật) | **CHỌN – nguồn chính** | Tải ngay, có nhãn sẵn làm ground truth, tái lập (seed 42), có paper để trích dẫn |
| Crawl sàn TMĐT VN (Tiki/Shopee) | Không chọn ở lượt này | Tiki trả **HTTP 403** cho IP cloud; ảnh Shopee bị chặn (`03_Chien/results/crawl_robots_probe.json`) |
| API chính thức sàn | Không chọn | Cần tư cách seller, không kịp 3 tuần |
| Tự chụp ảnh ngoài đời | **CHỌN – chỉ cho tập test** (US_11) | Cách duy nhất có ảnh giống người dùng; **CHƯA LÀM** (0/80 ảnh) |
| Sinh bằng LLM | **CHỌN – bổ trợ cho bộ đánh giá** | Nhanh, phủ câu khó; bắt buộc gắn `origin`; bị giới hạn quota 20 request/ngày/model |
| Mua dataset / hợp tác DN / Google Images / dataset cuộc thi | Không chọn | Chi phí, thời gian xin quyền, bản quyền ảnh không rõ |

### 1.2 Nguồn và tính chính thống (chi tiết: `02_TuanDat/docs/US_10_bang_nguon_va_tinh_chinh_thong.md`)
| Nguồn | Tổ chức / năm | Mức tin cậy (1 = cao) | License | Đã dùng |
|---|---|---|---|---|
| Fashion Product Images (small, mirror HF `ashraq/fashion-product-images-small`) | Param Aggarwal / Myntra, ~2019 | 2 – cộng đồng, truy được nguồn gốc | theo trang Kaggle `[cần xác minh]` | 4.593 SP → 4.385 sau làm sạch |
| ViMRHP (HF `trucmtnguyen/ViMRHP`, arXiv 2505.07416 `[cần xác minh mã arXiv]`) | Nguyen và cs., NLDB 2025 `[cần xác minh]` | 1 – học thuật | **CC BY-NC-ND 4.0** (chỉ nội bộ học thuật, không phát hành bản chỉnh) | 509 SP, 11.009 review |
| Amazon Reviews 2023, ABO, Clothing Dataset CC0, DeepFashion | McAuley Lab 2024, Amazon+Berkeley 2022, Grigorev 2020, CUHK 2016 | 1–2 | ghi trong US_10 | Dự phòng, chưa dùng (bị chặn / cần xin quyền) |

### 1.3 Kết quả: số lượng, phân loại, đặc điểm [Thật–thật]
| Nhóm | Quota tối thiểu | Sau làm sạch (`02_TuanDat/results/clean_report.json`) | Đạt? | Lá (taxonomy v1 + sửa 7 nhãn mũ) |
|---|---|---|---|---|
| Giày dép | 1.200 | 1.400 | Đạt | sneaker, sandal, heel_flat, leather_shoe, boot (3) |
| Quần áo | 2.000 | 2.000 | Đạt | top 1.529, bottom 349, dress 70, outerwear 52 |
| Phụ kiện | 500 | 700 | Đạt | bag 465, eyewear 135, belt 100 |
| Mũ | 300 | **285** | **Thiếu 15** | cap 258, beanie 21, wide_brim 6, bucket 0 |
| **Tổng** | 4.000–6.000 | **4.385** | Đạt | Phân loại 2 cấp, 168/168 nhãn FPI map được (`01_Trung/results/taxonomy_coverage.json`) |

Vì sao các tài liệu khác ghi mũ 293/286/298: `00_Chung/QUYET_DINH_CAN_CHOT.md` mục A (cùng nguồn, khác bước xử lý).

Đặc điểm đo được (`04_Khoa/docs/US_09_eda/eda_report.md`, 9 biểu đồ; `02_TuanDat/results/clean_report.json`):
- **Ảnh:** 100 % ảnh 60×80 px, 1 ảnh/SP, nền trắng studio; 0 % ảnh lỗi; 20 ảnh trùng MD5 → bỏ 21 SP trùng.
- **Metadata:** tiêu đề, thương hiệu, màu, giới tính, mùa có đủ; **giá, mô tả, rating thiếu 100 %** (FPI không có).
- **Review tiếng Việt (ViMRHP):** 428 SP sau khi bỏ 81 đồng hồ (trong đó 361 SP thuộc 4 nhóm); 9.403 review → 9.317 sau khử trùng; **93,4 % review 5 sao**, 57,8 % review theo mẫu Shopee → dữ liệu lệch tích cực; lệch về sandal/cao gót/áo khoác, gần như không có giày thể thao (2), mũ (5), túi (0).
- **Bộ đánh giá:** eval_visual 600 truy vấn (360 test) + 60 OOD [Thật–tổng hợp]; eval_qa 280 câu (25,4 % không có đáp án) + eval_router 78 câu [Chưa người duyệt].

Hạn chế phải nói thẳng với thầy: ảnh 60×80 làm số visual lạc quan; không có giá/size nên bộ lọc giá/size chỉ kiểm được trên dữ liệu tổng hợp; mũ chỉ ở mức demo (sheet Rủi ro, cắt scope thứ tự 3).

---

## Yêu cầu 2 – Độ đo: có những gì, chọn gì, vì sao

Khảo sát đầy đủ (công thức, ưu/nhược, quyết định): Visual `04_Khoa/docs/US_12_do_do_visual_search.md`; QA/RAG `03_Chien/docs/US_13_do_do_qa_rag.md`; Search/Compare/Agent `03_Chien/docs/US_14_do_do_search_compare_agent.md`; chốt + ngưỡng `01_Trung/docs/US_18_chot_do_do_va_nguong.md`. Giải thích dễ hiểu kèm ví dụ: `00_Chung/THUAT_NGU.md`.

| Module | Đã khảo sát | **Chọn (chính)** | Không chọn / phụ | Vì sao (gắn mục tiêu sản phẩm) |
|---|---|---|---|---|
| Visual search | Recall@K, Precision@K, mAP, MRR, NDCG, CTE, AUROC, latency | macro Recall@5, MRR@10, CTE@5, latency p95 | mAP (khó giải thích, cần GT đầy đủ); NDCG, P@5 làm phụ | Người dùng chỉ xem ~5 kết quả; macro để nhóm mũ nhỏ không bị nhóm áo che; nhầm giày↔áo là lỗi khó chấp nhận nhất |
| RAG – tìm | Hit@K, MRR, context precision/recall | Hit@5 (lọc theo product_id), MRR@10 | context precision/recall (cần nhãn từng câu) | Tìm sai thì LLM không thể đúng; tách lỗi "không tìm ra" khỏi "nói sai" |
| RAG – trả lời | EM/F1, ROUGE, BLEU, BERTScore, faithfulness, relevancy, hallucination, abstention, human eval | Faithfulness, Hallucination rate, Abstention accuracy (+ false-refusal), human eval 50 câu | ROUGE/BLEU (không phản ánh đúng/sai nghĩa tiếng Việt) | Mục tiêu số 1 là **không bịa**; thiếu dữ kiện phải nói "chưa có thông tin" |
| Tìm/So sánh | attribute F1, factual correctness | Attribute F1, % ô so sánh khớp DB | – | Bộ lọc sai thì kết quả sai từ đầu; bảng so sánh lấy từ DB phải ~100 % |
| Agent + Gemini | intent/route accuracy, tool-call accuracy, TSR, latency e2e, chi phí/lượt, fallback rate, unsupported-store-fact | route accuracy, TSR, unsupported-store-fact, fallback rate, token/100 lượt hội thoại | – | Router là "não"; Gemini không được bịa giá/size/tồn kho/danh mục |

Ngưỡng mục tiêu (đặt từ baseline thật – bảng đầy đủ ở US_18 §2):
| Độ đo | Baseline đo thật | Mục tiêu | Đạt? |
|---|---|---|---|
| Visual macro R@5 (test) | 0,846 DINOv2-S [Thật–tổng hợp] | 0,85 (tổng hợp) / 0,70 (ảnh thật) | gần đạt / CHƯA ĐO ảnh thật |
| Visual CTE@5 | 0,043 | ≤ 0,05 | Đạt |
| RAG Hit@5 (test, n=114) | 0,895 hybrid [Chưa người duyệt] | 0,90 | gần đạt |
| Faithfulness / Hallucination | 1,00 / 0,00 (Chiến, 52 câu, giám khảo Gemini chấm câu trả lời của Gemini); 0,939 / 0,111 (Đạt, 36 câu, giám khảo `gemini-2.5-flash`) [LLM chấm – **không phải đánh giá của người**] | ≥ 0,85 / ≤ 0,10 | Đạt theo LLM chấm – chờ người chấm |
| Abstention accuracy | 15/15 = 1,00 (sau khi sửa nhãn qa108 trên chính tập này; trước sửa 15/16 = 0,94) [LLM sinh nhãn, chưa người duyệt] | ≥ 0,90 | Đạt (n nhỏ, không phải held-out) |
| Route accuracy (held-out, n=49) | 0,878 | ≥ 0,90 | **Chưa đạt** |
| Unsupported-store-fact (Gemini) | giá/size/tồn kho 0/40 (Trung), 0/20 (Chiến); nhận bán hàng ngoài danh mục 2/40 | 0 | **Chưa đạt** (2/40) |

---

## Yêu cầu 3 – Khảo sát phiên bản (so sánh bằng số liệu)

### 3.1 Bảng A – Embedding ảnh (Khoa, `04_Khoa/results/bench_image_embed.csv`) [Thật–tổng hợp]
Cấu hình: catalog 4.593 ảnh FPI 60×80, 360 truy vấn test (240 instance + 120 category), cùng tiền xử lý, cùng FAISS IndexFlatIP, CPU 2 luồng dùng chung (latency có nhiễu), seed 42.
| Model | Năm | macro R@5 | MRR@10 | CTE@5 | cat P@5 | Nhúng 1 ảnh p50 (ms) | RAM đỉnh (MB) |
|---|---|---|---|---|---|---|---|
| DINOv2 ViT-S/14 | 2023 | **0,846** | **0,791** | **0,043** | 0,307 | 289 | 1.446 |
| SigLIP B/16 | 2023 | 0,833 | 0,760 | 0,055 | 0,355 | **190** | 2.431 |
| FashionCLIP | 2022 | 0,829 | 0,757 | 0,062 | **0,378** | 294 | 1.597 |
| CLIP ViT-B/32 | 2021 | 0,721 | 0,660 | 0,076 | 0,353 | 428 | 2.024 |
| ResNet-50 (ImageNet) | 2016 (CVPR; arXiv 2015) | 0,704 | 0,644 | 0,138 | 0,332 | 1.603 | 1.357 |
| CLIP B/16, OpenCLIP LAION-2B, Marqo-FashionSigLIP | | CHƯA ĐO (thiếu thời gian CPU) | | | | | |

Độ bền với ảnh giống ảnh người dùng (`04_Khoa/results/recall_by_transform.csv`): truy vấn đổi nền R@5 – SigLIP 0,906, DINOv2-S 0,812, FashionCLIP 0,656.

### 3.2 Bảng F – Chấm điểm có trọng số → model chọn (`01_Trung/docs/US_25_bang_cham_diem_co_trong_so.md`)
DINOv2-S **4,83** > SigLIP 3,98 ≈ FashionCLIP 3,96 > CLIP B/32 2,99 > ResNet-50 2,40; hạng 1 giữ nguyên ở 12/12 cấu hình trọng số ±0,05.
**Đề xuất chọn DINOv2-S** (dự phòng SigLIP B/16); chốt lại khi có ảnh ngoài đời. (README Khoa trước đó chọn tạm FashionCLIP – xem `00_Chung/QUYET_DINH_CAN_CHOT.md` mục E.)

### 3.3 Bảng B – Vector index
FAISS IndexFlatIP (tìm chính xác): 4.593 vector, search median 0,3–1,6 ms, index 7–38 MB (`04_Khoa/results/bench_image_embed.csv`) → không cần index xấp xỉ (IVF/HNSW) ở quy mô < 10.000 SP.

### 3.4 Bảng C – Text-embedding cho RAG tiếng Việt (Chiến, `03_Chien/results/rag_retrieval_eval.json`) [Chưa người duyệt]
Kho 10.173 chunk (428 SP), lọc theo product_id, câu có đáp án của eval_qa; test n = 114.
| Retriever | Hit@1 (test) | Hit@5 (test) | MRR@10 (test) |
|---|---|---|---|
| **Hybrid RRF (BM25 + multilingual-e5-small)** | **0,377** | **0,895** | **0,599** |
| TF-IDF ký tự 2–4 | 0,289 | 0,877 | 0,541 |
| BM25 | 0,272 | 0,868 | 0,541 |
| multilingual-e5-small | 0,298 | 0,807 | 0,525 |
| paraphrase-multilingual-MiniLM-L12 | 0,316 | 0,763 | 0,511 |

Kiểm chéo độc lập của Hoàng (3 seed, kho chỉ review, `05_Hoang/results/bench_text_embed.csv`): cũng thấy phương pháp từ vựng ≥ dense (TF-IDF word Hit@5 0,875 > e5-small 0,803). → **Chọn Hybrid** cho RAG v0. bge-m3 CHƯA ĐO (thiếu RAM).

### 3.5 Bảng D – LLM trả lời (Đạt, `02_TuanDat/results/bench_llm_summary.json`) [LLM chấm, giám khảo `gemini-2.5-flash`]
Cùng prompt, cùng ngữ cảnh review, temperature cố định.
| Model | n | Faithfulness | Hallucination | Từ chối đúng | Latency p50 (s) | Token vào / ra (gồm thinking) / 100 câu |
|---|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite (API) | 36 | 0,939 | 0,111 | 7/7 | 14,5* | 60.619 / 3.631 |
| Gemma 4 26B (API) | 32 | **0,992** | **0,031** | 6/6 | 13,8* | 62.075 / 63.112 (thinking ~600/câu) |
| Qwen2.5-0.5B (CPU local) | 18 | 0,255 | 0,333 | 1/3 | 39,5 | 68.994 / 2.417 |
\* latency API gồm chờ do quota free tier → không phải độ trễ thuần.
Kết luận: Flash-Lite là điểm cân bằng (chất lượng đủ, token ra ít hơn Gemma ~17 lần); Qwen 0,5B không dùng được cho tiếng Việt. `gemini-3.5-flash` CHƯA ĐO (hết quota).

### 3.6 Bảng D2 – Gemini ở vai trò Fallback / Router
| Chỉ số | Giá trị | Nguồn |
|---|---|---|
| Route accuracy router luật v1 (held-out, n=49) | 0,878 | `01_Trung/results/router_eval_v1.json` |
| Route accuracy Gemini Flash-Lite làm router (n=14) | 0,857 | `02_TuanDat/results/bench_llm_summary.json` |
| Fallback rate (172 câu eval) | 0,273 | `01_Trung/results/gemini_fallback_live.json` |
| Vi phạm giá/size/tồn kho | 0/40 (Trung), 0/20 + 0/2 câu bẫy (Chiến) | `01_Trung/results/gemini_store_fact_recheck.json`, `03_Chien/results/gemini_fallback_check.json` |
| Token / 100 lượt hội thoại | ≈ 6.028 (prompt ngắn) – ≈ 21.566 (prompt few-shot, dự kiến dùng) | giải thích: `00_Chung/QUYET_DINH_CAN_CHOT.md` mục F |
| Cache | 10/10 trúng, ≈ 0 lời gọi API | `01_Trung/...gemini_fallback_live.json`, `05_Hoang/results/llm_gateway_live.json` |

### 3.7 Bảng E – Hệ thống và bài báo tương tự
`04_Khoa/docs/US_21_he_thong_va_bai_bao_tuong_tu.md` (Google Lens, Pinterest Lens, Shopee, Amazon Rufus, CLIP, RAG, Visual Search at Pinterest/eBay/Alibaba) – mỗi mục có "điểm đáng học" và "liên hệ đồ án" (ví dụ: crop vật thể trước khi tìm → cải tiến I1; hỏi lại khi không chắc → τ_v + clarify).

---

## 4. Dàn ý slide (18 trang)
1 Tiêu đề · 2 Bài toán & 5 luồng demo · 3 Phạm vi · **Yêu cầu 1:** 4 Phương pháp & lý do (bảng 1.1) · 5 Nguồn & chính thống (1.2) · 6 Phân bố 4 nhóm + quota (1.3, biểu đồ `04_Khoa/docs/US_09_eda/01_catalog_type_sub.png`) · 7 Taxonomy + ca mơ hồ · 8 Hạn chế dữ liệu · **Yêu cầu 2:** 9 Bản đồ độ đo theo module · 10 Độ đo chọn + lý do · 11 Ngưỡng baseline → mục tiêu · **Yêu cầu 3:** 12 Bảng A · 13 Bảng F → model chọn · 14 Bảng C · 15 Bảng D/D2 · 16 Kiến trúc Tuần 3 · 17 Rủi ro & kế hoạch B · 18 Kế hoạch Tuần 3.

## 5. Việc còn lại để đạt tiêu chí
1. Xuất `report_week2.docx` + slide từ file này (Trung, N13).
2. Nhóm chốt các mục trong `00_Chung/QUYET_DINH_CAN_CHOT.md` trước khi xuất (đặc biệt mục A, E).
3. 2 người duyệt ≥ 30 % eval_qa/eval_router, người chấm 50 câu RAG – sau đó cập nhật các số [Chưa người duyệt]/[LLM chấm].
4. Chụp 80–100 ảnh ngoài đời (US_11) → chạy lại Bảng A cho 3 model đầu.
