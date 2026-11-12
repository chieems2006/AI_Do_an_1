# Phần việc của Khoa (trích tự động từ MSA_PLAN_v2.xlsx)

## Vai trò (sheet Phân công)

- **Thành viên**: Khoa
- **Vai trò chính**: ML: embedding ảnh, đánh giá, tối ưu
- **Tuần 1**: Khảo sát phiên bản embedding ảnh; khảo sát hệ thống tương tự; EDA; dựng khung benchmark.
- **Tuần 2**: Độ đo Visual Search; eval_visual (200 query); benchmark >= 5 phiên bản embedding ảnh.
- **Tuần 3**: Build FAISS index; baseline end-to-end; cải tiến visual (crop, TTA, adapter); đo lại sau cải tiến.
- **Đầu ra bắt buộc**: Sheet 3 Bảng A, eval_visual, index, kết quả cải tiến visual
- **Lưu ý**: Là người cầm 'số liệu quyết định' của cả đề tài; luôn lưu config (model, seed, version dữ liệu) cho mỗi lần chạy.

## User story mà Khoa là Owner

### US_09 – EDA & mô tả đặc điểm dữ liệu (3.0 pt, Sprint 1, ưu tiên High)
- Muốn: thống kê số lượng, phân bố category, kích thước ảnh, độ dài mô tả, phân bố rating, ngôn ngữ, mức độ nhiễu
- Để: mô tả được đặc điểm dữ liệu bằng số liệu trong báo cáo
- Support: Tuấn Đạt
- DOCS (đầu ra): notebook EDA + ít nhất 6 biểu đồ
- TEST (nghiệm thu): Báo cáo có số liệu cụ thể cho từng nguồn dữ liệu

### US_12 – Khảo sát độ đo cho Visual Search (3.0 pt, Sprint 2, ưu tiên High)
- Muốn: liệt kê Recall@K, Precision@K, mAP, MRR, NDCG@K, latency và phân tích ưu/nhược
- Để: chọn độ đo phù hợp mục tiêu sản phẩm
- Support: Trung
- DOCS (đầu ra): Sheet '2_Độ đo' - phần Visual Search
- TEST (nghiệm thu): Mỗi độ đo có công thức, ưu/nhược và quyết định chọn/không chọn

### US_15 – Xây bộ đánh giá Visual Search (query + ground truth) (5.0 pt, Sprint 2, ưu tiên High)
- Muốn: tạo ít nhất 200 query (ảnh studio khác góc + ảnh ngoài đời) kèm product_id đúng; phân tầng 4 nhóm (mỗi nhóm ≥ 30 query ở tập test), ≥ 20 query dễ nhầm giữa nhóm
- Để: đo được Recall@K và MRR một cách khách quan
- Support: Chiến
- DOCS (đầu ra): eval_visual.csv + mô tả cách tạo
- TEST (nghiệm thu): Có ít nhất 200 query; chia val/test; query không nằm trong dữ liệu fine-tune (nếu có); đáp án có thêm cột product_type

### US_19 – Khảo sát các phiên bản embedding ảnh (CLIP / SigLIP / FashionCLIP / DINOv2...) (3.0 pt, Sprint 1, ưu tiên High)
- Muốn: liệt kê model, năm, kiến trúc, số chiều embedding, điểm mạnh/yếu
- Để: chọn được danh sách ứng viên có cơ sở để benchmark
- Support: Hoàng
- DOCS (đầu ra): Sheet '3_Khảo sát phiên bản' - Bảng A
- TEST (nghiệm thu): Có ít nhất 6 phiên bản, mỗi phiên bản có lý do đưa vào so sánh

### US_21 – Khảo sát hệ thống & bài báo tương tự (2.0 pt, Sprint 1, ưu tiên Medium)
- Muốn: tìm hiểu Google Lens, Pinterest Lens, Shopee image search, Amazon Rufus và các bài báo nền tảng (CLIP, RAG, Visual Search at Pinterest/eBay/Alibaba)
- Để: học kiến trúc và bài học đã có thay vì tự mò
- Support: Chiến
- DOCS (đầu ra): Sheet '3_Khảo sát phiên bản' - Bảng E
- TEST (nghiệm thu): Mỗi hệ thống/bài báo có 'điểm đáng học' và 'liên hệ đồ án'

### US_22 – Benchmark embedding ảnh: ít nhất 5 phiên bản (8.0 pt, Sprint 2, ưu tiên High)
- Muốn: chạy ResNet-50, CLIP B/32, CLIP B/16, SigLIP, FashionCLIP (và DINOv2 nếu kịp) trên cùng eval_visual, đo Recall@1/5/10, MRR, latency, RAM; báo cáo Recall@5 theo nhóm + cross-type error@5 + có/không type gate cho 2 model dẫn đầu
- Để: chọn model dựa trên số liệu thay vì cảm tính
- Support: Hoàng
- DOCS (đầu ra): Sheet '3_Khảo sát phiên bản' - Bảng A (cột kết quả) + notebook
- TEST (nghiệm thu): Mọi model dùng cùng tiền xử lý và cùng FAISS Flat; latency đo ít nhất 3 lần lấy median

### US_29 – Trích embedding & build FAISS index toàn danh mục (5.0 pt, Sprint 3, ưu tiên High)
- Muốn: embed toàn bộ ảnh bằng model đã chọn và lưu embedding + FAISS index
- Để: tìm kiếm ảnh nhanh khi demo
- Support: Hoàng
- DOCS (đầu ra): build_index.py, file index
- TEST (nghiệm thu): Build index dưới 30 phút cho ít nhất 3.000 sản phẩm; truy vấn dưới 200ms (không tính tải ảnh)

