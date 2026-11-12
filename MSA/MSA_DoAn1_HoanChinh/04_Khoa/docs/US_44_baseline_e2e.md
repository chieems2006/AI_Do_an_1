# US_44 – Đo baseline hệ thống end-to-end

| Mục | Nội dung |
|---|---|
| Mã US | US_44 (Owner: Khoa, Support: Chiến) – Sprint 3, 3.0 pt |
| Mục tiêu | Biết cải tiến nào đáng làm nhất: TSR, latency, top-10 lỗi, bảng route (tỉ lệ chuyển Gemini, chi phí/100 lượt) |
| Đầu ra | `src/scripts/baseline_e2e.py`, `eval/e2e_scenarios.jsonl` (60 kịch bản), `results/e2e_*.json`, `results/e2e_*_per_case.csv`, file này |
| Tiêu chí nghiệm thu | Bảng số liệu baseline + top-10 lỗi + bảng route (tỉ lệ Gemini, chi phí/100 lượt) |
| Trạng thái | **Đã đo trên hệ thống ghép (12/11/2026)**: TSR, latency, tỉ lệ chuyển Gemini, token/100 lượt (mục 3b, `results/e2e_http.json`). Còn thiếu: chi phí/100 lượt (chưa có đơn giá đã xác minh), 2 người chấm lại các ca qa/compare/chitchat. Phần visual-only cũ giữ ở mục 3. |

## 1. 60 kịch bản (`eval/e2e_scenarios.jsonl`, sinh tất định từ `build_scenarios()`)

| Route mong đợi | Số | Tiêu chí thành công tự động |
|---|---|---|
| visual | 18 (12 instance + 4 category + 2 bổ sung, lấy từ split **test** của eval_visual) | instance: SP đúng trong top-5; category: top-1 cùng product_type |
| search | 10 | route đúng + top-1 đúng product_type |
| qa | 10 | route đúng + có `citations` hoặc trả "chưa có thông tin" |
| compare | 6 | route đúng + đủ 2–3 SP |
| gemini_chitchat | 6 | `source ∈ {gemini, cache}` |
| gemini_ood | 6 | `source ∈ {gemini, cache}` + **không nêu dữ kiện cửa hàng** (giá/size/tồn kho – regex) |
| clarify | 4 | route = clarify |
| **Tổng** | **60** (12 chitchat/ngoài phạm vi ≥ 10 ✔) | |

Các tiêu chí qa/compare/chitchat là **tự động thô**; trước khi báo cáo, 2 người chấm lại các ca này (thang đúng/sai) – chưa có người chấm thật ở lượt này.

## 2. Cách chạy

```bash
# Kiểm thử khung (agent giả theo luật – số KHÔNG dùng cho báo cáo)
python src/scripts/baseline_e2e.py --agent fake
# Phần visual THẬT (index đã build ở US_29)
python src/scripts/baseline_e2e.py --agent visual-only --index-dir indexes/best
# Khi hệ thống đã ghép (API của Hoàng)
GEMINI_PRICE_IN_PER_M=<đơn giá> GEMINI_PRICE_OUT_PER_M=<đơn giá> python src/scripts/baseline_e2e.py --agent http --base-url http://localhost:8000
# Chạy nhiều đợt để không vượt quota free tier (~20 request/ngày/model): ghi từng kịch bản vào results/e2e_http_cases.jsonl,
# dừng đợt khi đủ ngân sách hoặc gặp 429 (kịch bản dính 429 không ghi), chạy lại cùng lệnh để tiếp; đủ 60 thì ghi e2e_http.json
python src/scripts/baseline_e2e.py --agent http --base-url http://127.0.0.1:8000 --resume --max-gemini-calls 11 --pace-s 15     --llm-log ../runtime/logs/llm_calls.jsonl --config-note "<mô tả cấu hình>"
# hoặc gọi trực tiếp Agent của Trung
python src/scripts/baseline_e2e.py --agent python --agent-cls msa.agent.router:Agent
```
Chi phí/100 lượt = (Σtokens_in × giá_in + Σtokens_out × giá_out) / 10⁶ × 100 / n. Đơn giá **[cần xác minh – điền theo bảng giá Google hiện hành]**; token lấy từ `usageMetadata` mà `LLMGateway` trả về (kể cả token thinking nếu gateway cộng vào `tokens_out`).

