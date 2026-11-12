# US_20 – Khảo sát text-embedding & LLM cho RAG tiếng Việt (Sheet "3_Khảo sát phiên bản" – Bảng C, D)

| Mục | Nội dung |
|---|---|
| Mã US | US_20 (3 pt, Sprint 1, Owner: Chiến, Support: Trung) |
| Mục tiêu | Chọn ứng viên embedding + LLM cho Product QA tiếng Việt |
| Đầu ra | Bảng C (8 text-embedding), Bảng D (8 LLM) dưới đây |
| Tiêu chí nghiệm thu | ≥ 4 text-embedding và ≥ 5 LLM, ghi rõ ưu/nhược cho tiếng Việt |
| Trạng thái | **Hoàn thành** (khảo sát). Cột "Kết quả đo" chỉ ghi số **đo thật**; ô chưa đo để `CHƯA ĐO` |

## Tóm tắt 5 dòng
1. Bảng C: 8 text-embedding đa ngôn ngữ; Bảng D: 8 LLM (API + open-source) với ưu/nhược cho tiếng Việt.
2. Đo thật retrieval: Hybrid RRF (BM25 + multilingual-e5-small) tốt nhất – Hit@5 0,866 trên 209 câu, 0,895 trên split test (n=114).
3. Phương pháp từ vựng (TF-IDF/BM25) ≥ dense; Hoàng kiểm chéo độc lập cùng kết luận (QUYET_DINH mục G3).
4. bge-m3 CHƯA ĐO (thiếu RAM); Gemini 3.5 Flash mặc định suy nghĩ ~388 token/câu, tắt bằng thinkingBudget=0.
5. Loại số liệu: [Thật–thật] trên câu hỏi [Chưa người duyệt].
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Quy ước: thông số công khai lấy từ model card HuggingFace / paper / trang chính thức; chỗ có thể sai hoặc đã đổi gắn `[cần xác minh]`.
Số đo thật: (a) của Chiến – `results/rag_retrieval_eval.json` (209 câu answerable eval_qa, lọc theo product_id, 10.173 chunk); (b) của Hoàng – `/home/claude/work/stage1/05_Hoang/results/bench_text_embed*.{csv,json}` (US_23); (c) của Đạt – `/home/claude/work/stage1/02_TuanDat/results/bench_llm_summary.{md,json}` (US_24).

## Bảng C – Text-embedding

| # | Model | Kích thước / chiều | License | Ưu điểm cho tiếng Việt | Nhược điểm | Kết quả đo (Hit@5 / MRR@10, lọc product_id) | Quyết định |
|---|---|---|---|---|---|---|---|
| 1 | `intfloat/multilingual-e5-small` (Wang et al., 2024, "Multilingual E5 Text Embeddings") | ~118M tham số, 384 chiều, 512 token | MIT | Đa ngôn ngữ có tiếng Việt; nhỏ, chạy CPU được | Phải thêm tiền tố `query:`/`passage:`; cosine dồn vào 0.8–0.9 nên ngưỡng tuyệt đối khó đặt | **0.794 / 0.490** (a); mã hoá 10.173 chunk mất 674,8 s trên 2 CPU dùng chung | Ứng viên dense chính (kết hợp BM25) |
| 2 | `intfloat/multilingual-e5-base` / `-large` | 278M / 560M; 768 / 1024 chiều `[cần xác minh]` | MIT | Chất lượng thường cao hơn bản small | Chậm hơn 2–5× trên CPU | CHƯA ĐO (máy 2 CPU) | Thử trên tập con nếu còn thời gian |
| 3 | `BAAI/bge-m3` (Chen et al., 2024) | ~568M, 1024 chiều, tới 8192 token; dense + sparse + multi-vector | MIT | Mạnh trên benchmark đa ngôn ngữ; có sparse (giống BM25) trong 1 model | Nặng cho CPU 2 nhân; 2,2 GB `[cần xác minh]` | CHƯA ĐO | Ứng viên nếu có GPU/Colab |
| 4 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | ~118M, 384 chiều | Apache-2.0 | Nhanh, không cần tiền tố | Huấn luyện cho paraphrase, yếu với câu hỏi–đoạn văn | **0.756 / 0.491** (a); toàn kho chỉ 0.024 | Không chọn |
| 5 | `bkai-foundation-models/vietnamese-bi-encoder` (PhoBERT) | ~135M, 768 chiều `[cần xác minh]` | `[cần xác minh]` | Huấn luyện riêng tiếng Việt | Cần tách từ (pyvi/underthesea); teencode/không dấu dễ lệch từ điển | CHƯA ĐO | Ứng viên đo bổ sung (US_23) |
| 6 | `hiieu/halong_embedding` (tinh chỉnh từ multilingual-e5-base) | 768 chiều `[cần xác minh]` | Apache-2.0 `[cần xác minh]` | Tinh chỉnh tiếng Việt, không cần tách từ | Cộng đồng nhỏ, ít kiểm chứng độc lập | CHƯA ĐO | Ứng viên đo bổ sung |
| 7 | Gemini embedding API (`gemini-embedding-001` `[cần xác minh tên]`) | API; nhiều chiều (có thể rút gọn) `[cần xác minh]` | Điều khoản Google API | Chất lượng đa ngôn ngữ tốt, không tốn CPU | Gửi dữ liệu ra ngoài (R15), tốn quota free tier (đã gặp giới hạn 20 request/ngày/model cho generateContent) | CHƯA ĐO | Không ưu tiên (quota) |
| 8 | Baseline từ vựng: TF-IDF char 2–4 (bỏ dấu) / BM25 âm tiết | – | – | Chịu được không dấu/teencode; 0 chi phí; tức thì (BM25 ~0,1 ms/truy vấn trong 1 SP) | Không hiểu đồng nghĩa ("êm" vs "mềm chân") | TF-IDF **0.833 / 0.500**; BM25 **0.837 / 0.496** (a) | Giữ làm thành phần hybrid |
| ★ | **Hybrid RRF (BM25 + e5-small)** | – | – | Kết hợp từ vựng + ngữ nghĩa | Chậm như dense | **0.866 / 0.548**, Hit@1 0.321 (a) – tốt nhất | **Chọn cho RAG v0** |

