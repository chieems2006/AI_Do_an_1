# repo: src/msa/eval/visual_metrics.py
"""Độ đo cho Visual Search (US_12). Tên hàm trùng hợp đồng `src/msa/eval/metrics.py` của Hoàng
để có thể thay thế qua lại; bản này là bản Khoa dùng cho benchmark.

Quy ước: `ranked` là list product_id theo thứ tự điểm giảm dần; `relevant` là tập product_id đúng.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence


def _rel(relevant) -> set:
    return set(relevant) if not isinstance(relevant, set) else relevant


def hit_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """1 nếu có ít nhất một SP đúng trong top-K."""
    r = _rel(relevant)
    return float(any(p in r for p in ranked[:k]))


def recall_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """|đúng ∩ top-K| / |đúng|. Với 1 SP đúng (tầng instance) thì Recall@K = Hit@K."""
    r = _rel(relevant)
    if not r:
        return 0.0
    return len(r.intersection(ranked[:k])) / len(r)


def precision_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """|đúng ∩ top-K| / K."""
    r = _rel(relevant)
    return sum(1 for p in ranked[:k] if p in r) / float(k)


def mrr(ranked: Sequence[str], relevant: Iterable[str], k: int | None = None) -> float:
    """Reciprocal rank của SP đúng đầu tiên (0 nếu không có trong top-k)."""
    r = _rel(relevant)
    for i, p in enumerate(ranked[:k] if k else ranked):
        if p in r:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """NDCG@K với độ liên quan nhị phân."""
    r = _rel(relevant)
    dcg = sum(1.0 / math.log2(i + 2) for i, p in enumerate(ranked[:k]) if p in r)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(r), k)))
    return dcg / idcg if idcg > 0 else 0.0


def average_precision(ranked: Sequence[str], relevant: Iterable[str], k: int | None = None) -> float:
    """AP (@k nếu có): trung bình precision tại các vị trí có SP đúng, chia cho min(|R|, k)."""
    r = _rel(relevant)
    if not r:
        return 0.0
    lst = ranked[:k] if k else ranked
    hits, s = 0, 0.0
    for i, p in enumerate(lst):
        if p in r:
            hits += 1
            s += hits / (i + 1)
    return s / min(len(r), len(lst) if k else len(r))


def cross_type_error_at_k(ranked_types: Sequence[str], query_type: str, k: int) -> float:
    """Tỉ lệ kết quả trong top-K thuộc product_type khác nhóm của truy vấn."""
    top = list(ranked_types[:k])
    if not top:
        return 0.0
    return sum(1 for t in top if t != query_type) / float(len(top))


def auroc(pos_scores: Sequence[float], neg_scores: Sequence[float]) -> float:
    """AUROC (xác suất điểm pos > điểm neg), dùng cho phân biệt truy vấn trong/ngoài phạm vi theo top-1 cosine."""
    pos, neg = list(pos_scores), list(neg_scores)
    if not pos or not neg:
        return float("nan")
    allv = sorted([(s, 1) for s in pos] + [(s, 0) for s in neg])
    # Mann–Whitney U với xử lý điểm bằng nhau (rank trung bình)
    ranks, i = {}, 0
    rank_sum_pos = 0.0
    n = len(allv)
    while i < n:
        j = i
        while j + 1 < n and allv[j + 1][0] == allv[i][0]:
            j += 1
        avg = (i + j) / 2 + 1
        rank_sum_pos += avg * sum(1 for t in range(i, j + 1) if allv[t][1] == 1)
        i = j + 1
    u = rank_sum_pos - len(pos) * (len(pos) + 1) / 2
    return u / (len(pos) * len(neg))
