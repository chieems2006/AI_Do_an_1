import math

from msa.eval import visual_metrics as M


def test_recall_hit_precision_mrr():
    ranked = ["a", "b", "c", "d", "e"]
    assert M.recall_at_k(ranked, {"c"}, 1) == 0.0
    assert M.recall_at_k(ranked, {"c"}, 5) == 1.0
    assert M.recall_at_k(ranked, {"c", "z"}, 5) == 0.5
    assert M.hit_at_k(ranked, {"e"}, 5) == 1.0
    assert M.precision_at_k(ranked, {"a", "c"}, 5) == 0.4
    assert M.mrr(ranked, {"c"}) == 1 / 3
    assert M.mrr(ranked, {"z"}) == 0.0
    assert M.mrr(ranked, {"e"}, k=3) == 0.0


def test_ndcg_ap_cte():
    # ví dụ tính tay trong docs/US_12: SP đúng ở hạng 3 -> NDCG = 1/log2(4) = 0.5
    assert abs(M.ndcg_at_k(["x", "y", "g"], {"g"}, 10) - 0.5) < 1e-9
    assert M.ndcg_at_k(["g"], {"g"}, 10) == 1.0
    # AP: đúng ở hạng 1 và 3, |R|=2 -> (1 + 2/3)/2
    assert abs(M.average_precision(["a", "b", "c"], {"a", "c"}) - (1 + 2 / 3) / 2) < 1e-9
    assert M.cross_type_error_at_k(["footwear", "clothing", "footwear", "accessory", "footwear"], "footwear", 5) == 0.4


def test_auroc():
    assert M.auroc([0.9, 0.8], [0.1, 0.2]) == 1.0
    assert M.auroc([0.1], [0.9]) == 0.0
    assert M.auroc([0.5], [0.5]) == 0.5
    assert math.isnan(M.auroc([], [0.1]))


def test_consistent_with_hoang_metrics_if_available():
    """Đối chiếu với src/msa/eval/metrics.py của Hoàng (nếu có trong máy) – cùng kết quả trên ví dụ."""
    import importlib.util
    from pathlib import Path

    import pytest

    p = Path(__file__).resolve().parents[2] / "05_Hoang" / "src" / "msa" / "eval" / "metrics.py"
    if not p.exists():
        pytest.skip("không có metrics.py của Hoàng")
    spec = importlib.util.spec_from_file_location("hoang_metrics", p)
    H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
    ranked, rel = ["x", "y", "g", "u", "v"], {"g", "v"}
    for k in (1, 3, 5):
        assert abs(H.recall_at_k(ranked, rel, k) - M.recall_at_k(ranked, rel, k)) < 1e-9
        assert abs(H.ndcg_at_k(ranked, rel, k) - M.ndcg_at_k(ranked, rel, k)) < 1e-9
        assert abs(H.precision_at_k(ranked, rel, k) - M.precision_at_k(ranked, rel, k)) < 1e-9
    assert abs(H.mrr(ranked, rel) - M.mrr(ranked, rel)) < 1e-9
    assert abs(H.cross_type_error_at_k(["a", "b", "a"], "a", 3) - M.cross_type_error_at_k(["a", "b", "a"], "a", 3)) < 1e-9
