# US_12 – Khảo sát độ đo cho Visual Search

| Mục | Nội dung |
|---|---|
| Mã US | US_12 (Owner: Khoa, Support: Trung) – Sprint 2, 3.0 pt |
| Mục tiêu | Chọn bộ độ đo phù hợp mục tiêu sản phẩm "chụp/tải ảnh → thấy món mình muốn trong vài kết quả đầu" |
| Đầu ra | File này (nội dung cho Sheet `2_Độ đo` – phần Visual Search) + cài đặt `src/msa/eval/visual_metrics.py` (có test `tests/test_metrics.py`) |
| Tiêu chí nghiệm thu | Mỗi độ đo có công thức, ưu/nhược và quyết định chọn/không chọn |
| Trạng thái | **Hoàn thành** (đã dùng để đo thật trong US_22) |

## Tóm tắt 5 dòng
1. Khảo sát 9 độ đo visual search, mỗi độ đo có công thức, ưu/nhược, quyết định chọn/không chọn.
2. Chọn chính: macro Recall@5 (theo 4 nhóm), MRR@10, Cross-type error@5, latency p50/p95.
3. Không chọn mAP (khó giải thích, cần ground truth đầy đủ); NDCG, P@5 làm phụ; AUROC dùng để chọn ngưỡng τ_v.
4. Vì sao: người dùng chỉ xem ~5 kết quả đầu; nhầm giày ↔ áo là lỗi khó chấp nhận nhất; nhóm mũ nhỏ không được bị nhóm áo che.
5. Ví dụ dễ hiểu từng độ đo: `00_Chung/THUAT_NGU.md` mục 2.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## 1. Ký hiệu
- Tập truy vấn \(Q\); với truy vấn \(q\): danh sách kết quả xếp hạng \(L_q = (d_1, d_2, …)\), tập SP đúng \(R_q\).
- \(\mathrm{rank}_q\) = hạng của SP đúng đầu tiên (∞ nếu không có).
- Hai tầng của eval_visual (US_15): **instance** (\(|R_q| = 1\) – đúng chính SP đó) và **category** (\(R_q\) = mọi SP cùng articleType + màu, trung vị 31 SP/truy vấn).

## 2. Bảng khảo sát

