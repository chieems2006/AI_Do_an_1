# US_17 – Script đánh giá tự động (`metrics.py`, `run_eval.py`)

| Mục | Nội dung |
|---|---|
| Mã US | US_17 (3 pt, Sprint 2) – Owner: Hoàng, Support: Khoa |
| Mục tiêu | Tính Recall@K, MRR, NDCG, Hit@K, F1, latency chỉ với một lệnh, nhất quán cho mọi benchmark |
| Đầu ra | `src/msa/eval/metrics.py`, `src/msa/eval/run_eval.py`, `tests/test_metrics.py` |
| Tiêu chí nghiệm thu | Unit test trên dữ liệu giả cho kết quả khớp tính tay |
| Trạng thái | **Hoàn thành** – 10 test pass (phép tính tay ghi trong comment của test) |

## 1. Hàm (tên cố định theo mục 5.3)

| Hàm | Định nghĩa (1 truy vấn) | Ghi chú |
|---|---|---|
| `recall_at_k(ret, rel, k)` | \|top-k ∩ rel\| / \|rel\| | rel rỗng → 0 |
| `precision_at_k(ret, rel, k)` | \|top-k ∩ rel\| / k | mẫu số luôn là k |
| `hit_at_k(ret, rel, k)` | 1 nếu có ≥ 1 id đúng trong top-k | |
| `mrr(ret, rel, k=None)` | 1/hạng của id đúng đầu tiên | trung bình qua truy vấn = MRR |
| `ndcg_at_k(ret, rel, k)` | DCG/IDCG, discount log2(i+1) | rel là dict → graded gain |
| `average_precision`, `mean_average_precision` | Σ P@i·rel_i / min(\|rel\|, k) | mAP |
| `cross_type_error_at_k(types, qtype, k)` | tỉ lệ kết quả top-k khác product_type của truy vấn | chỉ tiêu US_30: ≤ 10% |
| `f1_tokens(pred, gold)`, `exact_match` | F1 token kiểu SQuAD sau `normalize_vi` (NFC, chữ thường, bỏ dấu câu, **giữ dấu thanh**) | |
| `latency_summary(ms)` | n, mean, p50, p95, p99, max (nội suy tuyến tính) | latency lấy median ≥ 3 lần chạy |
| `evaluate_ranking`, `classification_report` | gộp độ đo xếp hạng; accuracy/macro-F1/ma trận nhầm lẫn cho router | |

## 2. CLI

```bash
cd src
python -m msa.eval.run_eval --task visual --pred preds_visual.jsonl --k 1,5,10 --out ../results/eval_visual.json
python -m msa.eval.run_eval --task qa     --pred preds_qa.jsonl       # retrieval + F1 + tỉ lệ từ chối đúng/sai
python -m msa.eval.run_eval --task router --pred preds_router.jsonl   # accuracy, macro-F1, confusion
```
Định dạng JSONL từng task ghi trong docstring `run_eval.py`. Khoa (visual), Chiến (qa), Trung (router) chỉ cần xuất file dự đoán đúng định dạng.

## 3. Đã dùng thật ở đâu
- `bench_text_embed.py` (US_23): Hit@1/5/10, MRR@10, NDCG@10, latency_summary.
- `eval_api.py` (US_30/37/38): cross_type_error@5, latency_summary.

## 4. Việc còn lại
- Khoa/Chiến/Trung xuất file dự đoán theo định dạng trên để chạy chung một lệnh (N10–N11).
