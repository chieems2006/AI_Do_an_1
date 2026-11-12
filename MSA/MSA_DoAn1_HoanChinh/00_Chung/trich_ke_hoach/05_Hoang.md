# Phần việc của Hoàng (trích tự động từ MSA_PLAN_v2.xlsx)

## Vai trò (sheet Phân công)

- **Thành viên**: Hoàng
- **Vai trò chính**: Python: data pipeline & backend
- **Tuần 1**: Repo + môi trường; tải & chuẩn hoá dataset public; gộp Data v1. Quần áo/mũ US_48.
- **Tuần 2**: metrics.py + run_eval.py; benchmark text-embedding; chạy lại mọi benchmark >= 3 lần; khung FastAPI. llm_gateway Gemini US_50.
- **Tuần 3**: API /search/image, /search/text, /compare; validate ảnh; metadata filter + re-rank; đóng gói chạy 1 lệnh; (stretch) gợi ý nên chọn.
- **Đầu ra bắt buộc**: Repo, script pipeline, metrics, API backend
- **Lưu ý**: Là xương sống kỹ thuật: bất kỳ thay đổi schema/API phải thông báo cả nhóm.

## User story mà Hoàng là Owner

### US_02 – Dựng repo, môi trường, quy ước code (2.0 pt, Sprint 1, ưu tiên High)
- Muốn: có GitLab repo chung, cấu trúc thư mục, requirements/conda env, quy ước branch & commit
- Để: mọi người chạy code giống nhau trên máy mình
- Support: Trung
- DOCS (đầu ra): README.md, requirements.txt, cấu trúc thư mục data/ src/ eval/ app/ notebooks/
- TEST (nghiệm thu): Người mới clone repo chạy được script kiểm tra môi trường trong dưới 10 phút

### US_06 – Tải & chuẩn hoá dataset công khai (ảnh + metadata) (5.0 pt, Sprint 1, ưu tiên High)
- Muốn: tải các dataset public (ví dụ Fashion Product Images, Amazon Berkeley Objects, Amazon Reviews 2023 - mục Clothing/Shoes) và chuyển nhóm giày dép + phụ kiện về schema chuẩn (quần áo + mũ: xem US_48)
- Để: có dữ liệu nền từ nguồn chính thống, có license rõ ràng
- Support: Tuấn Đạt
- DOCS (đầu ra): script 01_download_public.py, log nguồn + license
- TEST (nghiệm thu): ≥ 1.700 SP giày + phụ kiện (ảnh + metadata); chạy lại script cho cùng kết quả.

### US_17 – Viết script đánh giá tự động (metrics.py, run_eval.py) (3.0 pt, Sprint 2, ưu tiên High)
- Muốn: tính Recall@K, MRR, NDCG, Hit@K, F1, latency chỉ với một lệnh
- Để: chạy lại benchmark nhanh và nhất quán
- Support: Khoa
- DOCS (đầu ra): eval/metrics.py, eval/run_eval.py, unit test
- TEST (nghiệm thu): Unit test trên dữ liệu giả cho kết quả khớp với tính tay

### US_23 – Benchmark text-embedding cho RAG (ít nhất 3 model) (5.0 pt, Sprint 2, ưu tiên High)
- Muốn: chạy các text-embedding đa ngôn ngữ trên eval_qa để đo Hit@1/5 và MRR của khâu retrieval
- Để: chọn embedding tốt nhất cho tiếng Việt
- Support: Chiến
- DOCS (đầu ra): Sheet '3_Khảo sát phiên bản' - Bảng C (cột kết quả)
- TEST (nghiệm thu): Cùng chunking, cùng top-K cho mọi model; ghi lại cấu hình

### US_30 – Tìm sản phẩm tương tự bằng ảnh tải lên (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: tải ảnh một món đồ (giày, áo/quần, mũ, phụ kiện) và nhận Top-5/Top-10 sản phẩm tương tự cùng nhóm
- Để: tìm nhanh sản phẩm giống món mình đang thấy
- Support: Khoa
- DOCS (đầu ra): API /search/image
- TEST (nghiệm thu): Recall@5 đạt ngưỡng mục tiêu trên test set; thời gian phản hồi dưới 1,5 giây; cross-type error@5 ≤ 10%

