# US_09 – EDA & mô tả đặc điểm dữ liệu

| Mục | Nội dung |
|---|---|
| Mã US | US_09 (Owner: Khoa, Support: Tuấn Đạt) – Sprint 1, 3.0 pt |
| Mục tiêu | Mô tả đặc điểm dữ liệu bằng số liệu thật cho báo cáo (Sheet 1, Mục D) |
| Đầu ra | `src/scripts/eda.py` (thay cho notebook – chạy được không cần Jupyter), `docs/US_09_eda/notebook_eda.ipynb` (gọi lại script), 9 biểu đồ PNG, `eda_stats.json`, file này |
| Tiêu chí nghiệm thu | Báo cáo có số liệu cụ thể cho từng nguồn dữ liệu; ≥ 6 biểu đồ |
| Trạng thái | **Hoàn thành** cho 2 nguồn đang có (FPI, ViMRHP). Phần crawl Tiki / ảnh ngoài đời: CHƯA CÓ DỮ LIỆU |

## Tóm tắt 5 dòng
1. Mô tả 2 nguồn bằng số liệu và 9 biểu đồ: FPI 4.593 SP (quần áo 2.200 / giày 1.400 / phụ kiện 700 / mũ 293) và ViMRHP 509 SP / 11.009 review.
2. 100 % ảnh FPI 60×80, 1 ảnh/SP, nền trắng; 785 dòng trùng tên; FPI không có giá/mô tả/rating.
3. ViMRHP lệch tích cực: 93,4 % review 5 sao, 57,8 % review theo mẫu Shopee.
4. Mũ 293 ở đây là số **trước** taxonomy và làm sạch; số chuẩn của nhóm là 285 (QUYET_DINH mục A).
5. Loại số liệu: [Thật–thật].
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


**Cấu hình**: dữ liệu `shared_data v1 (prep_shared_data.py seed 42)`; lệnh tái lập `python src/scripts/eda.py`; mọi số dưới đây đọc từ `eda_stats.json` (đo thật ngày 05/11/2026).

## 1. Tổng quan các nguồn

| Nguồn | Số bản ghi | Ngôn ngữ | Có ảnh | Có mô tả | Có giá | Có review | Giấy phép |
|---|---|---|---|---|---|---|---|
| Fashion Product Images (small) – bản gốc HF `ashraq/fashion-product-images-small` | 44.072 dòng, 141 articleType | EN (tên SP) | Có (60×80) | Không | Không | Không | Bản gốc Kaggle `paramaggarwal/fashion-product-images-dataset` – `[cần xác minh]` |
| **Catalog FPI** (lọc 4 nhóm, `catalog_fpi.parquet`) | **4.593 SP** (10,42 % của 44.072), 37 articleType, 248 brand | EN – 0 % tên có dấu tiếng Việt | 100 % (1 ảnh/SP) | 0 % | 0 % | 0 % | như trên |
| **ViMRHP** (`trucmtnguyen/ViMRHP`, NLDB 2025) | **509 SP Shopee VN, 11.009 review** (428 SP trong phạm vi khi loại 81 SP đồng hồ) | VI – 99,77 % review có dấu tiếng Việt | Chỉ URL (100 % có URL, nhưng `susercontent.com` bị chặn → không tải được) | Không | Không | Có | CC BY-NC-ND 4.0 (chỉ dùng nội bộ học thuật) |
| Crawl Tiki/Shopee (kế hoạch gốc 300–500 SP) | CHƯA CÓ | – | – | – | – | – | Tiki trả 403 cho IP cloud |
| Ảnh truy vấn ngoài đời (80–100 ảnh) | CHƯA CÓ | – | – | – | – | – | Nhóm phải tự chụp |

## 2. Catalog FPI (4.593 SP)

### 2.1 Phân bố nhóm / sub_category (biểu đồ `01_catalog_type_sub.png`)

| product_type | Số SP | Quota tối thiểu (kế hoạch) | Đạt? | sub_category (số SP) |
|---|---|---|---|---|
| footwear | 1.400 | 1.200 | Đạt | sneaker 729, sandal 306, heel_flat* 270, leather_shoe 95, **boot 0** |
| clothing | 2.200 | 2.000 | Đạt | top 1.721 (78 % nhóm), bottom 355, dress 72, outerwear 52 |
| accessory | 700 | 500 | Đạt | bag 465, eyewear 135, belt 100 |
| headwear | 293 | 300 | **Thiếu 7** | cap 283, unknown (Headband) 7, wide_brim* (Hat) 3 – **không có beanie/bucket** theo nhãn |

