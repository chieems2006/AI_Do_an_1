---
title: "Đồ án 1 – AI Agent trợ lý mua sắm thời trang: Báo cáo tổng hợp công việc từng thành viên"
subtitle: "Nhóm: Trung (nhóm trưởng) · Tuấn Đạt · Chiến · Khoa · Hoàng — bản kiểm định ngày 05/11/2026"
lang: vi
---

# Đồ án 1 – AI Agent trợ lý mua sắm thời trang (MSA)
## Báo cáo tổng hợp: những gì từng thành viên đã làm

| Mục | Nội dung |
|---|---|
| Đề tài | AI Agent trợ lý mua sắm thời trang: tìm bằng ảnh, hỏi đáp RAG tiếng Việt, tìm kiếm có bộ lọc + so sánh 2–3 sản phẩm, trò chuyện/ngoài phạm vi chuyển Gemini (cache, nhãn nguồn) |
| Nhóm | Trung (nhóm trưởng, kiến trúc, Agent), Tuấn Đạt (dữ liệu, LLM, UI, kiểm thử), Chiến (dữ liệu tiếng Việt, RAG, độ đo), Khoa (ML – embedding ảnh), Hoàng (Python – pipeline, API, LLM gateway) |
| Kế hoạch | 05/11 – 25/11/2026 · 3 tuần · 51 user story (US) · 199 point (`MSA_PLAN_v2.xlsx`) |
| Ngày chốt số liệu | 05/11/2026 (cuối lượt làm việc 04–05/11) |
| Cách làm | Phần việc của mỗi thành viên do một tác nhân AI đóng vai thực hiện trên dữ liệu thật; kết quả qua rà soát (Tác nhân 2) và kiểm định số liệu (Tác nhân 3). **Mọi việc cần người thật (duyệt nhãn, chụp ảnh, họp chốt, review chéo) đều chưa làm** và được ghi rõ ở từng mục. |

**Tóm tắt 6 dòng**

1. Dữ liệu: dùng dataset public Fashion Product Images (**4.385 SP sau làm sạch**, 4 nhóm, ảnh 60×80) + ViMRHP (509 SP Shopee, 11.009 review tiếng Việt, CC BY-NC-ND 4.0) vì crawl sàn bị chặn (Tiki trả HTTP 403). Nhóm mũ chỉ có **285/300 SP** → giữ ở mức demo.
2. Độ đo: visual dùng macro Recall@5, MRR@10, CTE@5, latency p95; RAG dùng Hit@5, faithfulness, hallucination, refusal accuracy; Agent dùng route accuracy, TSR, unsupported-store-fact, token/100 lượt hội thoại.
3. Khảo sát ảnh: 5 model đo thật; Bảng F chấm điểm có trọng số xếp **DINOv2-S hạng 1 (4,83/5)**, macro R@5 0,846 trên truy vấn **biến đổi tổng hợp** – chưa có ảnh ngoài đời.
4. Khảo sát RAG/LLM: Hybrid BM25 + multilingual-e5-small tốt nhất (Hit@5 test **0,895**); trên dữ liệu này phương pháp từ vựng (TF-IDF/BM25) ≥ embedding neural; Gemini 3.5 Flash-Lite đạt faithfulness 0,939 **[LLM chấm]**.
5. Agent: router luật đạt **0,878** trên tập held-out (chưa đạt 0,90); tỉ lệ chuyển Gemini **0,273**; ≈ 6.028 – 21.566 token/100 lượt hội thoại tuỳ prompt.
6. Tổng: 51 US → **Đạt 23 · Một phần 23 · Chưa đạt 5** theo cột TEST; **0/51 US đạt Definition of Done** vì chưa có review của người Support và chưa có người duyệt nhãn. 233 test tự động pass, 4 skip (thiếu file nặng không đóng gói).

---

# 1. Mở đầu

## 1.1 Mục tiêu và phạm vi
Sản phẩm cuối của Đồ án 1 là một AI Agent chạy demo local với 5 luồng: (1) **tìm bằng ảnh** – embedding ảnh + FAISS, trả top-K SP giống; (2) **hỏi đáp** về một SP bằng tiếng Việt – RAG trên review, có trích nguồn và từ chối khi thiếu dữ kiện; (3) **tìm bằng văn bản** có lọc metadata; (4) **so sánh 2–3 SP** – bảng thuộc tính lấy từ dữ liệu, LLM chỉ diễn giải; (5) **trò chuyện/ngoài phạm vi** – chuyển Gemini API khi mô hình nội bộ không tự tin, có cache và nhãn nguồn ("Từ dữ liệu cửa hàng" / "Trả lời bởi Gemini").
Phạm vi domain: 4 nhóm thời trang với cây danh mục 2 cấp – giày dép (sneaker, sandal, giày da, cao gót/bệt, boot), quần áo (áo, quần/váy ngắn, đầm, áo khoác), mũ (lưỡi trai, beanie, bucket, rộng vành), phụ kiện (túi, thắt lưng, kính). **Không làm** trong Đồ án 1: tích hợp website, đăng nhập/giỏ hàng, DWH, gửi ảnh người dùng cho Gemini, fine-tune Gemini.
Hai tuần đầu trả lời **3 yêu cầu của thầy**: (1) thu thập dữ liệu, (2) độ đo, (3) khảo sát phiên bản bằng số liệu; Tuần 3 xây demo và cải tiến (đo trước/sau).

## 1.2 Quy trình 3 tác nhân
| Bước | Tác nhân | Việc đã làm | Sản phẩm |
|---|---|---|---|
| 1 | **Tác nhân 1** – chuyên gia thiết kế AI | Trích phần việc từng người từ Backlog/Phân công/Lịch; ban hành thiết kế chung (schema, định dạng response, quy tắc Gemini, quy tắc ghi số liệu); chuẩn bị dữ liệu dùng chung `shared_data v1` (seed 42); giao việc cho 5 tác nhân thành viên và gom kết quả | `00_Chung/00_THIET_KE_CHUNG.md`, `giao_viec/`, `trich_ke_hoach/`, `prep_shared_data.py`, `TONG_HOP_TAC_NHAN_1.md` |
| 1' | 5 tác nhân thành viên | Mỗi tác nhân đóng vai 1 thành viên, làm các US được giao trên dữ liệu thật, đo thật, ghi `CHƯA ĐO` khi không làm được | 5 folder `01_Trung/` … `05_Hoang/` |
| 2 | **Tác nhân 2** – giảng viên hướng dẫn | Đối chiếu từng US với cột DOCS/TEST; phát hiện 13 mâu thuẫn chéo (A–F, G1–G7) và đề xuất cách chốt; chạy Bảng F trên số thật; viết thuật ngữ dùng chung; sửa nhãn nguồn `source="fallback"` | `QUYET_DINH_CAN_CHOT.md`, `THUAT_NGU.md`, `CHANGELOG_TAC_NHAN_2.md` |
| 3 | **Tác nhân 3** – kiểm định viên cuối | Đối chiếu tự động 211 con số trong tài liệu với file kết quả; kiểm định nghĩa độ đo, kết luận, thông tin model/dataset; sửa lỗi; chạy lại toàn bộ test; bỏ đường dẫn tuyệt đối khỏi code; viết báo cáo này | `00_Chung/kiem_dinh/`, `KIEM_DINH_TAC_NHAN_3.md`, `README.md`, file này |

## 1.3 Nhãn loại số liệu (bắt buộc đọc trước các bảng)
Theo `00_Chung/THUAT_NGU.md`: **[Thật–thật]** đo thật trên dữ liệu thật, đúng/sai do dữ liệu gốc quyết định · **[Thật–tổng hợp]** đo thật nhưng truy vấn/câu hỏi do máy tạo (vd ảnh catalog bị xoay, cắt, đổi nền) · **[LLM chấm]** đúng/sai do một LLM làm giám khảo – **không phải đánh giá của người** · **[Tác nhân kiểm]** tác nhân AI kiểm tay, chưa có người thật · **[Chưa người duyệt]** nhãn/đáp án bộ đánh giá chưa được 2 người duyệt · **CHƯA ĐO**.
Dấu phẩy thập phân trong văn bản (0,846) và dấu chấm trong JSON/CSV (0.846) là cùng một số. Mọi số trong báo cáo đã được đối chiếu với file nguồn bằng `00_Chung/kiem_dinh/check_numbers.py` (bảng đầy đủ: `00_Chung/kiem_dinh/doi_chieu_so_lieu.md`).

## 1.4 Tình trạng tổng quát
| Thành viên | Vai trò | Số US (Owner) | Đạt | Một phần | Chưa đạt | pytest (bản giao nộp) |
|---|---|---|---|---|---|---|
| Trung | Nhóm trưởng, kiến trúc, router, taxonomy, báo cáo | 12 | 3 | 6 | 3 | 53 passed, 1 skipped |
| Tuấn Đạt | Phương pháp thu thập, làm sạch, LLM benchmark, UI, kiểm thử | 10 | 3 | 5 | 2 | 21 passed, 3 skipped |
| Chiến | Dữ liệu tiếng Việt, eval QA, độ đo, RAG, prompt Gemini | 9 | 4 | 5 | 0 | 51 passed |
| Khoa | EDA, eval visual, benchmark embedding ảnh, index, cải tiến | 9 | 6 | 3 | 0 | 30 passed |
| Hoàng | Repo, dữ liệu public, metrics, API, LLM gateway | 11 | 7 | 4 | 0 | 78 passed |
| **Tổng** | | **51** | **23** | **23** | **5** | **233 passed, 4 skipped** |

"Đạt/Một phần/Chưa đạt" so với cột TEST (tiêu chí nghiệm thu) của Backlog. Tác nhân 3 hạ US_35 (Chiến) từ Đạt xuống Một phần vì mới đo 15/71 câu không đáp án. Các test *skipped* cần file nặng (`catalog_clean.parquet`, `catalog_fpi_taxonomy_v1.parquet`) không đóng gói – sinh lại bằng script thì chạy.

---

# 2. Dữ liệu thật đã dùng và các ràng buộc gặp phải

