# THIẾT KẾ CHUNG – do Tác nhân 1 (chuyên gia thiết kế AI) ban hành cho 5 thành viên

Đề tài: **AI Agent trợ lý mua sắm thời trang đa phương thức (MSA)** – Đồ án 1, 3 tuần (05/11 – 25/11/2026).
Nguồn kế hoạch: `MSA_PLAN_v2.xlsx` (bản text từng sheet ở `/home/claude/work/sheets/*.tsv`).

## 1. Mục tiêu của lượt làm việc này

Mỗi thành viên tạo **toàn bộ sản phẩm đầu ra (cột DOCS) có thể làm được ngay bây giờ** cho các user story mình là Owner,
đúng tiêu chí TEST trong Backlog, và ghi rõ phần nào cần chạy trên máy thật với dữ liệu/model thật.

## 2. Ràng buộc môi trường (BẮT BUỘC đọc)

- Môi trường làm việc KHÔNG truy cập được HuggingFace, Kaggle, sàn TMĐT, Gemini API. `pip install` thì được (PyPI mở).
- Vì vậy: **không có dữ liệu thật, không có model thật, không có số đo thật.**
- **CẤM bịa số liệu thực nghiệm** (Recall, MRR, Hit@K, latency, chi phí, số sản phẩm thu thập…). Ô kết quả để `CHƯA ĐO` kèm lệnh/script sẽ sinh ra số đó.
- Được phép ghi thông tin công khai đã biết (năm ra mắt model, số chiều embedding, license dataset, giá API công bố…) nhưng phải kèm nguồn (tên paper/trang chính thức) và gắn nhãn `[cần xác minh]` nếu không chắc chắn hoặc có thể đã thay đổi (giá API, tên model Gemini, license).
- Code phải **chạy được và có test** trên dữ liệu giả (synthetic) sinh trong code: dùng `DummyEmbedder` thay CLIP khi không tải được model, mock Gemini khi không có key. Chạy test bằng `python -m pytest -q` trong folder của mình và ghi kết quả vào README.
- Thư viện đã có: numpy, pandas. Có thể `pip install --break-system-packages faiss-cpu fastapi uvicorn httpx pytest pillow imagehash pydantic` nếu cần. Không cài torch/gradio nếu không cần chạy (code UI vẫn viết, chỉ cần import an toàn / kiểm tra cú pháp bằng `python -m py_compile`).

## 3. Ngôn ngữ & trình bày

- Tài liệu viết **tiếng Việt có dấu**, rõ ràng, có bảng; thuật ngữ chuyên môn giữ tiếng Anh khi cần (Recall@K, FAISS…).
- Mỗi file tài liệu mở đầu bằng: mã US, mục tiêu, đầu ra, tiêu chí nghiệm thu, trạng thái (`Hoàn thành` / `Khung sẵn – cần dữ liệu thật` / `Chưa làm`).
- Code: Python 3.10+, có docstring tiếng Việt ngắn, type hint, không hard-code key.

## 4. Cấu trúc folder của mỗi thành viên

```
<NN_TenThanhVien>/
├── README.md            # Bảng tổng hợp: US nào → file nào → trạng thái → việc còn lại khi có dữ liệu thật; kết quả pytest
├── docs/                # Tài liệu, bảng khảo sát, báo cáo, biên bản…
├── src/                 # Code (đường dẫn trong repo chung ghi ở đầu file, vd: "# repo: src/msa/search/visual.py")
├── eval/ hoặc data/     # Bộ đánh giá, template CSV/JSONL, file mẫu
└── tests/               # pytest chạy được trên dữ liệu giả
```

## 5. Hợp đồng chung (để code 5 người ghép được với nhau)

