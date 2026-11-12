# US_36 – Tóm tắt đánh giá khách hàng theo sản phẩm (ưu/nhược)

| Mục | Nội dung |
|---|---|
| Mã US | US_36 (Owner: Tuấn Đạt, Support: Chiến) – Sprint 3, 3.0 pt |
| Mục tiêu | Tóm tắt offline ưu/nhược mỗi SP từ review để trả lời nhanh, ổn định câu "có bền không?" |
| Đầu ra | `src/scripts/summarize_reviews.py`; `results/product_review_summary.json` (baseline, 428 SP); `results/product_review_summary_llm20.json` (LLM, 20 SP); `results/us36_kiem_tay_20sp.csv` |
| Tiêu chí nghiệm thu | Kiểm tay 20 SP: tóm tắt không có thông tin bịa |
| Trạng thái | **Hoàn thành phần chạy thật**; kiểm tay do tác nhân AI làm – **nhóm cần 1 người thật kiểm lại** |

Repo chung: `data/processed/product_review_summary.json` (copy file baseline). Dữ liệu: ViMRHP (CC BY-NC-ND 4.0 – không phát hành file tóm tắt ra ngoài).

## 1. Cách làm
**Baseline (từ khoá):** 8 khía cạnh – chất liệu/vải, độ bền, êm/thoải mái, size/form, màu sắc/giống hình, đường may, giao hàng/đóng gói, giá.
Mỗi khía cạnh có regex tích cực/tiêu cực (kiểm tiêu cực trước; xử lý phủ định "không/ko/k bền", "không biết có bền không", "không chỉ thừa", "rộng rãi").
Ưu điểm = khía cạnh có ≥ 2 review khen và khen > chê; Lưu ý = ≥ 2 review chê hoặc chê ≥ 20%. Mỗi ý kèm số review + `comment_id` + đoạn trích quanh từ khoá
→ **không thể sinh thông tin ngoài review** (chỉ có thể bắt nhầm ngữ nghĩa). Lọc review spam/quảng cáo bằng regex (`[QC]`, voucher, "soạn … gửi", "nhận xu", "đặt lịch"…).

**LLM:** `gemini-3.5-flash-lite`, temperature 0, JSON, gộp 5 SP/lời gọi (do quota free tier 20 request/ngày/model), mỗi SP ≤ 12 review, bắt buộc ghi chỉ số review minh chứng.
Kiểm tự động: chỉ số review hợp lệ + tỉ lệ từ của ý có trong review minh chứng (`auto_overlap`).

Lệnh: `python src/scripts/summarize_reviews.py baseline` (0,7 s) ; `MSA_ENV_FILE=… python src/scripts/summarize_reviews.py llm --n 20 --model gemini-3.5-flash-lite`.

## 2. Kết quả THẬT
| Chỉ số | Giá trị | File |
|---|---|---|
| SP trong phạm vi (bỏ 81 Đồng hồ) | 428 | `product_review_summary.json` `_meta` |
| Review xử lý | 9.403 | idem |
| Review spam/quảng cáo bị lọc | 262 (2,8%) | idem |
| SP có ≥ 1 ưu điểm / ≥ 1 lưu ý / rỗng | 423 / 384 / 3 | idem |
| LLM: số lời gọi / SP | 4 lời gọi / 20 SP (+1 lần thử lại do lỗi tạm thời, tính vào ngân sách) | `product_review_summary_llm20.json` `_meta.calls` |
| LLM: latency mỗi lời gọi (5 SP) | 2,5 – 14,3 s (4 lần đo) | idem |
| LLM: token vào / ra mỗi lời gọi | 3.097–3.708 / 931–1.156 (thinking = 0) | idem |
| LLM: số ý tóm tắt (ưu + nhược) | 93 | `us36_kiem_tay_20sp.csv` |
| LLM: ý trích chỉ số review không tồn tại | 0/93 | idem |
| **Kiểm tay 20 SP – ý có chi tiết không có trong review** | **3/93 ý (3,2%), ở 3/20 SP** | idem |

3 ý lỗi (tác nhân đọc toàn văn review minh chứng): S03 "…nhẹ và **bền**" (review chỉ nói "chắc chắn"); S05 "…**tôn dáng**…" (không review nào nói);
S16 "…**ít nhăn**…" (không có, và 1 "minh chứng" là đoạn quảng cáo của shop lọt vào review). → **Tiêu chí "không có thông tin bịa" chưa đạt 100% với LLM**;
baseline từ khoá không bịa nhưng có bắt nhầm (vd. "size M rộng rãi thoải mái" trước khi sửa regex bị tính là phàn nàn size).

## 3. Khuyến nghị dùng trong hệ thống
1. Dùng **baseline** làm nguồn mặc định cho câu "có bền không / có êm không" (trả lời kèm số review + trích dẫn), LLM chỉ để viết câu mượt từ các ý baseline.
2. Nếu dùng tóm tắt LLM: bắt buộc hậu kiểm `auto_overlap` và lọc spam trước khi đưa review vào prompt (lỗi S16).
3. Việc còn lại: 1 người thật kiểm lại `us36_kiem_tay_20sp.csv` (cột verdict) + kiểm 20 SP của baseline với cùng tiêu chí.
