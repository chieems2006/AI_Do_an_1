# Báo cáo làm sạch (sinh tự động bởi 03_clean.py)

Đầu vào: `/home/claude/work/shared_data/catalog_fpi.parquet` – cấu hình: `{"phash_max_dist": 4, "min_side": 32, "blank_std": 3.0, "cap": 800, "quota": {"footwear": 1200, "clothing": 2000, "accessory": 500, "headwear": 300}, "seed": 42, "sample_per_type": 100, "drop_title_jaccard": 0.6, "fix_brand": true}`

| Bước | Số SP | Ghi chú |
|---|---|---|
| Ban đầu | 4593 | |
| Loại ảnh lỗi | -0 | trạng thái ảnh: {'ok': 4593} |
| Khử trùng lặp | -21 | MD5 trùng: 20; cặp pHash ≤ ngưỡng cùng type+brand: 395 |
| Loại category unknown | -7 | {'Headband': 7} |
| Cap mỗi lá | -180 | cap=800 |
| **Sau làm sạch** | **4385** | |

| Nhóm lá | Trước | Sau |
|---|---|---|
| accessory/bag | 465 | 465 |
| accessory/belt | 100 | 100 |
| accessory/eyewear | 135 | 135 |
| clothing/bottom | 355 | 349 |
| clothing/dress | 72 | 70 |
| clothing/outerwear | 52 | 52 |
| clothing/top | 1721 | 1529 |
| footwear/heel_flat | 0 | 270 |
| footwear/heel_flat* | 270 | 0 |
| footwear/leather_shoe | 95 | 95 |
| footwear/sandal | 306 | 306 |
| footwear/sneaker | 729 | 729 |
| headwear/beanie | 0 | 21 |
| headwear/cap | 283 | 258 |
| headwear/unknown | 7 | 0 |
| headwear/wide_brim | 0 | 6 |
| headwear/wide_brim* | 3 | 0 |

| product_type | Quota | Sau | Đạt? |
|---|---|---|---|
| footwear | 1200 | 1400 | Đạt |
| clothing | 2000 | 2000 | Đạt |
| accessory | 500 | 700 | Đạt |
| headwear | 300 | 285 | THIẾU |

Cặp pHash toàn cục theo ngưỡng Hamming: {'0': 52, '2': 634, '4': 3937, '6': 13940, '8': 36724}
Kiểm nhãn tự động theo từ khoá tiêu đề (mẫu 100/nhóm): {'accessory': {'n': 100, 'inconsistent': 0, 'inconsistent_rate': 0.0}, 'clothing': {'n': 100, 'inconsistent': 0, 'inconsistent_rate': 0.0}, 'footwear': {'n': 100, 'inconsistent': 0, 'inconsistent_rate': 0.0}, 'headwear': {'n': 100, 'inconsistent': 1, 'inconsistent_rate': 0.01}}
