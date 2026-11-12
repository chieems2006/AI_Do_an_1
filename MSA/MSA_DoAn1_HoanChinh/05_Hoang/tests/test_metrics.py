"""US_17 – Unit test metrics.py: so với kết quả tính tay (phép tính ghi trong comment)."""
import math

import pytest
from msa.eval import metrics as M

RET = ["a", "b", "c", "d", "e"]
REL = {"b", "d", "x"}


def test_recall_precision_hit():
    assert M.recall_at_k(RET, REL, 1) == 0.0                 # top1={a} ∩ REL = ∅
    assert M.recall_at_k(RET, REL, 5) == pytest.approx(2 / 3)  # {b,d} / 3
    assert M.precision_at_k(RET, REL, 5) == pytest.approx(2 / 5)
    assert M.precision_at_k(["b"], REL, 5) == pytest.approx(1 / 5)  # mẫu số luôn là k
    assert M.hit_at_k(RET, REL, 1) == 0.0 and M.hit_at_k(RET, REL, 2) == 1.0
    assert M.recall_at_k(RET, set(), 5) == 0.0


def test_mrr():
    assert M.mrr(RET, REL) == pytest.approx(1 / 2)   # b ở hạng 2
    assert M.mrr(RET, {"e"}, k=3) == 0.0             # e ở hạng 5 > k
    assert M.mean_over_queries(M.mrr, [RET, RET], [{"a"}, {"c"}]) == pytest.approx((1 + 1 / 3) / 2)


def test_ndcg_binary_and_graded():
    # binary: DCG@5 = 1/log2(3) + 1/log2(5) = 0.63093 + 0.43068 = 1.06161
    # IDCG@5 (3 relevant) = 1 + 1/log2(3) + 1/log2(4) = 1 + 0.63093 + 0.5 = 2.13093 → 0.49819
    assert M.ndcg_at_k(RET, REL, 5) == pytest.approx(1.06161 / 2.13093, abs=1e-4)
    # graded: gains {a:3, c:1}; DCG@3 = 3/1 + 1/log2(4)=3.5 ; IDCG = 3 + 1/log2(3) = 3.63093 → 0.96394
    assert M.ndcg_at_k(["a", "b", "c"], {"a": 3, "c": 1}, 3) == pytest.approx(3.5 / 3.63093, abs=1e-4)
    assert M.ndcg_at_k(["z"], {"a": 1}, 1) == 0.0


def test_average_precision():
    # hit ở hạng 2 (P=1/2) và 4 (P=2/4) → (0.5+0.5)/|REL|=3 → 1/3
    assert M.average_precision(RET, REL) == pytest.approx(1 / 3)
    # cắt k=2: chỉ hạng 2 → 0.5 / min(3,2)=2 → 0.25
    assert M.average_precision(RET, REL, k=2) == pytest.approx(0.25)
    assert M.mean_average_precision([RET, ["b"]], [REL, {"b"}]) == pytest.approx((1 / 3 + 1) / 2)


def test_cross_type_error():
    types = ["footwear", "clothing", "footwear", "accessory", "footwear"]
    assert M.cross_type_error_at_k(types, "footwear", 5) == pytest.approx(2 / 5)
    assert M.cross_type_error_at_k(types, "footwear", 1) == 0.0
    assert M.cross_type_error_at_k([], "footwear", 5) == 0.0


def test_f1_tokens_vietnamese():
    # pred: "giày màu đen" (3 token), gold: "giày đen size 42" (4 token); chung {giày, đen}=2
    # P=2/3, R=2/4 → F1 = 2·(2/3·1/2)/(2/3+1/2) = 0.5714
    assert M.f1_tokens("Giày màu đen!", "giày đen, size 42") == pytest.approx(4 / 7)
    assert M.f1_tokens("má", "mã") == 0.0  # giữ dấu thanh
    assert M.f1_tokens("", "") == 1.0 and M.f1_tokens("a", "") == 0.0
    assert M.exact_match("Còn hàng.", "còn hàng") == 1.0


def test_latency_summary():
    s = M.latency_summary([10, 20, 30, 40, 100])
    assert s["n"] == 5 and s["p50"] == 30 and s["mean"] == 40
    assert s["p95"] == pytest.approx(40 + 0.8 * 60)  # nội suy: vị trí 3.8 → 40 + 0.8·(100-40) = 88
    assert M.latency_summary([])["p50"] is None


def test_evaluate_ranking_and_classification():
    r = M.evaluate_ranking([RET], [REL], ks=(1, 5))
    assert r["hit@5"] == 1.0 and r["mrr"] == 0.5 and r["n_queries"] == 1
    c = M.classification_report(["qa", "qa", "search", "chit"], ["qa", "search", "search", "qa"])
    assert c["accuracy"] == 0.5
    # qa: P=1/2 R=1/2 F1=.5 ; search: P=1/2 R=1 F1=.6667 ; chit: 0 → macro=(0.5+0.6667+0)/3
    assert c["macro_f1"] == pytest.approx((0.5 + 2 / 3) / 3)
    assert c["confusion"]["qa"]["search"] == 1


def test_bad_k():
    with pytest.raises(ValueError):
        M.recall_at_k(RET, REL, 0)


def test_run_eval_cli(tmp_path):
    import json
    from msa.eval import run_eval
    p = tmp_path / "v.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in [
        {"query_id": "q1", "query_type": "footwear", "relevant": ["a"],
         "retrieved": [{"product_id": "a", "product_type": "footwear"}, {"product_id": "b", "product_type": "clothing"}],
         "latency_ms": 10},
        {"query_id": "q2", "query_type": "clothing", "relevant": ["z"],
         "retrieved": [{"product_id": "c", "product_type": "clothing"}, {"product_id": "z", "product_type": "clothing"}],
         "latency_ms": 30}]), encoding="utf-8")
    r = run_eval.main(["--task", "visual", "--pred", str(p), "--k", "1,2"])
    assert r["hit@1"] == 0.5 and r["mrr"] == pytest.approx(0.75)
    assert r["cross_type_error@2"] == pytest.approx(0.25)  # (1/2 + 0)/2
    assert r["latency_ms"]["p50"] == 20
    q = tmp_path / "q.jsonl"
    q.write_text("\n".join(json.dumps(r) for r in [
        {"id": 1, "relevant": ["r1"], "retrieved": ["r1"], "pred_answer": "giao nhanh", "gold_answer": "giao hàng nhanh",
         "answerable": True, "refused": False},
        {"id": 2, "answerable": False, "refused": True}]), encoding="utf-8")
    r = run_eval.main(["--task", "qa", "--pred", str(q)])
    assert r["refusal_rate_unanswerable"] == 1.0 and r["f1_tokens"] == pytest.approx(0.8)  # P=1,R=2/3
    rt = tmp_path / "r.jsonl"
    rt.write_text("\n".join(json.dumps({"id": i, "gold_route": g, "pred_route": p}) for i, (g, p) in
                            enumerate([("qa", "qa"), ("search", "qa")])), encoding="utf-8")
    assert run_eval.main(["--task", "router", "--pred", str(rt)])["accuracy"] == 0.5
