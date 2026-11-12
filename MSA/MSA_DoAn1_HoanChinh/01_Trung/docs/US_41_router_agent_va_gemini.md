# US_41 – Router ý định + tool calling + nhánh Gemini (kèm US_42 session memory)

| Mục | Nội dung |
|---|---|
| Mã US | US_41 (Owner: Trung, Support: Hoàng); US_42 stretch (Support: Chiến) |
| Mục tiêu | Một khung chat: ảnh / hỏi đáp / tìm / so sánh được xử lý đúng; chitchat & ngoài phạm vi chuyển Gemini; không chắc thì hỏi lại 1 lần rồi chuyển Gemini |
| Đầu ra | `src/msa/agent/router.py` (Router, Agent, hậu kiểm I18), `session_memory.py`, `gemini_client.py` (REST tối giản), `intent_embed.py` (tuỳ chọn); `eval/eval_router_seed.jsonl` (45 câu), `eval/eval_router_gemini_gen.jsonl` (49 câu); kết quả `results/router_eval_v*.json`, `results/gemini_fallback_live.json`, `results/gemini_store_fact_recheck.json` |
| Tiêu chí nghiệm thu | Route accuracy ≥ 90% trên eval_router (≥ 60 câu, ≥ 15 chitchat/ngoài phạm vi); hỏi lại + chuyển Gemini khi không chắc |
| Trạng thái | **Khung chạy được, đo thật**. Đạt 92,3% trên bộ của Chiến **nhưng sau khi đã xem lỗi**; trên tập độc lập (Gemini sinh, chưa chỉnh theo) **87,8% – chưa đạt 90%**. Chưa nối công cụ thật của Khoa/Chiến/Hoàng |

## 1. Thiết kế
- **Chuẩn hoá**: chữ thường, bỏ dấu, gộp ký tự Unicode lạ, teencode (`ko, k, dc, sz, ss, bn, tks, 500k → 500 nghin`). Danh từ sản phẩm dò trên chữ **có dấu** khi người dùng gõ có dấu (tránh `vậy`→`váy`, `đám`→`đầm`, `mùa mưa`→`mua`).
- **Điểm 5 ý định** (search, qa, compare, gemini_chitchat, gemini_ood) từ cụm từ khoá có trọng số + ngữ cảnh phiên: SP đang xem (`current_product_id`), kết quả vừa tìm (`last_results`), số thứ tự ("đôi thứ 2"). `confidence = b1 / (b1 + b2 + 0.5)`.
- **Luật cứng**: có ảnh → `visual`; có SP đang xem + câu hỏi → `qa`; so sánh 2 nhóm khác nhau → hỏi lại (R19); `confidence < τ_intent = 0.6` → `clarify` **1 lần**, lần sau → Gemini.
- **Agent.handle**: công cụ nội bộ trước (qua `Tools`), Gemini chỉ cho `gemini_*`; QA thiếu dữ kiện giữ "chưa có thông tin" (không gọi Gemini – đã test); Gemini lỗi/429 → câu dự phòng, `source=internal`; câu trả lời Gemini qua **hậu kiểm regex I18** (giá, size, tồn kho, khuyến mãi, chính sách, khẳng định "cửa hàng có nhiều…").
- **Session memory (US_42)**: `resolve_product_ref` ("đôi thứ 2", "cái cuối", "cái vừa tìm"), `resolve_compare_refs` ("so sánh đôi vừa tìm với đôi thứ 2", "3 cái mũ vừa tìm"); `SessionMemory` lưu RAM có TTL. Mới test đơn vị, **chưa đo 10 kịch bản đa lượt**.

