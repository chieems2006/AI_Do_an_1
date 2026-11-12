# repo: src/msa/eval/weighted_scoring.py
"""US_25 – Bảng chấm điểm có trọng số (Sheet 3, Bảng F) từ số liệu benchmark THẬT.

Mỗi tiêu chí = trung bình (có trọng số con) của các độ đo đã chuẩn hoá min-max giữa các ứng viên, quy về thang 1-5:
    điểm = 1 + 4 * (x - min) / (max - min)          (độ đo ↑ tốt hơn)
    điểm = 1 + 4 * (max - x) / (max - min)          (độ đo ↓ tốt hơn: latency, RAM, cross-type error)
Nếu mọi ứng viên bằng nhau -> 3 (trung tính). Tiêu chí định tính (license, dễ tích hợp) nhập trực tiếp điểm 1-5 trong CSV.
Thiếu số liệu -> tiêu chí đó = None, tổng điểm chuẩn hoá lại theo trọng số còn lại và gắn cờ 'thieu'.

CLI:  PYTHONPATH=src python -m scoring.weighted_scoring <bench.csv> [--md out.md] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Metric:
    name: str            # tên chuẩn
    higher_better: bool
    weight: float = 1.0  # trọng số con trong tiêu chí
    aliases: tuple[str, ...] = ()
    raw_score: bool = False  # True: cột đã là điểm 1-5, không min-max


@dataclass(frozen=True)
class Criterion:
    name: str
    weight: float
    metrics: tuple[Metric, ...]


DEFAULT_CRITERIA: tuple[Criterion, ...] = (
    Criterion("Độ chính xác", 0.35, (
        Metric("recall_at_5_macro", True, 0.5, ("recall@5_macro", "macro_recall@5", "recall_at_5", "recall@5", "r@5")),
        Metric("mrr", True, 0.3, ("MRR", "mrr@10")),
        Metric("cross_type_error_at_5", False, 0.2, ("cross_type_error@5", "cte@5", "cross_type_error")),
    )),
    Criterion("Tốc độ", 0.15, (Metric("latency_ms_p50", False, 1.0, ("latency_ms", "latency_ms_per_image", "ms_per_image", "latency_p50_ms")),)),
    Criterion("Tài nguyên", 0.15, (
        Metric("ram_gb", False, 0.5, ("ram", "peak_ram_gb", "rss_gb")),
        Metric("ckpt_mb", False, 0.5, ("checkpoint_mb", "size_mb", "params_m")),
    )),
    Criterion("Phù hợp miền", 0.15, (Metric("recall_at_5_min_group", True, 1.0, ("recall@5_min_group", "worst_group_recall@5", "domain_fit")),)),
    Criterion("License", 0.10, (Metric("license_score", True, 1.0, ("license",), raw_score=True),)),
    Criterion("Dễ tích hợp", 0.10, (Metric("integration_score", True, 1.0, ("integration", "ease"), raw_score=True),)),
)


def _canon(s: str) -> str:
    return re.sub(r"[^a-z0-9@]", "", s.lower())


def resolve_columns(df: pd.DataFrame, criteria: tuple[Criterion, ...] = DEFAULT_CRITERIA) -> dict[str, str | None]:
    """Tìm cột CSV cho từng độ đo theo tên/alias (không phân biệt hoa thường, bỏ ký tự đặc biệt)."""
    cols = {_canon(c): c for c in df.columns}
    out: dict[str, str | None] = {}
    for c in criteria:
        for m in c.metrics:
            out[m.name] = next((cols[_canon(a)] for a in (m.name, *m.aliases) if _canon(a) in cols), None)
    return out


def minmax_score(values: list[float | None], higher_better: bool) -> list[float | None]:
    xs = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not xs:
        return [None] * len(values)
    lo, hi = min(xs), max(xs)
    out: list[float | None] = []
    for v in values:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            out.append(None)
        elif hi == lo:
            out.append(3.0)
        else:
            t = (v - lo) / (hi - lo)
            out.append(1 + 4 * (t if higher_better else 1 - t))
    return out


def score_table(df: pd.DataFrame, name_col: str = "model", criteria: tuple[Criterion, ...] = DEFAULT_CRITERIA) -> pd.DataFrame:
    """Trả DataFrame: model, điểm từng tiêu chí (1-5), tong_diem (thang 5), thieu (danh sách tiêu chí thiếu), hang."""
    total_w = sum(c.weight for c in criteria)
    if abs(total_w - 1.0) > 1e-6:
        raise ValueError(f"Tổng trọng số phải = 1, hiện = {total_w}")
    colmap = resolve_columns(df, criteria)
    res = pd.DataFrame({"model": df[name_col].astype(str).values})
    for c in criteria:
        parts, wsum = [0.0] * len(df), [0.0] * len(df)
        for m in c.metrics:
            col = colmap[m.name]
            if col is None:
                continue
            vals = [None if pd.isna(v) else float(v) for v in df[col].values]
            sc = [None if v is None else max(1.0, min(5.0, v)) for v in vals] if m.raw_score else minmax_score(vals, m.higher_better)
            for i, s in enumerate(sc):
                if s is not None:
                    parts[i] += m.weight * s
                    wsum[i] += m.weight
        res[c.name] = [round(p / w, 3) if w > 0 else None for p, w in zip(parts, wsum)]
    totals, missing = [], []
    for _, row in res.iterrows():
        have = [(c.weight, row[c.name]) for c in criteria if row[c.name] is not None and not pd.isna(row[c.name])]
        miss = [c.name for c in criteria if row[c.name] is None or pd.isna(row[c.name])]
        w = sum(a for a, _ in have)
        totals.append(round(sum(a * b for a, b in have) / w, 3) if w else None)
        missing.append(", ".join(miss))
    res["tong_diem"] = totals
    res["thieu"] = missing
    res = res.sort_values("tong_diem", ascending=False, na_position="last").reset_index(drop=True)
    res["hang"] = range(1, len(res) + 1)
    return res


def to_markdown(res: pd.DataFrame, criteria: tuple[Criterion, ...] = DEFAULT_CRITERIA) -> str:
    head = ["Hạng", "Ứng viên"] + [f"{c.name} ({c.weight:.2f})" for c in criteria] + ["Tổng (thang 5)", "Thiếu số liệu"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for _, r in res.iterrows():
        cells = [str(r["hang"]), r["model"]] + ["CHƯA ĐO" if r[c.name] is None or pd.isna(r[c.name]) else f"{r[c.name]:.2f}" for c in criteria]
        cells += ["—" if r["tong_diem"] is None else f"{r['tong_diem']:.2f}", r["thieu"] or "—"]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--name-col", default="model")
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    df = pd.read_csv(a.csv)
    res = score_table(df, a.name_col)
    md = to_markdown(res)
    print(md)
    print("\nCột đã nhận diện:", json.dumps(resolve_columns(df), ensure_ascii=False))
    if a.md:
        open(a.md, "w", encoding="utf-8").write(md + "\n")
    if a.json:
        res.to_json(a.json, orient="records", force_ascii=False, indent=1)


if __name__ == "__main__":
    main()