| Độ đo | Công thức | Ưu điểm | Nhược điểm | Quyết định | Lý do |
|---|---|---|---|---|---|
| **Recall@K** (= Hit@K khi \(|R_q|=1\)) | \(\frac{1}{|Q|}\sum_q \frac{|R_q \cap L_q[1..K]|}{|R_q|}\); K = 1, 5, 10 | Sát trải nghiệm "có thấy món mình trong K kết quả đầu"; dễ giải thích | Không phân biệt hạng 1 với hạng K | **CHÍNH** (Recall@5 là chỉ số chọn model) | Người dùng chỉ xem 5–10 kết quả đầu trên màn hình demo |
| **Hit@K** | \(\frac{1}{|Q|}\sum_q \mathbb{1}[R_q \cap L_q[1..K] \neq \emptyset]\) | Dùng được khi \(R_q\) lớn (tầng category) | Không nói danh sách "sạch" đến đâu | PHỤ (tầng category) | Với \(|R_q|\)≈31, Recall@5 ≤ 5/31 nên không đọc được; Hit@5 hợp lý hơn |
| **MRR@10** | \(\frac{1}{|Q|}\sum_q \frac{1}{\mathrm{rank}_q}\) (0 nếu rank > 10) | Thưởng SP đúng ở hạng cao; 1 con số | Chỉ xét SP đúng đầu tiên | **CHÍNH** | Bổ sung thông tin thứ hạng cho Recall@K |
| **Precision@K** | \(\frac{1}{|Q|}\sum_q \frac{|R_q \cap L_q[1..K]|}{K}\) | Đo "độ sạch" danh sách | Với \(|R_q|=1\) bị chặn trên 1/K | PHỤ – **chỉ tầng category** (P@5) | Tầng category có nhiều đáp án đúng nên P@5 có nghĩa |
| **mAP@K** | \(\frac{1}{|Q|}\sum_q \frac{1}{\min(|R_q|,K)}\sum_{i\le K} P@i \cdot \mathbb{1}[d_i\in R_q]\) | Chuẩn học thuật khi nhiều đáp án | Khó giải thích; cần GT đầy đủ | KHÔNG CHỌN (có cài đặt `average_precision`) | Tầng instance: AP = RR (trùng MRR); tầng category: GT theo articleType+màu chỉ là xấp xỉ "giống" nên AP dễ gây hiểu nhầm |
| **NDCG@10** | \(\mathrm{DCG}=\sum_{i\le K}\frac{rel_i}{\log_2(i+1)}\), chia IDCG | Hỗ trợ mức liên quan nhiều cấp | Cần nhãn mức liên quan (tốn công) | PHỤ (báo cáo nhị phân) | Chưa có nhãn nhiều cấp do người gán; với nhị phân & 1 đáp án, NDCG = \(1/\log_2(\mathrm{rank}+1)\) |
| **Cross-type error@5 (CTE@5)** | \(\frac{1}{|Q|}\sum_q \frac{|\{d\in L_q[1..5]: type(d)\neq type(q)\}|}{5}\) | Phát hiện nhầm giày/áo/mũ/phụ kiện – lỗi người dùng khó chấp nhận | Không đo giống kiểu dáng/màu | **CHÍNH** | Đề tài mở rộng 4 nhóm; cần cho I19 (type gate) |
| **Recall@5 theo nhóm + Macro Recall@5** | Recall@5 tính riêng 4 nhóm, macro = trung bình cộng | Không để nhóm lớn (quần áo 2.200 SP) che nhóm yếu (mũ 293) | Nhóm ít truy vấn → phương sai lớn | **CHÍNH** (macro Recall@5 là điểm chọn model) | Theo ghi chú Sheet 3 Bảng A2 |
| **SubP@5** (precision cùng sub_category) | tỉ lệ top-5 cùng sub_category với truy vấn | Đo "cùng loại" mà không cần cùng màu | Phụ thuộc taxonomy tạm (`*`) | PHỤ | Phân tích lỗi tầng category |
| **Category accuracy@1** | \(\mathbb{1}[type(d_1)=type(q)]\) | Đơn giản | Chỉ xét hạng 1 | PHỤ (dùng trong US_44 cho kịch bản category) | CTE@5 đã bao trùm |
| **Latency p50/p95** | thời gian embed 1 ảnh (batch 1) + FAISS search; ≥ 3 lần, lấy median và p95 | Quyết định demo có mượt | Phụ thuộc phần cứng & tải máy | **CHÍNH** | Mục tiêu P95 < 1.000 ms (không tính LLM) |
| **RAM / kích thước** | RSS sau khi nạp model, peak RSS; trọng số fp32 = số tham số × 4 B; index = N × D × 4 B | Quyết định chạy được trên máy demo | Đo RSS có nhiễu thư viện | PHỤ (cột của Bảng A) | Máy demo dự kiến CPU, RAM hạn chế |
| **AUROC trong/ngoài phạm vi theo top-1 cosine** | xác suất top-1 cosine của truy vấn trong phạm vi > truy vấn ngoài phạm vi | Hiệu chỉnh τ_v (khi nào nói "chưa thấy SP giống") | Cần tập OOD | PHỤ (bổ sung) | Hợp đồng chung yêu cầu τ_v; dùng ảnh thật Personal Care/Watches làm OOD |

## 3. Ví dụ tính tay (khớp test `tests/test_metrics.py`)

Truy vấn \(q\) (tầng instance, \(R_q=\{g\}\)), top-5 = `[x, y, g, u, v]`, loại tương ứng `[footwear, clothing, footwear, accessory, footwear]`, truy vấn là footwear.
- Recall@1 = 0; Recall@5 = 1; Recall@10 = 1.
- MRR = 1/3 ≈ 0,333.
- NDCG@10 = \(1/\log_2(3+1)\) = 0,5.
- Precision@5 = 1/5 = 0,2.
- CTE@5 = 2/5 = 0,4 (clothing và accessory sai nhóm).

Tầng category: \(R_q\) có 31 SP, top-5 có 3 SP thuộc \(R_q\) → Hit@5 = 1, P@5 = 0,6, Recall@5 = 3/31 ≈ 0,097 (khó đọc → không dùng).

## 4. Quyết định cho nhóm
1. **Chỉ số chọn model**: Macro Recall@5 (4 nhóm) trên tầng instance – split **test**; MRR@10 làm tiêu chí phụ khi chênh < 1 điểm.
2. **Ràng buộc chất lượng**: CTE@5 (càng thấp càng tốt), P@5 tầng category.
3. **Ràng buộc vận hành**: latency embed truy vấn p50/p95 (batch 1, CPU 2 luồng), RAM sau nạp model.
4. **Ngưỡng τ_v**: chọn trên split val (giữ ≥ 95 % truy vấn trong phạm vi), báo cáo tỉ lệ loại OOD trên test.
5. Ngưỡng mục tiêu ban đầu (Sheet 2 Bảng B): Recall@5 macro ≥ 0,8; MRR ≥ 0,6; latency P95 ≤ 1.000 ms – **lưu ý**: đo trên truy vấn tổng hợp từ ảnh studio 60×80, số đạt ngưỡng không có nghĩa đạt trên ảnh ngoài đời (CHƯA ĐO – thiếu ảnh).

Số đo thật: xem `docs/US_22_benchmark_embedding.md` và `results/bench_image_embed.csv`.
