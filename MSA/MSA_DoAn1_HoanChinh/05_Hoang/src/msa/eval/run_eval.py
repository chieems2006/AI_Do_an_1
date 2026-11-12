# repo: src/msa/eval/run_eval.py
"""US_17 – Chạy đánh giá bằng một lệnh từ file dự đoán JSONL.

  python -m msa.eval.run_eval --task visual --pred preds_visual.jsonl [--k 1,5,10] [--out result.json]
  python -m msa.eval.run_eval --task qa     --pred preds_qa.jsonl
  python -m msa.eval.run_eval --task router --pred preds_router.jsonl

Định dạng mỗi dòng:
- visual: {"query_id", "query_type", "relevant": [pid...], "retrieved": [pid... | {"product_id","product_type"}...], "latency_ms"}
- qa:     {"id", "relevant": [pid|chunk...], "retrieved": [...], "pred_answer", "gold_answer", "answerable", "refused", "latency_ms"}
- router: {"id", "gold_route", "pred_route", "latency_ms"}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from . import metrics as M


def _ids_types(retrieved: list) -> tuple[list, list]:
    ids, types = [], []
    for r in retrieved:
        if isinstance(r, dict):
            ids.append(r["product_id"])
            types.append(r.get("product_type"))
        else:
            ids.append(r)
            types.append(None)
    return ids, types


def eval_visual(rows: list[dict], ks=(1, 5, 10)) -> dict:
    runs, qrels, cte = [], [], {k: [] for k in ks}
    for r in rows:
        ids, types = _ids_types(r["retrieved"])
        runs.append(ids)
        qrels.append(set(r.get("relevant") or []))
        if r.get("query_type") and all(t is not None for t in types):
            for k in ks:
                cte[k].append(M.cross_type_error_at_k(types, r["query_type"], k))
    out = M.evaluate_ranking(runs, qrels, ks) if any(qrels) else {"n_queries": len(rows)}
    for k in ks:
        if cte[k]:
            out[f"cross_type_error@{k}"] = float(np.mean(cte[k]))
    out["latency_ms"] = M.latency_summary([r["latency_ms"] for r in rows if r.get("latency_ms") is not None])
    return out


def eval_qa(rows: list[dict], ks=(1, 5, 10)) -> dict:
    ans = [r for r in rows if r.get("answerable", True)]
    una = [r for r in rows if not r.get("answerable", True)]
    out: dict = {"n": len(rows), "n_answerable": len(ans), "n_unanswerable": len(una)}
    with_ret = [r for r in ans if r.get("relevant")]
    if with_ret:
        out["retrieval"] = M.evaluate_ranking([r["retrieved"] for r in with_ret], [set(r["relevant"]) for r in with_ret], ks)
    gen = [r for r in ans if r.get("gold_answer") is not None and r.get("pred_answer") is not None]
    if gen:
        out["f1_tokens"] = float(np.mean([M.f1_tokens(r["pred_answer"], r["gold_answer"]) for r in gen]))
        out["exact_match"] = float(np.mean([M.exact_match(r["pred_answer"], r["gold_answer"]) for r in gen]))
    if una:  # câu không trả lời được → hệ thống phải từ chối ("chưa có thông tin")
        out["refusal_rate_unanswerable"] = float(np.mean([bool(r.get("refused")) for r in una]))
    if ans:
        out["false_refusal_rate_answerable"] = float(np.mean([bool(r.get("refused")) for r in ans]))
    out["latency_ms"] = M.latency_summary([r["latency_ms"] for r in rows if r.get("latency_ms") is not None])
    return out


def eval_router(rows: list[dict]) -> dict:
    out = M.classification_report([r["gold_route"] for r in rows], [r["pred_route"] for r in rows])
    out["latency_ms"] = M.latency_summary([r["latency_ms"] for r in rows if r.get("latency_ms") is not None])
    return out


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=["visual", "qa", "router"], required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--k", default="1,5,10")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    rows = [json.loads(l) for l in open(a.pred, encoding="utf-8") if l.strip()]
    ks = tuple(int(x) for x in a.k.split(","))
    res = {"visual": lambda: eval_visual(rows, ks), "qa": lambda: eval_qa(rows, ks), "router": lambda: eval_router(rows)}[a.task]()
    res = {"task": a.task, "pred_file": a.pred, **res}
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(txt, encoding="utf-8")
    print(txt)
    return res


if __name__ == "__main__":
    main(sys.argv[1:])