## 2.1 Nguồn và quy mô
| Nguồn | Tổ chức / năm | License | Quy mô dùng | Loại số liệu |
|---|---|---|---|---|
| Fashion Product Images (small), mirror HF `ashraq/fashion-product-images-small` | Param Aggarwal (Kaggle, ~2019, dữ liệu Myntra) | `[cần xác minh]` (chưa đọc được Data Card gốc) – chỉ dùng học thuật | 44.072 dòng gốc → 4.593 SP 4 nhóm (`shared_data v1`) → **4.385 SP sau làm sạch** | [Thật–thật] |
| ViMRHP, HF `trucmtnguyen/ViMRHP` (phần Fashion, dữ liệu Shopee VN) | Nguyen và cs., NLDB 2025 `[cần xác minh]` | **CC BY-NC-ND 4.0** – phi thương mại, không phát hành bản chỉnh sửa | 509 SP / 11.009 review; bỏ 81 đồng hồ → 428 SP / 9.403 review (9.317 sau khử 86 trùng `comment_id`); trong đó 361 SP thuộc 4 nhóm | [Thật–thật] |
| Amazon Reviews 2023 (McAuley Lab), ABO (Amazon + UC Berkeley, CVPR 2022, CC BY-NC 4.0), Clothing Dataset (CC0), DeepFashion (CUHK 2016) | – | xem US_10 | **chưa dùng** (ảnh bị chặn / cần xin quyền) | – |

Phân bố sau làm sạch (`02_TuanDat/results/clean_report.json`) [Thật–thật]:

| Nhóm | Quota tối thiểu | Sau làm sạch | Đạt? | Lá danh mục |
|---|---|---|---|---|
| Giày dép | 1.200 | 1.400 | Đạt | sneaker 729, sandal 306, heel_flat 270, leather_shoe 95 (taxonomy v1: 3 SP là boot) |
| Quần áo | 2.000 | 2.000 | Đạt | top 1.529, bottom 349, dress 70, outerwear 52 (giới hạn 800 SP/lá) |
| Phụ kiện | 500 | 700 | Đạt | bag 465, eyewear 135, belt 100 |
| Mũ | 300 | **285** | **Thiếu 15** | cap 258, beanie 21, wide_brim 6, bucket 0 |
| **Tổng** | 4.000–6.000 | **4.385** | Đạt | 168/168 nhãn FPI map được vào taxonomy |

**Vì sao các tài liệu từng ghi mũ 293/286/298:** 293 là nhãn gốc FPI (gồm 7 băng đô); 286 sau taxonomy v1 (băng đô → ngoài phạm vi); **285** sau taxonomy + bỏ 1 ảnh trùng MD5 (con số chuẩn); 298 là Data v1 của Hoàng (giữ băng đô + 5 mũ ViMRHP không có ảnh). Chi tiết: `QUYET_DINH_CAN_CHOT.md` mục A.

## 2.2 Ràng buộc gặp phải (đo/ghi nhận thật)
| Ràng buộc | Bằng chứng | Ảnh hưởng | Cách xử lý |
|---|---|---|---|
| Gemini free tier: **5 request/phút, 20 request/ngày/model**, key dùng chung 5 người | HTTP 429 `GenerateRequestsPerDayPerProjectPerModel-FreeTier` (`02_TuanDat/results/failed/`, `05_Hoang/results/llm_gateway_live_gemini35_quota429.json`) | `gemini-3.5-flash` hết quota trong ngày; Đạt mất 144 lời gọi do retry trên 36 câu bị 429; latency đo được gồm thời gian chờ quota | Chuyển sang `gemini-3.5-flash-lite`; cache SQLite; ngắt mạch khi 429; sinh câu theo lô; mỗi người ≤ 250 lời gọi |
| Crawl sàn VN bị chặn | Tiki `robots.txt` trả **HTTP 403** cho IP cloud; Shopee không kết nối (`03_Chien/results/crawl_robots_probe.json`); Kaggle chặn → dùng mirror HF | Không có 300 SP crawl, không có giá/size/tồn kho thật | Kế hoạch B (R1): ViMRHP thay cho crawl review; bộ lọc giá/size chỉ test trên dữ liệu tổng hợp |
| Ảnh FPI chỉ **60×80 px**, 1 ảnh/SP, nền trắng studio | `04_Khoa/docs/US_09_eda/eda_stats.json` (100 % ảnh 60×80) | Số visual lạc quan, không phản ánh ảnh người dùng; pHash kém tin cậy | Bắt buộc có 80–100 ảnh ngoài đời (US_11) trước khi chốt model |
| Mũ **285 < 300** | `clean_report.json` | Không đủ quota | Cắt scope thứ tự 3: mũ chỉ giữ mức demo; Amazon có 372 mũ nhưng ảnh bị chặn |
| Máy **2 CPU / 7 GB RAM**, không GPU, dùng chung 5 tác nhân | log OOM-kill (`04_Khoa/logs/`, `05_Hoang/results/logs/`) | Latency là cận trên có nhiễu; chưa đo CLIP B/16, OpenCLIP, Marqo-FashionSigLIP, bge-m3 | Chạy 1 model/tiến trình; cache embedding `.npy` |
| ViMRHP lệch tích cực | 93,4 % review 5 sao; 57,8 % review theo mẫu Shopee; gần như không có giày thể thao (2), mũ (5), túi (0) | RAG chủ yếu hỏi về giao hàng/chất liệu/size theo review | Lọc review spam; ghi hạn chế |

## 2.3 Bộ đánh giá đã có
| Bộ | Quy mô | Cách tạo | Loại số liệu |
|---|---|---|---|
| `04_Khoa/eval/eval_visual.csv` | 600 truy vấn (val 240 / test 360; 90 test/nhóm), 96 câu dễ nhầm khác nhóm (53 ở test) + 60 ảnh OOD (đồng hồ/mỹ phẩm) | instance: ảnh catalog bị 7 họ biến đổi; category: ảnh SP khác cùng loại + màu; tách val/test theo product_id | [Thật–tổng hợp], [Chưa người duyệt] |
| `03_Chien/eval/eval_qa.jsonl` | 280 câu / 80 SP; 71 câu không có đáp án (25,4 %); 251 câu Gemini sinh + 29 câu tác nhân viết | sinh từ review + câu viết tay; 1 nhãn đã sửa sau khi xem kết quả (qa108) | [Chưa người duyệt] |
| `03_Chien/eval/eval_router.jsonl` | 78 câu (21 chitchat/ood) | tác nhân viết tay | [Chưa người duyệt] |
| `01_Trung/eval/` | 45 câu dev + 49 câu Gemini sinh (held-out) | – | [Chưa người duyệt] |
| `04_Khoa/eval/e2e_scenarios.jsonl` | 60 kịch bản end-to-end | – | [Chưa người duyệt] |
| Ảnh ngoài đời (US_11) | **0/80** | cần nhóm tự chụp | CHƯA CÓ |

Phát hiện quan trọng: **45/280 câu eval_qa và 4/78 câu eval_router** hỏi về SP mà taxonomy coi là ngoài phạm vi (trang sức, tất…) – danh sách ở `03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv`; kho RAG có 67 SP ngoài phạm vi (`QUYET_DINH_CAN_CHOT.md` mục B).

---

# 3. Trung – nhóm trưởng, kiến trúc, router và nhánh Gemini

## 3.1 Vai trò
Chủ trì phạm vi (charter), chốt schema và taxonomy, chốt độ đo và ngưỡng, chủ trì chấm điểm chọn model (Bảng F), viết kiến trúc + hợp đồng API, viết router Agent và nhánh Gemini, tổng hợp báo cáo Tuần 1/2, kịch bản demo. 12 US, 39 point.

## 3.2 Các US phụ trách
| US | Đầu ra | Trạng thái | Ghi chú |
|---|---|---|---|
| US_01 Project Charter | `docs/US_01_project_charter.md` | Một phần | Có charter; buổi kickoff mỗi người nói lại 2' chưa có biên bản |
| US_03 Biên bản họp | `docs/US_03_bien_ban_hop_template.md` | Chưa đạt | Mới có mẫu, chưa có biên bản thật |
| US_05 Schema | `docs/US_05_schema.md`, `src/schema/product.schema.json`, 8 ví dụ SP thật | **Đạt** | Catalog taxonomy v1 hợp lệ 4.586/4.586; ViMRHP 361/361 |
| US_18 Chốt độ đo & ngưỡng | `docs/US_18_chot_do_do_va_nguong.md` | **Đạt** | Bảng ngưỡng cập nhật theo số mới nhất của 5 thành viên |
| US_25 Bảng F chấm điểm có trọng số | `docs/US_25_bang_cham_diem_co_trong_so.md`, `scripts/run_scoring_from_khoa.py` | **Đạt** (kỹ thuật) | Chạy thật trên CSV của Khoa; chờ họp N12 chốt điểm định tính |
| US_26 Báo cáo Tuần 1 | `docs/US_26_bao_cao_tuan1_khung.md` | Một phần | Đủ 3 mục có số; chưa xuất .docx |
| US_27 Báo cáo Tuần 2 + slide | `docs/US_27_bao_cao_tuan2_khung.md` | Một phần | Nội dung đủ 3 yêu cầu có số; chưa xuất .docx/slide |
| US_40 Kiến trúc + OpenAPI | `docs/US_40_architecture.md`, `docs/openapi_contract.yaml` | Một phần | Sơ đồ + ví dụ endpoint; chưa có cả nhóm xác nhận |
| US_41 Router + nhánh Gemini | `src/msa/agent/router.py`, `gemini_client.py`, `docs/US_41_router_agent_va_gemini.md` | Chưa đạt | 0,878 < 0,90 trên held-out |
| US_42 Session memory (stretch) | `src/msa/agent/session_memory.py` | Chưa đạt | Có code + unit test; 10 kịch bản đa lượt CHƯA ĐO |
| US_47 Kịch bản demo | `docs/US_47_demo_script_va_dien_tap.md` | Một phần | Kịch bản với SP thật; diễn tập là việc Sprint 3 |
| US_49 Taxonomy | `docs/US_49_taxonomy.md`, `data/category_map.csv` | Một phần | 168/168 nhãn map được; 30 mẫu/nguồn sai 0 [Tác nhân kiểm]; Tác nhân 2 phát hiện 7 nhãn mũ sai ngoài mẫu |

