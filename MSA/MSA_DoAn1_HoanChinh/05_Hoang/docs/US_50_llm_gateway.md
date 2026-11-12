# US_50 – LLM Gateway cho Gemini (cấu hình model, timeout, retry, cache)

| Mục | Nội dung |
|---|---|
| Mã US | US_50 (3 pt, Sprint 2) – Owner: Hoàng, Support: Tuấn Đạt |
| Mục tiêu | Một module gọi Gemini dùng chung cho fallback/chitchat/benchmark; demo không sập khi API lỗi |
| Đầu ra | `src/msa/llm_gateway.py`, `repo_skeleton/.env.example`, `src/scripts/llm_gateway_live.py`, `tests/test_llm_gateway.py`, `results/llm_gateway_live.json`, `results/llm_gemini35_thinking_probe.json`, `results/llm_gateway_live_gemini35_quota429.json` |
| Tiêu chí nghiệm thu | Gọi thành công 10 request mẫu; giả lập 429/timeout → thông điệp dự phòng, không crash; key không nằm trong repo; đổi model chỉ bằng biến môi trường |
| Trạng thái | **Hoàn thành** – 10/10 request thật thành công (`gemini-3.5-flash-lite`, đổi model chỉ bằng `GEMINI_MODEL`); 429 thật và giả lập đều trả dự phòng; 16 test pass (+1 test live) |

## Tóm tắt 5 dòng
1. Module gọi Gemini dùng chung: đọc key/model từ biến môi trường, timeout, retry/backoff khi 429, cache exact-match SQLite, log token/latency.
2. 10/10 request thật thành công (`gemini-3.5-flash-lite`); lặp lại 10 câu: 10/10 trúng cache, 0 lời gọi API.
3. 429 thật (free tier 5 request/phút, 20 request/ngày/model) → trả thông điệp dự phòng, không crash, `source="fallback"` (QUYET_DINH mục D).
4. Token: 10.460 vào + 6.370 ra / **100 lời gọi** (prompt ngắn) ≈ 4.599 token / 100 lượt hội thoại (mục F).
5. Đơn giá `[cần xác minh]`; key không có trong repo.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## 1. Giao diện

```python
from msa.llm_gateway import LLMGateway
gw = LLMGateway()                       # đọc GEMINI_API_KEY, GEMINI_MODEL (mặc định gemini-3.5-flash), MSA_LLM_MOCK…
r = gw.generate("Chào bạn", system="persona…", thinking_budget=0, temperature=0.3)
# r = {answer, source: gemini|cache|fallback, origin, cached, tokens_in, tokens_out, tokens_thinking,
#      latency_ms (đầu-cuối), api_latency_ms (riêng HTTP), wait_ms (chờ limiter/backoff), error, retries,
#      model, model_version, finish_reason, mock}
gw.stats.as_dict()                      # requests, api_calls, cache_hits, errors, fallbacks, retries, tokens…, cache_hit_rate
LLMGateway.cost_usd(tin, tout, tthink)  # quy ra tiền từ GEMINI_PRICE_*_PER_1M  [cần xác minh – điền theo bảng giá Google hiện hành]
```

| Tính năng | Cách làm |
|---|---|
| Gọi API | REST `v1beta/models/{model}:generateContent` qua httpx; key ở header `x-goog-api-key` (không bao giờ trong URL) |
| Timeout | `GEMINI_TIMEOUT` (mặc định 30 s) |
| Retry | exponential backoff + jitter cho 429/500/502/503/504/timeout/lỗi mạng, tối đa `GEMINI_MAX_RETRIES`; đọc `RetryInfo.retryDelay` trong body lỗi (Gemini không gửi header Retry-After); **429 quota NGÀY → không retry** (phát hiện qua `quotaId …PerDay…`) |
| Rate limiter | token-bucket `GEMINI_RPM` (mặc định 4 vì free tier đo được 5 RPM) |
| Cache | exact-match SQLite, khoá = sha256(model, system, prompt, generationConfig); chỉ lưu câu thành công; hook `SemanticCache` (embed_fn + ngưỡng cosine) cho chitchat |
| Thinking | `thinking_budget` → `thinkingConfig.thinkingBudget`; `thinking_level` → `thinkingConfig.thinkingLevel` |
| An toàn | chỉ gửi text (tham số `image/inline_data…` → `ValueError`); log JSONL chỉ có hash prompt, token, latency; mọi chuỗi lỗi qua `_redact` |
| Dự phòng | lỗi cuối cùng → `source="fallback"` + thông điệp tiếng Việt, không raise |
| Mock | `MSA_LLM_MOCK=1` → câu `[MOCK] …`, không gọi mạng |

> Đề xuất bổ sung hợp đồng 5.2: thêm giá trị `source="fallback"` (thông điệp dự phòng khi Gemini lỗi) để UI không gắn nhầm nhãn "Trả lời bởi Gemini". Cache trả `source="cache"`, `origin="gemini"` → UI vẫn hiện nhãn Gemini. **Cần Trung/Tuấn Đạt xác nhận.**

## 2. Kết quả đo THẬT

