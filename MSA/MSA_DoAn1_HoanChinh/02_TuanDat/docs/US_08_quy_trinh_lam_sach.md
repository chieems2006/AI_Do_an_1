# US_08 – Làm sạch, khử trùng lặp, phân loại dữ liệu

| Mục | Nội dung |
|---|---|
| Mã US | US_08 (Owner: Tuấn Đạt, Support: Hoàng) – Sprint 1, 5.0 pt |
| Mục tiêu | Loại ảnh lỗi/trùng (perceptual hash), chuẩn hoá text, gán category/sub-category theo taxonomy, chuẩn hoá màu/size, giới hạn mỗi nhóm lá |
| Đầu ra | `src/scripts/03_clean.py`, `data/category_map.csv`, `results/catalog_clean.parquet`, `results/clean_report.json/.md`, `results/dup_pairs.csv`, `results/label_check_sample.csv`, `results/figures/dup_pairs_d{0,2,4}.png` |
| Tiêu chí nghiệm thu | Ảnh lỗi < 1%; không còn ảnh trùng; 100% SP có category; nhãn sai ≤ 5% trên mẫu 100 SP/nhóm; không nhóm nào dưới quota |
| Trạng thái | **Hoàn thành phần chạy thật trên FPI**; 2 tiêu chí còn mở: (a) kiểm nhãn bởi 2 người thật, (b) mũ 285 < quota 300 (giới hạn nguồn) |

## Tóm tắt 5 dòng
1. Pipeline 7 bước: chuẩn hoá text → kiểm ảnh lỗi → khử trùng (MD5 + pHash) → gán nhóm theo bảng map → chuẩn hoá màu/size → giới hạn tối đa mỗi lá (cap) → lấy mẫu kiểm nhãn 100 SP/nhóm.
2. Kết quả thật: 4.593 → 4.385 SP; ảnh lỗi 0 %; bỏ 7 băng đô (ngoài phạm vi) + 21 SP trùng MD5; cắt 180 áo top để cân bằng.
3. pHash không dùng để xoá trên ảnh 60×80 vì 3.937 cặp gần giống phần lớn là SP khác nhau (chỉ đánh dấu biến thể/cần xem).
4. Chưa đạt: mũ 285 < 300; nhãn mới kiểm tự động theo tiêu đề, chưa có người thật; 3 đôi boot bị gán sai (Tác nhân 2 phát hiện – QUYET_DINH mục A).
5. Loại số liệu: [Thật–thật]; kiểm nhãn [Tác nhân kiểm].
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Lệnh tái lập (≈ 9 giây trên CPU):
```bash
python src/scripts/03_clean.py --catalog /home/claude/work/shared_data/catalog_fpi.parquet \
    --image-root /home/claude/work/shared_data --out results          # cấu hình mặc định: pHash ≤ 4, cap 800, seed 42
python src/scripts/dup_montage.py --dist 4 --n 40 --out results/figures/dup_pairs_d4.png
```
Dữ liệu: `shared_data v1 (prep_shared_data.py seed 42)`.

## 1. Quy trình