## 3.3 Việc đã làm cụ thể
- **Taxonomy 2 cấp** (`src/msa/data/taxonomy.py`, `data/category_map.csv`): map 168 nhãn `articleType` của FPI (61 giữ, 5 unknown, 102 loại) và 509 SP ViMRHP bằng luật tiêu đề tiếng Việt (giữ 349, unknown 12, loại 148 – gồm 81 đồng hồ và trang sức/tất). Kiểm 30 mẫu/nguồn: 0 sai, 3 mơ hồ [Tác nhân kiểm].
- **Schema JSON** draft 2020-12 + adapter từng nguồn; kiểm bằng `jsonschema` trên dữ liệu thật: catalog gốc 4.320/4.593 hợp lệ (273 nhãn tạm có dấu `*`), catalog sau taxonomy **4.586/4.586**.
- **Router luật v0 → v1** (7 route: visual, qa, search, compare, gemini_chitchat, gemini_ood, clarify; τ_intent 0,6), đóng băng v0 trước khi xem bộ của Chiến để có số held-out trung thực; thử thêm embedding e5-small (không cải thiện → tắt).
- **Nhánh Gemini end-to-end** đo thật 40 + 10 lời gọi: system prompt có guardrail, cache, hậu kiểm regex "cửa hàng có bán X".
- **Bảng F** (cùng Tác nhân 2): chuẩn hoá min–max từng tiêu chí về thang 1–5 rồi nhân trọng số (độ chính xác 0,35; tốc độ 0,15; tài nguyên 0,15; phù hợp miền 0,15; license 0,10; dễ tích hợp 0,10). Ví dụ: tốc độ FashionCLIP = 1 + 4·(1.603 − 294)/(1.603 − 190) = 4,71.

## 3.4 Số liệu thật chính
| Chỉ số | Giá trị | Loại | File |
|---|---|---|---|
| Router v0 trên bộ Chiến (n=78, v0 đóng băng trước) | 0,667 | [Chưa người duyệt] | `01_Trung/results/router_eval_v0.json` |
| Router v1 trên bộ Chiến (**đã chỉnh luật sau khi xem lỗi** – không dùng nghiệm thu) | 0,923 | [Chưa người duyệt] | `01_Trung/results/router_eval_v1.json` |
| **Router v1 trên tập held-out Gemini sinh (n=49)** | **0,878** (compare recall 0,57) | [Chưa người duyệt] | như trên |
| Router + e5-small (ablation, bộ Chiến) | 0,846 | – | `router_eval_v1_emb.json` |
| Tỉ lệ chuyển Gemini (172 câu của 3 bộ) | 0,273 (47/172) | trên bộ eval cân bằng nhãn | `gemini_fallback_live.json` |
| Gemini Flash-Lite: token vào / ra / thinking mỗi lời gọi | 165,1 / 55,5 / 0 (bật thinking 1024: 164,7 / 37,3 / 350,3) | [Thật–thật] | như trên |
| Latency nhánh Gemini p50 / p95 | 14,4 s / 41,1 s (**gồm chờ retry 429**) | có nhiễu quota | như trên |
| Câu Gemini nêu giá/size/tồn kho | 0/40 | [Tác nhân kiểm] | `gemini_store_fact_recheck.json` |
| Câu Gemini tự nhận cửa hàng có bán hàng ngoài danh mục | **2/40** (đồng hồ, khuyên tai) | [Tác nhân kiểm] | như trên |
| Cache (10 câu lặp) | 10/10 trúng, p50 0,3 ms | [Thật–thật] | `gemini_fallback_live.json` |
| Bảng F | DINOv2-S 4,83 > SigLIP 3,98 > FashionCLIP 3,96 > CLIP B/32 2,99 > ResNet-50 2,40 | tính từ số [Thật–tổng hợp] | `01_Trung/results/weighted_scoring.json` |

## 3.5 Quyết định / phát hiện
- Số trung thực để báo cáo route accuracy là **0,878 (held-out)**, không phải 0,923 (tập đã dùng để sửa luật). Lỗi chính: "tui" (teencode "tôi") bị hiểu là "túi"; thiếu mẫu "phân vân giữa X và Y"; 3 lỗi do mâu thuẫn phạm vi trang sức/tất.
- Hậu kiểm regex v1 bỏ sót 2 ca "cửa hàng có bán đồng hồ/khuyên tai" và bắt nhầm 1 câu toán; regex v2 sửa sau khi xem nên **chưa phải số held-out**.
- `gemini-3.5-flash-lite` trả HTTP 400 với `thinkingBudget=0`; mặc định không suy nghĩ. Bật thinking 1024 làm token ×2,5 và có 2/10 câu bị cắt `MAX_TOKENS`.
- Đã đổi thông điệp hệ thống khi Gemini lỗi sang `source="fallback"` (trước đó gắn nhầm `internal` → UI hiện "Từ dữ liệu cửa hàng").

## 3.6 Hạn chế và việc còn lại
Chưa có biên bản họp, chưa xuất báo cáo .docx/slide, chưa có xác nhận của cả nhóm cho kiến trúc. Việc tiếp: Router v2 (sửa 3 nhóm lỗi trên) + quét τ_intent trên val; đo lại trên bộ ≥ 60 câu do người thật viết; thêm 2 luật tiêu đề mũ vào `map_fpi` (mục A); chủ trì ký các quyết định A–F; xuất `report_week1/2.docx`.

---

# 4. Tuấn Đạt – phương pháp thu thập, làm sạch, benchmark LLM, UI, kiểm thử

## 4.1 Vai trò
Trả lời chính Yêu cầu 1 (phương pháp + nguồn), làm sạch dữ liệu, benchmark LLM (Bảng D, D2), giao diện demo Gradio, kế hoạch kiểm thử và báo cáo cuối. 10 US, 39 point.

## 4.2 Các US phụ trách
| US | Đầu ra | Trạng thái | Ghi chú |
|---|---|---|---|
| US_04 Phương pháp thu thập | `docs/US_04_phuong_phap_thu_thap.md` | **Đạt** | 9 phương pháp, chọn 3, lý do gắn bằng chứng thật |
| US_08 Làm sạch | `src/scripts/03_clean.py`, `results/clean_report.{json,md}`, `docs/US_08_quy_trinh_lam_sach.md` | Một phần | Ảnh lỗi 0 %, 100 % có category; mũ 285 < 300; 122 cặp pHash chưa người xem |
| US_10 Bảng nguồn + tính chính thống | `docs/US_10_bang_nguon_va_tinh_chinh_thong.md` | **Đạt** | 12 nguồn có URL, license, mức tin cậy |
| US_11 Tập ảnh ngoài đời | hướng dẫn + template CSV + `check_visual_queries.py` | Chưa đạt | 0 ảnh – cần người thật chụp |
| US_24 Benchmark LLM | `src/scripts/bench_llm.py`, `docs/US_24_benchmark_llm.md` | Một phần | 3 model cùng prompt/ngữ cảnh; router chỉ 14 câu; `gemini-3.5-flash` CHƯA ĐO |
| US_28 Báo cáo cuối | `docs/US_28_bao_cao_cuoi_khung.md` | Chưa đạt | Sprint 3 – mới có khung |
| US_31 Card kết quả | `app/components.py` | **Đạt** | 20/20 SP thật đủ 5 trường |
| US_36 Tóm tắt review | `src/scripts/summarize_reviews.py`, `results/product_review_summary.json` | Một phần | Bản LLM có 3/93 ý không có trong review |
| US_43 App demo | `app/app.py`, `app/mock_api.py` | Một phần | 1 lệnh, 4 luồng chạy qua API giả lập |
| US_46 Test plan / report | `docs/US_46_test_plan.md`, `docs/test_report.md` | Một phần | 20 kịch bản; 4 kịch bản có test tự động |

## 4.3 Việc đã làm cụ thể
- **So sánh 9 phương pháp thu thập** (dataset public, crawl sàn, API sàn, tự chụp, sinh bằng LLM, mua dataset, hợp tác DN, Google Images, dataset cuộc thi) theo ưu/nhược/chi phí/pháp lý; chọn 3: public làm nguồn chính, tự chụp cho tập test, LLM sinh câu hỏi đánh giá (bắt buộc gắn `origin`).
- **Làm sạch thật** 4.593 SP (~9 s): kiểm 4.593 ảnh (0 lỗi), khử trùng MD5 (20 nhóm trùng, xoá 21 SP), pHash (3.937 cặp ≤ 4 – phần lớn là SP khác nhau trên ảnh 60×80 nên không xoá tự động; 122 cặp để người xem), chuẩn hoá thương hiệu (1.304 dòng), sửa 27 nhãn mũ theo tiêu đề, giới hạn 800 SP/lá → 4.385 SP.
- **Benchmark LLM** cùng prompt, cùng ngữ cảnh review, temperature cố định, log từng câu (JSONL); giám khảo `gemini-2.5-flash`.
- **UI Gradio**: khung chat + tải ảnh + card SP + bảng so sánh; nhãn nguồn "Từ dữ liệu cửa hàng" / "Trả lời bởi Gemini" / "Thông báo hệ thống".
- **Gemini client** dùng chung: cache SQLite, đếm ngân sách, ngắt mạch 429.

## 4.4 Số liệu thật chính
| Chỉ số | Giá trị | Loại | File |
|---|---|---|---|
| SP trước → sau làm sạch | 4.593 → **4.385** | [Thật–thật] | `02_TuanDat/results/clean_report.json` |
| Ảnh lỗi / có category | 0 % / 100 % | [Thật–thật] | như trên |
| Kiểm nhãn 400 dòng (100/nhóm) | 1/100 lệch ở mũ (so tiêu đề tự động) | [Tác nhân kiểm] | `results/label_check_sample.csv` |
| Bảng D – Gemini 3.5 Flash-Lite (n=36) | faithfulness 0,939 · hallucination 0,111 · từ chối đúng 7/7 | **[LLM chấm]** | `02_TuanDat/results/bench_llm_summary.json` |
| Bảng D – Gemma 4 26B API (n=32) | 0,992 · 0,031 · 6/6 (thinking ~600 token/câu) | **[LLM chấm]** | như trên |
| Bảng D – Qwen2.5-0.5B CPU local (n=18) | 0,255 · 0,333 · 1/3 | **[LLM chấm]** | như trên |
| Token vào / ra (gồm thinking) /100 câu QA | Flash-Lite 60.619 / 3.631; Gemma 62.075 / 63.112; Qwen 68.994 / 2.417 | [Thật–thật] | như trên |
| Gemini Flash-Lite làm router (n=14) | 0,857 | [Chưa người duyệt] | như trên |
| Tóm tắt review bằng LLM (20 SP) | 3/93 ý không có trong review (3/20 SP) | [Tác nhân kiểm] | `results/us36_kiem_tay_20sp.csv` |
| Ngân sách Gemini | 250/250 lời gọi, 144 lời gọi bị 429 (36 câu × 4 lần thử) | [Thật–thật] | `results/gemini_budget.json`, `results/failed/` |

