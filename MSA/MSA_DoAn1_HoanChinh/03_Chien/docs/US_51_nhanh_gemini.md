# US_51 – Nhánh Gemini: chitchat, ngoài phạm vi, câu khó & fallback khi nội bộ không tự tin

| Mục | Nội dung |
|---|---|
| Mã US | US_51 (5 pt, Sprint 3, Owner: Chiến, Support: Hoàng) |
| Mục tiêu | Hội thoại không bị cụt nhưng không bịa thông tin cửa hàng; có nhãn nguồn |
| Đầu ra | `prompts/gemini_fallback.md` (v1.0, system + few-shot + thông điệp dự phòng + changelog), `src/msa/rag/fallback.py` (`GeminiFallback`, `should_fallback`), `src/scripts/check_gemini_hallucination.py`, `src/scripts/run_gemini_fallback_check.py`, kết quả `results/gemini_fallback_check.json` |
| Tiêu chí nghiệm thu | Route accuracy ≥ 90% trên eval_router; 0/60 phản hồi Gemini bịa giá/size/tồn kho; UI có nhãn nguồn; 429/timeout trả thông điệp dự phòng; câu in-domain có product_id không bị đẩy sang Gemini trừ khi retrieval rỗng |
| Trạng thái | **Khung sẵn + đo thật một phần**: prompt, hậu kiểm, xử lý lỗi, luật R14 xong và có test; 0/20 vi phạm trên câu thật. Route accuracy phụ thuộc router của Trung (chưa đo ở đây); mục tiêu "0/60" cần chạy đủ 60 phản hồi khi có quota |

## Tóm tắt 5 dòng
1. Nhánh Gemini xử lý chitchat/ngoài phạm vi bằng prompt có version (`prompts/gemini_fallback.md` v1.0, system + few-shot) + hậu kiểm regex.
2. 0/20 phản hồi vi phạm giá/size/tồn kho, 0/2 câu bẫy (mới 22/60 phản hồi theo tiêu chí).
3. Prompt dài (~750 token vào/lời gọi) → ≈ 21.566 token / 100 lượt hội thoại khi quy cùng đơn vị với Trung (QUYET_DINH mục F).
4. Khi Gemini lỗi 429/503: trả thông điệp dự phòng – nên gắn `source="fallback"` (mục D).
5. Latency đo lúc server quá tải (503) → cần đo lại; route accuracy phụ thuộc router (0,878).
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## 1. Luồng xử lý

```
router (Trung) → route, confidence
   ├─ route ∈ {gemini_chitchat, gemini_ood}                → GeminiFallback.respond()
   ├─ có product_id  → giữ công cụ nội bộ (QA/RAG); chỉ sang Gemini khi retrieval rỗng   (R14)
   └─ không product_id và confidence < τ_intent (0.6)       → GeminiFallback.respond()
GeminiFallback: prompt v1.0 → LLM (thinkingBudget=0 nếu model hỗ trợ) → hậu kiểm regex
   ├─ lỗi 429/timeout/503 → messages.llm_error  (không ném lỗi lên UI)
   ├─ vi phạm giá/size/tồn kho/chính sách → messages.postcheck_violation (ghi raw để phân tích)
   └─ hợp lệ → answer, source="gemini"|"cache", label "Trả lời bởi Gemini – thông tin tham khảo chung"
```

QA thiếu dữ kiện (giá, tồn kho…) **không** đi sang Gemini: RAG trả "Hiện cửa hàng chưa có thông tin về …" (quy tắc 5.4).

## 2. Hậu kiểm `check_gemini_hallucination.py`

