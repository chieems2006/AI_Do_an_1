# US_07 – Crawl bổ sung dữ liệu sàn TMĐT Việt Nam: kiểm tra robots.txt/ToS và kế hoạch B

| Mục | Nội dung |
|---|---|
| Mã US | US_07 (5 pt, Sprint 1, Owner: Chiến, Support: Hoàng) |
| Mục tiêu | Có dữ liệu tiếng Việt thực tế (tên, giá, mô tả, size, ảnh, review) cho phần hỏi đáp |
| Đầu ra | `src/scripts/02_crawl_vn.py` (crawler lịch sự + parser tách biệt), ghi chú robots/ToS (file này), bằng chứng `results/crawl_robots_probe.json`, file raw (chưa có – xem dưới) |
| Tiêu chí nghiệm thu | ≥ 300 SP và ≥ 1.000 review tiếng Việt; không bị block; có bằng chứng đã kiểm tra robots/ToS |
| Trạng thái | **Khung sẵn – crawl thật không thực hiện được từ môi trường cloud**; tiêu chí số lượng đạt bằng **kế hoạch B (ViMRHP)**: 428 SP thời trang + 9.317 review tiếng Việt (sau khi bỏ đồng hồ và khử trùng) |

## 1. Sự thật của lượt làm việc này (05/11/2026)

| Kiểm tra | Kết quả thật | Bằng chứng |
|---|---|---|
| `GET https://tiki.vn/robots.txt` từ IP cloud, UA dự án | **HTTP 403** – bị chặn ngay ở robots.txt | `results/crawl_robots_probe.json` (chạy `--dry-run`, 00:09 05/11/2026) |
| `GET https://shopee.vn/robots.txt` | **Không kết nối được** (status -1, proxy môi trường không cho phép) | cùng file |
| Ảnh Shopee `*.susercontent.com` | Không truy cập được (mục 7.1 thiết kế chung) | – |
| Số trang sản phẩm đã tải | **0** – crawler tự dừng vì không đọc được robots.txt (không đọc được = không được phép) | `logs/crawl_vn_probe.log` |

Kết luận: **không crawl** trong lượt này. Không viết/không dùng bất kỳ kỹ thuật né chặn nào (giả UA trình duyệt, xoay IP/proxy, giải captcha, dùng API nội bộ không công khai).

## 2. Crawler đã viết (`src/scripts/02_crawl_vn.py`)

| Yêu cầu | Cách đáp ứng | Test |
|---|---|---|
| Kiểm robots trước mỗi URL | `RobotsGate.allowed()` dùng `urllib.robotparser`, cache theo host | `test_robots_gate_respects_disallow_and_delay` |
| robots.txt lỗi/403 | Coi là **không được phép**, không tải trang SP | `test_robots_403_means_not_allowed` |
| Delay + jitter | `max(--delay, Crawl-delay của robots) + U(0, 0.5·delay)` | `test_crawl_writes_raw_and_uses_delay` |
| User-Agent | `MSA-DoAn1-StudentBot/0.1 (academic project; small-scale; respects robots.txt)` – không email, không giả trình duyệt | `test_user_agent_has_no_email_and_is_not_browser` |
| Gặp chặn | 401/403/429/503 hoặc trang có "captcha" ⇒ **dừng hẳn** | `test_crawl_stops_on_429_and_captcha` |
| Giới hạn trang | `--max-pages` (mặc định 50) | `test_dry_run_and_max_pages` |
| Raw + log | JSONL `{fetched_at, status, record}` + `logs/crawl_vn.log` | như trên |
| Parser tách biệt | `parse_product_html()` – JSON-LD schema.org `Product` + Open Graph → dict theo schema 5.1 | `test_parser_extracts_schema_fields` |
| `--dry-run` | Chỉ kiểm robots, in danh sách URL được phép | `test_dry_run_and_max_pages` |

## 3. Nếu nhóm muốn crawl thật (từ máy cá nhân)