## Bảng D – LLM sinh câu trả lời

| # | Model | Loại / kích thước | License / điều khoản | Ưu điểm tiếng Việt | Nhược điểm | Kết quả đo thật | Quyết định |
|---|---|---|---|---|---|---|---|
| 1 | **Gemini 3.5 Flash** (`gemini-3.5-flash`) | API | Google AI Studio ToS; free tier có thể dùng dữ liệu để cải thiện sản phẩm `[cần xác minh]` | Tiếng Việt tự nhiên, theo JSON tốt | Mặc định "thinking": 388 token thinking cho câu trả lời 20 token, 16,0 s; **thinkingBudget=0 ⇒ 0 token thinking, 1,3 s** (`results/gemini_thinking_probe.json`, n=1). Free tier **20 request/ngày/model** (429 thật) | Xem (c) và RAG e2e | LLM chính khi có quota; luôn đặt thinkingBudget=0 |
| 2 | **Gemini 3.5 Flash-Lite** | API | như trên | Rẻ/nhanh hơn `[cần xác minh giá]`; đủ tốt cho chitchat; quota riêng | Không nhận `thinkingConfig.thinkingBudget=0` (HTTP 400 khi thử); latency đo được cao lúc server quá tải (503) | Nhánh Gemini: P50 16,0 s, P95 27,8 s; 747,5 token in / 41,7 token out mỗi lượt; 0/20 vi phạm (`results/gemini_fallback_check.json`) | Model dự phòng + nhánh chitchat |
| 3 | GPT-4o-mini (OpenAI) `[cần xác minh model hiện hành]` | API | OpenAI ToS | Tiếng Việt tốt, tuân lệnh tốt | Không có key trong dự án; thêm nhà cung cấp | CHƯA ĐO (không có key) | Không dùng |
| 4 | Qwen2.5-Instruct (0.5B / 1.5B / 7B) | Open-source | Apache-2.0 (trừ 3B, 72B `[cần xác minh]`) | Đa ngôn ngữ có tiếng Việt; bản nhỏ chạy CPU | Bản 0.5B yếu về grounding/từ chối | Đạt đo 0.5B (c) | Dự phòng local cho chitchat đơn giản (R12) |
| 5 | Llama 3.1-8B / 3.2-1B,3B-Instruct | Open-source | Llama Community License | Hệ sinh thái lớn | Tiếng Việt không phải ngôn ngữ chính thức hỗ trợ `[cần xác minh]`; 8B quá nặng cho CPU | CHƯA ĐO | Không ưu tiên |
| 6 | Vistral-7B-Chat (Viet-Mistral) | Open-source, tiền huấn luyện tiếp tiếng Việt từ Mistral-7B | `[cần xác minh]` | Tiếng Việt rất tự nhiên | 7B: cần GPU; license cần đọc kỹ | CHƯA ĐO | Ứng viên nếu có GPU |
| 7 | SeaLLMs v3 (1.5B / 7B, DAMO) | Open-source, tập trung Đông Nam Á | `[cần xác minh]` | Có tiếng Việt trong dữ liệu chính | Ít tài liệu RAG tiếng Việt | CHƯA ĐO | Ứng viên |
| 8 | Gemma 4 (`gemma-4-26b-a4b-it`, `gemma-4-31b-it` qua Gemini API) | Open-weight, có trên API | Gemma Terms of Use `[cần xác minh]` | Có sẵn qua cùng key | Thử 2 lần (có/không system prompt) đều **HTTP 500** ngày 05/11/2026 | Không gọi được | Không dùng lượt này |

## Khuyến nghị cho Product QA

- Retrieval: **Hybrid RRF (BM25 + multilingual-e5-small)**, lọc theo product_id, K=5. Mã hoá corpus 1 lần, lưu `.npy`.
- LLM: Gemini 3.5 Flash (thinkingBudget=0) → dự phòng Gemini 3.5 Flash-Lite → thông điệp tĩnh (R11/R12). Tên model trong biến môi trường.
- Quota là rủi ro lớn nhất: free tier 20 request/ngày/model, key dùng chung 5 người ⇒ cache bắt buộc, gom lô khi đánh giá, cân nhắc key riêng cho demo.
