# Phần việc của Trung (trích tự động từ MSA_PLAN_v2.xlsx)

## Vai trò (sheet Phân công)

- **Thành viên**: Trung
- **Vai trò chính**: Nhóm trưởng / PM + Agent & tích hợp
- **Tuần 1**: Kickoff, Charter, chốt schema; điều phối daily; bắt đầu báo cáo Tuần 1. Taxonomy US_49.
- **Tuần 2**: Chốt độ đo + ngưỡng; chủ trì chấm điểm chọn model; tổng hợp báo cáo + slide Tuần 2; chốt kiến trúc Tuần 3.
- **Tuần 3**: Router + tool calling; (stretch) đa lượt; chọn cải tiến theo lỗi baseline; duyệt và tổng hợp báo cáo cuối; diễn tập demo. Hiệu chỉnh τ.
- **Đầu ra bắt buộc**: Charter, schema, báo cáo T1/T2, router/agent
- **Lưu ý**: Dễ quá tải: ưu tiên review thay vì tự làm mọi thứ; stretch (US_39, US_42) là thứ đầu tiên bị cắt.

## User story mà Trung là Owner

### US_01 – Kickoff & chốt phạm vi (2.0 pt, Sprint 1, ưu tiên High)
- Muốn: chốt domain thời trang 4 nhóm (giày dép, quần áo, mũ, phụ kiện), 3 tính năng (visual search, product QA, tìm & so sánh) + nhánh trò chuyện/fallback Gemini và vai trò từng người
- Để: cả nhóm hiểu cùng một mục tiêu và không làm lan man
- Support: All
- DOCS (đầu ra): Project Charter 1 trang (mục tiêu, phạm vi, vai trò, mốc)
- TEST (nghiệm thu): Mỗi thành viên nói lại được mục tiêu, phạm vi và vai trò của mình trong 2 phút

### US_03 – Họp daily 15' + review cuối tuần (1.0 pt, Sprint 1, ưu tiên Medium)
- Muốn: họp nhanh mỗi ngày (hôm qua làm gì / hôm nay làm gì / đang vướng gì) và review demo cuối tuần
- Để: phát hiện blocker sớm
- Support: All
- DOCS (đầu ra): Biên bản họp (1 dòng/người/ngày) trong Notion hoặc Google Sheet
- TEST (nghiệm thu): Có biên bản cho ít nhất 90% số ngày làm việc

### US_05 – Chốt schema dữ liệu sản phẩm chuẩn (2.0 pt, Sprint 1, ưu tiên High)
- Muốn: định nghĩa schema chung (product_id, title, category, brand, price, colors, sizes, description, specs, image_paths, rating, reviews, source, license, product_type, sub_category, gender, size_system, view_type, variant_id)
- Để: mọi nguồn dữ liệu được quy về cùng một định dạng
- Support: Hoàng
- DOCS (đầu ra): schema.md + JSON schema
- TEST (nghiệm thu): Mọi nguồn map được vào schema; các trường bắt buộc được xác định rõ

### US_18 – Chốt bộ độ đo của nhóm + lý do + ngưỡng mục tiêu (2.0 pt, Sprint 2, ưu tiên High)
- Muốn: chọn độ đo chính/phụ và đặt ngưỡng mục tiêu dựa trên baseline
- Để: mọi cải tiến sau này được đánh giá bằng cùng một thước đo
- Support: Khoa
- DOCS (đầu ra): Sheet '2_Độ đo' - cột Nhóm chọn + bảng ngưỡng
- TEST (nghiệm thu): Mỗi độ đo được chọn có ít nhất 1 lý do gắn với mục tiêu sản phẩm

### US_25 – So sánh & chọn phiên bản bằng bảng chấm điểm có trọng số (3.0 pt, Sprint 2, ưu tiên High)
- Muốn: chấm điểm các ứng viên theo tiêu chí có trọng số (độ chính xác, tốc độ, tài nguyên, phù hợp miền, license, dễ tích hợp)
- Để: quyết định chọn model minh bạch và bảo vệ được trước thầy
- Support: Khoa
- DOCS (đầu ra): Sheet '3_Khảo sát phiên bản' - Bảng F
- TEST (nghiệm thu): Mỗi điểm số có số liệu thực nghiệm đi kèm

### US_26 – Báo cáo mốc Tuần 1 (dữ liệu) (3.0 pt, Sprint 1, ưu tiên High)
- Muốn: tổng hợp phương pháp thu thập, lý do chọn, kết quả thu thập thành một báo cáo ngắn
- Để: có thể báo cáo thầy sớm và nhận phản hồi
- Support: Tuấn Đạt
- DOCS (đầu ra): report_week1.docx (5-8 trang)
- TEST (nghiệm thu): Có đủ 3 mục: phương pháp, lý do chọn, kết quả (nguồn, phân loại, đặc điểm)

