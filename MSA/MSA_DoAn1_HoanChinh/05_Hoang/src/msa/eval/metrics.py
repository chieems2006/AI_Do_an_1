# repo: src/msa/eval/metrics.py
"""Độ đo đánh giá dùng chung cho MSA (US_17 – Owner: Hoàng).

Quy ước: mọi hàm xếp hạng tính cho **một truy vấn** (`retrieved` = danh sách id đã xếp hạng,
`relevant` = tập id đúng). Trung bình trên nhiều truy vấn dùng `mean_over_queries` hoặc
`evaluate_ranking`. `mrr(...)` cho một truy vấn trả reciprocal rank; trung bình của nó là MRR.
"""
from __future__ import annotations

import math
import re
import string
import unicodedata
from collections import Counter
from typing import Callable, Hashable, Iterable, Mapping, Sequence

import numpy as np

Rel = Iterable[Hashable] | Mapping[Hashable, float]


def _rel_set(relevant: Rel) -> set:
    """Chuẩn hoá `relevant` (list/set/dict độ liên quan) thành tập id có độ liên quan > 0."""
    if isinstance(relevant, Mapping):
        return {k for k, v in relevant.items() if v > 0}
    return set(relevant)


def _check_k(k: int) -> None:
    if not isinstance(k, (int, np.integer)) or k <= 0:
        raise ValueError(f"k phải là số nguyên dương, nhận {k!r}")


def recall_at_k(retrieved: Sequence[Hashable], relevant: Rel, k: int) -> float:
    """|top-k ∩ relevant| / |relevant|. Không có relevant → 0.0."""
    _check_k(k)
    rel = _rel_set(relevant)
    if not rel:
        return 0.0
    return len(set(retrieved[:k]) & rel) / len(rel)


def precision_at_k(retrieved: Sequence[Hashable], relevant: Rel, k: int) -> float:
    """|top-k ∩ relevant| / k (mẫu số luôn là k, kể cả khi trả về ít hơn k)."""
    _check_k(k)
    rel = _rel_set(relevant)
    return sum(1 for d in retrieved[:k] if d in rel) / k


def hit_at_k(retrieved: Sequence[Hashable], relevant: Rel, k: int) -> float:
    """1.0 nếu có ít nhất 1 id đúng trong top-k, ngược lại 0.0."""
    _check_k(k)
    rel = _rel_set(relevant)
    return 1.0 if any(d in rel for d in retrieved[:k]) else 0.0


def mrr(retrieved: Sequence[Hashable], relevant: Rel, k: int | None = None) -> float:
    """Reciprocal rank của id đúng đầu tiên (cắt ở k nếu có). Trung bình qua truy vấn = MRR."""
    rel = _rel_set(relevant)
    lim = retrieved if k is None else retrieved[:k]
    for i, d in enumerate(lim, start=1):
        if d in rel:
            return 1.0 / i
    return 0.0


reciprocal_rank = mrr


def ndcg_at_k(retrieved: Sequence[Hashable], relevant: Rel, k: int) -> float:
    """NDCG@k, gain = rel (nhị phân nếu relevant là tập; dùng điểm nếu là dict), discount log2(i+1)."""
    _check_k(k)
    gains = dict(relevant) if isinstance(relevant, Mapping) else {d: 1.0 for d in relevant}
    dcg = sum(gains.get(d, 0.0) / math.log2(i + 1) for i, d in enumerate(retrieved[:k], start=1))
    ideal = sorted((g for g in gains.values() if g > 0), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 1) for i, g in enumerate(ideal, start=1))
    return dcg / idcg if idcg > 0 else 0.0


def average_precision(retrieved: Sequence[Hashable], relevant: Rel, k: int | None = None) -> float:
    """AP = (Σ_i P@i · rel_i) / min(|relevant|, k) (k=None → /|relevant|)."""
    rel = _rel_set(relevant)
    if not rel:
        return 0.0
    lim = retrieved if k is None else retrieved[:k]
    hits, s = 0, 0.0
    for i, d in enumerate(lim, start=1):
        if d in rel:
            hits += 1
            s += hits / i
    denom = len(rel) if k is None else min(len(rel), k)
    return s / denom


def mean_average_precision(runs: Sequence[Sequence[Hashable]], qrels: Sequence[Rel], k: int | None = None) -> float:
    """mAP = trung bình AP qua các truy vấn."""
    return mean_over_queries(average_precision, runs, qrels, k=k)


def cross_type_error_at_k(retrieved_types: Sequence[str], query_type: str, k: int) -> float:
    """Tỉ lệ kết quả trong top-k có product_type khác loại của truy vấn (càng thấp càng tốt).
    Mẫu số là số kết quả thực có trong top-k (trả rỗng → 0.0)."""
    _check_k(k)
    top = list(retrieved_types[:k])
    if not top:
        return 0.0
    return sum(1 for t in top if t != query_type) / len(top)


