# US_11 – Tạo tập ảnh truy vấn "ngoài đời" (eval_visual – phần ngoài đời)

| Mục | Nội dung |
|---|---|
| Mã US | US_11 (Owner: Tuấn Đạt, Support: Chiến) – Sprint 2, 3.0 pt |
| Mục tiêu | 80–100 ảnh truy vấn thực tế (tự chụp, chụp màn hình, nền phức tạp, góc lạ, người mặc nhiều món), ground truth do 2 người gán |
| Đầu ra | `data/eval/visual_queries/` (ảnh) + `ground_truth.csv` theo mẫu `eval/visual_queries_ground_truth_template.csv`; script kiểm `src/scripts/check_visual_queries.py` |
| Tiêu chí nghiệm thu | ≥ 80 ảnh; mỗi ảnh ≥ 1 SP đúng được 2 người xác nhận; giày ≥ 25 / quần áo ≥ 25 / mũ ≥ 15 / phụ kiện ≥ 15 |
| Trạng thái | **Khung sẵn – cần dữ liệu thật.** Số ảnh đã có: **0 – CHƯA ĐO** (ảnh phải do người thật chụp; tác nhân AI không thể chụp và không được dùng ảnh tải bừa trên mạng) |

## 1. Phân bổ (tối thiểu → mục tiêu)

| product_type | Tối thiểu | Mục tiêu | Gợi ý kịch bản |
|---|---|---|---|
| footwear | 25 | 30 | 10 tu_chup (giày đang đi/đặt sàn), 6 nen_phuc_tap, 6 chup_man_hinh, 4 studio_khac_goc, 4 nguoi_mac_nhieu_mon |
| clothing | 25 | 30 | 10 nguoi_mac_nhieu_mon, 8 tu_chup (treo móc/gấp), 6 chup_man_hinh, 6 nen_phuc_tap |
| headwear | 15 | 18 | 6 tu_chup, 5 nguoi_mac_nhieu_mon (đang đội), 4 chup_man_hinh, 3 nen_phuc_tap |
| accessory | 15 | 18 | túi/thắt lưng/kính: 6 tu_chup, 4 nguoi_mac_nhieu_mon, 4 chup_man_hinh, 4 nen_phuc_tap |
| **Tổng** | **80** | **96** | ≥ 10 ảnh `nguoi_mac_nhieu_mon` (ảnh 1 người mặc ≥ 2 món) |

Lưu ý catalog (đo thật trong `results/catalog_clean.parquet`): mũ chỉ có `cap` 258, `beanie` 21, `wide_brim` 6, **không có bucket**;
giày **không có boot**. Ảnh truy vấn nên ưu tiên loại có trong catalog; được phép thêm 3–5 ảnh boot/bucket làm truy vấn "không có
SP tương ứng" (ghi `gt_product_ids` = `NONE`, cột note = `ngoai_catalog`) để đo khả năng từ chối – script coi `NONE` là ground truth hợp lệ
nếu nhóm thống nhất (sửa `check()` khi cần).

## 2. Quy trình chụp & đặt tên
1. Chụp bằng điện thoại (≥ 720 px cạnh ngắn), JPG; **không** chụp mặt người lạ; người trong ảnh phải đồng ý (cột `consent`).
2. Ảnh chụp màn hình: chỉ từ ảnh SP công khai, ghi URL nguồn vào `note`; không dùng để huấn luyện.
3. Đặt tên `VQ001.jpg`… lưu `data/eval/visual_queries/`. Xoá EXIF vị trí: `python -c "from PIL import Image; ..."` hoặc app chỉnh ảnh.
4. Mỗi ảnh 1 dòng CSV; ảnh nhiều món → ghi `product_type` của món cần tìm (có thể tạo nhiều dòng cùng file khác `query_id`).

## 3. Gán nhãn 2 người (ground truth)
1. Người 1 (Tuấn Đạt) tìm trong catalog 1–5 SP giống nhất (dùng UI hoặc lọc `results/catalog_clean.parquet` theo product_type/sub_category/màu), ghi `gt_product_ids` dạng `fpi_123|fpi_456`, điền `annotator_1`.
2. Người 2 (Chiến) xem độc lập, đồng ý/không → `annotator_2`; nếu khác, 2 người thảo luận, chỉ giữ ID cả hai đồng ý; `agreed=yes`.
3. Ghi tỉ lệ đồng thuận ban đầu (trước thảo luận) vào báo cáo: số ảnh hai người chọn trùng ≥ 1 ID / tổng ảnh.
4. Chạy kiểm: `python src/scripts/check_visual_queries.py --csv data/eval/visual_queries/ground_truth.csv --image-root . --catalog results/catalog_clean.parquet` → phải in `ĐẠT`.

## 4. Kết quả
| Chỉ số | Giá trị |
|---|---|
| Số ảnh | **CHƯA ĐO** (0) |
| Theo nhóm | CHƯA ĐO |
| Tỉ lệ đồng thuận ban đầu 2 người | CHƯA ĐO |
| Recall@5 ảnh ngoài đời (Bảng A2) | CHƯA ĐO – Khoa chạy eval_visual sau khi có tập này |

Script kiểm và mẫu CSV đã có test (`tests/test_bench_reviews_vq.py`: tập đủ quota → ĐẠT; thiếu người 2 / thiếu quota / ID ngoài catalog → báo lỗi).