Mất cân bằng mạnh: `clothing/top` chiếm 37,5 % catalog, trong khi `clothing/outerwear` chỉ 52 SP và `headwear/wide_brim*` 3 SP. Hệ quả: (1) mọi độ đo visual phải báo **macro theo nhóm**, (2) không đủ dữ liệu để đánh giá riêng sub_category hiếm.

Quan sát khi xem ảnh: nhãn `Caps` trong FPI **có lẫn mũ len (beanie)** – ví dụ ảnh mẫu trong `eval/queries/` – nên "không có beanie" chỉ đúng ở mức nhãn, không đúng ở mức ảnh. Trong 44.072 dòng gốc chỉ có 19 tên SP chứa "beanie", 1 chứa "bucket", 26 chứa "boot(s)" (tìm theo tên) → đề xuất Trung xem lại map taxonomy (US_49).

### 2.2 Thuộc tính khác (biểu đồ `03`, `04`, `05`)

| Thuộc tính | Phân bố (catalog) |
|---|---|
| Giới tính | Men 2.367 (51,5 %), Women 1.576, Unisex 459, Boys 104, Girls 87 |
| Màu (`baseColour`, 42 giá trị) | Black 1.077, White 578, Blue 559, Brown 392, Grey 322, Red 287, Navy Blue 212, Green 192… |
| Mùa | Summer 2.400, Fall 1.433, Winter 671, Spring 89 |
| Mục đích | Casual 3.518 (76,6 %), Sports 570, Formal 258, Ethnic 237, khác 10 |
| Năm | 2008 – 2018 |

### 2.3 Văn bản & chất lượng trường

| Chỉ số | Giá trị |
|---|---|
| Số từ tên SP | trung bình 5,8; trung vị 6; min 3; max 11 |
| Tỉ lệ thiếu: price / description / sizes / rating / reviews | 100 % / 100 % / 100 % / 100 % / 100 % |
| Tỉ lệ thiếu: title / brand / colors / season / usage | 0 % |
| Tên SP trùng (không phân biệt hoa thường) | 785 dòng thuộc 325 nhóm tên (vd "catwalk women black heels" ×12) → tên KHÔNG đủ phân biệt SP, cần `product_id` |

### 2.4 Ảnh (biểu đồ `06_image_whitebg_filesize.png`, `09_sample_images.png`)

| Chỉ số | Giá trị |
|---|---|
| Kích thước | **100 % ảnh 60×80 px** (độ phân giải rất thấp – hạn chế lớn nhất của nguồn này) |
| Dung lượng file | trung bình 12,09 KB; p05 1,34 KB; p95 24,47 KB (phân phối 2 đỉnh: một phần ảnh có metadata kèm theo) |
| Tỉ lệ pixel gần trắng (> 240) | trung bình 0,687; trung vị 0,711; 1,7 % ảnh có < 20 % nền trắng |
| Theo nhóm | footwear 0,774 · headwear 0,771 · accessory 0,745 · clothing 0,603 (quần áo thường có người mẫu → ít nền trắng hơn) |

Hệ quả cho visual search: ảnh catalog gần như đều là ảnh studio nền trắng, 1 ảnh/SP → **không có "ảnh khác góc" thật**; bộ đánh giá US_15 phải tạo truy vấn bằng biến đổi có kiểm soát và điều này chỉ xấp xỉ ảnh người dùng. Model được upscale 60×80 → 224×224 nên chi tiết nhỏ (logo, hoạ tiết) gần như mất.

## 3. FPI bản gốc 44.072 dòng (biểu đồ `02_fpi_raw_article_types.png`)

| masterCategory | Số dòng |
|---|---|
| Apparel | 21.361 |
| Accessories | 11.244 |
| Footwear | 9.197 |
| Personal Care | 2.139 |
| Free Items | 105 |
| Sporting Goods | 25 |
| Home | 1 |