# ---------------- Văn bản (QA) ----------------
_PUNCT = set(string.punctuation) | set("“”‘’…–—«»")


def normalize_vi(text: str) -> str:
    """Chuẩn hoá câu tiếng Việt để so token: NFC, chữ thường, bỏ dấu câu, gộp khoảng trắng.
    GIỮ dấu thanh (bỏ dấu sẽ làm 'má'/'mã' trùng nhau)."""
    t = unicodedata.normalize("NFC", text or "").lower()
    t = "".join(" " if ch in _PUNCT else ch for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def f1_tokens(pred: str, gold: str) -> float:
    """F1 theo token (kiểu SQuAD) sau `normalize_vi`. Cả hai rỗng → 1.0; một bên rỗng → 0.0."""
    p, g = normalize_vi(pred).split(), normalize_vi(gold).split()
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    common = sum((Counter(p) & Counter(g)).values())
    if common == 0:
        return 0.0
    prec, rec = common / len(p), common / len(g)
    return 2 * prec * rec / (prec + rec)


def exact_match(pred: str, gold: str) -> float:
    """1.0 nếu hai chuỗi trùng sau chuẩn hoá."""
    return 1.0 if normalize_vi(pred) == normalize_vi(gold) else 0.0


# ---------------- Latency & tổng hợp ----------------
def latency_summary(latencies_ms: Sequence[float]) -> dict:
    """Thống kê latency (ms): n, mean, p50 (median), p95, p99, max – percentile nội suy tuyến tính."""
    a = np.asarray(list(latencies_ms), dtype=float)
    if a.size == 0:
        return {"n": 0, "mean": None, "p50": None, "p95": None, "p99": None, "max": None}
    return {"n": int(a.size), "mean": float(a.mean()), "p50": float(np.percentile(a, 50)),
            "p95": float(np.percentile(a, 95)), "p99": float(np.percentile(a, 99)), "max": float(a.max())}


def mean_over_queries(fn: Callable, runs: Sequence[Sequence[Hashable]], qrels: Sequence[Rel], **kw) -> float:
    """Trung bình một độ đo theo truy vấn."""
    if len(runs) != len(qrels):
        raise ValueError("runs và qrels phải cùng số truy vấn")
    if not runs:
        return 0.0
    return float(np.mean([fn(r, q, **kw) for r, q in zip(runs, qrels)]))


def evaluate_ranking(runs: Sequence[Sequence[Hashable]], qrels: Sequence[Rel], ks: Sequence[int] = (1, 5, 10)) -> dict:
    """Tính trọn bộ độ đo xếp hạng trung bình: Recall/Precision/Hit/NDCG@k, MRR, mAP."""
    out: dict = {"n_queries": len(runs)}
    for k in ks:
        out[f"recall@{k}"] = mean_over_queries(recall_at_k, runs, qrels, k=k)
        out[f"precision@{k}"] = mean_over_queries(precision_at_k, runs, qrels, k=k)
        out[f"hit@{k}"] = mean_over_queries(hit_at_k, runs, qrels, k=k)
        out[f"ndcg@{k}"] = mean_over_queries(ndcg_at_k, runs, qrels, k=k)
    out["mrr"] = mean_over_queries(mrr, runs, qrels)
    out["map"] = mean_average_precision(runs, qrels)
    return out


def classification_report(gold: Sequence[str], pred: Sequence[str]) -> dict:
    """Accuracy, macro-F1, P/R/F1 từng lớp và ma trận nhầm lẫn (dùng cho router)."""
    if len(gold) != len(pred):
        raise ValueError("gold và pred phải cùng độ dài")
    labels = sorted(set(gold) | set(pred))
    per = {}
    for c in labels:
        tp = sum(1 for g, p in zip(gold, pred) if g == c and p == c)
        fp = sum(1 for g, p in zip(gold, pred) if g != c and p == c)
        fn = sum(1 for g, p in zip(gold, pred) if g == c and p != c)
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        per[c] = {"precision": pr, "recall": rc, "f1": f1, "support": sum(1 for g in gold if g == c)}
    present = [c for c in labels if per[c]["support"] > 0]
    conf = {g: {p: 0 for p in labels} for g in labels}
    for g, p in zip(gold, pred):
        conf[g][p] += 1
    acc = sum(1 for g, p in zip(gold, pred) if g == p) / len(gold) if gold else 0.0
    macro = float(np.mean([per[c]["f1"] for c in present])) if present else 0.0
    return {"n": len(gold), "accuracy": acc, "macro_f1": macro, "per_class": per, "confusion": conf}
