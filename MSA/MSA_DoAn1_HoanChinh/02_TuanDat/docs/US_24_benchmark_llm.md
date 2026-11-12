# US_24 – Benchmark LLM trả lời (API + open-source) và Gemini vai trò Router/Fallback

| Mục | Nội dung |
|---|---|
| Mã US | US_24 (Owner: Tuấn Đạt, Support: Chiến) – Sprint 2, 5.0 pt |
| Mục tiêu | Cùng prompt + cùng ngữ cảnh + temperature cố định trên nhiều LLM; đo faithfulness, hallucination, từ chối, latency, token/chi phí per 100 câu; Gemini đo thêm vai trò Router/Fallback |
| Đầu ra | `src/scripts/bench_llm.py`, `src/scripts/bench_common_subset.py`, `src/msa_td/gemini_client.py` (để Hoàng tái dùng trong LLMGateway), `eval/bench_qa.jsonl` (36 câu), log `results/bench_llm_*.jsonl`, tổng hợp `results/bench_llm_summary.json/.md`, `results/bench_llm_common_subset.json` → Sheet 3 Bảng D + D2 |
| Tiêu chí nghiệm thu | Cùng prompt, cùng context, temperature cố định; có log câu trả lời; Gemini có số liệu cho cả 2 vai trò |
| Trạng thái | **Hoàn thành một phần với số đo thật**: 3 model đã đo (Gemini 3.5 Flash-Lite, Gemma 4 26B-A4B qua API, Qwen2.5-0.5B CPU). `gemini-3.5-flash` **CHƯA ĐO** (hết quota ngày). Router đo trên 14/78 câu. Điểm judge do LLM chấm, **chưa có người chấm** |

## Tóm tắt 5 dòng
1. So 3 LLM trên cùng 36 câu hỏi, cùng prompt, cùng ngữ cảnh review, temperature cố định: Gemini 3.5 Flash-Lite, Gemma 4 26B (API), Qwen2.5-0.5B (CPU).
2. Gemma 4 26B tốt nhất (faithfulness 0,992, hallucination 0,031) nhưng tốn token ra gấp ~17 lần vì thinking; Flash-Lite đủ tốt (0,939 / 0,111) và rẻ nhất.
3. Qwen 0,5B không dùng được cho tiếng Việt (faithfulness 0,255).
4. Gemini làm router: 0,857 trên 14 câu (chưa đủ 78 câu); `gemini-3.5-flash` CHƯA ĐO do hết quota free tier.
5. Loại số liệu: [LLM chấm] (giám khảo `gemini-2.5-flash`), bộ câu [Chưa người duyệt]; latency API gồm chờ quota.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## 1. Thiết lập (giống nhau cho mọi model)
- **Dữ liệu:** 36 câu hỏi tiếng Việt viết tay từ review THẬT ViMRHP (`eval/build_bench_qa.py`, `origin=tac_nhan_AI_viet_tay_tu_review_that`, chưa người duyệt), 36 SP (giày 14, quần áo 14, phụ kiện/mũ 8), **7 câu (19,4%) không có đáp án** trong ngữ cảnh. Ngữ cảnh = 6 review/SP (≤ 260 ký tự/review, `eval/bench_contexts.jsonl`, seed 42) – giữ nguyên nhiễu thật (review spam quảng cáo lẫn vào).
- **Prompt:** `SYSTEM_QA` trong `bench_llm.py` – chỉ dùng review, ghi nguồn `[R#]`, thiếu thông tin thì nói đúng câu từ chối, không bịa giá/size/tồn kho, ≤ 3 câu.
- **Giải mã:** temperature 0 (API) / greedy `do_sample=False` (local); max 200–300 token trả lời.
- **Chấm:** LLM-judge `gemini-2.5-flash` (không phải ứng viên), ẩn danh + xáo thứ tự câu trả lời, gộp 4–8 câu/lời gọi; chấm faithfulness (0–1), hallucination (có/không), correctness (0/0,5/1 so với đáp án tham chiếu), refused. Kèm heuristic không tốn API: tỉ lệ token câu trả lời có trong ngữ cảnh, tỉ lệ có trích `[R#]`, regex từ chối.
- **Phần cứng:** máy chung 2 CPU / 7 GB RAM, nhiều tác nhân chạy song song → latency có nhiễu lớn (xem mục 4).

