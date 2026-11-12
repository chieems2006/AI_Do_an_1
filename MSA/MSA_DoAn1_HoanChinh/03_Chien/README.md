# Chiến – Dữ liệu tiếng Việt, RAG, bộ đánh giá QA, độ đo, prompt Gemini fallback

Đồ án 1 – AI Agent trợ lý mua sắm thời trang (MSA). Dữ liệu: `shared_data v1 (prep_shared_data.py seed 42)` – ViMRHP (CC BY-NC-ND 4.0, chỉ dùng nội bộ học thuật).
Mọi số liệu dưới đây là **đo thật** trong lượt 04–05/11/2026, kèm file kết quả; ô chưa làm được ghi `CHƯA ĐO`.

## 0. Đối chiếu yêu cầu kế hoạch (Tác nhân 2 – 05/11/2026)

Chiến là Owner của **9 US** (Backlog). Kết luận: **Đạt 4 · Một phần 5 · Chưa đạt 0** (Tác nhân 3 hạ US_35 từ Đạt xuống Một phần – lý do ở dòng US_35) – nhưng mọi bộ đánh giá **chưa có người thật duyệt** và số RAG generation là **[LLM chấm]** (giải thích nhãn: `00_Chung/THUAT_NGU.md`).

| US | Đầu ra yêu cầu (DOCS) | File đầu ra | Tiêu chí nghiệm thu (TEST) | Kết quả | Bằng chứng / lý do |
|---|---|---|---|---|---|
| US_07 | `02_crawl_vn.py`, file raw, ghi chú robots/ToS | `src/scripts/02_crawl_vn.py`, `docs/US_07_kiem_tra_robots_tos.md`, `results/crawl_robots_probe.json` | ≥ 300 SP và ≥ 1.000 review tiếng Việt; không bị block; có bằng chứng robots/ToS | **Một phần** | Số lượng đạt bằng **kế hoạch B** (ViMRHP 428 SP / 9.317 review – không phải crawl); crawl thật **bị chặn** (Tiki robots.txt HTTP 403); bằng chứng kiểm robots có. Lưu ý: chỉ 361/428 SP thuộc 4 nhóm (QUYET_DINH mục B, G2) |
| US_13 | Sheet 2 – phần QA/RAG | `docs/US_13_do_do_qa_rag.md` | Mỗi độ đo có công thức, ưu/nhược, quyết định | **Đạt** | 12+ độ đo retrieval + generation đủ 3 cột |
| US_14 | Sheet 2 – Search/Compare/Agent | `docs/US_14_do_do_search_compare_agent.md` | Mỗi độ đo có công thức, ưu/nhược, quyết định | **Đạt** | Đủ intent/tool-call/attribute F1/TSR/latency/chi phí/fallback rate/unsupported-store-fact |
| US_16 | eval_qa.jsonl, eval_router.jsonl | `eval/eval_qa.jsonl`, `eval/eval_router.jsonl`, `docs/US_16_quy_trinh_eval_qa.md` | ≥ 150 cặp; > 15 % không có đáp án; ≥ 30 % được 2 người kiểm; eval_router ≥ 60 câu, ≥ 15 chitchat/ood, ≥ 30 % 2 người duyệt | **Một phần** | Đạt: 280 câu, 25,4 % không đáp án, có cả câu LLM sinh (251) và viết tay (29); eval_router 78 câu, 21 chitchat/ood. **Chưa: 0 % có người duyệt** (annotator trống). **45/280 câu eval_qa và 4/78 câu eval_router thuộc SP ngoài phạm vi** (trang sức, tất…) – danh sách `eval/ngoai_pham_vi_taxonomy_v1.csv` |
| US_20 | Sheet 3 – Bảng C, D | `docs/US_20_khao_sat_text_embedding_llm.md` | ≥ 4 text-embedding, ≥ 5 LLM, ưu/nhược cho tiếng Việt | **Đạt** | 8 embedding, 8 LLM; Bảng C có số đo thật |
| US_33 | ingest script + vector store | `src/msa/rag/ingest.py`, `data/kb/chunks.jsonl` | Mỗi chunk truy ngược được product_id và nguồn | **Đạt** | 10.173 chunk, 100 % có `product_id` + `source` + `chunk_id` (có test) |
| US_34 | API /qa | `src/msa/rag/{retriever,pipeline,llm}.py`, `prompts/rag_grounded.md` | Hit@5 và Faithfulness đạt ngưỡng mục tiêu trên eval_qa | **Một phần** | Hit@5 test **0,895** (hybrid, n=114) ≥ 0,85 của sheet nhưng < 0,90 đề xuất ở US_18; Faithfulness **1,00** trên 52 câu – [LLM chấm, cùng họ Gemini] cần người chấm 50 câu; endpoint `/qa` do Hoàng ghép chưa nối pipeline này |
| US_35 | prompt grounding + guard | `src/msa/rag/pipeline.py`, `docs/US_33_34_35_rag.md` | ≥ 90 % câu ngoài phạm vi trong eval_qa được từ chối đúng | **Một phần** | 15/15 câu không đáp án của 52 câu split test (**sau khi sửa nhãn qa108 trên chính tập này**; trước sửa 15/16 = 0,94); false-refusal 0/37. TEST tính trên eval_qa nhưng mới đo 15/71 câu không đáp án (21 %) vì quota Gemini → chưa đủ để kết luận đạt |
| US_51 | `prompts/gemini_fallback.md` + nhánh Gemini + τ | `prompts/gemini_fallback.md` v1.0, `src/msa/rag/fallback.py`, `docs/US_51_nhanh_gemini.md` | Route accuracy ≥ 90 %; 0/60 phản hồi Gemini bịa giá/size/tồn kho; UI có nhãn nguồn; 429/timeout có thông điệp dự phòng; câu in-domain có product_id không bị đẩy sang Gemini | **Một phần** | Đạt: 0/20 vi phạm + 0/2 câu bẫy (mới 22/60 phản hồi), nhãn nguồn trên UI (Đạt), thông điệp dự phòng khi 429/503. Chưa: route accuracy 0,878 (router của Trung); chưa đủ 60 phản hồi |