Lưu ý so sánh Bảng D: n khác nhau (36/32/18) nên Tác nhân 2 thêm tập con chung 18 câu (`bench_llm_common_subset.json`): Flash-Lite 0,925 / Gemma 0,986 / Qwen 0,255 faithfulness – thứ hạng không đổi. Kết luận: Flash-Lite là điểm cân bằng (token ra ít hơn Gemma ~17 lần); Qwen 0,5B không dùng được cho tiếng Việt.

## 4.5 Quyết định / phát hiện
- Luật tiêu đề của Đạt đúng cho 7 SP mũ (fedora/boonie là `wide_brim`, beanie) nhưng gán sai 3 đôi boot thành heel_flat/sneaker → dùng taxonomy v1 của Trung làm gốc và bổ sung 2 luật mũ (mục A).
- Lỗi hallucination của cả hai model API đều đến từ 1 review spam → lọc spam trước khi chunk (gợi ý cho RAG).
- Client bản đầu retry 3 lần khi 429 làm lãng phí 144 lời gọi → đã thêm ngắt mạch.

## 4.6 Hạn chế và việc còn lại
Chưa có ảnh ngoài đời (việc quan trọng nhất của Tuần 2, N8–N9); chưa có người xem 122 cặp pHash và 400 dòng kiểm nhãn; UI chưa nối API thật; benchmark router mới 14 câu. Việc tiếp: chụp + 2 người gán nhãn 80–100 ảnh; nối UI với API Hoàng (`MSA_API_URL`); chạy 20 kịch bản kiểm thử N19; báo cáo cuối N20.

---

# 5. Chiến – dữ liệu tiếng Việt, bộ đánh giá QA, độ đo, RAG, prompt Gemini

## 5.1 Vai trò
Nguồn dữ liệu tiếng Việt (crawl hoặc kế hoạch B), bộ đánh giá eval_qa/eval_router, khảo sát độ đo QA/RAG và Search/Compare/Agent, khảo sát text-embedding và LLM (Bảng C, D), xây RAG có trích nguồn + từ chối, prompt Gemini fallback. 9 US, 40 point.

## 5.2 Các US phụ trách
| US | Đầu ra | Trạng thái | Ghi chú |
|---|---|---|---|
| US_07 Crawl TMĐT VN | `src/scripts/02_crawl_vn.py`, `docs/US_07_kiem_tra_robots_tos.md` | Một phần | Crawl bị chặn (403); đạt số lượng bằng kế hoạch B (ViMRHP 428 SP / 9.317 review) |
| US_13 Độ đo QA/RAG | `docs/US_13_do_do_qa_rag.md` | **Đạt** | Mỗi độ đo có công thức, ưu/nhược, quyết định |
| US_14 Độ đo Search/Compare/Agent | `docs/US_14_do_do_search_compare_agent.md` | **Đạt** | intent, tool-call, attribute F1, TSR, latency, chi phí, fallback rate, unsupported-store-fact |
| US_16 eval_qa + eval_router | `eval/eval_qa.jsonl`, `eval/eval_router.jsonl` | Một phần | Đủ quy mô; 0 % có người duyệt; 45 câu ngoài phạm vi |
| US_20 Khảo sát text-embedding & LLM | `docs/US_20_khao_sat_text_embedding_llm.md` | **Đạt** | 8 embedding, 8 LLM |
| US_33 Kho tri thức | `src/msa/rag/ingest.py`, `data/kb/chunks.jsonl` | **Đạt** | 10.173 chunk, 100 % có product_id + nguồn |
| US_34 Hỏi đáp RAG | `src/msa/rag/{retriever,pipeline,llm}.py` | Một phần | Hit@5 test 0,895 (< 0,90 đề xuất); faithfulness [LLM chấm]; /qa chưa nối |
| US_35 Trích nguồn + từ chối | `pipeline.py` (guard), `docs/US_33_34_35_rag.md` | Một phần | 15/15 trên mẫu 15/71 câu không đáp án |
| US_51 Prompt + nhánh Gemini | `prompts/gemini_fallback.md` v1.0, `src/msa/rag/fallback.py` | Một phần | 0/20 vi phạm; mới 22/60 phản hồi; route accuracy chưa đạt |

## 5.3 Việc đã làm cụ thể
- **Kiểm robots/ToS thật** Tiki/Shopee (403, không kết nối) → chuyển kế hoạch B; nạp ViMRHP 428 SP, khử 86 review trùng `comment_id`.
- **eval_qa 280 câu** sinh theo lô bằng Gemini (6 lô `gemini-3.5-flash` trước khi hết quota, 7 lô `flash-lite`) + 29 câu viết tay; mỗi câu có `answerable`, `evidence_review_ids`, `origin`, `split`. **eval_router 78 câu** có dấu/không dấu/teencode.
- **Kho tri thức** 10.173 chunk (428 tiêu đề + 9.317 review + 428 chunk điểm chi tiết).
- **6 retriever** so sánh trên cùng kho (TF-IDF ký tự, BM25, BM25 + viết lại teencode, e5-small, MiniLM-L12, Hybrid RRF BM25 + e5-small).
- **RAG v0**: hybrid → prompt grounding (`prompts/rag_grounded.md` v1.0) → guard; τ_r = 0 vì điểm top-1 tách câu có/không đáp án kém (AUC 0,72–0,77; τ_r = 0,35 chặn nhầm 60 % câu có đáp án).
- **Prompt Gemini fallback** có system prompt + few-shot cấm nêu giá/size/tồn kho; hậu kiểm regex; 2 câu bẫy.

## 5.4 Số liệu thật chính
Retrieval (lọc theo product_id, câu có đáp án; `03_Chien/results/rag_retrieval_eval.json`) [Chưa người duyệt]:

| Retriever | Hit@5 (209 câu) | Hit@5 test (n=114) | Hit@1 test | MRR@10 test |
|---|---|---|---|---|
| **Hybrid RRF (BM25 + e5-small)** | **0,866** | **0,895** | **0,377** | **0,599** |
| TF-IDF ký tự 2–4 | 0,833 | 0,877 | 0,289 | 0,541 |
| BM25 | 0,837 | 0,868 | 0,272 | 0,541 |
| multilingual-e5-small | 0,794 | 0,807 | 0,298 | 0,525 |
| paraphrase-multilingual-MiniLM-L12 | 0,756 | 0,763 | 0,316 | 0,511 |

RAG end-to-end (52 câu split test, hybrid, `gemini-3.5-flash-lite`, sinh theo lô 13 câu/lời gọi; `03_Chien/results/rag_e2e_eval.json`):

| Chỉ số | Giá trị | Loại |
|---|---|---|
| Refusal accuracy (câu không đáp án được từ chối đúng) | **15/15 = 1,00** – sau khi sửa nhãn qa108 trên chính tập này; **trước sửa 15/16 = 0,9375** | [Chưa người duyệt], không còn là held-out |
| False-refusal | 0/37 | như trên |
| Citation rate / cited-gold | 1,00 / 0,865 | [Thật–thật] (so với evidence_review_ids) |
| Faithfulness / hallucination / relevancy | 1,00 / 0,00 / 1,00 | **[LLM chấm]** – giám khảo cùng họ Gemini, chấm 1,0 toàn bộ ⇒ có thể dễ dãi |
| Token mỗi câu (vào / ra) | 378,9 / 46,2 | [Thật–thật] |

Nhánh Gemini fallback (`03_Chien/results/gemini_fallback_check.json`): 22 phản hồi hợp lệ (20 câu eval_router + 2 câu bẫy, 1 lỗi API); **0/20 vi phạm** giá/size/tồn kho, 0/2 câu bẫy [Tác nhân kiểm bằng regex]; token TB 747,5 vào / 41,7 ra mỗi lời gọi (= 74.750 / 4.170 trên **100 lời gọi**); latency p50 16,0 s / p95 27,8 s (đo lúc server trả 503 – vượt mục tiêu 4 s, cần đo lại).

## 5.5 Quyết định / phát hiện
- Chọn **Hybrid RRF** cho RAG v0. Lý do bằng số: cao nhất trên cả 209 câu và split test; TF-IDF chỉ kém 1,8 điểm Hit@5 test và rẻ hơn nhiều – là phương án dự phòng.
- Nhờ chạy e2e phát hiện nhãn sai qa108 (tên SP ghi "gót nhọn cao 9cm") → sửa nhãn và ghi rõ cả số trước/sau.
- Chọn prompt few-shot của Chiến cho demo (0/20 vi phạm) dù tốn token hơn prompt ngắn của Trung (có 2/40 câu nhận bán hàng ngoài danh mục).

## 5.6 Hạn chế và việc còn lại
Chưa có người duyệt eval_qa/eval_router (yêu cầu ≥ 30 %, 2 người); giám khảo LLM cùng họ; n e2e = 52 và sinh theo lô ≠ chế độ phục vụ thật; chưa đủ 60 phản hồi Gemini; 45 câu ngoài phạm vi cần gắn `in_scope=false`. Việc tiếp: eval v1.1 (mục B), 2 người duyệt, người chấm 50 câu RAG, đo e2e 1 câu/lời gọi, lọc review spam, ghép `/qa` với API của Hoàng.

---

# 6. Khoa – EDA, đánh giá visual search, benchmark embedding ảnh, cải tiến

## 6.1 Vai trò
Người cầm số liệu quyết định phần visual: EDA, độ đo visual, xây eval_visual, khảo sát và benchmark ≥ 5 model embedding ảnh (Bảng A), hệ thống/bài báo tương tự (Bảng E), build index, baseline e2e và cải tiến trước/sau. 9 US, 40 point.