Lệnh tái lập (key qua `MSA_ENV_FILE`, không in ra):
```bash
python eval/build_bench_qa.py
python src/scripts/bench_llm.py qa --model gemini:gemini-3.5-flash-lite --tag gemini35flashlite --max-tokens 300
python src/scripts/bench_llm.py qa --model gemini:gemma-4-26b-a4b-it --tag gemma4_26b_api --limit 32 --max-tokens 300
python src/scripts/bench_llm.py qa --model hf:Qwen/Qwen2.5-0.5B-Instruct --tag qwen25_05b --limit 18     # bf16, CPU
python src/scripts/bench_llm.py judge --tags gemini35flashlite,gemma4_26b_api,qwen25_05b --judge-model gemini-2.5-flash
python src/scripts/bench_llm.py router --tag gemini35flashlite --gemini-model gemini-3.5-flash-lite --per-route 2
python src/scripts/bench_llm.py summary && python src/scripts/bench_common_subset.py
# máy có GPU: OPENAI_BASE_URL=http://localhost:11434/v1 python src/scripts/bench_llm.py qa --model openai:qwen2.5:7b-instruct --tag ollama_qwen7b
```

## 2. Bảng D – kết quả THẬT (`results/bench_llm_summary.json`)

| Mô hình | Hình thức | n câu | Faithfulness (0–1) | Hallucination rate | Correctness | Từ chối đúng câu không đáp án | Latency p50 / p95 (s) | Token vào / 100 câu | Token ra (+thinking) / 100 câu | Chi phí / 100 câu |
|---|---|---|---|---|---|---|---|---|---|---|
| Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) | API | 36 | **0,939** | 0,111 (4/36) | 0,903 | 7/7 | 14,5 / 33,0 | 60.619 | 3.631 (thinking 0) | công thức mục 5 |
| Gemma 4 26B-A4B IT (`gemma-4-26b-a4b-it`, open-weight, gọi qua Gemini API) | API (model mở) | 32 | **0,992** | 0,031 (1/32) | 0,984 | 6/6 | 13,8 / 21,1 | 62.075 | 63.112 (≈ 600 token thinking/câu) | công thức mục 5 |
| Qwen2.5-0.5B-Instruct | Local CPU (bf16, 2 luồng) | 18 | 0,255 | 0,333 | 0,139 | 1/3 | 39,5 / 186,2 | 68.994 | 2.417 | 0 (điện + máy) |
| Gemini 3.5 Flash (`gemini-3.5-flash`) | API | 0 | **CHƯA ĐO** | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO | – | – | – |
| Qwen 7B / Llama 8B / Vistral | Local GPU | 0 | **CHƯA ĐO** (máy 2 CPU không chạy nổi; dùng adapter `openai:` trên máy GPU) | | | | | | | |

**So sánh công bằng trên 18 câu chung q001–q018** (`results/bench_llm_common_subset.json`): Flash-Lite faithfulness 0,925 / hallucination 0,111 / correctness 0,889;
Gemma 4 26B 0,986 / 0,056 / 0,972; Qwen 0,5B 0,255 / 0,333 / 0,139. Câu không đáp án trong 18 câu: Flash-Lite 3/3, Gemma 3/3, Qwen 1/3.

Heuristic (không phụ thuộc judge): tỉ lệ câu trả lời có trích `[R#]` – Flash-Lite 0,806, Gemma 0,812, Qwen 0,444; từ chối nhầm câu có đáp án – Flash-Lite 1/29, Gemma 0/26.

Phân tích lỗi (đọc ghi chú judge + câu trả lời):
- Flash-Lite 4 câu bị gắn hallucination: q006 thêm ý mâu thuẫn từ R1; q007 lấy chất liệu từ R3 – **R3 là review spam mô tả giày sneaker khác** (nhiễu thật của ViMRHP); q023, q026 gán nhầm mã review. → lỗi chủ yếu là *trích dẫn sai*, không phải bịa giá/size.
- Gemma 1 câu (q007, cùng review spam). → **Cần lọc spam trước khi đưa review vào RAG** (regex của US_36 đã lọc 262 review).
- Qwen 0,5B: thường chỉ trả `[R1]` hoặc lặp số liệu, không theo được định dạng; không dùng được cho QA tiếng Việt.

## 3. Bảng D2 – Gemini vai trò Router/Fallback (`results/bench_llm_router_gemini35flashlite.jsonl`)

eval_router = bản chụp `eval/eval_router_snapshot_from_Chien.jsonl` (78 câu do tác nhân Chiến viết, sha256 b6cf9600…). Do quota, chỉ chạy **mẫu phân tầng 2 câu/route = 14 câu** (seed 42).

