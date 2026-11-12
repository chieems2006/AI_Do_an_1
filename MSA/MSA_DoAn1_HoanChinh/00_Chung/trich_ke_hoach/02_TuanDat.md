# Phần việc của Tuấn Đạt (trích tự động từ MSA_PLAN_v2.xlsx)

## Vai trò (sheet Phân công)

- **Thành viên**: Tuấn Đạt
- **Vai trò chính**: Dữ liệu & giao diện demo
- **Tuần 1**: Bảng phương pháp thu thập; làm sạch + phân loại; bảng nguồn và tính chính thống.
- **Tuần 2**: Tập ảnh truy vấn ngoài đời; benchmark LLM (chất lượng, chi phí, latency); hỗ trợ eval_qa.
- **Tuần 3**: UI Gradio; card kết quả; tóm tắt review; test plan 15-20 kịch bản; viết báo cáo cuối; video dự phòng.
- **Đầu ra bắt buộc**: Sheet 1 (Mục B, C, E), data sạch, benchmark LLM, UI, test report
- **Lưu ý**: Phần việc trải đều theo giai đoạn nên dễ làm đúng hạn; cần bám deadline Tuần 1 vì dữ liệu chặn mọi người.

## User story mà Tuấn Đạt là Owner

### US_04 – Liệt kê & so sánh các phương pháp thu thập dữ liệu (3.0 pt, Sprint 1, ưu tiên High)
- Muốn: liệt kê ít nhất 6 phương pháp (dataset public, crawl, API sàn, tự chụp, sinh bằng LLM, mua dữ liệu...) và so sánh ưu/nhược/chi phí/pháp lý
- Để: biện luận được vì sao chọn phương pháp này mà không chọn phương pháp khác
- Support: Chiến
- DOCS (đầu ra): Sheet '1_Thu thập dữ liệu' - Mục B hoàn chỉnh
- TEST (nghiệm thu): Mỗi phương pháp có đủ ưu/nhược/chi phí/pháp lý và có quyết định Chọn/Không chọn kèm lý do

### US_08 – Làm sạch, khử trùng lặp, phân loại dữ liệu (5.0 pt, Sprint 1, ưu tiên High)
- Muốn: loại ảnh lỗi/trùng (perceptual hash), chuẩn hoá text, gán category/sub-category theo taxonomy US_49; chuẩn hoá size/màu theo nhóm; giới hạn tối đa mỗi nhóm lá
- Để: dữ liệu sạch và nhất quán trước khi dùng cho mô hình
- Support: Hoàng
- DOCS (đầu ra): script 03_clean.py + báo cáo trước/sau làm sạch
- TEST (nghiệm thu): Ảnh lỗi dưới 1%; không còn ảnh trùng; 100% sản phẩm có category; nhãn sai ≤ 5% trên mẫu 100 SP/nhóm; không nhóm nào dưới quota

### US_10 – Tổng hợp nguồn & đánh giá tính chính thống (2.0 pt, Sprint 1, ưu tiên Medium)
- Muốn: lập bảng nguồn (URL, loại, license, mức tin cậy)
- Để: chứng minh được nguồn dữ liệu đáng tin cậy
- Support: Trung
- DOCS (đầu ra): Sheet '1_Thu thập dữ liệu' - Mục C và E
- TEST (nghiệm thu): Mọi nguồn đều có URL, license và đánh giá mức tin cậy

### US_11 – Tạo tập ảnh truy vấn 'ngoài đời' (3.0 pt, Sprint 2, ưu tiên Medium)
- Muốn: tạo 80-100 ảnh truy vấn thực tế (ảnh tự chụp, chụp màn hình, nền phức tạp, góc lạ); ground truth là danh sách sản phẩm giống nhất do 2 người gán nhãn; phân bổ tối thiểu giày 25 / quần áo 25 / mũ 15 / phụ kiện 15, có ảnh người mặc nhiều món
- Để: kiểm tra được mô hình khi ảnh người dùng khác ảnh studio của catalog
- Support: Chiến
- DOCS (đầu ra): thư mục data/eval/visual_queries/ + CSV ground truth
- TEST (nghiệm thu): Ít nhất 80 ảnh; mỗi ảnh có ít nhất 1 sản phẩm đúng được 2 người xác nhận; mỗi nhóm đạt mức tối thiểu

