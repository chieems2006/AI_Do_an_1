# US_44 – Đo baseline hệ thống end-to-end

| Mục | Nội dung |
|---|---|
| Mã US | US_44 (Owner: Khoa, Support: Chiến) – Sprint 3, 3.0 pt |
| Mục tiêu | Biết cải tiến nào đáng làm nhất: TSR, latency, top-10 lỗi, bảng route (tỉ lệ chuyển Gemini, chi phí/100 lượt) |
| Đầu ra | `src/scripts/baseline_e2e.py`, `eval/e2e_scenarios.jsonl` (60 kịch bản), `results/e2e_*.json`, `results/e2e_*_per_case.csv`, file này |
| Tiêu chí nghiệm thu | Bảng số liệu baseline + top-10 lỗi + bảng route (tỉ lệ Gemini, chi phí/100 lượt) |
| Trạng thái | **Khung sẵn – cần hệ thống đã ghép.** Phần **visual** đã đo THẬT bằng `--agent visual-only` (mục 3). TSR toàn hệ thống, tỉ lệ chuyển Gemini, chi phí/100 lượt: **CHƯA ĐO** (Agent của Trung + API của Hoàng chưa ghép ở lượt này). |

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

## 4. Bảng route (điền khi ghép hệ thống)

| Route | n | TSR | Latency p50 / p95 (ms) | % chuyển Gemini | Token in/out /100 lượt | Chi phí/100 lượt |
|---|---|---|---|---|---|---|
| visual | 18 | xem mục 3 (đo thật) | xem mục 3 | 0 % (visual không gọi Gemini) | 0 | 0 |
| search, qa, compare, chitchat, ood, clarify | 42 | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO |
| **Tổng** | 60 | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO | CHƯA ĐO |

## 5. Việc còn lại
1. Ghép `Agent.handle` (Trung) / API `/chat`, `/search/image` (Hoàng) → chạy `--agent http`.
2. Điền đơn giá Gemini đã xác minh → chạy lại để có chi phí/100 lượt.
3. Hai người chấm lại các ca qa/compare/chitchat; ghi top-10 lỗi cuối cùng.