## 6.2 Các US phụ trách
| US | Đầu ra | Trạng thái | Ghi chú |
|---|---|---|---|
| US_09 EDA | `docs/US_09_eda/` (9 biểu đồ, notebook, `eda_stats.json`) | **Đạt** | Số liệu riêng FPI và ViMRHP |
| US_12 Độ đo visual | `docs/US_12_do_do_visual_search.md`, `src/msa/eval/visual_metrics.py` | **Đạt** | Recall@K, P@K, mAP, MRR, NDCG, CTE, AUROC, latency |
| US_15 eval_visual | `eval/eval_visual.csv`, `eval_visual_ood.csv`, `docs/US_15_eval_visual.md` | Một phần | 600 truy vấn; 0 ảnh ngoài đời |
| US_19 Khảo sát embedding ảnh | `docs/US_19_khao_sat_embedding_anh.md` | **Đạt** | 10 model trong bảng khảo sát, 8 trong registry |
| US_21 Hệ thống & bài báo | `docs/US_21_he_thong_va_bai_bao_tuong_tu.md` | **Đạt** | Trích dẫn cần xác minh lại |
| US_22 Benchmark ≥ 5 model | `results/bench_image_embed.csv`, `docs/US_22_benchmark_embedding.md` | **Đạt** | 5 model, cùng tiền xử lý, FAISS Flat, latency 60 lần đo |
| US_29 Build index | `src/scripts/build_index.py`, `docs/US_29_build_index.md` | **Đạt** | embed catalog 775,8 s < 30 phút; truy vấn median 168,8 ms |
| US_44 Baseline e2e | `docs/US_44_baseline_e2e.md`, `eval/e2e_scenarios.jsonl`, `results/e2e_http.json` | Một phần | Đo đủ 60 kịch bản trên hệ thống ghép (12/11): TSR 39/60 = 0,650 (chấm tự động); visual-only cũ TSR 15/18. Còn thiếu: đơn giá (chi phí CHƯA TÍNH), người chấm lại |
| US_45 Cải tiến trước/sau | `docs/US_45_cai_tien_va_do_truoc_sau.md`, `results/improvements_fashionclip.*` | Một phần | 4 cải tiến visual đo trên truy vấn tổng hợp; chưa có cải tiến nhóm Gemini |

## 6.3 Việc đã làm cụ thể
- **EDA** 2 nguồn: 37 `articleType`, 785 dòng trùng tên, giá/mô tả/rating thiếu 100 %, ảnh 100 % 60×80; ViMRHP 93,4 % review 5 sao.
- **eval_visual**: tầng instance (ảnh catalog qua 7 họ biến đổi: lệch khung, xoay, đổi màu, lật + co giãn, đổi nền, giảm phân giải/nén JPEG, kết hợp) và tầng category (ảnh SP khác cùng loại + màu, lấy từ 44.072 dòng FPI ngoài catalog; mũ dùng leave-one-out); 60 ảnh OOD (đồng hồ, mỹ phẩm) để chọn τ_v.
- **Benchmark 5 model** trên cùng catalog 4.593 ảnh, cùng tiền xử lý (pad vuông nền trắng → resize → chuẩn hoá theo model), cùng `faiss.IndexFlatIP` (vector chuẩn hoá L2 ⇒ tích vô hướng = cosine), seed 42, có/không type gate, phân tích τ_v.
- **Index + truy vấn** (`VisualSearcher`: embed → gate → FAISS → kiểm τ_v), baseline e2e 60 kịch bản, 4 cải tiến I1 (crop theo nền trắng), I2 (TTA lật ngang), I3 (adapter tuyến tính nghiệm đóng), I19 (type gate).

## 6.4 Số liệu thật chính – Bảng A (split test: 240 instance + 120 category) [Thật–tổng hợp]
| Model (năm, tổ chức) | Chiều | macro R@5 | R@1 | MRR@10 | CTE@5 | cat P@5 | Nhúng 1 ảnh median (ms) | RAM đỉnh (MB) |
|---|---|---|---|---|---|---|---|---|
| DINOv2 ViT-S/14 (2023, Meta AI) | 384 | **0,846** | **0,750** | **0,791** | **0,043** | 0,307 | 288,8 | 1.446 |
| SigLIP B/16 (2023, Google) | 768 | 0,833 | 0,704 | 0,760 | 0,055 | 0,355 | **190,0** | 2.431 |
| FashionCLIP (2022, Farfetch/Coveo) | 512 | 0,829 | 0,704 | 0,757 | 0,062 | **0,378** | 294,2 | 1.597 |
| CLIP ViT-B/32 (2021, OpenAI) | 512 | 0,721 | 0,621 | 0,660 | 0,076 | 0,353 | 428,3 | 2.024 |
| ResNet-50 ImageNet (2016, Microsoft Research) | 2048 | 0,704 | 0,604 | 0,644 | 0,138 | 0,332 | 1.602,9 | 1.357 |
| CLIP B/16, OpenCLIP LAION-2B, Marqo-FashionSigLIP | | CHƯA ĐO (thiếu thời gian CPU) | | | | | | |

Nguồn: `04_Khoa/results/bench_image_embed.csv`. Vì mỗi nhóm có đúng 60 truy vấn instance ở test nên macro R@5 = R@5 tổng. Latency có nhiễu (máy dùng chung).

Độ bền theo họ biến đổi (R@5 instance test, `04_Khoa/results/recall_by_transform.csv`): **đổi nền** (gần ảnh người dùng nhất) SigLIP 0,906 / DINOv2-S 0,812 / FashionCLIP 0,656; **kết hợp** 0,750 / 0,750 / 0,667; **mờ + nén** 0,278 / 0,417 / 0,500.

Ngưỡng τ_v (`04_Khoa/results/tau_v_analysis.json`): τ_v = 0,25 của thiết kế chung **loại 0 % ảnh OOD** với cả 5 model. Chọn trên val bằng "max cosine OOD val + 0,01": DINOv2-S 0,5923 (loại 97,2 % OOD, giữ 94,2 % truy vấn instance), FashionCLIP 0,7039 (100 %, 84,2 %), SigLIP 0,7531 (100 %, 96,3 %).

Build index FashionCLIP (`results/build_index_fashionclip.json`): embed catalog 775,8 s (12,9 phút); search-only 1,9 ms; embed + gate + search median 168,8 ms / p95 674,6 ms. Baseline e2e visual-only: TSR **15/18 = 0,833** (3 lỗi do τ_v loại ảnh nền lạ); các route khác chưa ghép nên TSR toàn hệ thống trong file (0,25) **không có ý nghĩa**.

**Baseline e2e trên hệ thống đã ghép (đo 12/11/2026, 22:52–22:58)** – `04_Khoa/results/e2e_http.json`, từng kịch bản ở `e2e_http_cases.jsonl` / `e2e_http_per_case.csv`, log Gemini của lượt đo ở `e2e_http_llm_calls.jsonl`. Đủ 60 kịch bản của `eval/e2e_scenarios.jsonl`, gọi API thật qua HTTP (`baseline_e2e.py --agent http --resume --max-gemini-calls 11 --pace-s 15`, 2 đợt trong cùng ngày để không vượt quota free tier).
Cấu hình: API `src/msa/api/main.py` (uvicorn 1 worker, Windows 11, embed ảnh trên CPU 2 luồng); `/search/image` = VisualSearcher **DINOv2-S** (`04_Khoa/indexes/dinov2_s`, τ_v 0,5923); `/chat` = Router + Agent (Trung); qa = RAG hybrid BM25 + e5-small, τ_r 0; Gemini `gemini-3.5-flash-lite` qua LLMGateway (cache SQLite bật, RPM 4); catalog shared_data v1 (FPI 4.593 SP). Mỗi kịch bản là **1 lượt trong phiên mới, không kèm product_id**. Server đã nóng (không tính thời gian nạp RAG lúc khởi động). Chấm tự động theo `judge()` **[Chưa người duyệt]**; truy vấn ảnh là ảnh biến đổi **[Thật–tổng hợp]**.

| Route mong đợi | n | TSR | Route đúng | Latency p50 / p95 (ms) | % chuyển Gemini | Lời gọi Gemini | Token in / out |
|---|---|---|---|---|---|---|---|
| visual | 18 | 16/18 = 0,889 | 18/18 | 195,3 / 215,0 | 0 % | 0 | 0 / 0 |
| search | 10 | 10/10 | 10/10 | 10,6 / 22,0 | 0 % | 0 | 0 / 0 |
| qa | 10 | 0/10 | 0/10 | 9,2 / 24.090,0 | 20 % | 2 | 334 / 123 |
| compare | 6 | 0/6 | 1/6 | 4,8 / 5,0 | 0 % | 0 | 0 / 0 |
| gemini_chitchat | 6 | 5/6 | 3/6 | 7.021,0 / 33.805,1 | 83 % | 5 | 822 / 248 |
| gemini_ood | 6 | 4/6 | 4/6 | 7.074,9 / 12.043,9 | 67 % | 4 | 658 / 217 |
| clarify | 4 | 4/4 | 4/4 | 3,4 / 4,7 | 0 % | 0 | 0 / 0 |
| **Tổng** | **60** | **39/60 = 0,650** | 40/60 = 0,667 | **29,1 / 12.759,5** | **11/60 = 18,3 %** | 11 (+2 lần thử lại) | 1.814 / 588 |