## 2. Route accuracy – đo thật (`PYTHONPATH=src python scripts/eval_router.py`)
| Bộ đánh giá | n | Vai trò | Router v0 (luật, đóng băng trước khi xem bộ Chiến) | **Router v1** (hiện tại) | v1 + embedding e5-small |
|---|---|---|---|---|---|
| `eval_router_seed.jsonl` (Trung viết, 13 chitchat/ood) | 45 | **dev** – dùng để viết luật | 1,000 | 1,000 | 1,000 |
| `03_Chien/eval/eval_router.jsonl` (21 chitchat/ood) | 78 | held-out cho v0; **v1 đã chỉnh sau khi xem lỗi** | **0,667** | 0,923 (gộp 2 nhãn gemini: 0,949) | 0,846 |
| `eval_router_gemini_gen.jsonl` (Gemini sinh, 14 chitchat/ood) | 49 | **held-out thật cho v1** (không chỉnh theo) | – | **0,878** | 0,878 |

Số trung thực nhất để báo cáo: **v0 = 0,667 trên bộ Chiến** và **v1 = 0,878 trên bộ Gemini sinh**. Hai bộ held-out đều **chưa có người thật duyệt nhãn** (origin `viet_tay_tac_nhan` / `llm_gemini:gemini-3.5-flash-lite`).

Chi tiết v1 trên bộ held-out Gemini sinh (`results/router_eval_v1.json`):
| Chỉ số | Giá trị |
|---|---|
| Recall theo route | visual 1,00 · qa 1,00 · search 1,00 · compare **0,57** · chitchat 0,86 · ood 0,86 · clarify 0,86 |
| Nhận diện câu cần Gemini (recall / precision) | 0,857 / 0,923 |
| Tỉ lệ chuyển Gemini dự đoán / tỉ lệ hỏi lại | 0,265 / 0,204 |
| Câu trong miền bị đẩy nhầm sang Gemini | 0 |
| Latency router p50 / p95 | 0,054 / 0,106 ms |

Lỗi còn lại (top) và nguyên nhân:
1. `so sanh giup tui chan vay nay vs cai vua xem` → clarify: "tui" (teencode = tôi) bị hiểu là **túi** → nhầm so sánh khác nhóm. Sửa: bỏ "tui" khỏi từ khoá túi khi đứng sau động từ.
2. `Nên mua áo khoác phao hay áo dạ hơn shop?` → clarify; `Phân vân giữa mũ bucket với mũ lưỡi trai` → search: thiếu mẫu "phân vân giữa", "X hay Y hơn" có 2 danh từ.
3. `Shop ơi mình ngủ đây, mai tư vấn tiếp nhé`, `Tư vấn … vòng cổ bạc hợp mệnh gì` → clarify (đáng lẽ Gemini).
4. Bộ của Chiến: 3 lỗi do **mâu thuẫn phạm vi** (tất, khuyên tai, dây chuyền – taxonomy v1 coi là ngoài phạm vi), 3 lỗi chitchat↔ood (đều sang Gemini, không ảnh hưởng hành vi).
→ Đề xuất Router v2 sửa 1–3 rồi **đo lại trên bộ mới do người thật viết** (≥ 60 câu, 2 người duyệt).

Ablation embedding (prototype k-NN, `intfloat/multilingual-e5-small`, prototype = seed của Trung): **không cải thiện** (0,846 < 0,923 trên bộ Chiến; bằng nhau trên bộ Gemini) → mặc định **tắt**.

## 3. Nhánh Gemini end-to-end – đo THẬT (`scripts/run_gemini_live.py`, 2026-11-05)
Cấu hình: router v1 → Agent → Gemini REST → hậu kiểm; system prompt `trung-v1`; `maxOutputTokens=512`, `temperature=0.4`.
**Model: `gemini-3.5-flash-lite`** – vì `gemini-3.5-flash` trả **429: free tier 20 request/ngày/model** (đã hết trong ngày do 5 thành viên dùng chung key; Hoàng cũng ghi nhận 5 RPM). `flash-lite` **không chấp nhận `thinkingBudget=0`** (HTTP 400 "invalid argument"), nên so sánh "mặc định (không suy nghĩ)" với "thinkingBudget=1024".