| Bước | Cách làm | Tham số |
|---|---|---|
| 1. Chuẩn hoá text | `html.unescape` → bỏ thẻ HTML → Unicode NFC → bỏ `​`, `&nbsp;` → gộp khoảng trắng (title, brand, description) | – |
| 1b. Sửa brand | Brand = các từ trước từ chỉ giới tính (Men/Women/Unisex/Boys/Girls…) thay cho "từ đầu tiên" của bản prep | `fix_brand=True` |
| 2. Kiểm ảnh | Thiếu file / không mở được (`PIL.verify` + `load`) / cạnh < 32 px / ảnh trơn (độ lệch chuẩn xám < 3) | `min_side=32`, `blank_std=3` |
| 3. Khử trùng | (a) MD5 trùng tuyệt đối → xoá; (b) pHash 64-bit, tính mọi cặp Hamming ≤ 8 để thống kê; **chỉ xoá** khi pHash = 0 + cùng product_type + brand + màu + Jaccard tiêu đề ≥ 0,6; cùng type/brand/màu nhưng d ≤ 4 → `review` (người kiểm); cùng type/brand khác màu → `variant` (giữ, gán `variant_id`) | `phash_max_dist=4`, `drop_title_jaccard=0.6` |
| 4. Category | `data/category_map.csv` (source, source_label → product_type, sub_category); không map → `unknown` → loại khỏi index; tinh chỉnh theo tiêu đề (`TITLE_REFINE`): beanie/skull cap → `beanie`, "Hat" → `wide_brim` | – |
| 5. Màu / size | 42 tên màu gốc → 13 nhóm chung (+ `other`); size → `size_system` (EU/US/alpha/free/numeric_waist/none) | – |
| 6. Cap lá | Tối đa 800 SP/lá, nhưng trả lại SP cho đủ quota product_type | quota: giày 1.200 / quần áo 2.000 / phụ kiện 500 / mũ 300 |
| 7. Mẫu kiểm nhãn | 100 SP/nhóm (seed 42) → `label_check_sample.csv` có cột cho 2 người + kiểm tự động bằng từ khoá tiêu đề | – |

## 2. Kết quả THẬT – bảng trước/sau (`results/clean_report.json`)

| Bước | Số SP | Ghi chú |
|---|---|---|
| Ban đầu | 4.593 | footwear 1.400 / clothing 2.200 / accessory 700 / headwear 293 |
| Ảnh lỗi | −0 | 4.593/4.593 ảnh mở được, **100% là 60×80 px**; 37 ảnh grayscale (mode L, giữ lại) → tỉ lệ ảnh lỗi **0%** |
| Khử trùng | −21 | 20 bản trùng MD5 + 1 cặp pHash = 0 cùng type/brand/màu/tiêu đề |
| Category unknown | −7 | 7 "Headband" (băng đô – ngoài 4 lá mũ) |
| Cap 800/lá | −180 | chỉ `clothing/top` (1.709 → 1.529) – dừng ở đúng quota 2.000 |
| **Sau làm sạch** | **4.385** | footwear 1.400 / clothing 2.000 / accessory 700 / headwear **285** |

| Nhóm lá | Trước | Sau | Ghi chú |
|---|---|---|---|
| footwear/sneaker | 729 | 729 | |
| footwear/sandal | 306 | 306 | |
| footwear/heel_flat | 270 (`heel_flat*`) | 270 | ngoài 4 lá của hợp đồng 5.1 – **chờ Trung chốt US_49** |
| footwear/leather_shoe | 95 | 95 | |
| footwear/boot | 0 | 0 | FPI không có boot |
| clothing/top | 1.721 | 1.529 | cap |
| clothing/bottom | 355 | 349 | trùng MD5 |
| clothing/dress | 72 | 70 | trùng MD5 |
| clothing/outerwear | 52 | 52 | |
| headwear/cap | 283 | 258 | 18 → beanie, 6 → wide_brim, 1 trùng |
| headwear/beanie | 0 | **21** | phát hiện khi kiểm nhãn: 18 "Caps" + 3 "Hat" thật ra là beanie/skull cap |
| headwear/wide_brim | 3 (`wide_brim*`) | 6 | 5 fedora "Flying Machine … Hat" + 1 mũ vành Wildcraft (đã xem ảnh) |
| headwear/bucket | 0 | 0 | không có trong FPI |
| accessory/bag / belt / eyewear | 465 / 100 / 135 | 465 / 100 / 135 | |

Các số khác:
- Thiếu dữ liệu: `price`, `description`, `rating` thiếu **100%** (FPI không có) → luồng lọc giá và QA theo mô tả phải dùng nguồn khác.
- Text: 59 ô text thay đổi khi chuẩn hoá; brand sửa ở 1.304 SP, số brand khác nhau 248 → 302 ("Red Tape"/"Red Chief" không còn bị gộp thành "Red").
- Màu sau chuẩn hoá: black 1.097, blue 784, white 618, brown 432, grey 377, red 340, green 256, purple 182, pink 175, yellow 135, beige 96, orange 47, multi 26.
- `size_system = none` cho 100% (FPI không có size).
- 100% SP còn lại có product_type + sub_category hợp lệ (`category_coverage = 1.0`).