- **Token/100 lượt:** vào 3.023,3, ra 980,0, tổng 4.003,3 (thinking 0). Chi phí/100 lượt **CHƯA TÍNH** vì đơn giá Gemini chưa xác minh. Cache bật nhưng 0 hit (mọi câu đều mới), nên token và latency đều là của lời gọi thật.
- **Latency tách theo loại:** ảnh p50 / p95 = 195,3 / 215,0 ms; văn bản 9,9 / 13.266,5 ms. p95 bị kéo bởi Gemini (mỗi lời gọi 1,9–13,3 s). Hai lời gọi (e2e_34, e2e_47) quá hạn ở lần đầu rồi thử lại, mất 38,4 s và 40,8 s.
- **Lỗi:** route_sai 15 (qa → search 5, clarify 3, gemini_ood 2; compare → clarify 5); khong_chuyen_gemini 3 ("Phối áo sơ mi trắng…" → search; "Viết giúp mình bài thơ…", "Tỉ giá đô la…" → clarify); ảnh bị gate loại 1 (e2e_03); SP đúng ngoài top-5 1 (e2e_18); compare thiếu SP 1 ("So sánh mũ A và mũ B").
- **Cách hiểu đúng:** TSR qa/compare = 0 chủ yếu do kịch bản một lượt nói "đôi giày này", "2 cái này" mà không có SP nào trong ngữ cảnh. Với compare, hỏi lại (clarify) là hành vi hợp lý. Đây chưa phải số đo năng lực RAG/so sánh (RAG đo riêng ở mục 4). Lỗi thật của router: 2 câu hỏi về SP bị đưa sang Gemini và 5 câu bị đưa sang search. Cần bộ kịch bản v1.1 có `product_id`/phiên (không sửa file gốc).
- **Gemini [Tác nhân kiểm]:** 0/10 câu trả lời Gemini nêu giá/size/tồn kho theo regex của `judge()`. Tuy nhiên e2e_51 ("Thời tiết Hà Nội mai thế nào?") Gemini tự đưa dự báo thời tiết, tức bịa thông tin thời gian thực mà regex không bắt được.
- DINOv2-S ở đây khác FashionCLIP ở lượt visual-only, nên 16/18 và 15/18 không so trực tiếp được (khác model).

Cải tiến (FashionCLIP, split test, `04_Khoa/results/improvements_fashionclip.json`) **[Thật–tổng hợp]**:

| Cải tiến | R@5 trước → sau | Tác động khác | Quyết định |
|---|---|---|---|
| I3 adapter tuyến tính (λ = 3 chọn trên val; học từ 800 ảnh biến đổi của SP ngoài eval) | 0,829 → 0,921 | MRR 0,757 → 0,872; CTE@5 0,062 → 0,026 | Giữ có điều kiện, **mặc định tắt**: adapter học trên cùng họ biến đổi tổng hợp với truy vấn test ⇒ **chưa chứng minh cải thiện trên ảnh thật** |
| I2 TTA lật ngang | 0,829 → 0,838 (+2/240 truy vấn) | latency embed ×2 | Bỏ |
| I1 crop theo nền trắng (chỉ truy vấn) | 0,829 → 0,825 | cat P@5 −0,022 | Bỏ biến thể này |
| I19 type gate zero-shot (τ = 0,9) | 0,829 → 0,821 | CTE@5 0,062 → 0,044 (−28 %) | Không thoả quy tắc "giảm CTE mà không giảm R@5"; đề xuất dạng mềm (hỏi lại khi gate không chắc) – CHƯA ĐO |

## 6.5 Quyết định / phát hiện
- Khoa chọn tạm **FashionCLIP** (cat P@5 cao nhất, có text tower cho gate zero-shot). Bảng F chạy trên chính số của Khoa xếp **DINOv2-S hạng 1** ở 12/12 cấu hình độ nhạy ±0,05; DINOv2-S không gate đã có CTE@5 0,043 ≈ FashionCLIP có gate 0,044. ⇒ Lựa chọn FashionCLIP **không được Bảng F ủng hộ**; đề xuất DINOv2-S, dự phòng SigLIP B/16 (bền nhất khi đổi nền), **chốt lại sau khi có ≥ 80 ảnh ngoài đời** (mục E).
- Lưu ý trung thực: DINOv2 được huấn luyện tự giám sát với các phép tăng cường tương tự biến đổi tổng hợp nên có thể được lợi trên tập này.
- Ngưỡng τ_v phải đi theo model (mỗi model có thang cosine riêng), lưu trong `indexes/<model>/config.json`.

## 6.6 Hạn chế và việc còn lại
100 % truy vấn là biến đổi tổng hợp trên ảnh 60×80; FashionCLIP có thể đã thấy dữ liệu cùng nguồn; nhãn eval chưa người duyệt; 3 model chưa đo. Việc tiếp: đo lại 3 model đầu trên ảnh ngoài đời; build index DINOv2-S (≈ 13 phút) nếu nhóm chốt mục E; đo lại I1/I2/I3/I19 cho model được chọn; chạy US_44 khi Agent + API đã ghép.

---

# 7. Hoàng – repo, dữ liệu public, metrics, API backend, LLM gateway

## 7.1 Vai trò
Dựng repo/môi trường, tải dữ liệu public (giày + phụ kiện, quần áo + mũ), viết `metrics.py` dùng chung, API FastAPI (/search/image, /search/text, /compare, validation), LLM gateway Gemini (cache, rate limit, dự phòng 429), kiểm chéo Bảng C. 11 US, 41 point.

## 7.2 Các US phụ trách
| US | Đầu ra | Trạng thái | Ghi chú |
|---|---|---|---|
| US_02 Repo + môi trường | `repo_skeleton/` | Một phần | check_env 17–32 s; chưa có GitLab thật, chưa đo cài trên máy sạch |
| US_06 Dataset giày + phụ kiện | `src/scripts/01_download_public.py` | **Đạt** | 2.335 SP (2.100 có ảnh ≥ 1.700); 2 lần chạy cùng hash |
| US_17 metrics.py + run_eval | `src/msa/eval/metrics.py`, `tests/test_metrics.py` | **Đạt** | 10 test khớp tính tay; Khoa đối chiếu chéo |
| US_23 Benchmark text-embedding | `src/scripts/bench_text_embed.py`, `docs/US_23_benchmark_text_embedding.md` | **Đạt** | 5 cấu hình × 3 seed |
| US_30 API /search/image | `src/msa/api/{main,searchers}.py` | Một phần | p95 1.106 ms; Recall@5 qua API CHƯA ĐO; đang dùng CLIP B/32 + τ_v 0,25 |
| US_32 Validate ảnh | `src/msa/api/validation.py` | **Đạt** | 10 + 3 tình huống lỗi, không crash |
| US_37 API /search/text | `src/msa/api/text_search.py` | **Đạt** | 15/15 truy vấn, 300/300 kết quả thoả lọc |
| US_38 API /compare | `src/msa/api/compare.py` | **Đạt** | 20 nhóm, 370/370 ô khớp dữ liệu gốc |
| US_39 Gợi ý (stretch) | `src/msa/api/recommend.py` | Một phần | Luật + bộ lọc câu bịa có test; chưa chạy Gemini thật |
| US_48 Quần áo + mũ | `src/scripts/01b_download_clothing_hats.py`, `02_merge_data_v1.py` | Một phần | Quần áo đạt; mũ thiếu (285 có ảnh) – đã ghi quyết định |
| US_50 LLM gateway | `src/msa/llm_gateway.py`, `docs/US_50_llm_gateway.md` | **Đạt** | 10/10 request thật; 429 thật → dự phòng, không crash |

## 7.3 Việc đã làm cụ thể
- **Repo skeleton** có `requirements.txt` ghim phiên bản thật, `.env.example` (không có key), Makefile, `check_env.py`.
- **Data v1**: script tải + chuyển schema, kiểm tái lập bằng hash; Data v1 = 5.021 SP (FPI 4.593 + ViMRHP 428); probe Amazon 20.000 dòng → 372 mũ nhưng ảnh bị chặn.
- **API FastAPI** đo trong tiến trình: 80 ảnh truy vấn (60 ảnh FPI không có trong catalog + 20 ảnh mũ leave-one-out); /search/text 15 truy vấn; /compare 20 nhóm.
- **LLM gateway**: cache exact-match SQLite, rate limiter ≤ 4 RPM, retry/backoff, thông điệp dự phòng `source="fallback"`, đổi model bằng biến môi trường, log token.
- **Bảng C kiểm chéo** trên kho 9.403 chunk chỉ review, 3 seed.

## 7.4 Số liệu thật chính
| Chỉ số | Giá trị | Loại | File |
|---|---|---|---|
| /search/image (CLIP B/32, n=80) latency p50 / p95 | 393 ms / 1.106 ms (97,5 % < 1,5 s) | [Thật–thật], có nhiễu | `05_Hoang/results/api_eval.json` |
| CTE@5 / sub-category P@5 qua API | 1,5 % / 0,925 | [Thật–thật] | như trên |
| Top-1 cosine trung bình / số truy vấn dưới τ_v 0,25 | 0,96 / 0 | [Thật–thật] | như trên |
| /search/text | 15/15 truy vấn, 300/300 kết quả thoả lọc, p50 20 ms | lọc giá/size chỉ trên dữ liệu tổng hợp | như trên |
| /compare | 370/370 ô khớp, p50 3,4 ms | [Thật–thật] | như trên |
| Text-embed Hit@5 trong SP (208–209 câu eval_qa) | TF-IDF word 0,875 > TF-IDF char 0,856 > e5-small 0,803 > MiniLM-L12 0,794 > vietnamese-sbert 0,775 | [Chưa người duyệt] | `05_Hoang/results/bench_text_embed_summary.csv` |
| LLM gateway (Flash-Lite, 10 câu) | 10/10 thành công; token TB 104,6 vào / 63,7 ra; cache 10/10, p50 17,9 ms | [Thật–thật] | `05_Hoang/results/llm_gateway_live.json` |
| Thinking `gemini-3.5-flash` (n=1, thăm dò) | mặc định 458 token thinking, `thinkingBudget=0` → 0 | thăm dò | `llm_gemini35_thinking_probe.json` |
| Data v1 | 5.021 SP; quần áo 2.388 (gồm ViMRHP), mũ 298 (gồm 7 băng đô + 5 mũ ViMRHP không ảnh) | [Thật–thật] | `05_Hoang/data/counts_data_v1.json` |

## 7.5 Quyết định / phát hiện
- **"TF-IDF > neural"** trên dữ liệu này (review ngắn, nhiều teencode, tên SP lặp từ khoá) – khớp với Chiến; Hybrid chỉ Chiến đo nên Bảng C chính thức dùng số của Chiến (đúng kho RAG sẽ chạy), số của Hoàng là kiểm chéo độc lập (mục G3). Lưu ý: 2 model (MiniLM, vietnamese-sbert) chạy trên 209 câu, 3 model còn lại trên 208 câu – chênh 1 câu do sửa nhãn qa108 giữa 2 lần chạy.
- Với CLIP B/32, ảnh studio có cosine top-1 ~0,96 nên τ_v 0,25 không chặn gì → API phải đọc model + τ_v từ config của Khoa (mục C, G4).
- Đề xuất bổ sung `source="fallback"` vào hợp đồng (mục D) – đã áp dụng ở UI và router, chờ Trung chốt.

