# US_14 – Khảo sát độ đo cho Tìm/So sánh & Agent (Sheet "2_Độ đo" – phần Search/Compare & Agent)

| Mục | Nội dung |
|---|---|
| Mã US | US_14 (2 pt, Sprint 2, Owner: Chiến, Support: Trung) |
| Mục tiêu | Đo chất lượng cả agent chứ không chỉ từng module |
| Đầu ra | File này; dữ liệu nhãn: `eval/eval_router.jsonl` (78 câu); log request `logs/requests.jsonl` (định dạng 5.2) |
| Tiêu chí nghiệm thu | Mỗi độ đo có công thức, ưu/nhược và quyết định |
| Trạng thái | **Hoàn thành** (khảo sát). Số đo route accuracy do Trung/Hoàng chạy router trên eval_router; nhánh Gemini đã đo một phần (mục 3) |

## Tóm tắt 5 dòng
1. Khảo sát độ đo cho tìm kiếm, so sánh và cả agent (không chỉ từng module).
2. Chọn chính: route accuracy, attribute F1, % ô so sánh khớp DB, Task Success Rate, latency e2e p95, chi phí/lượt, fallback rate, unsupported-store-fact.
3. Chi phí báo bằng **token / 100 lượt hội thoại** + công thức quy tiền (đơn giá `[cần xác minh]`) – đơn vị thống nhất ở QUYET_DINH mục F.
4. Số thật hiện có: route accuracy 0,878 (Trung), so sánh 370/370 ô khớp (Hoàng), vi phạm giá/size Gemini 0/20.
5. Ví dụ dễ hiểu: `00_Chung/THUAT_NGU.md` mục 4.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## 1. Bảng độ đo

| Độ đo | Công thức | Ưu điểm | Nhược điểm | Quyết định | Lý do / nguồn dữ liệu |
|---|---|---|---|---|---|
| **Route accuracy** (= intent accuracy) | (1/N) Σ 1[route_dự_đoán = route_nhãn] trên eval_router | Đo "não" của agent; 1 số | Không phân biệt lỗi nặng/nhẹ | **CHÍNH** (mục tiêu ≥ 0.90) | eval_router 78 câu, 7 route; báo cáo kèm **ma trận nhầm lẫn** và accuracy theo route (macro) để route ít câu không bị che |
| OOD detection precision/recall | P = \|dự đoán gemini_* ∩ nhãn gemini_*\| / \|dự đoán gemini_*\|; R tương tự trên nhãn | Biết router có lạm dụng Gemini (P thấp) hay bỏ sót câu ngoài phạm vi (R thấp) | Cần đủ câu OOD (eval_router có 21) | **CHÍNH** | R14 |
| **Tool-call accuracy** | % lượt gọi đúng công cụ **và** đúng tham số bắt buộc (product_id, product_type, ảnh) | Bắt lỗi "đúng route nhưng sai tham số" | Cần nhãn tham số | **CHÍNH** | Trên tập kịch bản US_46; eval_router có trường product_id |
| **Attribute extraction F1** | Micro-F1 trên cặp (thuộc tính, giá trị): màu, giá min/max, size, product_type, sub_category, gender | Lỗi bộ lọc làm kết quả sai từ đầu | Cần nhãn bộ lọc; quy ước chuẩn hoá ("200k" = 200000) | **CHÍNH** | Bổ sung nhãn filter cho 13 câu `search` của eval_router (việc của nhóm) |
| Comparison factual correctness | % ô trong bảng so sánh khớp DB | Kiểm tra trực tiếp bịa thông số | Cần script đối chiếu | **CHÍNH** (mục tiêu ~1.0) | Bảng lấy thẳng từ DB (I10) |
| Cùng-nhóm khi so sánh | % yêu cầu so sánh khác product_type bị chặn/hỏi lại | R19 | – | **PHỤ** | Câu r076 eval_router |
| **Task Success Rate (TSR)** | % kịch bản hoàn thành đúng từ đầu đến cuối (định nghĩa thành công cho từng kịch bản) | 1 số tổng thể | Cần định nghĩa rõ; tốn công chấm | **CHÍNH** (mục tiêu ≥ 0.80 / 50 kịch bản) | US_44/US_46 |
| **Latency end-to-end P50/P95** | Phân vị thời gian 1 lượt (gồm LLM), đo ≥ 3 lần, bỏ warm-up | Quyết định demo mượt | Phụ thuộc mạng/API | **CHÍNH** (mục tiêu P95 ≤ 8 s) | Trường `latency_ms` trong log 5.2 |
| **Chi phí / lượt** | (token_in·giá_in + token_out·giá_out + token_thinking·giá_out)/số lượt; báo **token/100 lượt** + công thức | So sánh cấu hình | Đơn giá thay đổi `[cần xác minh – điền theo bảng giá Google hiện hành]` | **CHÍNH** (dạng token) | `usageMetadata` của Gemini |
| **Tỉ lệ chuyển Gemini (fallback rate)** | số lượt source∈{gemini, cache-gemini} / tổng lượt | Kiểm soát phụ thuộc + quota | Phụ thuộc kịch bản test | **CHÍNH** (mục tiêu 0.10–0.25) | log route mỗi lượt |
| Cache hit rate | lượt source="cache" / lượt cần LLM | Hiệu quả cache (I15) | Exact-match trúng ít với câu tự do | **PHỤ** | Báo cáo cùng fallback rate |
| **Unsupported-store-fact rate** (nhánh Gemini) | % phản hồi Gemini nêu giá/size/tồn kho/chính sách không có trong ngữ cảnh | Mục tiêu "không bịa" | Regex bỏ sót cách diễn đạt lạ ⇒ cần đọc tay | **CHÍNH** (mục tiêu 0/60) | `check_gemini_hallucination.py` + đọc tay |
| Tỉ lệ thông điệp dự phòng | % lượt Gemini trả llm_error (429/timeout/503) | Độ ổn định demo (R12) | – | **PHỤ** | trường `error` |

## 2. Quy trình

1. Router chạy trên toàn bộ eval_router (không cần gọi Gemini nếu router là luật/embedding) → route accuracy, ma trận nhầm lẫn, OOD P/R.
2. Câu `gemini_*` → nhánh Gemini → hậu kiểm regex + đọc tay → unsupported-store-fact rate.
3. Mọi request ghi 1 dòng `logs/requests.jsonl` → latency, fallback rate, cache hit, token/100 lượt.

## 3. Số đo thật đã có cho nhánh Gemini (05/11/2026)

`results/gemini_fallback_check.json` – 21 câu chitchat/ood của eval_router + 2 câu bẫy, prompt `gemini_fallback.md v1.0`, model `gemini-3.5-flash-lite`, mỗi câu 1 lời gọi:
- Phản hồi hợp lệ 22/23 (1 lỗi HTTP 503 – server quá tải ⇒ thông điệp dự phòng).
- Vi phạm giá/size/tồn kho/chính sách (regex): **0/20** câu eval_router hợp lệ, **0/2** câu bẫy; tác nhân đã đọc toàn bộ 22 phản hồi, không thấy nội dung bịa thông tin cửa hàng (chưa có người thật đọc).
- Token trung bình: in 747,5 / out 41,7 ⇒ **74.750 token in + 4.170 token out / 100 lời gọi Gemini** (≈ 21.566 token / 100 lượt hội thoại khi nhân fallback rate 0,273 – QUYET_DINH mục F); latency P50 16,0 s, P95 27,8 s (server đang quá tải 503 trong lúc đo – **vượt mục tiêu 4 s**, cần đo lại giờ thấp điểm).