### US_27 – Báo cáo + slide mốc 2 tuần (dữ liệu, độ đo, khảo sát) (5.0 pt, Sprint 2, ưu tiên High)
- Muốn: tổng hợp 3 yêu cầu của thầy thành báo cáo và slide
- Để: trình bày với thầy cuối Tuần 2
- Support: All
- DOCS (đầu ra): report_week2.docx + slide 15-20 trang
- TEST (nghiệm thu): Trả lời đủ 3 yêu cầu của thầy; mỗi kết luận có số liệu hoặc bảng đi kèm

### US_40 – Thiết kế kiến trúc & API contract cho demo (3.0 pt, Sprint 2, ưu tiên High)
- Muốn: vẽ kiến trúc (UI - API - Agent router - [công cụ nội bộ | nhánh Gemini + cache] - dữ liệu) và chốt định dạng request/response của từng endpoint; request/response có route, confidence, source
- Để: Tuần 3 mọi người code song song mà không vướng nhau
- Support: Hoàng
- DOCS (đầu ra): architecture.md + openapi/mô tả endpoint
- TEST (nghiệm thu): Mỗi endpoint có ví dụ request/response; cả nhóm đọc và đồng ý; có sơ đồ quyết định route + ngưỡng τ mặc định

### US_41 – Agent tự nhận biết ý định và gọi đúng công cụ (8.0 pt, Sprint 3, ưu tiên High)
- Muốn: gửi ảnh, câu hỏi, yêu cầu tìm hoặc so sánh trong cùng một khung chat và được xử lý đúng, kể cả câu chitchat/ngoài phạm vi (chuyển Gemini)
- Để: không phải chọn chức năng thủ công
- Support: Hoàng
- DOCS (đầu ra): router + tool calling + fallback hỏi lại + nhánh Gemini
- TEST (nghiệm thu): Route accuracy ≥ 90% trên eval_router (≥ 60 câu, ≥ 15 chitchat/ngoài phạm vi); hỏi lại + chuyển Gemini khi không chắc

### US_42 – Hội thoại nhiều lượt có nhớ ngữ cảnh (stretch) (5.0 pt, Sprint 3, ưu tiên Low)
- Muốn: nói 'so sánh đôi vừa tìm với đôi thứ 2' mà không phải lặp lại thông tin
- Để: trò chuyện tự nhiên
- Support: Chiến
- DOCS (đầu ra): session memory
- TEST (nghiệm thu): 9/10 kịch bản đa lượt đúng

### US_47 – Diễn tập demo + video dự phòng + gắn tag release (3.0 pt, Sprint 3, ưu tiên High)
- Muốn: chạy trọn kịch bản demo 2 lần và quay video dự phòng
- Để: không bị bất ngờ khi trình bày
- Support: All
- DOCS (đầu ra): demo_script.md, video, git tag v1.0
- TEST (nghiệm thu): Chạy trọn kịch bản 2 lần liên tiếp không lỗi

### US_49 – Chốt taxonomy 2 cấp & bảng map category giữa các nguồn (2.0 pt, Sprint 1, ưu tiên High)
- Muốn: định nghĩa cây product_type -> sub_category và bảng map nhãn từng nguồn về cây đó (kèm quy tắc cho ca mơ hồ như khăn, áo khoác mũ trùm)
- Để: tránh gán nhãn lệch giữa các nguồn và tránh nhầm nhóm khi tìm kiếm ảnh
- Support: Khoa
- DOCS (đầu ra): taxonomy.md + category_map.csv
- TEST (nghiệm thu): Mọi nhãn nguồn map được hoặc vào 'unknown'; kiểm 30 mẫu/nguồn sai ≤ 3; Khoa và Hoàng đọc và đồng ý


## User story mà Trung là Support