## 7.6 Hạn chế và việc còn lại
Recall@5 qua API chưa đo; API chưa nạp model được chọn; endpoint `/qa`, `/chat` chưa nối pipeline của Chiến/Trung; đơn giá token chưa xác minh. Việc tiếp: API đọc `indexes/best/config.json`; ghép `/qa` + `/chat`; log `requests.jsonl` cho bảng route; cài thử máy sạch (N20); cache làm nóng 5 kịch bản demo (I15).

---

# 8. Trả lời 3 yêu cầu của thầy (tổng hợp xuyên thành viên)

## 8.1 Yêu cầu 1 – Thu thập dữ liệu: phương pháp, lý do, kết quả
| Phương pháp | Quyết định | Lý do (bằng chứng thật) | Người |
|---|---|---|---|
| Dataset public (HF/Kaggle/học thuật) | **Chọn – nguồn chính** | Tải ngay, có nhãn làm ground truth, tái lập được (seed 42, hash), có paper/trang nguồn để trích dẫn | Đạt, Hoàng |
| Crawl sàn TMĐT VN | Không chọn ở lượt này | Tiki 403 với IP cloud, Shopee không kết nối, rủi ro ToS | Chiến |
| API chính thức sàn | Không chọn | Cần tư cách seller, không kịp 3 tuần | Đạt |
| Tự chụp ảnh ngoài đời | **Chọn – chỉ cho tập test** | Cách duy nhất có ảnh giống ảnh người dùng – **chưa làm (0/80)** | Đạt |
| Sinh bằng LLM | **Chọn – bổ trợ bộ đánh giá** | Nhanh, phủ câu khó; bắt buộc gắn `origin`; giới hạn quota | Chiến, Trung |
| Mua dataset / hợp tác doanh nghiệp / Google Images / dataset cuộc thi | Không chọn | Chi phí, thời gian xin quyền, bản quyền ảnh không rõ | Đạt |

Kết quả: xem §2 (nguồn, license, mức tin cậy, phân bố 4 nhóm, đặc điểm). Hạn chế phải nói thẳng: ảnh 60×80 làm số visual lạc quan; không có giá/size; mũ thiếu 15 SP; review lệch tích cực.

## 8.2 Yêu cầu 2 – Độ đo: có những gì, chọn gì, vì sao
| Module | Đã khảo sát | Chọn (chính) | Không chọn / phụ | Lý do gắn mục tiêu sản phẩm |
|---|---|---|---|---|
| Visual search | Recall@K, Precision@K, mAP, MRR, NDCG, CTE, AUROC, latency | **macro Recall@5, MRR@10, CTE@5, latency p95** | mAP (khó giải thích, cần GT đầy đủ); NDCG, P@5 phụ; AUROC để chọn τ_v | Người dùng xem ~5 kết quả; macro để mũ không bị quần áo che; nhầm giày↔áo là lỗi khó chấp nhận nhất |
| RAG – tìm | Hit@K, MRR, context precision/recall | **Hit@5** (lọc theo product_id), MRR@10 | context precision/recall (cần nhãn từng câu) | Tìm sai thì LLM không thể đúng; tách lỗi "không tìm ra" khỏi "nói sai" |
| RAG – trả lời | EM/F1, ROUGE, BLEU, BERTScore, faithfulness, relevancy, hallucination, abstention, human eval | **Faithfulness, hallucination rate, refusal accuracy + false-refusal**, human eval 50 câu | ROUGE/BLEU (không phản ánh đúng/sai nghĩa tiếng Việt) | Mục tiêu số 1 là không bịa; thiếu dữ kiện phải nói "chưa có thông tin" |
| Tìm / So sánh | attribute F1, factual correctness | **Attribute F1, % ô so sánh khớp DB** | – | Lọc sai thì kết quả sai từ đầu; bảng so sánh lấy từ DB phải ~100 % |
| Agent + Gemini | route accuracy, tool-call accuracy, TSR, latency e2e, chi phí/lượt, fallback rate, unsupported-store-fact | **Route accuracy, TSR, unsupported-store-fact, fallback rate, token/100 lượt hội thoại** | – | Router là "não"; Gemini không được bịa giá/size/tồn kho/danh mục |

Định nghĩa + ví dụ tính tay: `00_Chung/THUAT_NGU.md`. Ví dụ: 3 truy vấn có SP đúng ở hạng 1, 2, 4 → MRR = (1 + 0,5 + 0,25)/3 = 0,583; macro R@5 FashionCLIP = (0,733 + 0,833 + 0,883 + 0,867)/4 = 0,829; 1 SP đúng ở hạng 3 → NDCG@10 = (1/log₂4)/(1/log₂2) = 0,5.

Ngưỡng mục tiêu đặt từ baseline thật (`01_Trung/docs/US_18_chot_do_do_va_nguong.md`):

| Độ đo | Baseline đo thật | Mục tiêu | Tình trạng |
|---|---|---|---|
| Visual macro R@5 (test) | 0,846 DINOv2-S [Thật–tổng hợp] | 0,85 (tổng hợp) / 0,70 (ảnh thật) | Gần đạt / ảnh thật CHƯA ĐO |
| Visual CTE@5 | 0,043 [Thật–tổng hợp] | ≤ 0,05 | Đạt |
| RAG Hit@5 (test, n=114) | 0,895 hybrid [Chưa người duyệt] | 0,90 | Gần đạt |
| Faithfulness / hallucination | 1,00 / 0,00 (Chiến); 0,939 / 0,111 (Đạt) **[LLM chấm]** | ≥ 0,85 / ≤ 0,10 | Đạt theo LLM chấm – chờ người chấm |
| Refusal accuracy | 15/15 (sau sửa nhãn; trước 15/16) | ≥ 0,90 | Đạt trên mẫu nhỏ, không phải held-out |
| Route accuracy (held-out, n=49) | 0,878 | ≥ 0,90 | **Chưa đạt** |
| Agent TSR e2e (60 kịch bản, hệ thống ghép, 12/11) | 0,650 (39/60) [Chưa người duyệt] | 0,80 | **Chưa đạt** (qa/compare 0 vì kịch bản không kèm SP – xem §6.4) |
| Token/100 lượt (e2e, 12/11) | 3.023,3 vào + 980,0 ra; 18,3 % lượt chuyển Gemini | ghi nhận | Chi phí CHƯA TÍNH (đơn giá cần xác minh) |
| Unsupported-store-fact (Gemini) | giá/size/tồn kho 0/40 (Trung), 0/20 (Chiến); nhận bán hàng ngoài danh mục 2/40 | 0 | **Chưa đạt** |
| Latency /search/image p95 | 1.106 ms (CLIP B/32); DINOv2-S qua API e2e 215,0 ms (18 ảnh, 12/11) | < 1,5 s | Đạt |

## 8.3 Yêu cầu 3 – Khảo sát phiên bản bằng số liệu
- **Bảng A – embedding ảnh** (Khoa): 5 model đo thật, xem §6.4. Kết luận: DINOv2-S và SigLIP/FashionCLIP chênh nhau ≤ 1,7 điểm macro R@5; CLIP B/32 và ResNet-50 kém rõ (thấp hơn 3 model đầu ≥ 10 điểm).
- **Bảng F – chấm điểm có trọng số** (Trung): DINOv2-S **4,83** > SigLIP 3,98 ≈ FashionCLIP 3,96 > CLIP B/32 2,99 > ResNet-50 2,40; hạng 1 giữ ở 12/12 cấu hình độ nhạy; kịch bản B (thêm tiêu chí tầng category 0,10): DINOv2-S 4,48 > FashionCLIP 4,03 > SigLIP 3,96. **Đề xuất DINOv2-S**, dự phòng SigLIP B/16.
- **Bảng B – vector index**: FAISS IndexFlatIP (tìm chính xác) 4.593 vector, search median 0,3–1,6 ms, index 7–38 MB → không cần index xấp xỉ (IVF/HNSW) ở quy mô < 10.000 SP.
- **Bảng C – text-embedding cho RAG tiếng Việt** (Chiến, kiểm chéo Hoàng): Hybrid RRF Hit@5 test 0,895 > TF-IDF 0,877 > BM25 0,868 > e5-small 0,807 > MiniLM 0,763; Hoàng độc lập: TF-IDF word 0,875 > e5-small 0,803. **Chọn Hybrid**. bge-m3 CHƯA ĐO (thiếu RAM).
- **Bảng D – LLM trả lời** (Đạt) [LLM chấm]: Gemini 3.5 Flash-Lite 0,939 / 0,111; Gemma 4 26B 0,992 / 0,031 nhưng token ra gấp ~17 lần; Qwen2.5-0.5B 0,255 / 0,333. **Chọn Flash-Lite** (chất lượng đủ, rẻ token). `gemini-3.5-flash` CHƯA ĐO (hết quota).
- **Bảng D2 – Gemini ở vai trò fallback/router**: router luật v1 0,878 (held-out, n=49); Gemini làm router 0,857 (n=14) – hai phương án khác nhau, không phải 2 lần đo cùng hệ thống; xem §9.
- **Bảng E – hệ thống/bài báo tương tự** (Khoa): Google Lens, Pinterest Lens, Shopee, Amazon Rufus, CLIP, RAG, Visual Search tại Pinterest/eBay/Alibaba – mỗi mục có "điểm đáng học" và "liên hệ đồ án" (trích dẫn cần xác minh lại).

---

# 9. Tỉ lệ chuyển Gemini và token / 100 lượt

Đơn vị chính thức (mục F): **token / 100 lượt hội thoại** = fallback rate × 100 × (token vào + ra + thinking trung bình mỗi lời gọi Gemini). Fallback rate đo trên 172 câu của 3 bộ eval (cân bằng nhãn, **không phải lưu lượng thật**, chưa trừ cache).

| Bộ eval | n | Chuyển Gemini | Tỉ lệ |
|---|---|---|---|
| Seed của Trung (dev) | 45 | 13 | 0,289 |
| eval_router của Chiến | 78 | 21 | 0,269 |
| Held-out Gemini sinh | 49 | 13 | 0,265 |
| **Tổng** | **172** | **47** | **0,273** |

