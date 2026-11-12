# US_15 – Bộ đánh giá Visual Search `eval_visual`

| Mục | Nội dung |
|---|---|
| Mã US | US_15 (Owner: Khoa, Support: Chiến) – Sprint 2, 5.0 pt |
| Mục tiêu | Đo Recall@K/MRR khách quan, phân tầng 4 nhóm |
| Đầu ra | `eval/eval_visual.csv` (600 truy vấn), `eval/eval_visual_ood.csv` (60 truy vấn ngoài phạm vi), `eval/queries/*.jpg` (660 ảnh), `eval/eval_visual_stats.json`, script `src/scripts/build_eval_visual.py` |
| Tiêu chí nghiệm thu | ≥ 200 query ✔ (600); chia val/test ✔; ≥ 30 query/nhóm ở test ✔ (90/nhóm: 60 instance + 30 category); ≥ 20 query dễ nhầm giữa nhóm ✔ (96, trong đó 53 ở test); query không nằm trong dữ liệu fine-tune ✔ (adapter I3 học trên SP không xuất hiện trong eval); có cột product_type ✔. Tự kiểm bằng `tests/test_eval_visual.py`. |
| Trạng thái | **Hoàn thành phần làm được với dữ liệu hiện có.** Phần **ảnh ngoài đời (80–100 ảnh) = CHƯA CÓ** – nhóm phải tự chụp (xem mục 6). |

## Tóm tắt 5 dòng
1. Bộ đánh giá 600 truy vấn (val 240 / test 360, 90 truy vấn test mỗi nhóm) + 60 ảnh ngoài phạm vi (đồng hồ, mỹ phẩm) để chỉnh τ_v.
2. Tầng instance: ảnh catalog bị biến đổi (xoay, cắt, đổi nền, mờ…) – tìm lại đúng món; tầng category: tìm SP khác cùng loại + màu.
3. 96 truy vấn dễ nhầm giữa nhóm (53 ở test); val/test tách theo product_id; có cột product_type.
4. Thiếu: 0 ảnh ngoài đời (chờ US_11) → Recall hiện tại lạc quan so với ảnh người dùng.
5. Loại số liệu: [Thật–tổng hợp], [Chưa người duyệt].
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Cấu hình: `shared_data v1 (prep_shared_data.py seed 42)`, seed 42; lệnh tái lập `python src/scripts/build_eval_visual.py`.

## 1. Vì sao phải "tổng hợp" truy vấn
FPI chỉ có **1 ảnh studio 60×80/SP** (EDA US_09) → không có "ảnh cùng SP khác góc" thật. Do đó bộ đánh giá gồm 3 tầng, mỗi tầng trả lời một câu hỏi khác nhau:

| Tầng | Câu hỏi đo | Cách tạo | GT | Số truy vấn (val/test) |
|---|---|---|---|---|
| `instance` | Có tìm lại **đúng SP** khi ảnh bị biến dạng (góc, sáng, nền, chất lượng) không? | Biến đổi có kiểm soát ảnh gốc của SP; ảnh gốc vẫn nằm trong index | 1 `product_id` | 400 (160/240), 100/nhóm |
| `category` | Với **SP khác** (chưa có trong catalog), có trả về SP cùng loại + cùng màu không? | Ảnh thật của SP **held-out** trong 44.072 dòng FPI gốc (không thuộc catalog). **Mũ**: FPI không còn SP mũ held-out → **leave-one-out** (ảnh SP trong catalog, loại chính nó khỏi kết quả qua cột `exclude_ids`) | mọi SP catalog cùng `articleType` + `baseColour` (trung vị 31 SP) | 200 (80/120), 50/nhóm |
| `ood` (file riêng) | Có nhận ra ảnh **ngoài phạm vi** để nói "chưa thấy SP giống" (τ_v) không? | Ảnh thật FPI thuộc Personal Care (30) và Watches (30) – ngoài 4 nhóm | rỗng | 60 (24/36) |

**Lưu ý trung thực**: tầng `instance` là **xấp xỉ** cho "ảnh studio khác góc" – nó không thay thế ảnh chụp ngoài đời (khác ánh sáng thật, nền thật, góc 3D, người mặc). Số Recall tầng này thường **lạc quan** so với thực tế.

## 2. Các phép biến đổi (tầng instance, xoay vòng theo thứ tự, tham số ngẫu nhiên seed 42 ghi trong cột `transform`)