- US_01 – Kickoff & chốt phạm vi (Owner: Trung)
- US_02 – Dựng repo, môi trường, quy ước code (Owner: Hoàng)
- US_03 – Họp daily 15' + review cuối tuần (Owner: Trung)
- US_10 – Tổng hợp nguồn & đánh giá tính chính thống (Owner: Tuấn Đạt)
- US_12 – Khảo sát độ đo cho Visual Search (Owner: Khoa)
- US_14 – Khảo sát độ đo cho Tìm/So sánh & Agent (Owner: Chiến)
- US_20 – Khảo sát text-embedding & LLM cho RAG tiếng Việt (Owner: Chiến)
- US_27 – Báo cáo + slide mốc 2 tuần (dữ liệu, độ đo, khảo sát) (Owner: Trung)
- US_28 – Báo cáo cuối + kịch bản demo Đồ án 1 (Owner: Tuấn Đạt)
- US_34 – Hỏi đáp về sản phẩm bằng tiếng Việt (Owner: Chiến)
- US_37 – Tìm sản phẩm bằng văn bản + bộ lọc (loại, màu, giá, size) (Owner: Hoàng)
- US_38 – So sánh 2-3 sản phẩm theo bảng thuộc tính (Owner: Hoàng)
- US_43 – Giao diện demo đơn giản (Gradio/Streamlit): upload ảnh + chat (Owner: Tuấn Đạt)
- US_45 – Thực hiện ít nhất 4 cải tiến ưu tiên cao & đo trước/sau (Owner: Khoa)
- US_46 – Kiểm thử 15-20 kịch bản & sửa lỗi (Owner: Tuấn Đạt)
- US_47 – Diễn tập demo + video dự phòng + gắn tag release (Owner: Trung)

## Lịch theo ngày của Trung

- N1 (05/11): US_01: Họp kickoff, chốt domain (giày dép, phụ kiện, quần áo, mũ), 3 tính năng, chia vai trò. Tạo Project Charter, nhập Backlog vào Google Sheet. Chốt vai trò Gemini (fallback, không thay RAG).
- N2 (06/11): US_05: Cùng Hoàng chốt schema sản phẩm chuẩn (schema.md). Duyệt nháp bảng phương pháp của Đạt.
- N3 (07/11): Họp chốt phương pháp chính thức (public làm chính + crawl bổ sung + tự chụp + synthetic QA). Rà schema với dữ liệu thật; gỡ blocker. US_49: chốt taxonomy + category_map.csv (Khoa review).
- N4 (08/11): Kiểm tra tiến độ; bắt đầu dàn ý báo cáo Tuần 1 (US_26).
- N5 (09/11): Chủ trì họp review tuần 1 (demo dữ liệu từng người, 45'). US_26: dựng khung báo cáo Tuần 1.
- N6 (10/11): US_26: Viết báo cáo Tuần 1 (3 mục: phương pháp, lý do chọn, kết quả).
- N7 (11/11): US_26: Chốt báo cáo Tuần 1, gửi thầy nếu thầy muốn xem sớm. Họp online 30' kiểm tra việc trễ.
- N8 (12/11): Họp phân việc Tuần 2; rà soát danh sách độ đo mà Khoa, Chiến khảo sát; hỗ trợ US_14.
- N9 (13/11): Chốt định dạng eval_qa; rà soát mẫu eval_visual; hỗ trợ viết câu hỏi.
- N10 (14/11): Rà soát 20% mẫu của eval sets (kiểm tra ground truth có sai không). Bắt đầu khung báo cáo Tuần 2.
- N11 (15/11): US_18: Chốt bộ độ đo chính/phụ + ngưỡng mục tiêu dựa trên kết quả vòng 1 (Sheet 2, Bảng B).
- N12 (16/11): US_25: Chủ trì họp chấm điểm có trọng số để chọn phiên bản (Sheet 3, Bảng F). US_27: tổng hợp báo cáo Tuần 2.
- N13 (17/11): US_27: Tổng hợp báo cáo + slide. US_40: nháp kiến trúc demo cho Tuần 3.
- N14 (18/11): US_27: Chốt báo cáo; họp tập thuyết trình 30'. US_40: Chốt architecture.md + API contract (cả nhóm đọc). architecture.md có nhánh Gemini + ngưỡng τ mặc định.
- N15 (19/11): Họp kickoff Sprint 3; duyệt API contract. US_41: viết Router v0 (rule-based theo ảnh/từ khoá).
- N16 (20/11): US_41: Router + LLM tool calling gọi các công cụ. Router + nhánh Gemini.
- N17 (21/11): US_41: Nối Router với đủ 4 công cụ. US_42 (stretch): bắt đầu bộ nhớ hội thoại.
- N18 (22/11): Chọn cải tiến ưu tiên theo lỗi baseline (sheet 'Cải tiến T3'); US_42 (stretch): hoàn thiện bộ nhớ hội thoại. I17: hiệu chỉnh τ.
- N19 (23/11): US_45: Chạy lại đánh giá toàn bộ (sau cải tiến), điền sheet 'Cải tiến T3', quyết định giữ/bỏ. Tuyên bố feature freeze 17:00.
- N20 (24/11): US_28: Review và tổng hợp báo cáo cuối. US_47: Soạn demo_script.md (5 kịch bản).
- N21 (25/11): US_47: Diễn tập trọn kịch bản 2 lần; gắn git tag v1.0; nộp.