| Chỉ số | Cách đo | Mục tiêu sheet | Kết quả THẬT |
|---|---|---|---|
| Route accuracy (zero-shot, `gemini-3.5-flash-lite`) | 14 câu phân tầng, JSON `{route, confidence, reply}` | ≥ 0,90 | **0,857 (12/14)** – sai: 1 chitchat → ood ("trời mưa mặc gì"), 1 clarify → qa ("cái này còn không") |
| Chất lượng chitchat/ngoài phạm vi | Người chấm 1–5, n = 30 | ≥ 4,0 | **CHƯA ĐO** (chưa có người chấm; 4 câu trả lời đã log để chấm) |
| Phản hồi bịa dữ kiện cửa hàng | Regex giá/size/tồn kho/khuyến mãi trên reply | 0/60 | **0/4** reply bị cờ (1 reply gợi ý "áo khoác trượt nước, giày chống thấm" – không nêu SP/giá cụ thể) |
| Latency P95 một lời gọi | 14 lời gọi | ≤ 4 s | **p50 0,7 s / p95 0,9 s** |
| Token / 100 lượt router | `usageMetadata` | ghi nhận | vào 31.579 / ra 3.271 (thinking 0) |
| Fallback rate | % câu dự đoán gemini_* | 10–25% | 28,6% trên mẫu phân tầng – **không đại diện traffic thật**; đo lại trên log demo |
| Toàn bộ 78 câu, `gemini-3.5-flash` | | | **CHƯA ĐO** (hết quota) |

## 4. Phát hiện quan trọng (đo thật)
1. **Quota free tier = 20 request/ngày/project/model.** Lỗi 429 `RESOURCE_EXHAUSTED`, `quotaId=GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `quotaValue=20` (`results/failed/bench_llm_qa_gemini35flash_t0_ALL_429.jsonl`). Key dùng chung 5 thành viên → `gemini-3.5-flash` hết quota trước khi benchmark. Bản client đầu retry 3 lần/câu nên **đốt 144 lời gọi 429** trong ngân sách 250 – đã sửa: chỉ thử lại 429 một lần khi server cho `retryDelay ≤ 60 s`, **ngắt mạch sau 3 lần 429 liên tiếp**, dừng benchmark sau 3 lỗi liên tiếp (có test). Hệ quả cho thiết kế: demo/bảo vệ cần cache + câu dự phòng tĩnh, hoặc key trả phí.
2. `gemini-3.5-flash-lite` **không nhận `thinkingConfig.thinkingBudget=0`** (HTTP 400 "invalid argument"); bỏ tham số thì thinking token = 0. `modelVersion` trả về của `gemini-3.5-flash` là `gemini-3.6-flash` (alias) – ghi lại để truy vết.
3. Gemma 4 qua API: không nhận `systemInstruction` (client tự ghép vào prompt) và vẫn tiêu ≈ 600 token thinking/câu → token ra/100 câu gấp ~17 lần Flash-Lite.
4. Latency phụ thuộc tải dùng chung: cùng Flash-Lite, lượt QA ban đêm p50 14,5 s, lượt router sau đó p50 0,7 s (prompt ngắn hơn ~2 lần và ít tác nhân chạy song song). Cần đo lại trên máy demo, ≥ 3 lần, lấy median/P95.
5. Qwen2.5-0.5B fp32 bị OOM-kill 2 lần (cgroup 7 GB dùng chung, `dmesg`) → chạy bf16; p50 39,5 s/câu trên CPU dùng chung.

## 5. Chi phí / 100 câu
Đơn giá USD/1M token **[cần xác minh – điền theo bảng giá Google hiện hành]** để trống trong `PRICE_PER_1M` (bench_llm.py); khi điền, `summary` tự tính:
`USD/100 = (token_vào × giá_vào + (token_ra + token_thinking) × giá_ra) / 1e6`.
Ví dụ dạng công thức với số đo thật của Flash-Lite: `(60.619 × giá_vào + 3.631 × giá_ra) / 1e6`. Ở free tier: chi phí 0 đ nhưng chỉ 20 request/ngày/model.

## 6. Kết luận đề xuất (để điền cột KẾT LUẬN của Bảng D)
- **RAG trả lời:** Gemma 4 26B (qua API) chất lượng cao nhất trên bộ này nhưng token ra lớn do thinking; Gemini 3.5 Flash-Lite đủ tốt (faithfulness 0,94, từ chối đúng 7/7), rẻ token nhất → **đề xuất Flash-Lite làm mặc định, Gemma 4 làm phương án 2**; kết luận cần xác nhận lại khi người thật chấm 36 câu và có số đo `gemini-3.5-flash`.
- **Router:** Flash-Lite zero-shot 0,857 trên 14 câu, nhanh (< 1 s) → dùng làm tầng 2 sau router nội bộ của Trung; chưa đủ dữ liệu để thay router nội bộ.
- **Open-source chạy local:** 0,5B không dùng được; cần ≥ 7B trên GPU (adapter đã sẵn).

## 7. Việc còn lại
1. Người thật chấm lại 36 câu (cột faithfulness/hallucination) để kiểm judge; duyệt câu hỏi `eval/bench_qa.jsonl`.
2. Ngày có quota: chạy `gemini-3.5-flash` (36 câu, thinking mặc định và tắt) + router đủ 78 câu; Gemma 4 thêm q033–q036; Qwen 0,5B thêm q019–q036 khi máy rảnh.
3. Điền đơn giá đã xác minh → chi phí/100 câu bằng tiền.
