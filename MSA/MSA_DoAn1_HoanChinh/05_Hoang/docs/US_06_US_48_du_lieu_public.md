# US_06 + US_48 – Tải & chuẩn hoá dataset công khai (giày dép, phụ kiện, quần áo, mũ)

| Mục | Nội dung |
|---|---|
| Mã US | **US_06** (giày dép + phụ kiện, 5 pt) · **US_48** (quần áo + mũ, 3 pt) – Owner: Hoàng, Support: Tuấn Đạt |
| Mục tiêu | Có dữ liệu nền từ nguồn chính thống, license rõ, chuyển về schema chuẩn mục 5.1, chạy lại cho cùng kết quả |
| Đầu ra | `src/scripts/01_download_public.py`, `src/scripts/01b_download_clothing_hats.py`, `src/scripts/02_merge_data_v1.py`, `src/msa/data/converters.py`, `src/msa/data/pipeline.py`, `data/sources_log.json`, `data/counts_*.json`, `data/amazon_probe.json`, `data/eda_data_v1.json` |
| Tiêu chí nghiệm thu | US_06: ≥ 1.700 SP giày + phụ kiện có ảnh + metadata; chạy lại cùng kết quả. US_48: ≥ 2.300 SP (quần áo ≥ 2.000, mũ ≥ 300); mọi nguồn có license; mũ < 300 phải ghi quyết định |
| Trạng thái | **US_06: Hoàn thành** (đo thật). **US_48: Hoàn thành một phần** – quần áo đạt, **mũ 298 < 300** (quyết định ở mục 4) |

## Tóm tắt 5 dòng
1. Script tải + chuẩn hoá dữ liệu public về schema chung, chạy lại cho cùng hash.
2. Giày + phụ kiện 2.335 SP (2.100 có ảnh ≥ 1.700 – đạt US_06); quần áo đạt quota.
3. Mũ 298 trong file này **gồm 7 băng đô (taxonomy loại) + 5 mũ ViMRHP không có ảnh**; số chuẩn có ảnh là **285** (`00_Chung/QUYET_DINH_CAN_CHOT.md` mục A).
4. Amazon Reviews 2023 có 372 mũ nhưng ảnh bị chặn – phương án bổ sung khi chạy trên máy thật.
5. Loại số liệu: [Thật–thật].
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Phiên bản dữ liệu: `Data v1 (scripts 01/01b/02, seed 42)`; trùng khớp 100% tập `product_id` FPI với `shared_data v1 (prep_shared_data.py seed 42)` (4.593/4.593, `data/counts_data_v1.json`).

## 1. Lệnh tái lập

```bash
python src/scripts/01_download_public.py --raw-dir /home/claude/realdata --check-repro      # US_06
python src/scripts/01b_download_clothing_hats.py --check-repro --amazon-lines 20000       # US_48 (+ probe Amazon)
python src/scripts/02_merge_data_v1.py                                                     # Data v1
# Máy mới chưa có dữ liệu gốc: thêm --download (huggingface_hub). Bản Kaggle gốc của FPI là tuỳ chọn.
```

## 2. Kết quả THẬT (chạy 04–05/11/2026)

### 2.1 Bảng đếm theo nhóm (Data v1, `data/counts_data_v1.json`)

| product_type | sub_category | FPI (ảnh 60×80) | ViMRHP (review VN, không ảnh local) | Tổng | Quota tối thiểu | Đạt? |
|---|---|---:|---:|---:|---:|---|
| footwear | sneaker / sandal / heel_flat* / leather_shoe / unknown | 1.400 | 171 | **1.571** | 1.200 | ✅ |
| accessory | bag / eyewear / belt / unknown | 700 | 64 | **764** | 500 | ✅ |
| clothing | top / bottom / outerwear / dress / unknown | 2.200 | 188 | **2.388** | 2.000 | ✅ |
| headwear | cap 286 / unknown 9 / wide_brim* 3 | 293 | 5 | **298** | 300 | ❌ thiếu 2 |
| **Tổng** | | **4.593** | **428** | **5.021** | | |

- US_06: giày + phụ kiện = **2.335 SP** (≥ 1.700 ✅), trong đó 2.100 SP có ảnh + metadata (FPI) – vẫn ≥ 1.700 khi chỉ tính SP có ảnh.
- US_48: quần áo + mũ = **2.686 SP** (≥ 2.300 ✅), quần áo 2.388 ✅, mũ 298 ❌.
- Chi tiết theo sub_category: footwear sneaker 731, sandal 400, heel_flat* 319, leather_shoe 95, unknown 26; accessory bag 467, eyewear 142, belt 106, unknown 49; clothing top 1.817, bottom 374, outerwear 110, dress 73, unknown 14.
- Số ảnh: **4.593** ảnh, tất cả **60×80 px** (bản *small* – hạn chế lớn cho visual search). ViMRHP: **9.403 review** trên 428 SP (TB 22,0 review/SP, min 3, max 43); ảnh chỉ là URL Shopee (`*.susercontent.com` bị chặn ở môi trường này).
- Thiếu dữ liệu (toàn catalog): giá 100%, size 100%, mô tả 100%, rating 91,5% (chỉ ViMRHP có rating) → bộ lọc giá/size và so sánh giá **chưa dùng được trên dữ liệu thật**; cần crawl VN (US_07) hoặc Amazon meta.
- Mất cân bằng 4 nhóm: lớn nhất/nhỏ nhất = 2.388/298 = **8,0**.

