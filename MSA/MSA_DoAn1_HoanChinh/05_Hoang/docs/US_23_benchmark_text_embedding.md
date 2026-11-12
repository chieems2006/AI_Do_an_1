# US_23 – Benchmark text-embedding cho khâu retrieval của RAG

| Mục | Nội dung |
|---|---|
| Mã US | US_23 (5 pt, Sprint 2) – Owner: Hoàng, Support: Chiến |
| Mục tiêu | So sánh các text-embedding đa ngôn ngữ / tiếng Việt trên review thật để chọn embedding cho RAG |
| Đầu ra | `src/scripts/bench_text_embed.py`, `results/bench_text_embed.csv` (từng lần chạy), `results/bench_text_embed_summary.csv` (mean ± std), `results/bench_text_embed.json`, `results/bench_runs/*.json` + `per_query_*.jsonl`; dữ liệu cho sheet "3_Khảo sát phiên bản" Bảng C |
| Tiêu chí nghiệm thu | Cùng chunking, cùng top-K cho mọi model; ghi cấu hình; ≥ 3 model; ≥ 3 lần chạy |
| Trạng thái | **Hoàn thành** – 5 cấu hình (2 baseline TF-IDF + 3 model neural), 3 seed mỗi cấu hình, có bộ eval_qa của Chiến. `BAAI/bge-m3` **bỏ** (lý do ở mục 4) |

## Tóm tắt 5 dòng
1. So 5 cấu hình text-embedding × 3 seed trên eval_qa của Chiến (208 câu), cùng chunking (1 review = 1 chunk), cùng top-K.
2. Phương pháp từ vựng thắng: TF-IDF word Hit@5 trong SP 0,875 > TF-IDF char 0,856 > e5-small 0,803 > MiniLM-L12 0,794 > vn-sbert 0,775.
3. Kho chunk khác Chiến (chỉ review, 9.403 chunk) và chưa thử hybrid → số không so trực tiếp với Bảng C của Chiến (QUYET_DINH mục G3).
4. bge-m3 bỏ vì RAM (máy 7 GB dùng chung, bị OOM-kill).
5. Loại số liệu: [Thật–thật] trên câu hỏi [Chưa người duyệt]; latency nhiễu do máy dùng chung.
Thuật ngữ và nhãn loại số liệu: `00_Chung/THUAT_NGU.md`.


## 1. Cấu hình (giống nhau cho mọi model)

| Tham số | Giá trị |
|---|---|
| Dữ liệu | `shared_data v1 (prep_shared_data.py seed 42)` – ViMRHP Fashion, 428 SP (bỏ DongHo), **9.403 review = 9.403 chunk** |
| Chunking | 1 review = 1 chunk, cắt 100 từ đầu (≈ 1% review > 100 từ); `max_seq_length = 256` cho model neural |
| Tìm kiếm | cosine trên vector L2-normalize (tương đương FAISS IndexFlatIP), **top-50 chunk** → gộp theo `product_id` bằng max (bộ A, B, C-product); top-10 chunk (C-evidence) |
| Model | `tfidf_word` (word 1–2gram, sublinear tf) · `tfidf_char` (char_wb 2–4gram) · `intfloat/multilingual-e5-small` (prefix `query:`/`passage:`) · `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` · `keepitreal/vietnamese-sbert` (không tách từ PhoBERT) |
| Seed | 42, 43, 44 (đổi review được giữ lại làm truy vấn ở bộ A, đổi thứ tự mẫu latency) |
| Máy | 2 CPU, `torch.set_num_threads(2)`, chạy song song với tác nhân khác (latency là cận trên) |
| Lệnh | `for m in tfidf_word tfidf_char e5-small minilm-l12 vn-sbert; do python src/scripts/bench_text_embed.py --models $m --seeds 42,43,44 --eval-qa ../03_Chien/eval/eval_qa.jsonl; done; python src/scripts/bench_text_embed.py --summarize-only` |

## 2. Bộ đánh giá

| Bộ | Truy vấn | Ground truth | Bản chất |
|---|---|---|---|
| **C – eval_qa (Chiến)** | 208 câu `answerable=true` có `evidence_review_ids` (trên 280 câu; 251 câu `origin=llm_gemini`, 29 câu tác nhân viết tay; **chưa có người thật duyệt**, `reviewed_by=[]`) | `inprod`: review bằng chứng trong review của đúng SP (bối cảnh RAG khi đã biết product_id); `global`: review bằng chứng trên toàn corpus; `product`: đúng product_id | Gần bài toán RAG nhất |
| A – review→product (proxy) | 428 review (≥ 8 từ) giữ lại, 1/SP theo seed | product_id của review | Proxy tự tạo; review rất chung chung ("giao nhanh, đẹp") nên khó |
| B – title→product (proxy) | 428 tên SP | product_id | Proxy; corpus chỉ có review, không có tên |

## 3. Kết quả THẬT (mean qua 3 seed; std = 0 với bộ B, C vì truy vấn cố định)