**Mâu thuẫn liên quan đã xử lý:** trang sức/tất (QUYET_DINH mục B – Chiến chốt); token Gemini: số "74.750 vào + 4.170 ra /100 lượt" của Chiến là **/100 lời gọi Gemini** với prompt dài có few-shot ≈ 750 token vào/lời gọi; quy về 100 lượt hội thoại ≈ 21.566 token (mục F); Bảng C: số của Chiến (hybrid) và Hoàng (TF-IDF thắng) không mâu thuẫn – khác kho chunk và Hoàng chưa đo hybrid (mục G3).

## 1. Truy vết US → file → trạng thái → số liệu thật → việc còn lại (bản của thành viên)

| US | File chính | Trạng thái | Số liệu thật (file) | Việc còn lại |
|---|---|---|---|---|
| US_07 Crawl TMĐT VN | `src/scripts/02_crawl_vn.py`, `docs/US_07_kiem_tra_robots_tos.md` | Khung sẵn; crawl thật không làm được; tiêu chí số lượng đạt bằng kế hoạch B | Tiki robots.txt **HTTP 403**, Shopee không kết nối (`results/crawl_robots_probe.json`); ViMRHP dùng được **428 SP / 9.317 review** | Nhóm tự đọc robots/ToS và chạy từ máy cá nhân nếu được phép |
| US_13 Độ đo QA/RAG | `docs/US_13_do_do_qa_rag.md` | Hoàn thành | Bảng retrieval mục 2 | Chốt ngưỡng ở N11 |
| US_14 Độ đo Search/Compare/Agent | `docs/US_14_do_do_search_compare_agent.md` | Hoàn thành | Nhánh Gemini (mục 2) | Route accuracy do router (Trung) |
| US_16 Bộ đánh giá | `eval/eval_qa.jsonl` (280), `eval/eval_router.jsonl` (78), `src/scripts/build_eval_qa.py`, `build_eval_router.py`, `docs/US_16_quy_trinh_eval_qa.md` | Khung sẵn – **cần người thật duyệt** | eval_qa: 280 câu / 80 SP, **71 câu answerable=false (25,4%)**, origin llm_gemini 251 + viet_tay_tac_nhan 29; eval_router: 78 câu, 21 chitchat/ood | **2 người duyệt ≥ 30%** (reviewed_by, annotator_1/2 đang trống) |
| US_20 Khảo sát embedding & LLM | `docs/US_20_khao_sat_text_embedding_llm.md` | Hoàn thành (8 embedding, 8 LLM) | Bảng C trỏ `results/rag_retrieval_eval.json`; probe thinking `results/gemini_thinking_probe.json` | Xác minh các ô `[cần xác minh]` |
| US_33 Kho tri thức | `src/msa/rag/ingest.py`, `data/kb/chunks.jsonl`, `results/cache/emb_*.npy` | Hoàn thành | **10.173 chunk** (title 428, review 9.317, detail_rating 428), mỗi chunk có product_id + source + chunk_id | – |
| US_34 Hỏi đáp RAG | `src/msa/rag/{retriever,pipeline,llm}.py`, `prompts/rag_grounded.md` v1.0 | Hoàn thành v0 | Hit@5 hybrid **0.866**; e2e faithfulness **1.00** (giám khảo LLM) – `results/rag_eval.json` | API `/qa` (Hoàng) gọi `build_default_pipeline()`; người chấm 50 câu |
| US_35 Trích nguồn + từ chối | `pipeline.py` (guard), `docs/US_33_34_35_rag.md` | Hoàn thành v0 | Refusal accuracy **15/15**, false-refusal **0/37**, citation rate **1.00** | Đo chế độ 1 câu/lời gọi |
| US_51 Nhánh Gemini | `prompts/gemini_fallback.md` v1.0, `src/msa/rag/fallback.py`, `src/scripts/check_gemini_hallucination.py`, `run_gemini_fallback_check.py`, `docs/US_51_nhanh_gemini.md` | Khung sẵn + đo một phần | **0/20** vi phạm giá/size/tồn kho, 0/2 câu bẫy; 74.750 in + 4.170 out token/**100 lời gọi Gemini** (≈ 21.566 token/100 lượt hội thoại – QUYET_DINH mục F); P50 16,0 s / P95 27,8 s (`results/gemini_fallback_check.json`) | Đủ 60 phản hồi; route accuracy; đo lại latency |

## 2. Số liệu thật chính

**Retrieval** (`results/rag_retrieval_eval.json`, lọc theo product_id, câu answerable của eval_qa):

| Retriever | Hit@1 | Hit@5 | MRR@10 | Hit@5 toàn kho |
|---|---|---|---|---|
| TF-IDF char 2–4 | 0.249 | 0.833 | 0.500 | 0.120 |
| BM25 | 0.244 | 0.837 | 0.496 | 0.163 |
| BM25 + rewrite teencode | 0.249 | 0.818 | 0.496 | 0.163 |
| multilingual-e5-small | 0.263 | 0.794 | 0.490 | 0.120 |
| MiniLM-L12 đa ngôn ngữ | 0.278 | 0.756 | 0.491 | 0.024 |
| **Hybrid RRF (BM25 + e5-small)** | **0.321** | **0.866** | **0.548** | **0.177** |

(Bảng trên tính trên **toàn bộ 209 câu** có đáp án; riêng split **test (n=114)**: Hybrid Hit@5 **0,895**, TF-IDF 0,877 – số dùng trong US_18/US_27. 209 câu là sau khi sửa nhãn qa108; tóm tắt gộp ở `results/rag_eval.json` – `python src/scripts/merge_rag_eval.py`.) Điểm top-1 tách câu có/không đáp án kém (AUC 0.72–0.77) ⇒ τ_r mặc định 0.0, từ chối dựa vào LLM + guard.

**RAG end-to-end** (`results/rag_e2e_eval.json`, 52 câu split test, hybrid, `gemini-3.5-flash-lite`, theo lô 13 câu): refusal accuracy 1.00 (15/15), false-refusal 0.00, citation 1.00, cited-gold 0.865, faithfulness 1.00, hallucination 0.00, relevancy 1.00 (giám khảo Gemini – có thể dễ dãi, cần người kiểm). Token/câu: in 378,9, out 46,2.

**Gemini**: thinkingBudget=0 với `gemini-3.5-flash`: 0 token thinking, 1,3 s, so với mặc định 388 token thinking, 16,0 s (n=1). Free tier: **20 request/ngày/model** (HTTP 429 thật).

## 3. Chạy lại

```bash
cd 03_Chien   # (bản gốc: /home/claude/work/stage1/03_Chien)
python src/scripts/build_eval_router.py --check
PYTHONPATH=src python src/scripts/build_eval_qa.py --check          # --rebuild: dựng lại từ raw + câu viết tay + sửa nhãn
PYTHONPATH=src python -m msa.rag.ingest --out data/kb/chunks.jsonl
HF_HUB_OFFLINE=1 PYTHONPATH=src python src/scripts/eval_rag.py retrieval
MSA_ENV_FILE=<file .env> PYTHONPATH=src python src/scripts/eval_rag.py e2e --n 52 --batch 13
PYTHONPATH=src python src/scripts/eval_rag.py resummarize           # áp nhãn đã sửa, không gọi API
MSA_ENV_FILE=<file .env> PYTHONPATH=src python src/scripts/run_gemini_fallback_check.py
python -m pytest -q                                                  # test live: pytest -m live
```

Key Gemini chỉ đọc từ `GEMINI_API_KEY` hoặc file trỏ bởi `MSA_ENV_FILE`; không ghi vào log/kết quả. Cache: `logs/gemini_cache.sqlite`; vector e5-small: `results/cache/emb_intfloat_*.npy` (cache MiniLM đã chuyển ra ngoài folder vì byte ngẫu nhiên khớp mẫu kiểm key – tự sinh lại khi chạy); log lời gọi (không có key): `logs/gemini_calls.jsonl`.

## 4. Ngân sách Gemini đã dùng

**96 request HTTP** (≤ 250): eval_qa 57 (trong đó 36 bị 429 + 9 bị 503 trên `gemini-3.5-flash` trước khi đổi sang flash-lite), fallback 26, probe 7, RAG e2e 6.

## 5. pytest

`python -m pytest -q` → **51 passed, 1 deselected** (test live bỏ qua mặc định) – chạy lại trên bản A2 sau chỉnh sửa của Tác nhân 2: **51 passed, 1 deselected**.

## 6. Hạn chế và việc nhóm cần làm

1. Chưa có người thật duyệt eval_qa/eval_router; mọi `origin` được ghi đúng (llm_gemini / viet_tay_tac_nhan).
2. ViMRHP không có mô tả/giá/size/tồn kho ⇒ các câu đó luôn là "chưa có thông tin"; không có ảnh.
3. Giám khảo LLM cùng họ Gemini; n e2e = 52; sinh theo lô ≠ phục vụ thật.
4. Latency nhánh Gemini đo lúc server quá tải (503) – cần đo lại.