### 2.2 Kho dữ liệu FPI còn dùng được (không áp quota, `fpi_available_by_sub`)

sneaker 4.861 · sandal 1.876 · heel_flat* 1.823 · leather_shoe 637 · bag 2.985 · eyewear 1.073 · belt 813 · top 14.445 · bottom 2.463 · dress 480 · outerwear 273 · **cap 283 · wide_brim* 3 · headband 7** (mũ đã lấy hết). FPI không có boot, beanie, bucket.

### 2.3 Tái lập (chạy 2 lần → so hash)

| Script | Hash catalog (sha256, 16 ký tự đầu) | Lần 2 trùng? | Hash ảnh trùng? | Ghi/đọc parquet giữ nguyên? | Thời gian |
|---|---|---|---|---|---|
| 01 (giày + phụ kiện) | `6eb4ee569336ff45` | ✅ | ✅ | ✅ | ≈ 5–7 s |
| 01b (quần áo + mũ) | `9e105186f79058be` | ✅ | ✅ | ✅ | ≈ 7–9 s |
| 02 Data v1 | `5674d36a8283c18e` | – | – | schema hợp lệ 100% (0 lỗi) | < 5 s |

Hash file gốc (sha256) lưu trong `data/sources_log.json` để phát hiện khi nguồn thay đổi.

### 2.4 Probe Amazon Reviews 2023 (đọc luồng 20.000 dòng đầu meta Clothing_Shoes_and_Jewelry, `data/amazon_probe.json`)

| Chỉ số | Giá trị đo thật |
|---|---:|
| Dòng đã đọc / SP map được vào 4 nhóm | 20.000 / 11.437 |
| clothing / footwear / accessory / headwear | 5.164 / 4.864 / 1.037 / **372** |
| headwear theo loại | cap 106, beanie 68, wide_brim 53, bucket 7, chưa rõ 138 |
| headwear có giá / có URL ảnh | 217 / 372 |
| Thời gian đọc luồng | ≈ 3,5 s |

Nhận xét: Amazon bù được mũ (và có giá USD, boot 525 SP) nhưng **ảnh `m.media-amazon.com` bị proxy chặn** ở môi trường này → chưa đưa vào index ảnh; 138 mũ "chưa rõ loại" có lẫn băng đô/kippah, cần lọc tay. Lưu metadata ở `data/processed/amazon_meta_probe.parquet` (không vào Data v1).

## 3. Nguồn & license (`data/sources_log.json`)

| Nguồn | URL | Mức chính thống | License | Vai trò |
|---|---|---|---|---|
| Fashion Product Images (small) | huggingface.co/datasets/ashraq/fashion-product-images-small (gốc Kaggle paramaggarwal, Myntra) | Mức 2 | `[cần xác minh]` – HF card không ghi rõ | Catalog + ảnh (visual search, text search, compare) |
| ViMRHP – Fashion | huggingface.co/datasets/trucmtnguyen/ViMRHP (NLDB 2025, arXiv 2505.07416) | Mức 1 | CC BY-NC-ND 4.0 – nội bộ học thuật, không phát hành lại bản đã chỉnh | Review tiếng Việt cho RAG/QA |
| Amazon Reviews 2023 (meta) | huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023 (arXiv 2403.03952) | Mức 1 | `[cần xác minh]` điều khoản nghiên cứu | Probe mũ/quần áo, metadata-only |
| ABO listings | amazon-berkeley-objects.s3.amazonaws.com | Mức 1 | CC BY 4.0 `[cần xác minh]` | Converter có sẵn, **chưa chạy** (S3 bị chặn) |
| Clothing Dataset (Grigorev) | github.com/alexeygrigorev/clothing-dataset | Mức 2 | CC0 `[cần xác minh]` | Converter có sẵn, **chưa tải** |

## 4. Quyết định cho mũ (298 < 300)

1. Giữ toàn bộ 293 mũ FPI + 5 mũ ViMRHP; **không** kéo thêm nguồn mới sau N4 (theo sheet 1_Thu thập, mục F).
2. Đề xuất nhóm chốt một trong hai: (a) **bổ sung mũ Amazon có ảnh** khi tải được ảnh trên máy thật (≥ 234 mũ thuộc 4 loại taxonomy trong 20.000 dòng đầu), hoặc ảnh tự chụp/crawl VN (US_07, Chiến); (b) **hạ chỉ tiêu mũ xuống 290** cho Data v1 và ghi vào báo cáo. Mặc định: (b) cho Data v1, (a) cho Data v2. → cần Trung xác nhận ở daily.
3. Lưu ý taxonomy: FPI chỉ có `cap` → các lớp beanie/bucket/wide_brim gần như rỗng; đánh giá theo sub_category mũ phải ghi rõ.

## 5. Việc còn lại

- Tải ảnh Amazon/ABO/Clothing Dataset trên máy có mạng mở; chạy lại 01b với `--amazon-include` (chưa làm) để thêm mũ có ảnh.
- Ghép crawl VN của Chiến (US_07) bằng `02_merge_data_v1.py --extra <parquet>`; đặt tag `data-v1`.
- Xác minh license FPI và Amazon (đọc Data Card/ToS) – thay nhãn `[cần xác minh]`.
- Kiểm tay 30 mẫu/nguồn cho mapping từ khoá tiếng Việt (182/235 SP giày-phụ kiện và 190/193 SP quần áo-mũ map theo từ khoá tên; còn lại theo nhóm ViMRHP) – **chưa có người thật kiểm**.
