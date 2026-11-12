# US_29 – Trích embedding & build FAISS index toàn danh mục

| Mục | Nội dung |
|---|---|
| Mã US | US_29 (Owner: Khoa, Support: Hoàng) – Sprint 3, 5.0 pt |
| Mục tiêu | Embed toàn bộ ảnh catalog bằng model đã chọn, lưu embedding + FAISS index để demo tìm ảnh nhanh |
| Đầu ra | `src/scripts/build_index.py`, `src/msa/search/visual.py` (`VisualSearcher.search/type_gate/query`), thư mục index `indexes/<model>/{index.faiss, embeddings.npy, meta.parquet, config.json}`, `results/build_index_<model>.json` |
| Tiêu chí nghiệm thu | Build < 30 phút cho ≥ 3.000 SP; truy vấn < 200 ms (không tính tải ảnh) |
| Trạng thái | **Hoàn thành trên catalog thật 4.593 SP** – xem số đo mục 2 và kết luận nghiệm thu mục 3 |

## 1. Thiết kế
- Index: `faiss.IndexFlatIP` trên vector L2-normalize (= cosine), tìm chính xác; thêm 4 sub-index theo `product_type` để lọc cứng khi type gate tự tin (I19).
- `VisualSearcher.query(image)` (giao diện cho Agent, response theo hợp đồng mục 5.2): embed → type gate (zero-shot prompt nếu model có text tower, ngược lại centroid) → nếu `conf ≥ gate_tau` thì tìm trong nhóm, ngược lại tìm toàn bộ → nếu top-1 cosine < τ_v thì `no_match=True`, `items=[]` và câu gợi ý *"Mình chưa thấy sản phẩm nào đủ giống… Bạn có thể mô tả bằng chữ…"*.
- **τ_v phải hiệu chỉnh theo model**: với CLIP B/32, cosine top-1 của ảnh ngoài phạm vi (đồng hồ, mỹ phẩm) có trung vị 0,804 → ngưỡng mặc định 0,25 của thiết kế chung **không loại được ảnh OOD nào (0 %)**; ngưỡng chọn trên val (p05 của truy vấn trong phạm vi) = **0,8748** loại **100 %** OOD test và giữ 99,17 % truy vấn trong phạm vi (số thật, `results/bench/clip_b32.json`). `config.json` của index lưu τ_v đã hiệu chỉnh. Index demo `indexes/best` → `indexes/fashionclip` với **τ_v = 0,7039** (max top-1 OOD val + 0,01: loại 100 % OOD test, giữ 100 % category, 84,2 % instance) và gate zero-shot τ = 0,9.
- Lệnh: `python src/scripts/build_index.py --model <m> --out indexes/<m> [--reuse-cache] --tau-v <τ_v> --gate-tau <τ>`.

## 2. Số đo thật

<!-- BUILD_RESULTS -->
| Model | Số SP | Dim | Embed catalog (s) | Từ cache? | Build tổng (s) | File index (MB) | Truy vấn e2e ms median / p95 (embed+gate+search) | Search-only ms median | Số lần đo |
|---|---|---|---|---|---|---|---|---|---|
| clip_b32 | 4593 | 512 | 1.05 | True | 206.6 | 9.41 | 464.47 / 2542.42 | 2.0197 | 90 |
| fashionclip | 4593 | 512 | 0.01 | True | 7.93 | 9.41 | 168.84 / 674.59 | 1.885 | 90 |
<!-- /BUILD_RESULTS -->

Ghi chú đo:
- Thời gian embed toàn catalog đo trong benchmark US_22 (`catalog_embed_total_s`, embed từ đầu, batch 32, 2 luồng) – đây là phần chi phối thời gian build; `build_index.py --reuse-cache` chỉ tái dùng embedding đó nên thời gian "Embed catalog" của nó ≈ 1 s.
- Máy 2 CPU **dùng chung với 4 tác nhân khác** (load average 6–8 lúc đo) → latency có nhiễu lớn; p95 cao do tranh chấp CPU, không phải do FAISS (search-only ~2 ms).
- Thời gian nạp model (`embedder_load_s`) lần đầu sau khi máy khởi động lại cao bất thường (đọc trọng số từ đĩa nguội) – không tính vào truy vấn.

## 3. Nghiệm thu
| Tiêu chí | Kết quả | Đạt? |
|---|---|---|
| Build < 30 phút, ≥ 3.000 SP | FashionCLIP: embed 4.593 ảnh 775,8 s (`results/bench/fashionclip.json`) + nạp model 7,6 s + ghi index < 1 s ≈ **13 phút** | **Đạt** |
| Truy vấn < 200 ms (không tính tải ảnh) | FashionCLIP, ảnh nạp sẵn: embed + gate + search **median 168,8 ms**, p95 674,6 ms (90 lần đo, máy dùng chung); search-only 1,9 ms | **Đạt theo median**; p95 chưa đạt do tải nền – đo lại trên máy demo |
