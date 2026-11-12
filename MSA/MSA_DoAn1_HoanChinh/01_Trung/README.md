# 01_Trung – Nhóm trưởng / Kiến trúc Agent (Đồ án 1 – MSA)

Data version: `shared_data v1 (prep_shared_data.py seed 42)`. Phần cứng: 2 CPU, 7 GB RAM, không GPU.
**Kiểm thử:** `cd 01_Trung && python -m pytest -q` → **54 passed, 1 deselected** ở bản gốc; trên bản A2 (không đóng gói file nặng `data/catalog_fpi_taxonomy_v1.parquet`) → **53 passed, 1 skipped, 1 deselected** – chạy `scripts/build_category_map.py` để sinh lại file thì test bị skip sẽ chạy (1 test `@pytest.mark.live` gọi Gemini thật, bỏ qua mặc định; chạy bằng `MSA_GEMINI_KEY_FILE=<file .env> python -m pytest -m live`).
Không có API key trong folder (`tests/test_no_secrets.py` + `grep -rn "AQ\." .` rỗng). Key chỉ đọc lúc chạy qua `GEMINI_API_KEY` hoặc `MSA_GEMINI_KEY_FILE`, gửi bằng header.

## 0. Đối chiếu yêu cầu kế hoạch (Tác nhân 2 – 05/11/2026)

Nguồn yêu cầu: sheet Backlog (cột DOCS = đầu ra, TEST = tiêu chí nghiệm thu). Trung là Owner của **12 US**. Kết luận: **Đạt 3 · Một phần 6 · Chưa đạt 3** (3 US chưa đạt đều cần người thật hoặc thuộc Sprint 3).

| US | Đầu ra yêu cầu (DOCS) | File đầu ra | Tiêu chí nghiệm thu (TEST) | Kết quả | Bằng chứng / lý do |
|---|---|---|---|---|---|
| US_01 | Project Charter 1 trang | `docs/US_01_project_charter.md` | Mỗi thành viên nói lại mục tiêu, phạm vi, vai trò trong 2' | **Một phần** | Charter có đủ nội dung; buổi kickoff nói lại 2' là việc của người thật – chưa có biên bản |
| US_03 | Biên bản họp | `docs/US_03_bien_ban_hop_template.md` | Biên bản ≥ 90 % ngày làm việc | **Chưa đạt** | Mới có mẫu; chưa có biên bản thật nào |
| US_05 | schema.md + JSON schema | `docs/US_05_schema.md`, `src/schema/product.schema.json` | Mọi nguồn map được; trường bắt buộc rõ | **Đạt** | catalog taxonomy v1 4.586/4.586 hợp lệ, ViMRHP 361/361 – `results/schema_validation.json` |
| US_18 | Cột "Nhóm chọn" + bảng ngưỡng | `docs/US_18_chot_do_do_va_nguong.md` | Mỗi độ đo chọn có ≥ 1 lý do gắn mục tiêu | **Đạt** | Bảng §1 có lý do từng độ đo; bảng ngưỡng §2 đã cập nhật theo số mới nhất của Khoa/Chiến/Đạt (Tác nhân 2) |
| US_25 | Bảng F | `docs/US_25_bang_cham_diem_co_trong_so.md`, `scripts/run_scoring_from_khoa.py` | Mỗi điểm số có số liệu thực nghiệm | **Đạt** (trước: chưa) | Chạy thật trên 5 model của Khoa: DINOv2-S 4,83 hạng 1; 4/6 tiêu chí từ số đo, 2 tiêu chí định tính ghi rõ – `results/weighted_scoring.md`, `weighted_scoring_sensitivity.json` |
| US_26 | report_week1.docx (5–8 trang) | `docs/US_26_bao_cao_tuan1_khung.md` | Đủ 3 mục: phương pháp, lý do, kết quả | **Một phần** | Nội dung đủ 3 mục có số thật; **chưa xuất .docx**; thiếu ảnh tự chụp |
| US_27 | report_week2.docx + slide 15–20 trang | `docs/US_27_bao_cao_tuan2_khung.md` | Trả lời đủ 3 yêu cầu; mỗi kết luận có số liệu | **Một phần** | Tác nhân 2 viết lại thành báo cáo đủ 3 yêu cầu có số; **chưa xuất .docx/slide** |
| US_40 | architecture.md + openapi | `docs/US_40_architecture.md`, `docs/openapi_contract.yaml` | Mỗi endpoint có ví dụ; cả nhóm đồng ý; có sơ đồ route + τ mặc định | **Một phần** | Sơ đồ + ví dụ có; τ_v đã sửa theo đo thật; **chưa có xác nhận của cả nhóm** |
| US_41 | router + tool calling + nhánh Gemini | `src/msa/agent/router.py`, `docs/US_41_router_agent_va_gemini.md` | Route accuracy ≥ 90 % trên eval_router (≥ 60 câu, ≥ 15 chitchat/ood); hỏi lại + chuyển Gemini khi không chắc | **Chưa đạt** | Held-out 0,878 < 0,90 (`results/router_eval_v1.json`); 0,923 trên bộ Chiến là **sau khi đã chỉnh luật theo lỗi** nên không dùng để nghiệm thu; nhánh hỏi lại/Gemini đã chạy |
| US_42 (stretch) | session memory | `src/msa/agent/session_memory.py` | 9/10 kịch bản đa lượt đúng | **Chưa đạt** | Có code + unit test; 10 kịch bản CHƯA ĐO (cắt scope thứ tự 1 nếu trễ) |
| US_47 | demo_script, video, tag v1.0 | `docs/US_47_demo_script_va_dien_tap.md` | Chạy trọn 2 lần liên tiếp không lỗi | **Một phần** | Kịch bản sẵn với SP thật; diễn tập/video là việc Sprint 3 |
| US_49 | taxonomy.md + category_map.csv | `docs/US_49_taxonomy.md`, `data/category_map.csv` | Mọi nhãn map được hoặc `unknown`; 30 mẫu/nguồn sai ≤ 3; Khoa + Hoàng đồng ý | **Một phần** | 168/168 nhãn FPI; 30 mẫu sai 0 [Tác nhân kiểm]; **Tác nhân 2 phát hiện 7 nhãn mũ sai ngoài mẫu** (fedora/boonie → cap, beanie → cap) – `00_Chung/QUYET_DINH_CAN_CHOT.md` mục A; chưa có Khoa/Hoàng đồng ý |

