# US_05 – Schema dữ liệu sản phẩm chuẩn

| Mục | Nội dung |
|---|---|
| Mã US | US_05 (Owner: Trung, Support: Hoàng) |
| Mục tiêu | Một schema chung để mọi nguồn (FPI, ViMRHP/Shopee, crawl, ảnh tự chụp, dataset khác) quy về cùng định dạng; ai cũng dùng y nguyên tên trường (mục 5.1 thiết kế chung) |
| Đầu ra | `docs/US_05_schema.md` (file này), `src/schema/product.schema.json` (JSON Schema draft 2020-12), adapter `src/msa/data/schema_adapters.py`, ví dụ thật `src/schema/examples/*.json` (8 file: 1 SP/nhóm × 2 nguồn), kết quả `results/schema_validation.json` |
| Tiêu chí nghiệm thu | Mọi nguồn map được vào schema; trường bắt buộc xác định rõ |
| Trạng thái | **Hoàn thành** (đã validate trên dữ liệu thật). Còn lại: Hoàng duyệt; bổ sung adapter cho nguồn crawl/ảnh tự chụp khi có |

Tái lập: `PYTHONPATH=src python scripts/build_category_map.py && PYTHONPATH=src python scripts/validate_catalog.py`

## 1. Quy ước
- **Mọi khoá phải có mặt** trong bản ghi (`required` = 24 trường) để code đọc không phải kiểm `KeyError`; trường "tuỳ chọn" được phép `null` hoặc mảng rỗng.
- Trường **bắt buộc có giá trị** (không null): `product_id, title, source, source_url, license, product_type, sub_category, size_system, view_type, language`, cùng 4 mảng `colors, sizes, image_paths, reviews` (có thể rỗng).
- `additionalProperties: false` → thêm trường mới phải sửa schema và thông báo cả nhóm (R6). Thông tin đặc thù nguồn để trong `specs`.
- **Không bịa**: nguồn không có giá/size/mô tả thì để `null`/`[]` (FPI và ViMRHP đều không có giá → `price=null`).
- Cặp `(product_type, sub_category)` bị ràng buộc theo cây taxonomy v1 (US_49) bằng `allOf/if-then`; SP `out_of_scope` không được vào catalog.

## 2. Danh sách trường
| Trường | Kiểu | Bắt buộc giá trị | Ý nghĩa / ràng buộc |
|---|---|---|---|
| `product_id` | string | ✔ | `<nguồn>_<id gốc>`, regex `^[a-z0-9]+_[A-Za-z0-9_-]+$`, duy nhất (vd `fpi_21744`, `shopee_18390665755`) |
| `title` | string | ✔ | tên gốc, ≥ 2 ký tự |
| `category` | string\|null | | nhãn gốc của nguồn để truy vết (`Footwear/Shoes/Casual Shoes`, `GiayDepNu`) |
| `brand` | string\|null | | FPI: lấy từ chữ đầu tiêu đề (**heuristic**, vd "United Colors of Benetton" → "United" – cần làm sạch ở US của Đạt) |
| `price` | number\|null | | ≥ 0; null nếu nguồn không có |
| `currency` | enum | | `VND, USD, INR, null` |
| `colors`, `sizes` | string[] | ✔ (có thể rỗng) | |
| `description` | string\|null | | |
| `specs` | object\|null | | thuộc tính có cấu trúc (season, usage, year, articleType; ViMRHP: `image_urls`, `taxonomy_rule`) |
| `image_paths` | string[] | ✔ (có thể rỗng) | đường dẫn ảnh cục bộ tương đối `data/`; ViMRHP chỉ có URL (không tải được) → rỗng |
| `rating` | number\|null | | 0–5 (ViMRHP: trung bình review) |
| `rating_count` | integer\|null | | |
| `reviews` | object[] | ✔ (có thể rỗng) | mỗi phần tử bắt buộc `review_id, text`; tuỳ chọn `rating, date, helpfulness, detail_rating` |
| `source` | enum | ✔ | `fashion_product_images_small, vimrhp_shopee, crawl_vn, self_photo, clothing_dataset_cc0, abo, amazon_reviews_2023` |
| `source_url` | string | ✔ | |
| `license` | string | ✔ | ghi rõ, kèm `[cần xác minh]` nếu chưa chắc |
| `product_type` | enum | ✔ | `footwear, clothing, headwear, accessory` |
| `sub_category` | enum | ✔ | lá của cây US_49 hoặc `unknown`; phải thuộc đúng `product_type` |
| `gender` | enum\|null | | `Men, Women, Unisex, Boys, Girls, null` |
| `size_system` | enum | ✔ | `EU, US, UK, VN, alpha, free, numeric_waist, none` |
| `view_type` | enum | ✔ | `studio, on_model, lifestyle, user_photo, unknown` |
| `variant_id` | string\|null | | gom biến thể màu/size của cùng mẫu |
| `language` | enum | ✔ | `vi, en` |