### 2.1 10 request mẫu (`results/llm_gateway_live.json`, 05/11/2026 00:03)
Model **`gemini-3.5-flash-lite`** (đặt bằng `GEMINI_MODEL`, không sửa code) vì quota ngày của `gemini-3.5-flash` đã hết (xem 2.3). System prompt persona + guardrail (trong file kết quả). 10 câu do tác nhân viết (`origin=agent_written`): 3 chitchat, 3 ngoài phạm vi, 3 câu khó, 1 câu hỏi giá/size (guardrail).

| Chỉ số | Lượt 1 (cache rỗng) | Lượt 2 (lặp lại, trúng cache) |
|---|---:|---:|
| Thành công | **10/10** | 10/10 |
| Lời gọi API thật | 11 (1 lần retry sau 429) | **0** |
| Latency HTTP p50 / p95 (ms) | **14.464 / 20.078** | – |
| Latency đầu-cuối p50 / p95 (ms) | 14.872 / 35.022 (gồm retry) | **17,9 / 28,5** |
| Token TB / request: vào – ra – thinking | 104,6 – 63,7 – 0 | 0 token phải trả |
| **Token / 100 lượt** (không cache) | vào 10.460, ra 6.370, thinking 0 | 0 |

Nhận xét: cả 10 câu tuân thủ guardrail (p10 từ chối nêu giá/size và mời dùng tìm kiếm; p05, p06 từ chối ngoài phạm vi). Câu p04 (thủ đô Úc) vẫn được trả lời – cần prompt của Chiến quyết định có cho trả lời kiến thức chung hay không. Latency ~14 s/lượt là đo thật nhưng **bất thường cao** (lúc đo nhiều tác nhân cùng gọi chung 1 project; cùng thời điểm `gemini-3.5-flash` budget 0 mất 5,3–6,3 s) → cần đo lại trên máy nhóm.

### 2.2 So sánh cấu hình thinking – `gemini-3.5-flash` (`results/llm_gemini35_thinking_probe.json`, 1 câu chào, 1 lần/cấu hình)

| Cấu hình | Token vào | Token ra | Token thinking | Latency (ms) |
|---|---:|---:|---:|---:|
| Mặc định (không đặt thinkingConfig) | 29 | 25 | **458** | 4.506 |
| `thinkingBudget=0` | 29 | 20 | **0** | **1.845** |
| `thinkingLevel=low` | 29 | 24 | 323 | 3.363 |
| `thinkingLevel=minimal` | – | – | – | 429 (hết quota, chưa đo) |

→ Đề xuất mặc định `GEMINI_THINKING_BUDGET=0` cho chitchat/fallback (giảm ≈ 96% token đầu ra tính tiền (483 → 20), latency ≈ −59% trên mẫu này). Mỗi cấu hình mới có **n = 1** → chỉ là chỉ báo; cần chạy lại 10 câu × 3 cấu hình khi có quota (`python src/scripts/llm_gateway_live.py --configs default,budget0,level_low`).

### 2.3 Hành vi khi gặp 429 thật (`results/llm_gateway_live_gemini35_quota429.json`)
- Phản hồi 429 cho biết hạn mức free tier: **5 request/phút/project/model** và **20 request/ngày/project/model** (`quotaId GenerateRequestsPerMinute…`, `…PerDay…`). Key dùng chung cho 5 thành viên → 20 request/ngày là nút thắt nghiêm trọng.
- Lượt chạy 10 câu `gemini-3.5-flash` budget 0 lúc 06:5x: 2/10 thành công (5,3 s và 6,3 s HTTP), 8/10 nhận 429 quota ngày → gateway trả thông điệp dự phòng ngay (không retry vô ích), **không crash**; lần lặp lại: 2 câu trúng cache.
- `quotaDimensions.model` trong lỗi ghi `gemini-3.6-flash` cho yêu cầu tới `gemini-3.5-flash` → có thể là alias `[cần xác minh]`.

### 2.4 Chi phí
Đơn giá chưa tra được chắc chắn → `GEMINI_PRICE_IN_PER_1M`, `GEMINI_PRICE_OUT_PER_1M` để trống, nhãn `[cần xác minh – điền theo bảng giá Google hiện hành]`.
Công thức: **chi phí/100 lượt = (10.460 × P_in + (6.370 + thinking) × P_out) / 10⁶** (số token đo với flash-lite). Với tỉ lệ cache hit h: nhân thêm (1 − h).

## 3. Test (mock, không tốn quota) – `tests/test_llm_gateway.py`
10 request mock; parse token & bỏ phần `thought`; 429 → retry rồi thành công (tôn trọng retryDelay); 429 hết lượt → fallback; 429 quota ngày → không retry; timeout & 503; 400 không retry; cache hit/miss theo tham số; key không xuất hiện trong kết quả/log/repr; đổi model bằng env; thiếu key → fallback; cấm ảnh; câu trả lời rỗng (SAFETY) → fallback; token bucket; semantic cache; công thức chi phí; nạp `.env`. Test live: `MSA_ENV_FILE=<.env> python -m pytest -m live`.

## 4. Việc còn lại
- Xin key riêng/billing hoặc mỗi thành viên một project để vượt 20 request/ngày; đo lại 10 câu × 3 cấu hình thinking với `gemini-3.5-flash`.
- Điền đơn giá và tính chi phí/100 lượt; đo tỉ lệ chuyển Gemini thật khi Router (Trung) chạy trên eval_router.
- Bọc hàm gọi Gemini của Tuấn Đạt (`bench_llm.py`) và nhánh fallback của Chiến qua gateway này.