### US_24 – Benchmark LLM trả lời (1 API + 1-2 open-source) (5.0 pt, Sprint 2, ưu tiên High)
- Muốn: chạy cùng bộ prompt và context trên các LLM, đo faithfulness, hallucination rate, latency, chi phí/100 câu; Gemini đo thêm ở vai trò Fallback/Router trên eval_router
- Để: chọn LLM cân bằng giữa chất lượng, giá và tốc độ
- Support: Chiến
- DOCS (đầu ra): Sheet '3_Khảo sát phiên bản' - Bảng D (cột kết quả) + Bảng D2
- TEST (nghiệm thu): Cùng prompt, cùng context, temperature cố định; có log câu trả lời; Gemini có số liệu đủ cho cả 2 vai trò

### US_28 – Báo cáo cuối + kịch bản demo Đồ án 1 (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: tổng hợp kết quả benchmark, cải tiến trước/sau, hạn chế, hướng phát triển
- Để: nộp và bảo vệ đồ án 1
- Support: Trung
- DOCS (đầu ra): report_final.docx + demo_script.md
- TEST (nghiệm thu): Mọi con số trong báo cáo truy ngược được về file kết quả

### US_31 – Hiển thị kết quả kèm ảnh, giá, độ tương đồng, link (3.0 pt, Sprint 3, ưu tiên Medium)
- Muốn: thấy ảnh, tên, giá và điểm tương đồng của từng kết quả
- Để: so sánh nhanh các kết quả
- Support: Hoàng
- DOCS (đầu ra): Component hiển thị card kết quả
- TEST (nghiệm thu): Hiển thị đúng 100% trường dữ liệu trên 20 sản phẩm thử

### US_36 – Tóm tắt đánh giá khách hàng theo sản phẩm (ưu/nhược) (3.0 pt, Sprint 3, ưu tiên Medium)
- Muốn: tóm tắt trước (offline) ưu/nhược của từng sản phẩm từ review
- Để: trả lời nhanh và ổn định các câu hỏi như 'có bền không?'
- Support: Chiến
- DOCS (đầu ra): file product_review_summary.json
- TEST (nghiệm thu): Kiểm tay 20 sản phẩm: tóm tắt không có thông tin bịa

### US_43 – Giao diện demo đơn giản (Gradio/Streamlit): upload ảnh + chat (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: dùng một giao diện web đơn giản để tải ảnh và chat; hiển thị nhãn nguồn "Trả lời bởi Gemini" / "Từ dữ liệu cửa hàng"
- Để: có sản phẩm trình diễn được
- Support: Trung
- DOCS (đầu ra): app.py
- TEST (nghiệm thu): Chạy local bằng 1 lệnh; hoạt động đủ 4 luồng: ảnh, hỏi đáp, tìm, so sánh

### US_46 – Kiểm thử 15-20 kịch bản & sửa lỗi (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: chạy các kịch bản thật (ảnh studio, ảnh đời thực, câu hỏi ngoài phạm vi, câu hỏi cố tình gài prompt, ảnh người mặc cả bộ, câu chitchat, giả lập Gemini lỗi 429/timeout...) và ghi bug
- Để: demo không vỡ trước thầy
- Support: All
- DOCS (đầu ra): test_report.md
- TEST (nghiệm thu): Không còn bug mức nghiêm trọng khi feature freeze


## User story mà Tuấn Đạt là Support