## 3. Kết quả validate trên dữ liệu thật (`results/schema_validation.json`)
| Tập dữ liệu | Hợp lệ / Tổng | Ghi chú |
|---|---|---|
| `shared_data/catalog_fpi.parquet` (nhãn **tạm**) | **4.320 / 4.593 (94,06%)** | 273 lỗi đều là `sub_category` tạm: `heel_flat*` 270, `wide_brim*` 3 → đúng như dự kiến, đã xử lý bằng taxonomy v1 |
| `data/catalog_fpi_taxonomy_v1.parquet` (phần trong phạm vi) | **4.586 / 4.586 (100%)** | 7 Headband bị loại (`out_of_scope`) |
| ViMRHP qua `vimrhp_to_record` (phần trong phạm vi) | **361 / 361 (100%)** | 148 SP loại (81 đồng hồ + 67 trang sức/tất/…); `price=null` cho 100% (không bịa) |

Validator: `jsonschema.Draft202012Validator`. Test tự động: `tests/test_schema.py`.

## 4. Ví dụ thật (rút gọn – bản đầy đủ ở `src/schema/examples/`)
FPI – footwear (`fpi_footwear.json`):
```json
{"product_id": "fpi_21744", "title": "Vans Unisex Classic Slip-On Black Casual Shoe", "category": "Footwear/Shoes/Casual Shoes",
 "brand": "Vans", "price": null, "currency": null, "colors": ["Black"], "sizes": [], "description": null,
 "specs": {"season": "Fall", "usage": "Casual", "year": 2011, "articleType": "Casual Shoes"},
 "image_paths": ["fpi_images/21744.jpg"], "rating": null, "rating_count": null, "reviews": [],
 "source": "fashion_product_images_small", "source_url": "https://huggingface.co/datasets/ashraq/fashion-product-images-small",
 "license": "[cần xác minh] – bản gốc Kaggle paramaggarwal/fashion-product-images-dataset",
 "product_type": "footwear", "sub_category": "sneaker", "gender": "Unisex", "size_system": "none", "view_type": "studio",
 "variant_id": null, "language": "en"}
```
ViMRHP – footwear (`vimrhp_footwear.json`, 1 review):
```json
{"product_id": "shopee_19890682149", "title": "Tông đi biển , dép kẹp đi biển độn đế cao cấp TA Store", "category": "GiayDepNam",
 "brand": null, "price": null, "currency": null, "colors": [], "sizes": [], "description": null,
 "specs": {"image_urls": ["https://down-bs-us.img.susercontent.com/…webp"], "taxonomy_rule": "vi.sandal"},
 "image_paths": [], "rating": 5.0, "rating_count": 24,
 "reviews": [{"review_id": "12134624341", "rating": 5, "text": "Đúng với mô tả:đúng … giao hàng nhanh", "date": "2023-07-31T08:34:30.000Z", "helpfulness": 3}],
 "source": "vimrhp_shopee", "license": "CC BY-NC-ND 4.0 (ViMRHP, NLDB 2025) – chỉ dùng nội bộ học thuật …",
 "product_type": "footwear", "sub_category": "sandal", "gender": null, "size_system": "none", "view_type": "unknown", "variant_id": null, "language": "vi"}
```
Các ví dụ còn lại: `fpi_clothing.json` (fpi_9465 John Miller shirt), `fpi_headwear.json` (fpi_40767 Quiksilver cap), `fpi_accessory.json` (fpi_7108 Wildcraft backpack), `vimrhp_clothing/headwear/accessory.json`.

## 5. Map nguồn → schema
| Nguồn | Cách map | Trạng thái |
|---|---|---|
| Fashion Product Images | `fpi_row_to_record` (catalog đã theo schema; chỉ đổi kiểu numpy → JSON) | Đã validate |
| ViMRHP | `vimrhp_to_record`: review → `reviews[]`, rating = trung bình, ảnh URL → `specs.image_urls`, taxonomy từ tiêu đề | Đã validate |
| Crawl VN (Tiki) | dự kiến map giá/size/mô tả; **Tiki chặn IP cloud (403)** → chưa có dữ liệu | CHƯA LÀM |
| Ảnh tự chụp | `view_type=user_photo`, chỉ dùng làm query, không vào catalog | CHƯA LÀM (chưa có ảnh) |
| ABO / Amazon Reviews 2023 / Clothing Dataset | map theo `data/category_map.csv` `[cần xác minh]` | chưa có file |