### US_32 – Xử lý ảnh đầu vào không hợp lệ (2.0 pt, Sprint 3, ưu tiên Medium)
- Muốn: nhận thông báo rõ ràng khi ảnh sai định dạng, quá lớn hoặc không phải sản phẩm
- Để: không bị lỗi im lặng hay treo
- Support: Tuấn Đạt
- DOCS (đầu ra): module validation ảnh
- TEST (nghiệm thu): 10 tình huống lỗi đều trả thông báo đúng, không crash

### US_37 – Tìm sản phẩm bằng văn bản + bộ lọc (loại, màu, giá, size) (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: gõ mô tả và lọc theo loại/màu/giá/size
- Để: thu hẹp danh sách theo nhu cầu
- Support: Trung
- DOCS (đầu ra): API /search/text
- TEST (nghiệm thu): Bộ lọc cho kết quả đúng trên 15 truy vấn thử

### US_38 – So sánh 2-3 sản phẩm theo bảng thuộc tính (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: chọn 2-3 sản phẩm và nhận bảng so sánh (giá, chất liệu, màu, size, rating, ưu/nhược)
- Để: thấy khác biệt chính trong một màn hình
- Support: Trung
- DOCS (đầu ra): API /compare + bảng so sánh
- TEST (nghiệm thu): Thuộc tính trong bảng trùng 100% với dữ liệu gốc trên 20 cặp thử

### US_39 – Gợi ý 'nên chọn cái nào' theo nhu cầu (stretch) (3.0 pt, Sprint 3, ưu tiên Low)
- Muốn: nói nhu cầu (đi bộ nhiều, ngân sách...) và nhận gợi ý dựa trên bảng so sánh
- Để: ra quyết định nhanh hơn
- Support: Chiến
- DOCS (đầu ra): prompt diễn giải trên bảng đã có
- TEST (nghiệm thu): LLM chỉ dùng thông số có trong bảng; không bịa thuộc tính

### US_48 – Mở rộng dữ liệu: Quần áo & Mũ (3.0 pt, Sprint 1, ưu tiên High)
- Muốn: tải/lọc các nguồn public cho quần áo và mũ (Fashion Product Images, Amazon Reviews 2023 - Clothing, Clothing Dataset CC0; DeepFashion nếu được cấp quyền), map về schema chuẩn kèm product_type/size_system; bổ sung mũ từ nhiều nguồn nếu thiếu quota
- Để: có đủ dữ liệu cho 2 nhóm mới mà không làm trễ mốc Data v1 (N5)
- Support: Tuấn Đạt
- DOCS (đầu ra): script 01b_download_clothing_hats.py + log nguồn/license + bảng đếm theo nhóm
- TEST (nghiệm thu): ≥ 2.300 SP (quần áo ≥ 2.000, mũ ≥ 300) có ảnh + metadata; mọi nguồn có license ghi lại; nếu mũ < 300 phải ghi quyết định (bổ sung từ crawl/tự chụp hoặc hạ chỉ tiêu)

### US_50 – Dựng LLM Gateway cho Gemini (cấu hình model, timeout, retry, cache cơ bản) (3.0 pt, Sprint 2, ưu tiên High)
- Muốn: có một module gọi Gemini dùng chung: đọc key và tên model từ biến môi trường, timeout, retry/backoff khi 429, cache exact-match, log token/latency
- Để: mọi nhánh (fallback, chitchat, benchmark US_24) gọi Gemini nhất quán và demo không sập khi API lỗi
- Support: Tuấn Đạt
- DOCS (đầu ra): llm_gateway.py + .env.example + README mục Gemini
- TEST (nghiệm thu): Gọi thành công 10 request mẫu; giả lập 429/timeout trả thông điệp dự phòng không crash; key không nằm trong repo; đổi model chỉ bằng biến môi trường


## User story mà Hoàng là Support