| Chỉ số | A: mặc định | B: thinkingBudget=1024 |
|---|---|---|
| Số lời gọi thành công / lỗi | 40 / 0 | 10 / 0 |
| Latency e2e p50 / p95 (ms) | **14.364 / 41.068** | 21.178 / 70.393 |
| Token vào / ra / thinking (TB mỗi lời gọi) | 165,1 / 55,5 / 0 | 164,7 / 37,3 / **350,3** |
| Token tổng TB mỗi lời gọi | 220,6 | 552,3 (×2,5) |
| finishReason | STOP 40 | STOP 7, **MAX_TOKENS 2, MALFORMED_RESPONSE 1** |
| Câu nêu giá/size/tồn kho/khuyến mãi | 0/40 | 0/10 |
| Câu khẳng định cửa hàng **có bán hàng ngoài danh mục** (kiểm tay) | **2/40** (đồng hồ Casio, khuyên tai) | 0/10 |
| Hậu kiểm regex v1 bắt được | 1 (bắt **nhầm** `$x=3$` ở câu toán) – bỏ sót 2 ca thật | 0 |
| Hậu kiểm regex v2 (sửa sau khi xem, nên **chưa phải số held-out**) | 2/40 (đúng 2 ca thật) | 0/10 |
| Cache (10 câu lặp lại) | 10/10 trúng, p50 0,3 ms, 0 lời gọi API | |

**Cảnh báo về latency**: 62 lời gọi HTTP cho 50 câu → 12 lần retry do 429 (5 RPM dùng chung với các thành viên khác chạy song song) và có `sleep` backoff → p50/p95 trên **gồm thời gian chờ quota**, KHÔNG phải độ trễ thuần của model. Từ nay client ghi `attempts` và `latency_ms_last_attempt` để tách. Mục tiêu "Gemini P95 ≤ 4 s" **hiện chưa đạt** trong điều kiện free tier dùng chung.

**Tỉ lệ chuyển Gemini & token/100 lượt** (trên 172 câu của 3 bộ eval, router v1):
| | Giá trị |
|---|---|
| Fallback rate (chuyển Gemini) | **0,273** (47/172) – vượt nhẹ mục tiêu ≤ 0,25 |
| Token / 100 lượt – cấu hình A | **≈ 6.028** (= 0,273 × 100 × 220,6) |
| Token / 100 lượt – cấu hình B | ≈ 15.092 |
| Chi phí / 100 lượt | `tokens_in × giá_in + (tokens_out + thinking) × giá_out` – đơn giá **[cần xác minh – điền theo bảng giá Google hiện hành]**; free tier = 0 đồng nhưng bị giới hạn 20 request/ngày/model |
Lưu ý: tỉ lệ này đo trên bộ eval (cân bằng nhãn), không phải lưu lượng thật; chưa trừ cache.

Quan sát định tính (40 câu A): Gemini luôn kéo về mua sắm; trả lời được câu ngoài phạm vi vô hại (code Python, phương trình, thủ đô Úc, nấu phở) – cần nhóm quyết định có cho phép không; từ chối "hack facebook". Nguy cơ chính là **tự nhận cửa hàng có bán** mặt hàng ngoài danh mục → đã thêm mẫu `danh_muc` vào hậu kiểm và đề xuất bổ sung vào system prompt (I16): "cửa hàng KHÔNG bán đồng hồ, trang sức, tất, ví…".

## 4. Việc còn lại
1. Router v2 (sửa lỗi §2) + đo trên eval_router do người thật viết/duyệt; hiệu chỉnh τ_intent (I17).
2. Nối `Tools` với VisualSearcher (Khoa), RAGPipeline (Chiến), search/compare + LLMGateway (Hoàng); dùng prompt `prompts/gemini_fallback.md` của Chiến thay `trung-v1`.
3. Đo lại nhánh Gemini trên `gemini-3.5-flash` khi có quota (hoặc key trả phí), tách latency thuần.
4. US_42: viết và chạy 10 kịch bản đa lượt (mục tiêu 9/10).
