# repo: scripts/eval_router.py
"""US_41 – Đo route accuracy + confusion matrix của Router trên eval_router_seed (+ eval_router của Chiến nếu có).

Chạy:  PYTHONPATH=src python scripts/eval_router.py [--emb] [--out results/router_eval.json]
--emb : bật bộ phân loại embedding (multilingual-e5-small, prototype k-NN) làm tín hiệu phụ.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from msa.agent.router import ROUTES, Router  # noqa: E402

SETS = {
    "seed_trung": os.path.join(ROOT, "eval", "eval_router_seed.jsonl"),
    "chien_eval_router": os.environ.get("MSA_CHIEN_EVAL_ROUTER", os.path.join(os.path.dirname(ROOT), "03_Chien", "eval", "eval_router.jsonl")),
    "gemini_gen_heldout": os.path.join(ROOT, "eval", "eval_router_gemini_gen.jsonl"),
}
GEMINI = {"gemini_chitchat", "gemini_ood"}


def load(path: str) -> list[dict]:
    return [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]


def session_of(ex: dict) -> dict:
    s = {}
    if ex.get("product_id"):
        s["current_product_id"] = ex["product_id"]
    if ex.get("session_last_results"):
        s["last_results"] = ex["session_last_results"]
    return s


def evaluate(router: Router, data: list[dict]) -> dict:
    cm = {g: collections.Counter() for g in ROUTES}
    rows, lat = [], []
    for ex in data:
        t0 = time.perf_counter()
        r = router.route_obj(ex.get("text"), b"img" if ex.get("has_image") else None, session_of(ex))
        lat.append((time.perf_counter() - t0) * 1000)
        cm[ex["route"]][r.route] += 1
        rows.append(dict(id=ex["id"], text=ex.get("text"), gold=ex["route"], pred=r.route, conf=round(r.confidence, 3), reason=r.reason))
    n = len(data)
    acc = sum(1 for r in rows if r["gold"] == r["pred"]) / n
    per = {}
    for g in ROUTES:
        tp = cm[g][g]
        sup = sum(cm[g].values())
        pp = sum(cm[x][g] for x in ROUTES)
        per[g] = dict(support=sup, recall=round(tp / sup, 3) if sup else None, precision=round(tp / pp, 3) if pp else None)
    # OOD/Gemini detection (gộp 2 nhãn gemini_*)
    tp = sum(1 for r in rows if r["gold"] in GEMINI and r["pred"] in GEMINI)
    gold_g = sum(1 for r in rows if r["gold"] in GEMINI)
    pred_g = sum(1 for r in rows if r["pred"] in GEMINI)
    lat.sort()
    return dict(
        n=n, route_accuracy=round(acc, 4),
        route_accuracy_gemini_merged=round(sum(1 for r in rows if r["gold"] == r["pred"] or (r["gold"] in GEMINI and r["pred"] in GEMINI)) / n, 4),
        per_route=per,
        gemini_detection=dict(recall=round(tp / gold_g, 3) if gold_g else None, precision=round(tp / pred_g, 3) if pred_g else None),
        predicted_gemini_rate=round(pred_g / n, 3), predicted_clarify_rate=round(sum(r["pred"] == "clarify" for r in rows) / n, 3),
        in_domain_pushed_to_gemini=sum(1 for r in rows if r["gold"] in {"visual", "qa", "search", "compare"} and r["pred"] in GEMINI),
        confusion={g: dict(cm[g]) for g in ROUTES},
        latency_ms_p50=round(lat[n // 2], 3), latency_ms_p95=round(lat[min(n - 1, int(0.95 * n))], 3),
        errors=[r for r in rows if r["gold"] != r["pred"]], rows=rows,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "router_eval.json"))
    ap.add_argument("--label", default="router_v0_rule")
    a = ap.parse_args()
    emb = None
    if a.emb:
        from msa.agent.intent_embed import PrototypeIntentEmbedder
        emb = PrototypeIntentEmbedder()
    router = Router(embedder=emb)
    res = dict(config=dict(router=a.label, tau_intent=router.tau, embedder=None if emb is None else emb.name,
                           data_version="shared_data v1 (prep_shared_data.py seed 42)"), sets={})
    for name, path in SETS.items():
        if os.path.exists(path):
            res["sets"][name] = dict(path=path, **evaluate(router, load(path)))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=1)
    for name, r in res["sets"].items():
        print(f"{name}: n={r['n']} acc={r['route_accuracy']} acc_gemini_merged={r['route_accuracy_gemini_merged']} gemini_rate={r['predicted_gemini_rate']} in_domain->gemini={r['in_domain_pushed_to_gemini']}")


if __name__ == "__main__":
    main()