### US_44 – Đo baseline hệ thống end-to-end (3.0 pt, Sprint 3, ưu tiên High)
- Muốn: chạy 60 kịch bản (≥ 10 chitchat/ngoài phạm vi) và ghi Task Success Rate, latency, danh sách lỗi
- Để: biết cải tiến nào đáng làm nhất
- Support: Chiến
- DOCS (đầu ra): baseline_report.md
- TEST (nghiệm thu): Có bảng số liệu baseline và top 10 lỗi phổ biến; bảng route: tỉ lệ chuyển Gemini, chi phí/100 lượt

### US_45 – Thực hiện ít nhất 4 cải tiến ưu tiên cao & đo trước/sau (8.0 pt, Sprint 3, ưu tiên High)
- Muốn: chọn các cải tiến từ sheet 'Cải tiến T3' và đo trước/sau trên cùng bộ test; ít nhất 4 cải tiến High, trong đó ≥ 1 thuộc nhóm Gemini (I15 hoặc I16) và ≥ 1 thuộc nhóm đa domain (I19)
- Để: tăng tỉ lệ thành công của hệ thống
- Support: All
- DOCS (đầu ra): Sheet 'Cải tiến T3' có số liệu
- TEST (nghiệm thu): Mỗi cải tiến có số baseline và số sau; chỉ giữ lại nếu cải thiện rõ


## User story mà Khoa là Support

- US_01 – Kickoff & chốt phạm vi (Owner: Trung)
- US_03 – Họp daily 15' + review cuối tuần (Owner: Trung)
- US_13 – Khảo sát độ đo cho Product QA / RAG (Owner: Chiến)
- US_17 – Viết script đánh giá tự động (metrics.py, run_eval.py) (Owner: Hoàng)
- US_18 – Chốt bộ độ đo của nhóm + lý do + ngưỡng mục tiêu (Owner: Trung)
- US_25 – So sánh & chọn phiên bản bằng bảng chấm điểm có trọng số (Owner: Trung)
- US_27 – Báo cáo + slide mốc 2 tuần (dữ liệu, độ đo, khảo sát) (Owner: Trung)
- US_30 – Tìm sản phẩm tương tự bằng ảnh tải lên (Owner: Hoàng)
- US_45 – Thực hiện ít nhất 4 cải tiến ưu tiên cao & đo trước/sau (Owner: Khoa)
- US_46 – Kiểm thử 15-20 kịch bản & sửa lỗi (Owner: Tuấn Đạt)
- US_47 – Diễn tập demo + video dự phòng + gắn tag release (Owner: Trung)
- US_49 – Chốt taxonomy 2 cấp & bảng map category giữa các nguồn (Owner: Trung)

## Lịch theo ngày của Khoa

- N1 (05/11): US_19: Đọc paper CLIP, chạy thử CLIP trên ~20 ảnh giày, xem embedding và cosine similarity hoạt động thế nào.
- N2 (06/11): US_19: Lập bảng các phiên bản embedding ảnh (CLIP B/32, B/16, L/14, OpenCLIP, SigLIP, FashionCLIP...).
- N3 (07/11): US_19: Khảo sát DINOv2, ResNet-50 (baseline), M-CLIP; viết khung code embed ảnh dùng lại cho benchmark Tuần 2.
- N4 (08/11): US_19: Hoàn tất bảng khảo sát. US_21: Bắt đầu đọc các bài báo/hệ thống tương tự.
- N5 (09/11): US_21: Hoàn tất khảo sát hệ thống/bài báo. US_09: bắt đầu EDA.
- N6 (10/11): US_09: Hoàn tất EDA: >= 6 biểu đồ, số liệu từng nguồn (Sheet 1, Mục D).
- N7 (11/11): Nghỉ (hoặc bù việc trễ).
- N8 (12/11): US_12: Khảo sát độ đo Visual Search (Recall@K, mAP, MRR, NDCG, latency); thiết kế định dạng eval_visual.
- N9 (13/11): US_15: Xây eval_visual (>= 200 query + product_id đúng; chia val/test). Phân tầng 4 nhóm.
- N10 (14/11): US_22: Benchmark embedding ảnh: ResNet-50, CLIP B/32, CLIP B/16 trên eval_visual.
- N11 (15/11): US_22: Benchmark SigLIP, FashionCLIP, DINOv2 (nếu kịp).
- N12 (16/11): Điền Sheet 3 Bảng A; viết phân tích vì sao model X hơn/kém Y + 10 ví dụ lỗi điển hình.
- N13 (17/11): Slide phần khảo sát/benchmark.
- N14 (18/11): Tập phần khảo sát; chuẩn bị sẵn script build index cho Tuần 3.
- N15 (19/11): US_29: Embed toàn bộ ảnh bằng model đã chọn, build FAISS index.
- N16 (20/11): US_29: Hoàn tất index; thêm tiền xử lý ảnh (resize/chuẩn hoá); hỗ trợ US_30 đạt Recall mục tiêu.
- N17 (21/11): US_44: Chạy 50 kịch bản baseline end-to-end cùng Chiến; ghi TSR, latency, top 10 lỗi.
- N18 (22/11): US_45: Cải tiến visual: crop/tách nền vật thể, TTA, hoặc adapter nhẹ nếu còn thời gian. I19: type gate.
- N19 (23/11): Đo lại Recall/MRR sau cải tiến; sửa bug visual.
- N20 (24/11): Chuẩn bị slide kết quả trước/sau cải tiến.
- N21 (25/11): Diễn tập phần visual search + số liệu.