### 5.1 Schema sản phẩm (US_05 – Trung chốt; mọi người dùng y nguyên tên trường)
`product_id, title, category, brand, price, currency, colors, sizes, description, specs, image_paths, rating, rating_count, reviews, source, source_url, license, product_type, sub_category, gender, size_system, view_type, variant_id, language`
- `product_type` ∈ {`footwear`, `clothing`, `headwear`, `accessory`}
- `sub_category`: footwear{sneaker, leather_shoe, sandal, boot}; clothing{top, bottom, dress, outerwear}; headwear{cap, beanie, bucket, wide_brim}; accessory{bag, belt, eyewear}; ngoài ra `unknown`.
- `size_system` ∈ {`EU`, `US`, `UK`, `VN`, `alpha` (S–XL), `free`, `numeric_waist`, `none`}
- Catalog lưu `data/processed/catalog.parquet`; ảnh ở `data/images/<product_id>/<n>.jpg`.

### 5.2 Định dạng response chung của mọi endpoint/công cụ
```json
{"route": "visual|qa|search|compare|gemini_chitchat|gemini_ood|clarify",
 "confidence": 0.0, "source": "internal|gemini|cache",
 "answer": "text tiếng Việt", "items": [ {"product_id": "...", "title": "...", "price": 0, "score": 0.0, "image": "..."} ],
 "citations": [ {"product_id": "...", "field": "description|review|specs", "chunk_id": "..."} ],
 "latency_ms": 0, "request_id": "uuid"}
```
Mỗi request ghi 1 dòng JSON vào `logs/requests.jsonl`.

### 5.3 Module và chủ sở hữu (tên hàm cố định để gọi chéo)
| Module (repo) | Owner | Giao diện chính |
|---|---|---|
| `src/msa/llm_gateway.py` | Hoàng | `class LLMGateway: generate(prompt:str, system:str|None=None, **kw) -> dict{answer, source, cached, tokens_in, tokens_out, latency_ms, error}`; đọc `GEMINI_API_KEY`, `GEMINI_MODEL` (mặc định `gemini-3.5-flash`, ghi `[cần xác minh]`); timeout, retry/backoff 429, cache exact-match SQLite; chế độ `MSA_LLM_MOCK=1` |
| `src/msa/eval/metrics.py` | Hoàng | `recall_at_k, precision_at_k, mrr, ndcg_at_k, hit_at_k, average_precision, f1_tokens, cross_type_error_at_k` |
| `src/msa/api/main.py` | Hoàng | FastAPI: `/search/image`, `/search/text`, `/compare`, `/qa`, `/chat`, validate ảnh |
| `src/msa/search/visual.py`, `src/msa/embed/image_embedders.py`, `scripts/build_index.py` | Khoa | `ImageEmbedder.embed(images)->np.ndarray (L2-normalized)`; `VisualSearcher.search(image, k=10, product_type=None) -> list[dict{product_id, score, product_type}]`; `type_gate(image)->(product_type, conf)` |
| `src/msa/rag/*`, `scripts/02_crawl_vn.py`, `prompts/gemini_fallback.md` | Chiến | `RAGPipeline.answer(question:str, product_id:str|None) -> dict{answer, citations, retrieval_score, refused}`; τ_r |
| `scripts/03_clean.py`, `app/app.py`, `scripts/bench_llm.py`, `scripts/summarize_reviews.py` | Tuấn Đạt | UI gọi API qua HTTP; card sản phẩm; nhãn "Trả lời bởi Gemini" / "Từ dữ liệu cửa hàng" |
| `src/msa/agent/router.py`, `docs/architecture.md`, `schema.md`, `taxonomy.md` | Trung | `Router.route(text:str|None, image:bytes|None, session:dict|None) -> dict{route, confidence, needs_clarification}`; `Agent.handle(...)` gọi công cụ nội bộ trước, Gemini khi chitchat/ood/câu khó/điểm < τ |

Ngưỡng mặc định (sẽ hiệu chỉnh khi có số đo): `τ_v = 0.25` (cosine top-1 visual), `τ_r = 0.35` (retrieval), `τ_intent = 0.6`.