**Mâu thuẫn liên quan đến Trung đã xử lý:** mũ 293/286/285/298 (mục A), trang sức/tất (B), τ_v (C), `source="fallback"` (D – đã sửa `router.py` + test), Bảng F (E), token Gemini (F) – tất cả ở `00_Chung/QUYET_DINH_CAN_CHOT.md`; Trung là người chốt A, B, D, E.

## 1. Truy vết US → file → trạng thái (bản của thành viên, giữ nguyên để đối chiếu)
| US | File chính | Trạng thái | Số liệu THẬT đã có | Việc còn lại |
|---|---|---|---|---|
| US_01 Charter | `docs/US_01_project_charter.md` | Bản nháp hoàn chỉnh | – | Kickoff: từng người nói lại 2' |
| US_03 Biên bản | `docs/US_03_bien_ban_hop_template.md` | Mẫu sẵn | – | Ghi biên bản ≥ 90% ngày |
| US_05 Schema | `docs/US_05_schema.md`, `src/schema/product.schema.json`, `src/schema/examples/` (8 SP thật), `src/msa/data/schema_adapters.py` | Hoàn thành | catalog gốc 4.320/4.593 hợp lệ (273 nhãn tạm); catalog taxonomy v1 **4.586/4.586**; ViMRHP **361/361** – `results/schema_validation.json` | Hoàng duyệt; adapter crawl/ảnh tự chụp |
| US_49 Taxonomy | `docs/US_49_taxonomy.md`, `data/category_map.csv`, `src/msa/data/taxonomy.py`, `data/catalog_fpi_taxonomy_v1.parquet`, `data/vimrhp_taxonomy_v1.csv` | Hoàn thành kỹ thuật | 168/168 nhãn FPI map được (100%); ViMRHP 509/509 khớp luật; kiểm 30 mẫu/nguồn: 0 sai – `results/taxonomy_coverage.json`, `results/taxonomy_audit.json` | 2 người thật kiểm lại mẫu; Khoa+Hoàng duyệt; chốt mâu thuẫn trang sức/tất với eval của Chiến |
| US_18 Độ đo & ngưỡng | `docs/US_18_chot_do_do_va_nguong.md` | Đề xuất có baseline thật | Visual (Khoa), RAG retrieval (Chiến), Router/Gemini (Trung) | Faithfulness/Hallucination/TSR CHƯA ĐO; chốt N11 |
| US_25 Chấm điểm | `docs/US_25_bang_cham_diem_co_trong_so.md`, `src/scoring/weighted_scoring.py`, `scripts/run_scoring_from_khoa.py` | **Đạt** (Tác nhân 2 chạy lại) | 5 model: DINOv2-S 4,83 > SigLIP 3,98 > FashionCLIP 3,96 > CLIP B/32 2,99 > ResNet-50 2,40 – `results/weighted_scoring.md` | Họp N12 chốt điểm định tính + model |
| US_26 Báo cáo T1 | `docs/US_26_bao_cao_tuan1_khung.md` | Khung + số thật | 4 nhóm theo taxonomy v1, hạn chế 60×80, thiếu mũ | Crawl/ảnh tự chụp CHƯA; xuất .docx |
| US_27 Báo cáo T2 | `docs/US_27_bao_cao_tuan2_khung.md` | Dàn ý + trỏ số liệu | – | Chờ benchmark đủ ứng viên |
| US_40 Kiến trúc | `docs/US_40_architecture.md`, `docs/openapi_contract.yaml` | Khung sẵn | – | Cả nhóm duyệt N14 |
| US_41 Router/Agent | `src/msa/agent/router.py`, `gemini_client.py`, `intent_embed.py`, `eval/eval_router_seed.jsonl` (45), `eval/eval_router_gemini_gen.jsonl` (49), `docs/US_41_router_agent_va_gemini.md` | Khung chạy được, đo thật | xem §2 | Router v2; nối công cụ thật; eval người thật |
| US_42 Session memory (stretch) | `src/msa/agent/session_memory.py` | Bản đơn giản + unit test | – | 10 kịch bản đa lượt CHƯA ĐO |
| US_47 Demo | `docs/US_47_demo_script_va_dien_tap.md` | Kịch bản sẵn (SP thật) | – | Diễn tập 2 lần, video, tag v1.0 |
| Cải tiến T3 | `docs/lua_chon_cai_tien_tuan3.md` | Đề xuất theo lỗi thật | – | Chốt N18, đo trước/sau |