| Nhóm | Ví dụ mẫu bắt | Ghi chú |
|---|---|---|
| gia | `350k`, `1.200.000đ`, `2 triệu`, `$20`, `giá từ 99`, `giảm 30%` | luôn tính vi phạm (kể cả câu phủ định có số) |
| size | `size 42`, `sz M`, `cỡ XL`, `42 EU` | bỏ qua nếu trong 30 ký tự trước có từ phủ định/hỏi lại |
| ton_kho | `còn hàng`, `hết hàng`, `có sẵn`, `còn size`, `chỉ còn` | như trên ("mình không biết còn hàng không" không tính) |
| chinh_sach | `đổi trả trong 7 ngày`, `bảo hành 6`, `freeship`, `giao trong 2h`, `phí ship 15` | như trên |

Giá trị có trong `context` (dữ liệu DB cấp cho prompt) được phép. 22 test (8 bắt đúng, 6 không bắt nhầm, ngữ cảnh) trong `tests/test_gemini_branch.py`. Regex có thể bỏ sót cách diễn đạt lạ ⇒ vẫn cần đọc tay.

## 3. Số đo thật (05/11/2026) – `results/gemini_fallback_check.json`

Lệnh: `MSA_ENV_FILE=<.env> PYTHONPATH=src python src/scripts/run_gemini_fallback_check.py` (mỗi câu 1 lời gọi; chuỗi model dự phòng `gemini-3.5-flash-lite → gemini-3-flash-preview → gemini-2.5-flash`; `gemini-3.5-flash` đã hết quota ngày).

| Chỉ số | Giá trị |
|---|---|
| Câu chạy | 21 câu gemini_chitchat/gemini_ood của eval_router + 2 câu bẫy (hỏi giá+size, hỏi freeship/đổi trả) |
| Model thực tế | `gemini-3.5-flash-lite` (prompt v1.0) |
| Phản hồi hợp lệ | 22/23 (1 lỗi HTTP 503 "model quá tải" ⇒ trả thông điệp dự phòng đúng thiết kế) |
| Vi phạm giá/size/tồn kho/chính sách (regex) | **0/20** câu eval_router · **0/2** câu bẫy |
| Đọc tay (tác nhân AI, không phải người) | Đọc cả 22 phản hồi: không nêu giá/size/tồn kho; câu hack được từ chối; câu giá vàng/bóng đá/thời tiết nói rõ không có dữ liệu cập nhật; luôn kéo về mua sắm |
| Token / lời gọi Gemini (trung bình) | in 747,5 · out 41,7 · thinking 0 ⇒ **74.750 in + 4.170 out / 100 lời gọi Gemini** (≈ 21.566 token / 100 lượt hội thoại khi nhân fallback rate 0,273 – QUYET_DINH mục F) |
| Chi phí / 100 lượt | = 74.750 × giá_in + 4.170 × giá_out (USD/token) – đơn giá `[cần xác minh – điền theo bảng giá Google hiện hành]` |
| Latency (không tính cache) | P50 16,0 s · P95 27,8 s – **vượt mục tiêu 4 s**; đo lúc server trả 503 nhiều (quá tải), cần đo lại; ghi chú: `gemini-3.5-flash` với thinkingBudget=0 đo 1,3 s (n=1) |

Quan sát chất lượng: một số câu ood vẫn được trả lời ngắn (thủ đô Úc, nghiệm phương trình, cách nấu phở) theo quy tắc 5 của prompt rồi kéo về thời trang – nhóm cần quyết định có muốn từ chối hẳn câu ood không (đổi quy tắc ⇒ tăng version).

## 4. Việc còn lại

1. Đủ 60 phản hồi cho tiêu chí "0/60": chạy thêm khi có quota (eval_router chỉ có 21 câu Gemini ⇒ chạy 3 mẫu/câu ở temperature 0.5 hoặc bổ sung câu chitchat/ood) – người thật đọc lại toàn bộ.
2. Route accuracy ≥ 90%: Trung chạy `Router.route` trên `eval/eval_router.jsonl`.
3. Đo lại latency giờ thấp điểm; so sánh `gemini-3.5-flash` (thinkingBudget=0) với flash-lite cho nhánh này.
4. UI (Đạt) hiển thị trường `label` khi `source ∈ {gemini, cache}`.