- US_01 – Kickoff & chốt phạm vi (Owner: Trung)
- US_03 – Họp daily 15' + review cuối tuần (Owner: Trung)
- US_05 – Chốt schema dữ liệu sản phẩm chuẩn (Owner: Trung)
- US_07 – Crawl bổ sung dữ liệu sàn TMĐT Việt Nam (quy mô nhỏ) (Owner: Chiến)
- US_08 – Làm sạch, khử trùng lặp, phân loại dữ liệu (Owner: Tuấn Đạt)
- US_19 – Khảo sát các phiên bản embedding ảnh (CLIP / SigLIP / FashionCLIP / DINOv2...) (Owner: Khoa)
- US_22 – Benchmark embedding ảnh: ít nhất 5 phiên bản (Owner: Khoa)
- US_27 – Báo cáo + slide mốc 2 tuần (dữ liệu, độ đo, khảo sát) (Owner: Trung)
- US_29 – Trích embedding & build FAISS index toàn danh mục (Owner: Khoa)
- US_31 – Hiển thị kết quả kèm ảnh, giá, độ tương đồng, link (Owner: Tuấn Đạt)
- US_40 – Thiết kế kiến trúc & API contract cho demo (Owner: Trung)
- US_41 – Agent tự nhận biết ý định và gọi đúng công cụ (Owner: Trung)
- US_45 – Thực hiện ít nhất 4 cải tiến ưu tiên cao & đo trước/sau (Owner: Khoa)
- US_46 – Kiểm thử 15-20 kịch bản & sửa lỗi (Owner: Tuấn Đạt)
- US_47 – Diễn tập demo + video dự phòng + gắn tag release (Owner: Trung)
- US_51 – Trò chuyện tự nhiên: Gemini xử lý chitchat, ngoài phạm vi, câu khó & fallback khi nội bộ không tự tin (Owner: Chiến)

## Lịch theo ngày của Hoàng

- N1 (05/11): US_02: Tạo GitLab repo, môi trường, cấu trúc thư mục, requirements; hướng dẫn cả nhóm cài đặt.
- N2 (06/11): US_06: Tìm và đánh giá dataset public (kích thước, license, có ảnh + metadata không); tải thử 1 dataset. US_02: hoàn tất README.
- N3 (07/11): US_06: Tải dataset chính, lọc 4 nhóm (giày dép, phụ kiện, quần áo, mũ), convert về schema. Bắt đầu US_48.
- N4 (08/11): US_06: Hoàn tất dataset public v1 (>= 4.000 SP, đủ quota 4 nhóm); script chạy lại được.
- N5 (09/11): Gộp public + crawl thành Data v1, đặt tag version; kiểm tra schema hợp lệ 100%.
- N6 (10/11): Dự phòng: sửa lỗi dữ liệu phát hiện ở EDA; thử embed 500 ảnh để kiểm tra pipeline.
- N7 (11/11): Nghỉ (hoặc bù việc trễ).
- N8 (12/11): US_17: Bắt đầu viết eval/metrics.py (Recall@K, MRR, NDCG, Hit@K, F1).
- N9 (13/11): US_17: Hoàn tất metrics.py + unit test với dữ liệu giả.
- N10 (14/11): US_23: Benchmark text-embedding trên eval_qa (Hit@K, MRR). Dựng FAISS Flat cho từng model ảnh; hỗ trợ Khoa đo latency.
- N11 (15/11): US_23: Chạy lại mọi benchmark >= 3 lần (latency lấy median), xuất CSV, vẽ biểu đồ.
- N12 (16/11): Viết phần dữ liệu cho báo cáo, hoàn tất biểu đồ, chuẩn bị hình cho slide.
- N13 (17/11): Kiểm lại toàn bộ số liệu; chạy lại nếu có chỗ nghi ngờ.
- N14 (18/11): Dựng sẵn khung FastAPI trống (health check) để Tuần 3 vào code ngay. US_50: llm_gateway (bọc hàm gọi Gemini của Đạt: timeout/retry/cache).
- N15 (19/11): US_30: FastAPI skeleton, load index, endpoint /search/image bản stub.
- N16 (20/11): US_30: Hoàn tất /search/image. US_37: Bắt đầu /search/text + bộ lọc.
- N17 (21/11): US_37: Hoàn tất /search/text. US_38: /compare. US_32: validate ảnh upload; ghi log JSON mỗi request.
- N18 (22/11): US_38 + US_32: Hoàn tất. US_45: Metadata filter + re-rank kết hợp điểm ảnh/text; cache (I11 + I15). US_39 (stretch) nếu còn thời gian.
- N19 (23/11): Sửa bug API; đóng gói chạy 1 lệnh (script hoặc Docker); cập nhật README.
- N20 (24/11): Cài đặt thử trên 1 máy sạch bằng README để chắc chắn chạy được.
- N21 (25/11): Trực kỹ thuật: xử lý sự cố khi demo.