## 2. Số liệu THẬT chính (lệnh tái lập trong từng file)
| Chỉ số | Giá trị | File |
|---|---|---|
| Route accuracy router v0 trên `03_Chien/eval/eval_router.jsonl` (n=78, held-out) | **0,667** | `results/router_eval_v0.json` |
| Router v1 trên bộ Chiến (đã chỉnh sau khi xem lỗi) | 0,923 (gộp 2 nhãn gemini 0,949) | `results/router_eval_v1.json` |
| **Router v1 trên tập độc lập Gemini sinh (n=49, không chỉnh theo)** | **0,878** – chưa đạt 0,90 | như trên |
| Router + embedding e5-small (ablation) | 0,846 (bộ Chiến) – không dùng | `results/router_eval_v1_emb.json` |
| Fallback rate (172 câu eval) | 0,273 | `results/gemini_fallback_live.json` |
| Gemini (`gemini-3.5-flash-lite`, 40 lời gọi) latency e2e p50/p95 | 14,4 s / 41,1 s (**gồm chờ retry 429**, 62 HTTP/50 câu) | như trên |
| Token TB/lời gọi in/out/thinking | 165,1 / 55,5 / 0; bật thinking 1024: 164,7 / 37,3 / 350,3 | như trên |
| Token / 100 lượt | ≈ 6.028 (≈ 15.092 nếu bật thinking) | như trên |
| Unsupported-store-fact | giá/size/tồn kho 0/40; khẳng định có bán hàng ngoài danh mục **2/40** | `results/gemini_store_fact_recheck.json` |
| Cache | 10/10 trúng, p50 0,3 ms | `results/gemini_fallback_live.json` |

Ghi chú quota: `gemini-3.5-flash` trả **429 – free tier 20 request/ngày/model** (key dùng chung 5 người) → nhánh Gemini đo trên `gemini-3.5-flash-lite` (không nhận `thinkingBudget=0`). Tổng lời gọi Gemini của Trung trong lượt: ~62 (đo) + 1 (sinh tập test) + ~6 thăm dò < 250.

## 3. Lệnh tái lập
```bash
PYTHONPATH=src python scripts/build_category_map.py      # taxonomy + catalog v1
PYTHONPATH=src python scripts/audit_taxonomy_samples.py  # kiểm 30 mẫu/nguồn
PYTHONPATH=src python scripts/validate_catalog.py        # schema trên dữ liệu thật
PYTHONPATH=src python scripts/eval_router.py [--emb]     # route accuracy + confusion
MSA_GEMINI_KEY_FILE=<.env> PYTHONPATH=src python scripts/run_gemini_live.py --model gemini-3.5-flash-lite
PYTHONPATH=src python scripts/recheck_store_facts.py     # hậu kiểm lại offline
PYTHONPATH=src python scripts/run_scoring_from_khoa.py   # Bảng F từ bench của Khoa
```

## 4. Cần nhóm xử lý
1. Thống nhất phạm vi: eval_router của Chiến coi trang sức/tất là hàng trong cửa hàng – trái taxonomy v1.
2. Script làm sạch của Đạt tự suy lá mũ (beanie 21, wide_brim 6) ≠ taxonomy v1 (beanie 20, wide_brim 0) → Tác nhân 2 xem ảnh: **luật của Đạt đúng cho 7 SP mũ, luật của Trung đúng cho 3 boot** → thêm 2 luật tiêu đề vào `map_fpi` (QUYET_DINH mục A).
3. Quota Gemini: chia ngân sách theo người, bật cache, cân nhắc key trả phí trước demo.
4. Mọi nhãn/kiểm mẫu hiện do tác nhân AI hoặc Gemini tạo – cần 2 người thật duyệt.
