# US_04 – Liệt kê & so sánh các phương pháp thu thập dữ liệu (Sheet 1, Mục B)

| Mục | Nội dung |
|---|---|
| Mã US | US_04 (Owner: Tuấn Đạt, Support: Chiến) – Sprint 1, 3.0 pt |
| Mục tiêu | Liệt kê ≥ 6 phương pháp thu thập dữ liệu (ảnh SP + mô tả + review tiếng Việt), so sánh ưu/nhược/chi phí/pháp lý, quyết định Chọn/Không chọn có lý do gắn ràng buộc nhóm |
| Đầu ra | Bảng B dưới đây (thay bảng B gợi ý trong `MSA_PLAN_v2.xlsx`, sheet `1_Thu thập dữ liệu`) |
| Tiêu chí nghiệm thu | Mỗi phương pháp đủ ưu/nhược/chi phí/pháp lý + quyết định Chọn/Không chọn kèm lý do |
| Trạng thái | **Hoàn thành** (đã kiểm chứng bằng thử truy cập thật ngày 04–05/11/2026; license đánh dấu `[cần xác minh]` khi chưa đọc được văn bản gốc) |

## Tóm tắt 5 dòng
1. So sánh 9 phương pháp thu thập theo ưu/nhược/chi phí/pháp lý; chọn 3: dataset public (chính), tự chụp (chỉ tập test), LLM sinh (chỉ bộ đánh giá).
2. Không crawl sàn vì Tiki trả HTTP 403 với IP cloud và ảnh Shopee bị chặn – bằng chứng thử thật ngày 04–05/11.
3. ViMRHP (509 SP Shopee, 11.009 review tiếng Việt thật, CC BY-NC-ND 4.0) thay phần crawl cho hỏi đáp tiếng Việt.
4. Kết quả: 4.593 SP FPI → 4.385 SP sau làm sạch; mũ 285 < quota 300 (số chuẩn – `00_Chung/QUYET_DINH_CAN_CHOT.md` mục A).
5. Loại số liệu: [Thật–thật] cho số lượng; ảnh ngoài đời CHƯA ĐO (0/80).
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Ràng buộc nhóm dùng để biện luận: **R1** 3 tuần; **R2** 5 người, không ai chuyên crawl; **R3** không có ngân sách;
**R4** cần tiếng Việt (QA/review); **R5** license rõ, chạy lại được; **R6** máy CPU 2 nhân/7 GB (môi trường chung).

## 1. Bằng chứng thực tế thu được trong lượt này (khác với giả định của sheet)

| # | Kiểm chứng | Kết quả thật | Hệ quả |
|---|---|---|---|
| E1 | Crawl Tiki từ máy chủ cloud | HTTP **403** (Tiki chặn IP cloud) – theo thông báo của Tác nhân 1 khi chuẩn bị dữ liệu | Không vượt chặn (không dùng proxy xoay vòng / giả trình duyệt vì rủi ro ToS). Crawl sàn chuyển sang **kế hoạch B** |
| E2 | Tải Kaggle (`paramaggarwal/fashion-product-images-dataset`) | Không truy cập được Kaggle từ môi trường | Dùng **bản mirror HuggingFace** `ashraq/fashion-product-images-small` (44.072 dòng, ảnh 60×80) – cùng dữ liệu gốc Myntra nhưng độ phân giải thấp |
| E3 | Ảnh Shopee (`*.susercontent.com`), S3 của ABO | Không truy cập được | ViMRHP dùng được phần text (tên SP + review), **không có ảnh**; ABO không tải được |
| E4 | ViMRHP (HF `trucmtnguyen/ViMRHP`) | Tải được: **509 SP Shopee VN, 11.009 review tiếng Việt thật** (6 nhóm thời trang, 2023–2024) | **Thay thế phần crawl sàn VN** cho Product QA và tóm tắt review (đáp ứng R4) |
| E5 | Gemini API free tier | Mỗi model có quota **20 request/ngày/project** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quotaValue 20 – đọc từ lỗi 429 thật, xem `results/failed/`) | Phương pháp 5 (sinh bằng LLM) bị giới hạn mạnh: phải gộp nhiều mục/lời gọi, dùng cache, hoặc trả phí |

## 2. Bảng B – So sánh phương pháp (đã chỉnh theo thực tế)

