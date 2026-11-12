# US_49 – Taxonomy 2 cấp & bảng map category giữa các nguồn

| Mục | Nội dung |
|---|---|
| Mã US | US_49 (Owner: Trung, Support: Khoa) |
| Mục tiêu | Một cây `product_type → sub_category` duy nhất + bảng map nhãn của từng nguồn về cây, có quy tắc cho ca mơ hồ, để ground truth không lệch giữa các nguồn và visual search không nhầm nhóm |
| Đầu ra | `docs/US_49_taxonomy.md` (file này), `data/category_map.csv` (254 dòng), code `src/msa/data/taxonomy.py`, catalog đã áp taxonomy `data/catalog_fpi_taxonomy_v1.parquet`, `data/vimrhp_taxonomy_v1.csv`, kiểm mẫu `data/taxonomy_audit_*_30.csv` |
| Tiêu chí nghiệm thu | (1) Mọi nhãn nguồn map được hoặc vào `unknown`/`out_of_scope`; (2) kiểm 30 mẫu/nguồn sai ≤ 3; (3) Khoa và Hoàng đọc và đồng ý |
| Trạng thái | **Hoàn thành phần kỹ thuật** (1) và (2) đo thật trên dữ liệu thật. **Còn lại:** (2) do tác nhân AI kiểm – nhóm phải kiểm lại bằng 2 người; (3) chờ Khoa, Hoàng duyệt |

## Tóm tắt 5 dòng
1. Cây 2 cấp: 4 nhóm (giày, quần áo, mũ, phụ kiện) × lá; nhãn ngoài phạm vi (tất, trang sức, đồng hồ, băng đô…) → `out_of_scope`.
2. 168/168 nhãn FPI map được; ViMRHP 509/509 khớp luật tiêu đề (giữ 349 + 12 unknown, loại 148).
3. Kiểm 30 mẫu/nguồn: 0 sai [Tác nhân kiểm]; nhưng Tác nhân 2 xem ảnh phát hiện thêm 7 mũ gán sai (mũ phớt/tai bèo → cap, beanie → cap).
4. Đề xuất thêm 2 luật tiêu đề (Hat → wide_brim, Beanie(s) → beanie); số mũ chuẩn 285 (QUYET_DINH mục A).
5. Eval của Chiến dùng trang sức/tất – trái taxonomy, xử lý ở QUYET_DINH mục B.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


Tái lập: `PYTHONPATH=src python scripts/build_category_map.py && PYTHONPATH=src python scripts/audit_taxonomy_samples.py`
Dữ liệu: `shared_data v1 (prep_shared_data.py seed 42)` + nhãn gốc FPI 44.072 dòng (`/home/claude/realdata/fpi/data/*.parquet`).

## 1. Cây taxonomy v1 (CHỐT)

| product_type | sub_category | Tên tiếng Việt | Ghi chú |
|---|---|---|---|
| `footwear` | `sneaker` | giày thể thao / casual | FPI Casual Shoes, Sports Shoes |
| | `leather_shoe` | giày da, giày tây | FPI Formal Shoes |
| | `sandal` | sandal, dép, dép kẹp | gồm Flip Flops, Sports Sandals |
| | `boot` | boot / bốt | FPI không có nhãn riêng → **luật tiêu đề** (xem §3) |
| | **`heel_flat`** | giày cao gót / búp bê (flats) | **MỚI** – thay nhãn tạm `heel_flat*` |
| `clothing` | `top` | áo (thun, sơ mi, len, nỉ, hoodie, kurta) | hoodie/sweatshirt → `top` |
| | `bottom` | quần, chân váy, legging | |
| | `dress` | váy liền, đầm, jumpsuit, romper | |
| | `outerwear` | áo khoác, blazer, áo chống nắng | |
| `headwear` | `cap` | mũ lưỡi trai, snapback | |
| | `beanie` | mũ len, skull cap | FPI `Hat` thực chất là skull cap → `beanie` |
| | `bucket` | mũ bucket | chưa có dữ liệu thật |
| | `wide_brim` | mũ rộng vành, nón chống nắng | chỉ 1 SP ViMRHP |
| `accessory` | `bag` | túi xách, balo, túi đeo | |
| | `belt` | thắt lưng | |
| | `eyewear` | kính mát, kính cận thời trang | |
| (mọi nhóm) | `unknown` | thuộc nhóm nhưng không rõ lá (bộ nhiều món, "giày" chung chung) | **không đưa vào index ảnh**, vẫn giữ trong catalog |
| `out_of_scope` | – | ngoài phạm vi Đồ án 1 | **loại khỏi catalog** |