## 3. Phát hiện quan trọng: pHash không dùng được để tự xoá trùng trên ảnh 60×80

| Ngưỡng Hamming | Số cặp toàn catalog | Trong đó (d ≤ 4) khác product_type |
|---|---|---|
| 0 | 52 | |
| ≤ 2 | 634 | |
| ≤ 4 | 3.937 | 5 cặp khác nhóm (vd. thắt lưng ↔ giày) |
| ≤ 6 | 13.940 | |
| ≤ 8 | 36.724 | |

Kiểm bằng mắt (tác nhân AI xem ảnh ghép, **nhóm cần xem lại**): với mẫu 40 cặp d = 4 (`dup_pairs_d4.png`) cả 40 cặp đều là
**sản phẩm khác nhau** (giày da đen/nâu cùng dáng chụp, kính râm cùng góc); ở d = 0 (52 cặp) các cặp quần áo trùng MD5 là
bản sao thật, còn các cặp giày/kính có d = 0 vẫn là SP khác nhau. Nguyên nhân: ảnh studio nền trắng, cùng góc chụp, độ phân
giải 60×80 → DCT pHash gần như chỉ mã hoá bóng dáng. Nếu áp quy tắc "pHash ≤ 4 cùng type+brand+màu → xoá" như bản đầu thì
sẽ **xoá nhầm 118 SP** (bản chạy đầu, đã bỏ). Quy tắc đang dùng: chỉ xoá MD5 trùng hoặc pHash = 0 + tiêu đề gần giống;
122 cặp `review` để người kiểm; 252 cặp `variant` (cùng kiểu khác màu, 120 nhóm `variant_id`).

## 4. Đối chiếu tiêu chí nghiệm thu

| Tiêu chí | Kết quả | Đạt? |
|---|---|---|
| Ảnh lỗi < 1% | 0/4.593 = 0% | Đạt |
| Không còn ảnh trùng | 0 cặp MD5 trùng; 122 cặp "nghi trùng" (pHash ≤ 4, cùng type/brand/màu) chờ người kiểm trong `dup_pairs.csv` (action = review) | **Một phần** – cần người kiểm 122 cặp |
| 100% SP có category | 4.385/4.385 | Đạt |
| Nhãn sai ≤ 5% (mẫu 100/nhóm) | Kiểm tự động theo từ khoá tiêu đề: giày 0/100, quần áo 0/100, phụ kiện 0/100, mũ 1/100. **Lưu ý thiên lệch:** lần chạy đầu cho 1% / 4% / 0% / 6% (phụ kiện/quần áo/giày/mũ); sau đó tác nhân bổ sung từ khoá (purse, jersey, dungaree) và luật beanie/hat dựa trên chính mẫu này → con số sau là lạc quan. **Kiểm bởi 2 người: CHƯA ĐO** | Chưa nghiệm thu |
| Không nhóm nào dưới quota | Mũ 285 < 300 | **Không đạt** – cần Amazon Reviews 2023 (Hats & Caps) / Clothing Dataset (Hat) / tự chụp; hoặc hạ quota mũ theo sheet Rủi ro |

## 5. Việc còn lại khi có người thật
1. Hai người điền `label_ok_annotator_1/2` trong `results/label_check_sample.csv` (400 dòng) → tính tỉ lệ sai thật mỗi nhóm.
2. Duyệt 122 cặp `review` trong `results/dup_pairs.csv`; nếu xác nhận trùng thì thêm vào danh sách loại.
3. Trung chốt lá `heel_flat`, `beanie`, `wide_brim` trong taxonomy (US_49) rồi chạy lại script.
4. Bổ sung nguồn mũ, sau đó chạy lại với `--catalog` gộp.