| # | Phương pháp | Mô tả | Ưu điểm | Nhược điểm | Chi phí | Pháp lý / đạo đức | Quyết định | Lý do (gắn ràng buộc) |
|---|---|---|---|---|---|---|---|---|
| 1 | **Dataset public (HuggingFace/Kaggle/học thuật)** | Tải bộ dữ liệu có sẵn ảnh + metadata: Fashion Product Images (mirror HF), ViMRHP, Amazon Reviews 2023, Clothing Dataset CC0… | Nhanh (tải trong vài phút), tái lập được (seed 42), có paper/trang nguồn để trích dẫn | FPI: tiếng Anh, ảnh studio 60×80, **thiếu mũ** (283 Caps + 3 Hat + 7 Headband), không có giá/review. ViMRHP: không có ảnh/giá/size | 0 đ | Thấp nếu tuân license; ViMRHP **CC BY-NC-ND 4.0** → chỉ dùng nội bộ học thuật, không phát hành lại bản đã chỉnh | **CHỌN – nguồn chính** | R1, R3, R5. Đã lấy thật 4.593 SP FPI + 509 SP/11.009 review ViMRHP |
| 2 | Crawl sàn TMĐT Việt Nam quy mô nhỏ | Script lấy tên/giá/mô tả/size/review từ trang SP công khai (Tiki, Shopee…) | Dữ liệu tiếng Việt, có giá, size thật | **Tiki 403 với IP cloud (E1)**, Shopee chặn ảnh (E3); anti-bot, cấu trúc trang đổi; ToS hạn chế | 1–2 ngày dev + rủi ro bị chặn | Trung bình–cao (ToS, robots.txt) | **KHÔNG CHỌN ở lượt này** (giữ làm tuỳ chọn chạy từ máy cá nhân, ≤ 300 SP, có rate-limit) | E1 chứng minh không khả thi từ máy chủ; ViMRHP đã bù phần tiếng Việt (R4). Nếu nhóm cần giá/size thật thì 1 người crawl thủ công nhỏ từ máy nhà, ghi rõ ngày, không phát tán |
| 3 | API chính thức / affiliate của sàn (Shopee/Lazada Open Platform, Tiki Affiliate) | Đăng ký tài khoản seller/đối tác, gọi API | Hợp pháp, dữ liệu cấu trúc | Cần duyệt tài khoản (thường là seller thật), thời gian chờ không kiểm soát; API seller chỉ trả SP của chính shop | Thời gian chờ duyệt | Thấp | KHÔNG CHỌN | R1: không kịp 3 tuần; R2: không có tư cách seller |
| 4 | Tự chụp / crowdsourcing nhỏ | Nhóm + người quen chụp giày, áo, mũ, phụ kiện ngoài đời; gán SP giống nhất | Đúng phân phối ảnh người dùng (góc lạ, nền phức tạp, nhiều món) – đo được domain gap | Ít ảnh, tốn công gán nhãn 2 người, thiên lệch người chụp | 0,5–1 ngày | Thấp (xin phép người trong ảnh, che mặt) | **CHỌN – chỉ cho tập test** (US_11, 80–100 ảnh) | R4/R5 không áp dụng; là cách DUY NHẤT có ảnh đời thực khi DeepFashion chưa được cấp quyền. **CHƯA làm** – cần người thật chụp |
| 5 | Sinh / dịch bằng LLM (QA, câu định tuyến, tóm tắt) | Dùng LLM tạo câu hỏi–đáp từ review thật, câu chitchat/ngoài phạm vi | Nhanh, phủ được câu khó, câu từ chối | Câu "quá sạch", có thể sai; **quota free tier 20 req/ngày/model (E5)** | Free tier (giới hạn) | Thấp nếu gắn nhãn `origin` | **CHỌN – bổ trợ, chỉ cho bộ đánh giá**, bắt buộc gắn `origin` + kiểm tay | Lượt này câu hỏi benchmark do tác nhân viết tay từ review thật (`origin=tac_nhan_AI_viet_tay_tu_review_that`), chưa người thật duyệt |
| 6 | Mua dataset thương mại | Mua bộ dữ liệu từ nhà cung cấp | Chất lượng, đúng miền | Đắt | Cao | Thấp | KHÔNG CHỌN | R3 |
| 7 | Hợp tác doanh nghiệp (xin catalog + log shop) | Ký thoả thuận lấy dữ liệu shop thật | Dữ liệu thật nhất | Đàm phán lâu, rủi ro bảo mật dữ liệu khách | Thời gian | Cao (dữ liệu cá nhân) | KHÔNG CHỌN | R1, R5 |
| 8 | Crawl Google/Bing Images theo từ khoá | Tải ảnh theo từ khoá | Nhiều ảnh nhanh | Không metadata/giá/review, bản quyền ảnh không rõ, nhiễu, khó gán ground truth | Thấp | Cao (bản quyền) | KHÔNG CHỌN | R5; không phục vụ QA/so sánh |
| 9 | Dataset cuộc thi/đăng ký (CAMEO/ViEcom-Rec NTCIR-19, DeepFashion, H&M Kaggle) | Đăng ký/xin quyền tải | Có dữ liệu VN (ViEcom-Rec) hoặc cặp consumer–shop (DeepFashion) | Cần đăng ký/ký thoả thuận; thời gian duyệt; Kaggle bị chặn (E2) | Thời gian | Trung bình (điều khoản cuộc thi) | KHÔNG CHỌN ở Đồ án 1 (ghi nhận cho Đồ án 2) | R1: không kiểm soát thời gian cấp quyền |

## 3. Chiến lược cuối (thay đoạn "Chiến lược đề xuất" của sheet)

1. **Catalog + ảnh (visual search):** Fashion Product Images – bản mirror HF small, 4.593 SP theo quota 4 nhóm (`shared_data v1`), làm sạch bằng `03_clean.py` → 4.385 SP (`results/clean_report.json`).
2. **Tiếng Việt (QA, tóm tắt review, eval):** ViMRHP 428 SP trong phạm vi (bỏ 81 SP Đồng hồ) – thay cho crawl Tiki.
3. **Ảnh ngoài đời (test):** nhóm tự chụp 80–100 ảnh (US_11) – **CHƯA ĐO**.
4. **Bộ đánh giá:** câu viết tay từ review thật + (tuỳ quota) LLM sinh nháp, luôn gắn `origin`.
5. **Khoảng trống còn lại:** mũ chỉ 285 SP sau làm sạch (< quota 300), không có boot/bucket; giá/size thật không có ở cả 2 nguồn → luồng "lọc theo giá/size" chỉ demo được trên dữ liệu bổ sung (crawl thủ công nhỏ hoặc Amazon Reviews 2023 metadata – có giá USD).