### Quyết định cho nhãn tạm của Tác nhân 1
| Nhãn tạm | Quyết định | Lý do (dữ liệu thật) |
|---|---|---|
| `heel_flat*` (270 SP) | → lá chính thức **`heel_flat`** (thêm lá thứ 5 cho footwear) | 270 SP thật + 84 SP ViMRHP GiayDepNu là giày cao gót; gộp vào `leather_shoe` sẽ làm ground truth lệch (ảnh khác hẳn giày tây nam) |
| `wide_brim*` (3 SP) | → **`beanie`** | Xem tiêu đề thật: cả 3 là "Skull Caps" (Timberland ×2, ADIDAS Beanie) |
| `headwear/unknown` (7 SP Headband) | → **`out_of_scope`** | Băng đô là phụ kiện tóc, không phải mũ; nhất quán với ViMRHP ("băng đô" → loại) |

## 2. Quy tắc ca mơ hồ
| Ca | Quy tắc | Ví dụ thật |
|---|---|---|
| Áo khoác có mũ trùm | **Danh từ đầu tiêu đề quyết định**: "áo khoác … có mũ" → `clothing/outerwear`, chữ "mũ" chỉ là chi tiết | `shopee_18390665755` "Áo Khoác Lông 2 lớp … có mũ tai gấu" |
| Hoodie / sweatshirt | Không có chữ "khoác" → `top`; "áo khoác hoodie" → `outerwear` | FPI Sweatshirts → top |
| Khăn (quàng, choàng, lau kính) | `out_of_scope` | "Khăn lau kính Nano…" → loại (không phải kính) |
| Sandal cao gót, dép cao gót, guốc | Giày dép có "cao gót/gót nhọn/búp bê/guốc" → `heel_flat` (ưu tiên hơn sandal) | "GIÀY SANDAL CAO GÓT NỮ ĐẾ NHỌN 7-9 PHÂN" |
| Boot | FPI: tiêu đề có "Boot(s)" → `boot`; riêng `Sports Shoes` chỉ khi tên **kết thúc** bằng Boot (tránh giày đá bóng "Pre L Boot") | `fpi_53440` (giày đá bóng) → sneaker; `fpi_13360` Timberland boot → boot |
| Bộ nhiều món (set áo + quần, kurta set, tracksuit) | `clothing/unknown` | "Set Bộ Áo Thun … + Quần Short" |
| Tất/vớ, ví, đồng hồ, trang sức, cà vạt, găng tay, đồ lót, đồ ngủ, sari, mỹ phẩm, ô/dù, khẩu trang, phụ kiện tóc | `out_of_scope` | ViMRHP DongHo (81 SP) loại toàn bộ |
| Nhãn nguồn mâu thuẫn tầng trên (vd `Accessories/Belts/Tshirts`) | **articleType + tiêu đề thắng** masterCategory | "Mr.Men … T-shirt" → `clothing/top` |
| Hàng tặng (FPI Free Items) là túi | Giữ theo articleType (`bag`), loại phần còn lại của Free Items | |
| ViMRHP: SubCategory gốc chỉ là gợi ý | Lá lấy từ tiêu đề tiếng Việt; nếu nhóm GiayDep* mà tiêu đề ra quần áo → `unknown` để người duyệt | |

## 3. Bảng map nguồn (tóm tắt) – chi tiết ở `data/category_map.csv`
Cột: `source, source_label, n_rows_source, product_type, sub_category, action{keep|unknown|exclude}, rule_id, title_refinement, verified`.

### 3.1 Fashion Product Images – **toàn bộ 168 bộ nhãn (master/sub/articleType) thật, 44.072 dòng**
| Chỉ số (đo thật) | Giá trị |
|---|---|
| Số nhãn khác nhau | 168 |
| Nhãn → lá hợp lệ / `unknown` / loại | 61 / 5 / 102 |
| Nhãn **không map được** | **0 → độ phủ 100%** |
| Dòng → lá hợp lệ / `unknown` / loại | 32.735 / 142 / 11.195 |
| Phân bố dòng giữ lại theo lá | top 14.908; sneaker 4.849; bag 3.063; bottom 2.604; sandal 1.876; heel_flat 1.817; eyewear 1.073; belt 813; leather_shoe 634; dress 492; outerwear 299; cap 266; boot 21; beanie 20 |
| Loại nhiều nhất | đồng hồ 2.542; Personal Care 2.139; đồ lót 1.806; trang sức 1.079; ví 927; tất 686 |

Map articleType chính: Casual/Sports Shoes→sneaker; Formal Shoes→leather_shoe; Heels/Flats→heel_flat; Sandals/Sports Sandals/Flip Flops→sandal; Tshirts/Shirts/Tops/Sweatshirts/Sweaters/Kurtas/Kurtis/Tunics→top; Jackets/Blazers/Rain Jacket/Nehru Jackets/Waistcoat/Shrug→outerwear; Jeans/Shorts/Trousers/Track Pants/Skirts/Capris/Leggings/Jeggings/Churidar/Patiala/Salwar/Tights→bottom; Dresses/Jumpsuit/Rompers→dress; Caps→cap (+luật beanie); Hat→beanie (luật tiêu đề); túi các loại→bag; Belts→belt; Sunglasses→eyewear.

**Catalog dùng chung `catalog_fpi.parquet` (4.593 SP) sau khi áp taxonomy v1** (file mới: `data/catalog_fpi_taxonomy_v1.parquet`, không sửa `shared_data/`):

