"""Kiểm US_25: chuẩn hoá min-max, chiều ↑/↓, thiếu số liệu, tổng trọng số = 1 (tính tay ghi trong comment)."""
import pandas as pd
import pytest

from scoring.weighted_scoring import DEFAULT_CRITERIA, Criterion, Metric, minmax_score, score_table, to_markdown


def test_weights_sum_to_one():
    assert abs(sum(c.weight for c in DEFAULT_CRITERIA) - 1) < 1e-9


def test_minmax_directions():
    # [0.6, 0.8, 1.0] ↑ -> 1, 3, 5 ; ↓ -> 5, 3, 1
    assert minmax_score([0.6, 0.8, 1.0], True) == pytest.approx([1, 3, 5])
    assert minmax_score([0.6, 0.8, 1.0], False) == pytest.approx([5, 3, 1])
    assert minmax_score([2, 2], True) == [3.0, 3.0]
    assert minmax_score([None, 1.0], True) == [None, 3.0]


def test_hand_calculated_two_criteria():
    crit = (Criterion("Acc", 0.6, (Metric("r5", True),)), Criterion("Speed", 0.4, (Metric("lat", False),)))
    df = pd.DataFrame({"model": ["A", "B"], "r5": [0.9, 0.7], "lat": [100, 50]})
    res = score_table(df, criteria=crit).set_index("model")
    # A: Acc=5, Speed=1 -> 0.6*5+0.4*1 = 3.4 ; B: Acc=1, Speed=5 -> 0.6+2.0 = 2.6
    assert res.loc["A", "tong_diem"] == pytest.approx(3.4)
    assert res.loc["B", "tong_diem"] == pytest.approx(2.6)
    assert res.loc["A", "hang"] == 1


def test_missing_metric_renormalized_and_flagged():
    df = pd.DataFrame({"model": ["A", "B"], "Recall@5": [0.8, 0.6], "latency_ms": [30, 10], "license_score": [5, 4]})
    res = score_table(df).set_index("model")
    assert "Tài nguyên" in res.loc["A", "thieu"]
    # A: Acc=5 (chỉ recall), Tốc độ=1, License=5 -> (0.35*5+0.15*1+0.10*5)/0.60 = 2.4/0.6 = 4.0
    assert res.loc["A", "tong_diem"] == pytest.approx(4.0)
    assert "CHƯA ĐO" in to_markdown(score_table(df))


def test_bad_weights_rejected():
    with pytest.raises(ValueError):
        score_table(pd.DataFrame({"model": ["A"], "x": [1]}), criteria=(Criterion("X", 0.5, (Metric("x", True),)),))