> **Cập nhật Tác nhân 2 (xem `QUYET_DINH_CAN_CHOT.md` mục C):** `τ_v = 0.25` đã được đo là **không loại được ảnh ngoài phạm vi nào với cả 5 model** → bỏ giá trị cố định; τ_v đi theo model, đọc từ `indexes/<model>/config.json` (FashionCLIP 0,7039; DINOv2-S 0,5923; SigLIP B/16 0,7531). `τ_r` thực tế dùng 0,0 (Chiến – thang điểm retriever khác nhau, AUC tách câu có/không đáp án chỉ 0,72–0,77). Hợp đồng §5.2 đề xuất thêm `source="fallback"` (mục D).

### 5.4 Quy tắc Gemini (áp dụng cho mọi người)
Chỉ gửi text, không gửi ảnh; không nêu giá/size/tồn kho nếu không có ngữ cảnh từ DB; mọi câu trả lời Gemini có `source="gemini"` và UI hiện nhãn; QA thiếu dữ kiện sản phẩm thì giữ "chưa có thông tin" – Gemini không bù.

## 6. Tiêu chuẩn hoàn thành của lượt này
1. Mọi US Owner có file đầu ra tương ứng (hoặc lý do rõ ràng vì sao chưa thể).
2. README của thành viên có bảng truy vết US → file → trạng thái → việc còn lại.
3. pytest pass (ghi số test pass vào README).
4. Không có số liệu thực nghiệm bịa.

---
## 7. CẬP NHẬT (23:45): ĐÃ CÓ DỮ LIỆU THẬT, MODEL THẬT, GEMINI THẬT – ưu tiên hơn mục 2

Mục 2 (không có dữ liệu) **không còn đúng**. Bây giờ:

### 7.1 Mạng
- HuggingFace mở hoàn toàn (`huggingface_hub`, `transformers`, `open_clip`, `sentence-transformers` tải được trọng số). PyPI mở.
- Gemini API mở (`generativelanguage.googleapis.com`). Kaggle, sàn TMĐT (Tiki chặn IP cloud, trả 403), `*.susercontent.com`, S3 ABO vẫn KHÔNG truy cập được.
- Đã cài: torch 2.x (chạy CPU), torchvision, open_clip_torch, transformers, sentence-transformers, pyarrow, matplotlib, scikit-learn, faiss-cpu, fastapi, pytest, imagehash.
- Máy chỉ có **2 CPU, 7 GB RAM, ~20 GB đĩa trống**: chạy model nặng ở chế độ nền, `torch.set_num_threads(2)`, batch nhỏ; KHÔNG dùng ViT-L/14 trở lên trên toàn catalog (nếu muốn thì chỉ trên tập con và ghi rõ).

### 7.2 Dữ liệu thật dùng chung (Tác nhân 1 đã chuẩn bị) – `/home/claude/work/shared_data/`
| File | Nội dung |
|---|---|
| `catalog_fpi.parquet` | **4.593 SP thật** từ Fashion Product Images (small, HF `ashraq/fashion-product-images-small`, 44.072 dòng gốc), đã theo schema mục 5.1: footwear 1.400 / clothing 2.200 / accessory 700 / headwear 293 (lấy hết – **thiếu quota 300**, chỉ có Caps 283, Hat 3, Headband 7; **không có boot, beanie, bucket**). `sub_category` có dấu `*` là tạm (heel_flat*, wide_brim*) – Trung chốt trong taxonomy. Trường gốc giữ ở `category` và `specs.articleType`. |
| `fpi_images/<id>.jpg` | Ảnh thật, **độ phân giải thấp 60×80** (hạn chế quan trọng – phải nêu trong báo cáo) |
| `vimrhp_fashion_products.jsonl` | **509 SP Shopee VN + 11.009 review tiếng Việt thật** (ViMRHP, NLDB 2025, HF `trucmtnguyen/ViMRHP`, **CC BY-NC-ND 4.0**: dùng nội bộ cho học thuật, không phát hành lại bản đã chỉnh). Nhóm con: ThoiTrangNu 94, ThoiTrangNam 87, GiayDepNu 92, GiayDepNam 79, PhuKienNu 76, DongHo 81 (đồng hồ ngoài phạm vi → loại). Có tên SP, review, rating, DetailRating; KHÔNG có mô tả/giá/size. Thay thế cho phần crawl Tiki (kế hoạch B). |
| `stats.json`, `scripts/prep_shared_data.py` | Thống kê + script tái lập (seed 42) |
| Dữ liệu gốc | `/home/claude/realdata/fpi/data/*.parquet`, `/home/claude/realdata/vimrhp/Annotation/Fashion-*.json`; trọng số CLIP B/32 tại `/home/claude/realdata/models/clip-b32/` (HF cache cũng dùng được) |