- US_01 – Kickoff & chốt phạm vi (Owner: Trung)
- US_03 – Họp daily 15' + review cuối tuần (Owner: Trung)
- US_06 – Tải & chuẩn hoá dataset công khai (ảnh + metadata) (Owner: Hoàng)
- US_09 – EDA & mô tả đặc điểm dữ liệu (Owner: Khoa)
- US_16 – Xây bộ đánh giá Product QA (câu hỏi - đáp án - nguồn) (Owner: Chiến)
- US_26 – Báo cáo mốc Tuần 1 (dữ liệu) (Owner: Trung)
- US_27 – Báo cáo + slide mốc 2 tuần (dữ liệu, độ đo, khảo sát) (Owner: Trung)
- US_32 – Xử lý ảnh đầu vào không hợp lệ (Owner: Hoàng)
- US_33 – Xây kho tri thức (chunk mô tả, specs, review) & vector store (Owner: Chiến)
- US_35 – Trả lời có trích nguồn và biết từ chối khi thiếu thông tin (Owner: Chiến)
- US_45 – Thực hiện ít nhất 4 cải tiến ưu tiên cao & đo trước/sau (Owner: Khoa)
- US_46 – Kiểm thử 15-20 kịch bản & sửa lỗi (Owner: Tuấn Đạt)
- US_47 – Diễn tập demo + video dự phòng + gắn tag release (Owner: Trung)
- US_48 – Mở rộng dữ liệu: Quần áo & Mũ (Owner: Hoàng)
- US_50 – Dựng LLM Gateway cho Gemini (cấu hình model, timeout, retry, cache cơ bản) (Owner: Hoàng)

## Lịch theo ngày của Tuấn Đạt

- N1 (05/11): US_04: Đọc kỹ yêu cầu thầy. Bắt đầu liệt kê các phương pháp thu thập dữ liệu (nháp).
- N2 (06/11): US_04: Hoàn thiện bảng so sánh >= 6 phương pháp + đề xuất chọn/không chọn (Sheet 1, Mục B).
- N3 (07/11): US_06 (hỗ trợ): Viết hàm map metadata từng dataset về schema chuẩn. Map metadata Clothing/Headwear.
- N4 (08/11): US_08: Viết script làm sạch: ảnh lỗi, ảnh trùng (perceptual hash), chuẩn hoá text. Áp category_map + cap mỗi nhóm lá.
- N5 (09/11): US_08: Chạy làm sạch toàn bộ + gán category/sub-category. US_10: bắt đầu bảng nguồn.
- N6 (10/11): US_10: Hoàn tất bảng nguồn + đánh giá tính chính thống (Sheet 1, Mục C và E).
- N7 (11/11): Nghỉ (hoặc bù việc trễ).
- N8 (12/11): US_11: Lập kế hoạch và bắt đầu chụp/thu ảnh truy vấn 'ngoài đời' (ảnh tự chụp, chụp màn hình, nền phức tạp).
- N9 (13/11): US_11: Hoàn tất 80-100 ảnh ngoài đời + gán ground truth (cùng Chiến, 2 người xác nhận).
- N10 (14/11): US_24: Benchmark LLM: chạy 100 câu với các LLM đã chọn (cùng prompt, cùng context, temperature cố định).
- N11 (15/11): US_24: Benchmark LLM tiếp (API và open-source); ghi chi phí và latency. Gemini vai trò fallback chạy trên eval_router (Bảng D2); viết sẵn hàm gọi Gemini để Hoàng tái dùng.
- N12 (16/11): Điền kết quả LLM vào Sheet 3 Bảng D; viết phần so sánh LLM + chi phí.
- N13 (17/11): Slide phần dữ liệu (phương pháp, nguồn, đặc điểm).
- N14 (18/11): Tập phần trình bày dữ liệu.
- N15 (19/11): US_43: Dựng khung giao diện Gradio: khung chat + nút tải ảnh.
- N16 (20/11): US_31: Card hiển thị kết quả (ảnh, giá, độ tương đồng). US_36: Bắt đầu tóm tắt review theo sản phẩm.
- N17 (21/11): US_43: Nối UI với API, hiển thị bảng so sánh. US_36: hoàn tất tóm tắt review.
- N18 (22/11): US_46: Lập test plan 15-20 kịch bản; chỉnh UI theo lỗi người dùng.
- N19 (23/11): US_46: Chạy 15-20 kịch bản kiểm thử, ghi bug.
- N20 (24/11): US_28: Viết báo cáo cuối (kết quả benchmark, bảng trước/sau, hạn chế). US_47: Quay video demo dự phòng.
- N21 (25/11): Diễn tập phần giao diện.