| Cấu hình (người đo, file) | Model | Token/lời gọi (vào + ra + thinking) | n lời gọi | Token / 100 lời gọi Gemini | **Token / 100 lượt hội thoại** |
|---|---|---|---|---|---|
| Prompt ngắn, không thinking (Trung, `gemini_fallback_live.json`) | gemini-3.5-flash-lite | 165,1 + 55,5 + 0 = 220,6 | 40 | 22.060 | **≈ 6.028** |
| Prompt ngắn, thinking 1024 (Trung) | gemini-3.5-flash-lite | 164,7 + 37,3 + 350,3 = 552,3 | 10 | 55.230 | ≈ 15.092 |
| Prompt few-shot dài – **dự kiến dùng cho demo** (Chiến, `gemini_fallback_check.json`) | gemini-3.5-flash-lite | 747,5 + 41,7 = 789,2 | 22 | 78.920 | **≈ 21.566** |
| Prompt 3 câu (Hoàng, `llm_gateway_live.json`) | gemini-3.5-flash-lite | 104,6 + 63,7 = 168,3 | 10 | 16.830 | ≈ 4.599 |
| Để tham chiếu: RAG có ngữ cảnh review (Đạt, Bảng D) | gemini-3.5-flash-lite | 606,2 + 36,3 | 36 | 64.250 /100 câu QA | không quy đổi (vai trò khác) |

Chi phí tiền / 100 lượt: **CHƯA TÍNH** – đơn giá `[cần xác minh – điền theo bảng giá Google hiện hành]`; công thức `USD = (token_vào × giá_vào + (token_ra + thinking) × giá_ra) / 10⁶`. Free tier = 0 đồng nhưng giới hạn 20 request/ngày/model, không đủ cho demo nhiều lượt → cân nhắc key riêng hoặc bật billing trước N21. Cache: 10/10 câu lặp trúng (0 lời gọi API) ở cả client của Trung và gateway của Hoàng. Tỉ lệ chuyển 0,273 dưới mức cảnh báo 0,30 (R14) nhưng vượt nhẹ mục tiêu 0,25 của US_41.

---

# 10. Tình trạng so với Definition of Done

Definition of Done (sheet Rủi ro & Quy ước, mục C): đạt đủ cột TEST · code chạy lại được từ README · có số liệu · **Support đã review** · Status = Done · nhánh Gemini có test 429/timeout.

| Tiêu chí DoD | Tình trạng | Bằng chứng |
|---|---|---|
| Đạt đủ cột TEST | 23/51 US | §1.4 và mục 0 trong README từng thành viên |
| Code chạy lại từ README | Đạt cho phần đã kiểm: 233 test pass; Tác nhân 3 chạy lại Bảng F, router eval, recall theo họ biến đổi – ra đúng số đã báo cáo | `KIEM_DINH_TAC_NHAN_3.md` §3 |
| Có số liệu hoặc ảnh chụp kết quả | Đạt – 211 con số đã đối chiếu, 0 lệch sau sửa | `00_Chung/kiem_dinh/doi_chieu_so_lieu.md` |
| Support đã review | **Chưa** – mới có review của tác nhân AI | – |
| Status = Done trong Backlog | **Chưa cập nhật** | – |
| Nhánh Gemini có test 429/timeout | Đạt | `05_Hoang/tests/test_llm_gateway.py`, `03_Chien/tests/test_gemini_branch.py` |
| **Kết luận** | **0/51 US đạt DoD chính thức**; 23 US đạt về mặt kỹ thuật, chờ người Support review và người thật duyệt nhãn | |

Những phần "KHÔNG được cắt" theo kế hoạch: 3 yêu cầu của thầy – **đã có nội dung + số liệu** (chưa xuất .docx/slide); Visual Search và Product QA chạy được – có ở mức module, **chưa ghép end-to-end**; bảng trước/sau cải tiến – có cho visual, thiếu nhóm Gemini (I15/I16); demo chạy 1 lệnh – có ở chế độ API giả lập; nhánh Gemini tối thiểu (chitchat, hỏi lại, nhãn nguồn, 429/timeout) – có.

---

# 11. Các quyết định nhóm cần chốt
Chi tiết bằng chứng và phương án: `00_Chung/QUYET_DINH_CAN_CHOT.md`.

| Mục | Vấn đề | Đề xuất | Người chốt | Hạn |
|---|---|---|---|---|
| A | Số mũ 293/286/285/298 | **285 SP có ảnh** là số chuẩn; sửa 7 nhãn mũ, giữ 3 boot; mũ ở mức demo | Trung + Đạt | N5 |
| B | Trang sức/tất trong eval và kho RAG | Giữ 4 nhóm; eval_router v1.1 đổi 4 câu sang `gemini_ood`; eval_qa thêm `in_scope` (báo cáo chính trên 235 câu) | Chiến + Trung | N6 |
| C | τ_v 0,25 cố định | Bỏ; τ_v theo model đọc từ `config.json` (DINOv2-S 0,5923; FashionCLIP 0,7039); hiệu chỉnh lại trên ảnh ngoài đời | Khoa + Trung + Hoàng | N11 |
| D | `source="fallback"` ngoài hợp đồng | Thêm giá trị `fallback`, UI hiện "Thông báo hệ thống" (đã áp dụng, có thể hoàn tác) | Trung + Hoàng + Đạt | N14 |
| E | Model embedding ảnh | **DINOv2-S** theo Bảng F, dự phòng SigLIP; chốt lại sau ≥ 80 ảnh ngoài đời | Trung + Khoa | N12 |
| F | Token/100 lượt lệch 6 nghìn – 79 nghìn | Đơn vị chính "/100 lượt hội thoại"; prompt few-shot của Chiến cho demo (≈ 21,6 nghìn token/100 lượt) | Chiến + Trung + Hoàng | N11 |
| G1 | Mỗi người một phiên bản catalog | **Data v1.1** = catalog sạch 4.385 SP + taxonomy v1 + 7 sửa mũ; index demo build trên v1.1 | Trung + Đạt + Hoàng | – |
| G2 | ViMRHP 428 hay 361 SP | 428 SP nạp kho, 361 thuộc 4 nhóm; review: 9.403 (thô, 428 SP) → 9.317 (khử trùng) → 7.833 (thô, 361 SP) / 7.575 (349 SP có lá) | Chiến + Trung | – |
| G3–G7 | Bảng C hai người; API dùng CLIP B/32; baseline cũ; số pytest; router 0,878 vs 0,857 | xem file | – | – |

---

# 12. Kế hoạch tiếp theo (Tuần 2–3, theo lịch)
Lưu ý: lượt làm việc này đã làm trước nhiều việc của Tuần 2–3 (benchmark, RAG, router, API). Các mốc dưới đây ưu tiên **việc cần người thật** và **ghép hệ thống**.

| Mốc | Ngày | Việc | Người |
|---|---|---|---|
| N5 | 09/11 | Họp review Tuần 1: ký mục A (mũ 285), G1 (Data v1.1); 2 luật tiêu đề mũ vào `map_fpi`; chạy lại `build_category_map.py`, `03_clean.py` | Trung, Đạt, Hoàng |
| N6–N7 | 10–11/11 | Ký mục B; eval_router/eval_qa v1.1; xuất `report_week1.docx` từ US_26 | Chiến, Trung |
| N8–N9 | 12–13/11 | **Chụp 80–100 ảnh ngoài đời** (giày 25, quần áo 25, mũ 15, phụ kiện 15), 2 người gán ground truth; 2 người duyệt ≥ 30 % eval_qa/eval_router | Đạt, Chiến (cả nhóm hỗ trợ) |
| N10–N11 | 14–15/11 | Chạy lại Bảng A cho DINOv2-S / SigLIP / FashionCLIP trên ảnh ngoài đời; hiệu chỉnh τ_v; người chấm 50 câu RAG; ký mục C, F | Khoa, Chiến, Trung |
| N12 | 16/11 | Họp chấm điểm Bảng F với số ảnh thật → **ký mục E** (model chính) | Trung, Khoa |
| N13–N14 | 17–18/11 | Xuất `report_week2.docx` + slide 18 trang từ US_27; chốt kiến trúc + OpenAPI (ký mục D) | Trung, cả nhóm |
| N15–N17 | 19–21/11 | Build index model đã chốt trên Data v1.1; API đọc config; ghép Router v2 + 4 công cụ + `/qa`, `/chat`; nối UI với API thật | Khoa, Hoàng, Trung, Chiến, Đạt |
| N17–N18 | 21–22/11 | Baseline e2e 60 kịch bản (TSR, tỉ lệ Gemini, token/100 lượt thật); chọn cải tiến theo lỗi (I12/I17 router, I15 cache làm nóng, I16 prompt, I19 gate mềm) | Khoa, Trung |
| N19 | 23/11 | Đo lại sau cải tiến, điền sheet Cải tiến T3; chạy 20 kịch bản kiểm thử; **feature freeze 17:00** | Cả nhóm |
| N20–N21 | 24–25/11 | Báo cáo cuối, video dự phòng, cài thử máy sạch; diễn tập 2 lần liên tiếp không lỗi; tag v1.0 | Đạt, Trung, Hoàng |

Rủi ro cần theo dõi: quota Gemini khi demo (R12 – cache làm nóng, key riêng); domain gap studio ↔ ảnh thật (R7 – số visual có thể giảm mạnh); mũ thiếu (R16); nhãn đánh giá do LLM/tác nhân tạo (cần người duyệt trước khi báo cáo chính thức).

---

# Phụ lục – Kiểm định và truy vết
- Đối chiếu số liệu tự động: `python 00_Chung/kiem_dinh/check_numbers.py` → `00_Chung/kiem_dinh/doi_chieu_so_lieu.md` (mỗi dòng: số trong tài liệu | file nguồn | giá trị trong file | khớp/lệch).
- Nhật ký kiểm định (lỗi đã sửa, kết quả pytest/py_compile/grep, rủi ro còn lại): `KIEM_DINH_TAC_NHAN_3.md`.
- Thuật ngữ, công thức, ví dụ tính tay: `00_Chung/THUAT_NGU.md`. Thiết kế chung: `00_Chung/00_THIET_KE_CHUNG.md`.
- Bảng đối chiếu US chi tiết (đầu ra DOCS, tiêu chí TEST, bằng chứng): mục 0 trong `README.md` của từng folder thành viên.