Top articleType: Tshirts 7.065, Shirts 3.212, Casual Shoes 2.845, **Watches 2.542 (ngoài phạm vi)**, Sports Shoes 2.016, Kurtas 1.844, Tops 1.762, Handbags 1.759, Heels 1.323, Sunglasses 1.073, **Wallets 928 (chưa đưa vào catalog – taxonomy accessory chỉ có bag/belt/eyewear)**. Mũ trong toàn bộ nguồn chỉ có Caps 283, Headband 7, Hat 3 → đã lấy hết vào catalog, không còn SP mũ nào để làm truy vấn held-out (ảnh hưởng thiết kế US_15). Không có giá trị thiếu ở 10 cột metadata.

## 4. ViMRHP (509 SP, 11.009 review) – biểu đồ `07`, `08`

| Chỉ số | Giá trị |
|---|---|
| SP theo nhóm | ThoiTrangNu 94, GiayDepNu 92, ThoiTrangNam 87, **DongHo 81 (loại)**, GiayDepNam 79, PhuKienNu 76 |
| Review/SP | trung bình 21,63; trung vị 23; min 3; max 43 |
| Rating (1→5) | 133 / 51 / 134 / 407 / **10.284** → trung bình 4,876; **93,4 % là 5 sao** (lệch rất mạnh) |
| Rating TB theo nhóm | GiayDepNam 4,933 · ThoiTrangNu 4,902 · GiayDepNu 4,898 · DongHo 4,887 · PhuKienNu 4,878 · ThoiTrangNam 4,763 |
| Số từ/review | trung bình 32,22; trung vị 29; p95 62 |
| Review rỗng hoặc < 3 từ | 0,31 % |
| Review theo **mẫu Shopee** ("Đúng với mô tả:", "Chất liệu:", "Màu sắc:") | **57,76 %** – nhiễu dạng khuôn, cần tách phần mẫu khi làm RAG |
| Review trùng nội dung | 1,91 % |
| Tên SP | trung bình 18,27 từ (dài, nhồi từ khoá: "Áo Khoác Lông 2 lớp nam nữ có mũ tai gấu…") |
| Ngôn ngữ | 99,77 % review có dấu tiếng Việt (heuristic ký tự có dấu) |
| Trường thiếu so với schema 5.1 | description, price, sizes, specs, colors |

## 5. Hạn chế dữ liệu (phải nêu trong báo cáo)

1. **Ảnh 60×80 px** – thấp hơn nhiều so với ảnh người dùng chụp; số Recall đo trên FPI không chuyển thẳng sang ảnh thật.
2. **1 ảnh/SP, nền trắng studio** → truy vấn "khác góc" chỉ là biến đổi tổng hợp (US_15).
3. **Mũ 293 SP (< quota 300)**, không có nhãn boot/beanie/bucket; một số "Caps" thực chất là beanie.
4. **ViMRHP không có mô tả/giá/size và ảnh không tải được** → không ghép được ảnh–review cho cùng SP; QA về giá/size phải trả "chưa có thông tin".
5. Rating ViMRHP lệch về 5 sao (93,4 %) → không dùng rating làm tín hiệu chất lượng đáng tin.
6. Hai nguồn **không trùng SP** (FPI là catalog Ấn Độ ~2011–2018, ViMRHP là Shopee VN 2023) – demo phải tách rõ "SP có ảnh" và "SP có review".

## 6. Biểu đồ (9 file, ≥ 6 theo yêu cầu)

| File | Nội dung |
|---|---|
| `01_catalog_type_sub.png` | Số SP theo product_type/sub_category |
| `02_fpi_raw_article_types.png` | Top-25 articleType trong 44.072 dòng gốc |
| `03_gender_by_type.png` | Giới tính theo nhóm |
| `04_colours_top15.png` | Top-15 màu |
| `05_season_usage.png` | Mùa và mục đích sử dụng |
| `06_image_whitebg_filesize.png` | Tỉ lệ nền trắng theo nhóm + dung lượng ảnh |
| `07_title_review_length.png` | Độ dài tên SP (FPI vs ViMRHP) và độ dài review |
| `08_vimrhp_rating_sub.png` | Phân bố rating và SP theo nhóm ViMRHP |
| `09_sample_images.png` | Lưới ảnh mẫu mỗi nhóm (seed 42) |

## 7. Việc còn lại
- Khi có dữ liệu crawl VN / ảnh ngoài đời: thêm nguồn vào `eda.py` (hàm đọc tương ứng) và chạy lại.
- Chuyển các số ở mục 1–4 vào Sheet 1 – Mục D.