1. **Tự đọc** robots.txt và Điều khoản sử dụng của sàn (Tiki: `tiki.vn/robots.txt`, trang "Điều khoản sử dụng"; Shopee: `shopee.vn/robots.txt`, "Điều khoản Shopee") và ghi vào bảng dưới: ngày đọc, người đọc, điều khoản liên quan đến thu thập tự động, kết luận được/không. *Tác nhân không đọc được các trang này nên KHÔNG kết luận thay nhóm.*
2. Chỉ chạy khi ToS không cấm thu thập tự động cho mục đích học thuật; nếu cấm hoặc mơ hồ ⇒ không crawl, dùng kế hoạch B.
3. `python src/scripts/02_crawl_vn.py --urls urls.txt --dry-run` → kiểm robots; sau đó chạy thật với `--max-pages 50 --delay 5`, theo dõi log; gặp 403/429/captcha thì dừng, không thử lại.
4. Kiểm 50 mẫu ngẫu nhiên (ảnh/giá/review) theo lịch N4.

| Sàn | Ngày đọc robots | Người đọc | Ngày đọc ToS | Điều khoản về thu thập tự động | Kết luận |
|---|---|---|---|---|---|
| Tiki | (nhóm điền) | | | | |
| Shopee | (nhóm điền) | | | | |

## 4. Kế hoạch B đã áp dụng (R1, sheet Rủi ro & Quy ước)

| Mục | Nội dung |
|---|---|
| Nguồn | **ViMRHP** (Vietnamese Multimodal Review Helpfulness Prediction, NLDB 2025), HF `trucmtnguyen/ViMRHP`; Tác nhân 1 đã trích sẵn ở `shared_data/vimrhp_fashion_products.jsonl` |
| License | **CC BY-NC-ND 4.0** – chỉ dùng nội bộ, phi thương mại, học thuật; **không phát hành lại bản đã chỉnh sửa** (eval_qa có trích mã review, không chép lại toàn văn review ra ngoài repo nhóm) |
| Quy mô dùng được | 509 SP gốc → bỏ 81 SP đồng hồ (ngoài phạm vi) → **428 SP**; 9.403 review → khử 86 review trùng `comment_id` trong cùng SP → **9.317 review** (đo bằng `PYTHONPATH=src python -m msa.rag.ingest`) |
| Phân nhóm | ThoiTrangNu 94, ThoiTrangNam 87 (→ clothing), GiayDepNu 92, GiayDepNam 79 (→ footwear), PhuKienNu 76 (→ accessory) |
| Đối chiếu tiêu chí US_07 | ≥ 300 SP ✔ (428) · ≥ 1.000 review ✔ (9.317) · không bị block ✔ (không crawl) · bằng chứng robots ✔ (mục 1) |

### Hệ quả của kế hoạch B (phải nêu trong báo cáo)

- **Không có mô tả, giá, size, tồn kho, chất liệu dạng cấu trúc** – chỉ có tên SP, review, số sao, DetailRating (chất lượng / người bán / giao hàng).
  ⇒ Câu hỏi "giá bao nhiêu", "còn size 40 không" **luôn phải trả "chưa có thông tin"** (đây chính là nhóm câu answerable=false trong eval_qa).
- Giá xuất hiện rải rác trong review là **giá khách mua lúc sale** (vd "mua lúc sale 69k") – không được dùng làm giá bán (đã đưa vào prompt RAG v1.0, quy tắc 5).
- Thông tin size chỉ có dạng kinh nghiệm cá nhân ("1m56 43kg mặc XL") – RAG trả lời được kiểu "theo đánh giá của khách…", không phải bảng size.
- Không có ảnh (CDN Shopee bị chặn) ⇒ ViMRHP **không** dùng cho Visual Search; chỉ dùng cho QA/RAG.
- Domain review Shopee (teencode, không dấu, nhiều câu khen chung chung về giao hàng) khác với catalog FPI (tiếng Anh, không review) ⇒ hai nguồn tách vai trò: FPI cho visual/search, ViMRHP cho QA.