## 3. Kết quả

<!-- E2E_RESULTS -->
Chạy THẬT `--agent visual-only` (index `indexes/best` → FashionCLIP, τ_v và gate như `config.json`), 18 kịch bản visual:

| Chỉ số | Giá trị |
|---|---|
| TSR phần visual | **0.833** (15/18) |
| Latency p50 / p95 (ms, gồm đọc ảnh + embed + gate + search) | 282.29 / 1118.05 |
| Lỗi | visual_no_match: 3 |
| 42 kịch bản text | route `not_ready` (chưa ghép) → TSR toàn hệ thống trong file = 0.25 **không có ý nghĩa**, CHƯA ĐO |

Khung đo đã kiểm thử bằng `--agent fake` (`results/e2e_fake.json`, chỉ để test, không phải số liệu).
<!-- /E2E_RESULTS -->

### 3b. Hệ thống đã ghép – `--agent http` (đo 12/11/2026, 22:52–22:58)

 – `04_Khoa/results/e2e_http.json`, từng kịch bản ở `e2e_http_cases.jsonl` / `e2e_http_per_case.csv`, log Gemini của lượt đo ở `e2e_http_llm_calls.jsonl`. Đủ 60 kịch bản của `eval/e2e_scenarios.jsonl`, gọi API thật qua HTTP (`baseline_e2e.py --agent http --resume --max-gemini-calls 11 --pace-s 15`, 2 đợt trong cùng ngày để không vượt quota free tier).
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
- **Cách hiểu đúng:** TSR qa/compare = 0 chủ yếu do kịch bản một lượt nói "đôi giày này", "2 cái này" mà không có SP nào trong ngữ cảnh. Với compare, hỏi lại (clarify) là hành vi hợp lý. Đây chưa phải số đo năng lực RAG/so sánh (RAG đo riêng ở `03_Chien/results/rag_e2e_eval.json`). Lỗi thật của router: 2 câu hỏi về SP bị đưa sang Gemini và 5 câu bị đưa sang search. Cần bộ kịch bản v1.1 có `product_id`/phiên (không sửa file gốc).
- **Gemini [Tác nhân kiểm]:** 0/10 câu trả lời Gemini nêu giá/size/tồn kho theo regex của `judge()`. Tuy nhiên e2e_51 ("Thời tiết Hà Nội mai thế nào?") Gemini tự đưa dự báo thời tiết, tức bịa thông tin thời gian thực mà regex không bắt được.
- DINOv2-S ở đây khác FashionCLIP ở lượt visual-only, nên 16/18 và 15/18 không so trực tiếp được (khác model).

Token lấy từ log LLMGateway của API theo từng kịch bản (gồm cả lời gọi Gemini bên trong RAG, vốn không trả token qua `/chat`); `HttpAgent` gửi đúng hợp đồng API (`/chat` `{message, session_id}`, `/search/image` trường `file`).

## 4. Bảng route

Đã điền ở mục 3b (đo thật 12/11/2026). Chi phí/100 lượt: **CHƯA TÍNH** (thiếu đơn giá đã xác minh; chạy lại với `GEMINI_PRICE_IN_PER_M`/`GEMINI_PRICE_OUT_PER_M` – bước tổng hợp không gọi lại Gemini vì mọi kịch bản đã có trong `e2e_http_cases.jsonl`).

## 5. Việc còn lại
1. ~~Ghép Agent/API → chạy `--agent http`~~ (xong 12/11). Tiếp: bộ kịch bản v1.1 cho qa/compare có `product_id`/phiên (không sửa file gốc); sửa router cho 2 câu QA bị đưa sang Gemini.
2. Điền đơn giá Gemini đã xác minh → chạy lại để có chi phí/100 lượt.
3. Hai người chấm lại các ca qa/compare/chitchat; ghi top-10 lỗi cuối cùng.