### 3.1 Bộ C – eval_qa của Chiến (208 câu)

| Model | inprod Hit@1 | inprod Hit@5 | inprod MRR@10 | global Hit@5 (chunk) | product Hit@1 | product Hit@5 | product MRR@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| tfidf_word | **0,481** | **0,875** | **0,632** | 0,154 | **0,125** | 0,284 | 0,193 |
| tfidf_char | 0,447 | 0,856 | 0,624 | **0,159** | 0,115 | **0,298** | **0,196** |
| e5-small | 0,385 | 0,803 | 0,573 | 0,130 | 0,101 | 0,236 | 0,161 |
| minilm-l12 | 0,354 | 0,794 | 0,540 | 0,029 | 0,033 | 0,129 | 0,078 |
| vn-sbert | 0,388 | 0,775 | 0,551 | 0,077 | 0,062 | 0,172 | 0,118 |

### 3.2 Bộ proxy A, B và latency

| Model | A Hit@1 | A Hit@5 | A MRR@10 | B Hit@1 | B Hit@5 | B MRR@10 | Latency 1 truy vấn p50 (ms) | p95 (ms) | Số chiều |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tfidf_word | 0,060 ± 0,011 | 0,147 ± 0,012 | 0,100 ± 0,011 | 0,175 | 0,341 | 0,250 | 5,7 | 11,3 | 81.535 (sparse) |
| tfidf_char | **0,086 ± 0,009** | **0,167 ± 0,012** | **0,122 ± 0,009** | 0,173 | **0,364** | **0,258** | 22,8 | 28,1 | 51.655 (sparse) |
| e5-small | 0,065 ± 0,005 | 0,145 ± 0,020 | 0,102 ± 0,006 | 0,150 | 0,266 | 0,203 | 465,8 | 2.064,8 | 384 |
| minilm-l12 | 0,051 ± 0,011 | 0,119 ± 0,008 | 0,079 ± 0,009 | 0,058 | 0,124 | 0,083 | 284,6 | 1.593,2 | 384 |
| vn-sbert | 0,072 ± 0,005 | 0,155 ± 0,011 | 0,110 ± 0,007 | 0,082 | 0,175 | 0,123 | 221,1 | 1.769,5 | 768 |

Latency = encode 1 câu + tìm trên 9.403 chunk + gộp, median của 3 seed (100 truy vấn/seed). Latency model neural bị phóng đại mạnh do CPU dùng chung (cùng e5-small ở lượt đầu chạy đo được p50 103–239 ms) → **chỉ so sánh tương đối**, cần đo lại trên máy rảnh.

## 4. Nhận xét & đề xuất

1. **Baseline lexical thắng mọi model neural nhỏ** trên cả 3 bộ. Với RAG trong phạm vi 1 sản phẩm (bối cảnh thực tế của `/qa`), `tfidf_word` đạt Hit@5 = 0,875, cao hơn e5-small (0,803) 7,2 điểm.
2. **Thiên lệch có thể có**: 90% câu eval_qa do Gemini sinh từ chính review → trùng từ vựng với review, có lợi cho TF-IDF. Cần tách kết quả theo `origin` (29 câu viết tay) và có người thật duyệt trước khi chốt.
3. Trong nhóm neural: e5-small tốt nhất ở bộ C (inprod Hit@5 0,803; product Hit@5 0,236); vn-sbert tốt nhất ở bộ A; MiniLM-L12 kém nhất, đặc biệt khi tìm toàn corpus (global Hit@5 0,029).
4. **Đề xuất cho Chiến (τ_r, RAG)**: dùng **hybrid** TF-IDF (word) + e5-small (cộng điểm chuẩn hoá hoặc RRF) và lọc theo product_id trước; đo hybrid ở lượt sau (`bench_text_embed.py` cần thêm chế độ hybrid – chưa làm).
5. **`BAAI/bge-m3` bỏ trong lượt này**: ≈ 568M tham số (XLM-R large, file trọng số ~2,2 GB fp32), tiến trình benchmark model nhỏ (~118M) đã dùng ~1,6 GB RAM và bị OOM-kill ít nhất 2 lần khi nhiều tác nhân cùng chạy trên máy 7 GB; mã hoá 9.403 chunk ước tính > 30 phút trên 2 CPU bận. Đã có sẵn khoá `bge-m3`/`e5-base` trong script để chạy trên máy nhóm: `python src/scripts/bench_text_embed.py --models bge-m3 --eval-qa ...`.

## 5. Việc còn lại
- Chạy bge-m3 và e5-base trên máy có ≥ 4 GB RAM trống; thêm hybrid.
- Tách số liệu theo `origin` của eval_qa; chạy lại khi Chiến có bản đã người thật duyệt.
- Đo lại latency khi máy không bị chia CPU; điền sheet "3_Khảo sát phiên bản" Bảng C bằng `results/bench_text_embed_summary.csv`.