**KHÔNG sửa** các file trong `shared_data/` và `realdata/`; muốn biến đổi thì ghi ra folder của mình.

### 7.3 Gemini
- Key nằm ở một file `.env` riêng **ngoài repo** (đường dẫn truyền qua biến `MSA_ENV_FILE`/`MSA_GEMINI_KEY_FILE`, hoặc đặt thẳng biến `GEMINI_API_KEY`) (dạng `GEMINI_API_KEY=...`). Nạp bằng `set -a; . <file>; set +a` hoặc đọc file trong Python lúc chạy.
- **TUYỆT ĐỐI KHÔNG** in key, ghi key vào file kết quả/log/README/test, hay copy file đó. Kiểm tra bằng `grep -r "AQ\." <folder>` trước khi kết thúc – phải rỗng.
- Model: `gemini-3.5-flash` (đã xác nhận tồn tại và gọi được). Model này mặc định "suy nghĩ" nhiều (câu trả lời 22 token dùng 379 token thinking) → đo cả cấu hình hạ thinking (`generationConfig.thinkingConfig.thinkingBudget` hoặc tương đương – kiểm tra tài liệu/thử) và ghi token thực tế từ `usageMetadata`.
- **Ngân sách: mỗi thành viên tối đa 250 lời gọi Gemini** trong lượt này; dùng cache; tests mặc định chạy mock, test gọi thật đánh dấu `@pytest.mark.live` và bỏ qua mặc định.
- Giá tiền/token: không tra được chắc chắn → ghi đơn giá vào config với nhãn `[cần xác minh – điền theo bảng giá Google hiện hành]`; báo cáo chi phí dưới dạng **token/100 lượt (đo thật)** + công thức quy ra tiền.

### 7.4 Quy tắc số liệu (thay mục 2)
- Số liệu nào **đo thật** trên dữ liệu thật → ghi vào bảng, kèm file kết quả (CSV/JSON) + lệnh tái lập + cấu hình (model, seed, data version = `shared_data v1 (prep_shared_data.py seed 42)`).
- Phần nào vẫn không làm được (crawl Tiki, ảnh Shopee, 80-100 ảnh tự chụp ngoài đời, duyệt nhãn 2 người thật) → để `CHƯA ĐO` và nói rõ lý do + việc nhóm phải làm.
- Câu hỏi/đáp án do mô hình hoặc tác nhân sinh phải gắn `origin` tương ứng; không ghi là "người duyệt" khi chưa có người thật duyệt.

---
## 8. CẬP NHẬT của Tác nhân 2 (rà soát chéo, 05/11/2026)
- Thuật ngữ + nhãn nguồn gốc số liệu dùng chung: `00_Chung/THUAT_NGU.md`.
- Các mâu thuẫn giữa thành viên và quyết định đề xuất: `00_Chung/QUYET_DINH_CAN_CHOT.md` (mũ 285; trang sức/tất ngoài phạm vi; τ_v theo model; `source="fallback"`; Bảng F chạy thật → DINOv2-S hạng 1; đơn vị token/100 lượt).
- Nhật ký thay đổi theo thành viên: `CHANGELOG_TAC_NHAN_2.md` ở gốc folder.
