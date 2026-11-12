# US_26 – Báo cáo mốc Tuần 1 (Dữ liệu) – khung + số liệu thật đã có

| Mục | Nội dung |
|---|---|
| Mã US | US_26 (Owner: Trung, Support: Tuấn Đạt) |
| Mục tiêu | Trả lời **Yêu cầu 1 của thầy**: phương pháp thu thập nào, vì sao chọn, kết quả (nguồn, tính chính thống, phân loại, đặc điểm) |
| Đầu ra | File này (bản markdown, chuyển sang `report_week1.docx` 5–8 trang khi chốt) |
| Tiêu chí nghiệm thu | Đủ 3 mục: phương pháp, lý do chọn, kết quả |
| Trạng thái | **Khung + số liệu thật** cho dữ liệu public & review VN. **CHƯA có**: crawl Tiki (bị chặn), 80–100 ảnh tự chụp, duyệt nhãn 2 người. Chưa xuất .docx |

Data version: `shared_data v1 (prep_shared_data.py seed 42)`; số theo nhóm lấy từ `shared_data/stats.json` và `results/taxonomy_coverage.json`.

## 1. Phương pháp thu thập
| Phương pháp | Dùng cho | Trạng thái thật |
|---|---|---|
| **Dataset công khai** (chính) | catalog ảnh + metadata 4 nhóm | Fashion Product Images (small) – HF `ashraq/fashion-product-images-small` (bản gốc Kaggle `paramaggarwal/fashion-product-images-dataset`): 44.072 dòng gốc → lấy **4.593 SP** phân tầng theo articleType (seed 42) |
| **Dataset review tiếng Việt công khai** (thay crawl) | RAG, hỏi đáp tiếng Việt | ViMRHP (NLDB 2025, HF `trucmtnguyen/ViMRHP`, **CC BY-NC-ND 4.0**): **509 SP Shopee + 11.009 review** tiếng Việt thật |
| Crawl sàn VN (bổ sung) | giá, size, mô tả tiếng Việt | **Không làm được**: Tiki trả 403 cho IP cloud; ảnh `*.susercontent.com` không truy cập được → kế hoạch B (R1) = ViMRHP |
| Ảnh tự chụp (80–100) | tập truy vấn ngoài đời | **CHƯA** – nhóm phải tự chụp (giày 25 / quần áo 25 / mũ 15 / phụ kiện 15) |
| Câu hỏi sinh bởi LLM + viết tay | eval_qa, eval_router | Có bản nháp (Chiến: eval_qa, eval_router 78 câu; Trung: seed 45 câu + 49 câu Gemini sinh) – **chưa người duyệt** |

## 2. Lý do chọn (và không chọn)
| Quyết định | Lý do |
|---|---|
| Public dataset làm chính | Tải ngay, có nhãn category sẵn làm ground truth, đủ 4 nhóm, tái lập được (seed) – phù hợp 3 tuần |
| ViMRHP thay crawl | Review tiếng Việt **thật** từ Shopee, có rating chi tiết; hợp pháp cho học thuật (CC BY-NC-ND – không phát hành lại bản chỉnh sửa); tránh rủi ro ToS/chặn IP |
| Không dùng DeepFashion/H&M | Phải xin quyền / quá nặng cho máy không GPU (R20) |
| Không crawl Tiki/Shopee | Bị chặn (403) + rủi ro điều khoản (R1) |

## 3. Kết quả (đo thật)
### 3.1 Số lượng theo nhóm – catalog sau taxonomy v1 (US_49)
> **Ghi chú Tác nhân 2:** bảng này là catalog **trước** làm sạch (4.586). Catalog dùng cho demo là **sau làm sạch 4.385 SP** (giày 1.400 / quần áo 2.000 – khử trùng 20 + cắt bớt 180 áo top để cân bằng nhóm (mục `cap` trong clean_report.json) / phụ kiện 700 / mũ 285) – `02_TuanDat/results/clean_report.json`. Vì sao có 4 con số mũ 293/286/285/298: `00_Chung/QUYET_DINH_CAN_CHOT.md` mục A.