| Biến đổi | Tham số | Mô phỏng | Số truy vấn |
|---|---|---|---|
| `crop_offset` | giữ 70–85 % cạnh, lệch ngẫu nhiên | chụp lệch/thiếu một phần | 60 |
| `rotate` | ±8–15°, nền trắng | cầm máy nghiêng | 60 |
| `color_jitter` | độ sáng/tương phản/bão hoà × 0,7–1,3 | ánh sáng khác | 56 |
| `hflip_scale` | lật ngang + thu 75–90 % | góc đối xứng, xa hơn | 56 |
| `background` | tách nền trắng bằng ngưỡng, thu 70–85 %, dán lên nền màu có nhiễu | đặt trên bàn/sàn | 56 |
| `lowres_jpeg` | thu 40–60 % rồi phóng lại + JPEG q=20–40 | ảnh chụp màn hình/nén mạnh | 56 |
| `combo` | xoay 5–10° + sáng 0,75–1,25 + nền nhiễu | tổ hợp khó nhất | 56 |

## 3. Truy vấn dễ nhầm giữa nhóm (`hard_cross_type`)
Tiêu chí **độc lập với mọi model được benchmark** (tránh thiên vị): trong không gian pixel thô (thumbnail 16×16 RGB, trừ trung bình, cosine), ảnh gốc của SP có **≥ 2/5 láng giềng gần nhất thuộc product_type khác**. Tỉ lệ SP catalog bị gắn cờ: headwear 17,75 %, accessory 4,43 %, clothing 2,41 %, footwear 1,50 %. Khi lấy mẫu, mỗi nhóm ưu tiên tối đa 25 SP "khó" → **96 truy vấn hard_cross_type (53 ở test)**. Ví dụ điển hình: mũ lưỡi trai tối màu chụp nghiêng gần giống túi/giày tối màu ở độ phân giải 60×80.

Ghi chú: các ví dụ "sandal vs dép xỏ ngón", "túi nhỏ vs ví" trong kế hoạch là nhầm **trong cùng nhóm** – được đo bằng `SubP@5`/`cat_P@5` ở tầng category, không phải cờ hard_cross_type.

## 4. Chia val/test & chống rò rỉ
- Chia theo **SP** (mỗi SP xuất hiện tối đa 1 lần ở tầng instance) → SP val và SP test không trùng (test tự động).
- Tỉ lệ 40 % val / 60 % test trong từng nhóm. **Val** chỉ dùng chọn siêu tham số (τ gate, λ adapter, τ_v); **mọi số báo cáo lấy trên test**.
- Adapter I3 học trên 800 SP **không xuất hiện trong eval_visual** (cả val lẫn test) với seed biến đổi khác (7).

## 5. Định dạng `eval_visual.csv`

| Cột | Ý nghĩa |
|---|---|
| `query_id` | `vq_inst_<nhóm>_<n>` / `vq_cat_<nhóm>_<n>` |
| `query_image` | đường dẫn tương đối tới `eval/queries/*.jpg` |
| `gt_product_ids` | các `product_id` đúng, phân tách bằng `|` |
| `product_type`, `sub_category`, `article_type`, `base_colour` | nhãn của truy vấn (theo catalog/taxonomy tạm) |
| `split` | `val` / `test` |
| `tier` | `instance` / `category` |
| `source` | `fpi_catalog_transformed` / `fpi_heldout_other_product` / `fpi_catalog_leave_one_out` |
| `hard_cross_type` | True/False (mục 3) |
| `transform` | tên + tham số biến đổi |
| `exclude_ids` | `product_id` phải loại khỏi kết quả (leave-one-out) |
| `origin` | nguồn gốc truy vấn: tất cả do tác nhân Khoa **sinh tự động**, **chưa có người duyệt** |

## 6. Việc còn lại (cần người thật)
1. **Chụp 80–100 ảnh ngoài đời** (giày 25 / quần áo 25 / mũ 15 / phụ kiện 15) của SP *có thật trong catalog* hoặc SP cùng loại; thêm vào CSV với `tier=real_world`, `source=team_photo`, `origin=chụp bởi <tên>` → chạy lại `bench_image_embed.py --model <m>` (cache catalog được giữ, chỉ embed truy vấn mới).
2. Hai người duyệt ngẫu nhiên 50 truy vấn tầng category (GT theo articleType+màu có thể quá rộng/hẹp) – ghi kết quả đồng thuận.
3. Khi taxonomy (US_49) chốt lại `heel_flat*`, `wide_brim*`, beanie trong `Caps` → sinh lại CSV (seed giữ nguyên).