| Thay đổi so với nhãn tạm | Số SP |
|---|---|
| `footwear/heel_flat*` → `footwear/heel_flat` | 269 |
| `footwear/heel_flat*` → `footwear/boot` | 1 |
| `footwear/sneaker` → `footwear/boot` | 2 |
| `headwear/cap` → `headwear/beanie` | 17 |
| `headwear/wide_brim*` → `headwear/beanie` | 3 |
| `headwear/unknown` (Headband) → `out_of_scope` (loại) | 7 |

Kết quả: 4.586 SP trong phạm vi – footwear 1.400 / clothing 2.200 / accessory 700 / **headwear 286 (thiếu quota 300 – 14 SP)**; lá `boot` 3 SP, `beanie` 20 SP, **`bucket` 0, `wide_brim` 0** → visual search mũ chỉ ở mức demo (đúng thứ tự cắt scope ở sheet Rủi ro, mục C).

### 3.2 ViMRHP (Shopee VN, 509 SP, 6 SubCategory) – luật tiêu đề tiếng Việt
| SubCategory gốc | Kết quả map (đo thật) |
|---|---|
| ThoiTrangNu (94) | outerwear 54, top 20, bottom 7, dress 1, unknown 7, loại 5 |
| ThoiTrangNam (87) | top 53, outerwear 22, bottom 5, unknown 4, **cap 1, belt 1** (nhãn gốc lệch → tiêu đề sửa), loại 1 |
| GiayDepNu (92) | heel_flat 84, sandal 8 |
| GiayDepNam (79) | sandal 75, sneaker 2, unknown 1 (giày bảo hộ), loại 1 (keo dán giày) |
| PhuKienNu (76) | eyewear 6, belt 5, cap 3, wide_brim 1, top 1, **loại 60** (trang sức, tất, phụ kiện tóc, khẩu trang, ô…) |
| DongHo (81) | **loại toàn bộ** |
| **Tổng** | giữ 349, unknown 12, loại 148; 7.575 review thuộc 349 SP giữ (cả 12 unknown: 7.833); luật tiêu đề khớp 509/509 (100%) |

Nhận xét: ViMRHP **lệch mạnh về sandal/cao gót/áo khoác**, gần như không có giày thể thao (2), mũ (5) và túi (0) → dùng cho RAG review tiếng Việt, không dùng làm nguồn cân bằng nhóm.

### 3.3 Nguồn chưa có file – map theo tài liệu `[cần xác minh]`
`clothing_dataset_cc0` (T-Shirt, Longsleeve, Pants, Shoes, Outwear, Hat, …), `abo_amazon_berkeley_objects` (SHOES, BOOT, SANDAL, HANDBAG, …), `amazon_reviews_2023_clothing_shoes_jewelry` (đường dẫn category). Danh sách nhãn lấy theo tài liệu công khai, **chưa đối chiếu file thật** – khi tải được phải chạy lại script và cập nhật cột `verified`.

## 4. Kiểm 30 mẫu/nguồn (seed 42) – `results/taxonomy_audit.json`
| Nguồn | n | Sai | Mơ hồ | Đạt (sai ≤ 3) | Cách kiểm |
|---|---|---|---|---|---|
| Fashion Product Images (catalog v1) | 30 | **0** | 2 | Có | tiêu đề + ảnh 60×80 (ảnh ghép đã xem) |
| ViMRHP | 30 | **0** | 1 | Có | chỉ tiêu đề (ảnh Shopee không tải được) |

**Người kiểm: tác nhân AI (vai Trung) – CHƯA phải 2 người thật.** Nhóm phải điền cột `nguoi_kiem_2` trong `data/taxonomy_audit_*_30.csv`.
Hạn chế của mẫu ngẫu nhiên: 30 mẫu FPI rơi chủ yếu vào lá lớn (top 9, bag 6); 11/30 mẫu ViMRHP là đồng hồ (dễ). Vì vậy kiểm thêm **6 ca khó chọn có chủ đích** (`hard_cases` trong JSON) – phát hiện và **đã sửa 1 lỗi luật**: giày đá bóng "ADIDAS … Pre L Boot Sports Shoes" bị gán `boot`.

Phát hiện phụ khi xem ảnh: nhiều ảnh quần áo FPI là **người mẫu mặc cả bộ** (thấy cả giày, áo) → rủi ro nhầm nhóm của visual search (R17) – Khoa cần đo cross-type error@K.

## 5. Mâu thuẫn cần nhóm chốt
1. Bộ `eval_router.jsonl` của Chiến coi **trang sức (dây chuyền, khuyên tai) và tất** là sản phẩm trong cửa hàng (nhãn `qa`/`search`/`compare`), trong khi taxonomy v1 đặt chúng **ngoài phạm vi**. Đề xuất: giữ taxonomy (đề tài chỉ 4 nhóm), Chiến đổi nhãn các câu đó sang `gemini_ood` hoặc thay sản phẩm.
2. Có muốn thêm lá `accessory/scarf` (khăn) hay không – hiện loại.