| Nhóm | Quota tối thiểu | Có (taxonomy v1) | Đạt? | Lá |
|---|---|---|---|---|
| Giày dép | 1.200 | **1.400** | Đạt | sneaker 727, sandal 306, heel_flat 269, leather_shoe 95, **boot 3** |
| Quần áo | 2.000 | **2.200** | Đạt | top 1.721, bottom 355, dress 72, outerwear 52 |
| Phụ kiện | 500 | **700** | Đạt | bag 465, eyewear 135, belt 100 |
| Mũ | 300 | **286** (sau làm sạch: **285 – số chuẩn**) | **THIẾU 15** | taxonomy v1: cap 266, beanie 20; sau sửa 7 nhãn (QUYET_DINH mục A): cap 258, beanie 21, wide_brim 6; **bucket 0** |
| **Tổng** | 4.000–6.000 | **4.586** (+7 headband loại) | Đạt | |

ViMRHP sau taxonomy: giữ **349 SP** (+12 unknown), loại 148 (81 đồng hồ, trang sức/tất/…); **7.575 review** thuộc 349 SP có lá (tính cả 12 unknown: 7.833). Lệch mạnh: sandal 83, heel_flat 84, outerwear 76, top 74; gần như không có giày thể thao (2), mũ (5), túi (0).

### 3.2 Tính chính thống
| Nguồn | Tổ chức / công bố | License | Ghi chú |
|---|---|---|---|
| Fashion Product Images | Kaggle (P. Aggarwal), bản HF ashraq | `[cần xác minh]` (trang Kaggle ghi license riêng) | dữ liệu catalog Myntra (Ấn Độ) |
| ViMRHP | bài báo NLDB 2025 | CC BY-NC-ND 4.0 | chỉ dùng nội bộ học thuật |

### 3.3 Đặc điểm & hạn chế (phải nêu trong báo cáo)
1. **Ảnh FPI chỉ 60×80 px** (bản "small") – chi tiết hoạ tiết/logo mất; domain gap lớn với ảnh người dùng (R7).
2. Ảnh FPI là ảnh studio, nhiều ảnh quần áo là **người mẫu mặc cả bộ** (thấy giày, quần) → rủi ro nhầm nhóm (R17). Baseline CLIP B/32 của Khoa: cross-type error@5 = 0,076 (test).
3. **Thiếu mũ (285 < 300 sau làm sạch), không có boot thật (3 SP từ luật tiêu đề), không có bucket/beanie đủ** → nhóm mũ chỉ ở mức demo (thứ tự cắt scope 3).
4. **Không có giá, size, mô tả** ở cả hai nguồn → bộ lọc giá/size và câu hỏi giá phải trả lời "chưa có thông tin".
5. Thương hiệu FPI lấy từ chữ đầu tiêu đề (vd "United" cho United Colors of Benetton) – cần làm sạch.
6. Nhãn nguồn có nhiễu nhỏ (`Accessories/Belts/Tshirts`, tiêu đề "Shoe" cho sandal) – xử lý bằng taxonomy v1; kiểm 30 mẫu/nguồn: 0 sai (tác nhân AI kiểm, nhóm cần kiểm lại).
7. Làm sạch (Đạt, `02_TuanDat/results/clean_report.md`): khử trùng lặp −21, cap 800/lá −180 → 4.385 SP. **Lưu ý đồng bộ**: script của Đạt đang tự suy lá mũ (beanie 21, wide_brim 6) khác taxonomy v1 (beanie 20, wide_brim 0) → Đạt cần dùng `msa.data.taxonomy.map_fpi`.

### 3.4 Phân loại (taxonomy)
Cây 2 cấp + bảng map 168 nhãn FPI (độ phủ 100%) + luật tiêu đề tiếng Việt cho ViMRHP (khớp 509/509) – xem `docs/US_49_taxonomy.md`.

## 4. Chỗ trỏ số liệu của các thành viên (điền khi chốt)
| Nội dung | Nguồn |
|---|---|
| Bảng phương pháp + bảng nguồn | Tuấn Đạt – sheet `1_Thu thập dữ liệu` |
| EDA (biểu đồ) | Khoa – `04_Khoa/docs/US_09_eda/eda_report.md` (9 hình) |
| Làm sạch | Đạt – `02_TuanDat/results/clean_report.md` |
| Robots/ToS crawl | Chiến – `03_Chien/docs/US_07_kiem_tra_robots_tos.md` |
| Schema, taxonomy | Trung – `docs/US_05_schema.md`, `docs/US_49_taxonomy.md` |
