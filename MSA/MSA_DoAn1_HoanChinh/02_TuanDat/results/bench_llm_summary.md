# Tổng hợp benchmark LLM (sinh tự động – results/bench_llm_summary.json)

## Bảng D – LLM trả lời trên 36 câu hỏi từ review ViMRHP

| Tag | Model | n | Faithfulness | Hallucination | Correctness | Từ chối đúng (7 câu không đáp án) | Latency p50/p95 (s) | Token in/100 | Token out+thinking/100 |
|---|---|---|---|---|---|---|---|---|---|
| gemini35flashlite | gemini-3.5-flash-lite | 36 | 0.939 | 0.111 | 0.903 | 1.0 | 14.5/33.0 | 60619 | 3631 |
| gemma4_26b_api | gemma-4-26b-a4b-it | 32 | 0.992 | 0.031 | 0.984 | 1.0 | 13.8/21.1 | 62075 | 63112 |
| qwen25_05b | Qwen/Qwen2.5-0.5B-Instruct | 18 | 0.255 | 0.333 | 0.139 | 0.333 | 39.5/186.2 | 68994 | 2417 |

## Bảng D2 – Gemini vai trò Router/Fallback (eval_router)

| Tag | n | Route accuracy | Latency p50/p95 (s) | Số reply chitchat/ood | Reply bị cờ dữ kiện cửa hàng | Token in/100 | Token out+thinking/100 |
|---|---|---|---|---|---|---|---|
| gemini35flashlite | 14 | 0.857 | 0.7/0.9 | 4 | 0 | 31579 | 3271 |

Tổng lời gọi Gemini đã dùng (kể cả retry): 250
