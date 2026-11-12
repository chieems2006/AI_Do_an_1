# repo: scripts/run_scoring_from_khoa.py
"""US_25 – Bảng F: chấm điểm có trọng số cho model embedding ảnh, dùng số liệu benchmark THẬT của Khoa.

Đầu vào mặc định: 04_Khoa/results/bench_image_embed.csv (5 model đo thật, split test của eval_visual.csv,
shared_data v1 seed 42, CPU 2 luồng). Có thể chỉ file khác bằng --csv.

Chạy (từ thư mục 01_Trung):
    PYTHONPATH=src python scripts/run_scoring_from_khoa.py
    PYTHONPATH=src python scripts/run_scoring_from_khoa.py --csv ../04_Khoa/results/bench_image_embed.csv
Ghi: results/bench_image_embed_from_khoa.csv (cột chuẩn hoá), results/weighted_scoring.md, results/weighted_scoring.json,
     results/weighted_scoring_sensitivity.json (độ nhạy trọng số ±0,05).

Ánh xạ cột CSV của Khoa -> cột chuẩn của weighted_scoring.py:
    recall_at_5_macro      <- test_macro_R@5
    mrr                    <- test_MRR@10
    cross_type_error_at_5  <- test_CTE@5
    latency_ms_p50         <- query_embed_ms_median_bs1   (nhúng 1 ảnh truy vấn, batch 1, median 60 lần đo)
    ram_gb                 <- peak_rss_mb / 1024           (RAM đỉnh của tiến trình benchmark)
    ckpt_mb                <- weights_fp32_total_mb
    recall_at_5_min_group  <- min(test_R@5_footwear, _clothing, _headwear, _accessory)
Điểm License/Dễ tích hợp là điểm ĐỊNH TÍNH do Trung đề xuất (bảng QUAL) – nhóm thống nhất lại ở buổi chấm điểm N12.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from scoring.weighted_scoring import DEFAULT_CRITERIA, Criterion, Metric, score_table, to_markdown  # noqa: E402

DEFAULT_CSV = os.path.normpath(os.path.join(ROOT, "..", "04_Khoa", "results", "bench_image_embed.csv"))
GROUPS = ("footwear", "clothing", "headwear", "accessory")
# (license_score, integration_score) 1-5 – định tính, [cần xác minh license trên model card]
QUAL = {"clip_b32": (5, 5), "clip_b16": (5, 5), "openclip_b32_laion2b": (5, 4), "siglip_b16": (5, 4), "fashionclip": (4, 4),
        "marqo_fashionsiglip": (4, 4), "dinov2_s": (5, 4), "resnet50": (5, 5)}


def load_khoa_csv(path: str) -> pd.DataFrame:
    """Đọc CSV benchmark của Khoa, chỉ giữ model status=ok, đổi sang cột chuẩn."""
    raw = pd.read_csv(path)
    raw = raw[raw["status"] == "ok"].copy()
    rows = []
    for _, r in raw.iterrows():
        lic, integ = QUAL.get(r["model"], (None, None))
        rows.append(dict(
            model=r["model"],
            recall_at_5_macro=r["test_macro_R@5"], mrr=r["test_MRR@10"], cross_type_error_at_5=r["test_CTE@5"],
            latency_ms_p50=r["query_embed_ms_median_bs1"], ram_gb=round(r["peak_rss_mb"] / 1024, 3),
            ckpt_mb=r["weights_fp32_total_mb"],
            recall_at_5_min_group=min(r[f"test_R@5_{g}"] for g in GROUPS),
            cat_hit_at_5=r["test_cat_Hit@5"], cat_p_at_5=r["test_cat_P@5"],
            license_score=lic, integration_score=integ, source_file=os.path.relpath(path, ROOT)))
    return pd.DataFrame(rows)


# Kịch bản B (ĐỀ XUẤT của Tác nhân 2, CHƯA được nhóm chốt): tách 0,10 từ "Độ chính xác" (tầng instance) sang tiêu chí
# "Tầng category" = tìm SP KHÁC nhưng cùng loại + màu (đúng use case "tìm sản phẩm tương tự" khi catalog không có đúng món).
CRITERIA_B: tuple[Criterion, ...] = (
    Criterion("Độ chính xác", 0.25, DEFAULT_CRITERIA[0].metrics),
    Criterion("Tầng category", 0.10, (Metric("cat_hit_at_5", True, 0.5), Metric("cat_p_at_5", True, 0.5))),
    *DEFAULT_CRITERIA[1:],
)


def with_weight(criteria: tuple[Criterion, ...], name: str, delta: float) -> tuple[Criterion, ...]:
    """Tăng trọng số tiêu chí `name` thêm delta, trừ đều phần chênh cho các tiêu chí còn lại (tổng vẫn = 1)."""
    others = [c for c in criteria if c.name != name]
    out = []
    for c in criteria:
        w = c.weight + delta if c.name == name else c.weight - delta / len(others)
        out.append(Criterion(c.name, round(w, 6), c.metrics))
    return tuple(out)


def sensitivity(df: pd.DataFrame, delta: float = 0.05) -> list[dict]:
    """Đổi từng trọng số ±delta, ghi model hạng 1 và thứ hạng đầy đủ."""
    res = []
    for c in DEFAULT_CRITERIA:
        for d in (+delta, -delta):
            crit = with_weight(DEFAULT_CRITERIA, c.name, d)
            t = score_table(df, criteria=crit)
            res.append({"tieu_chi": c.name, "delta": d, "hang_1": t.iloc[0]["model"], "thu_hang": t["model"].tolist(),
                        "tong_diem": dict(zip(t["model"], t["tong_diem"]))})
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DEFAULT_CSV)
    a = ap.parse_args()
    df = load_khoa_csv(a.csv)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    df.to_csv(os.path.join(ROOT, "results", "bench_image_embed_from_khoa.csv"), index=False)
    res = score_table(df)
    md = to_markdown(res)
    base_rank = res["model"].tolist()
    sens = sensitivity(df)
    n_same_top = sum(s["hang_1"] == base_rank[0] for s in sens)
    note = (f"\n\nNguồn: `{os.path.relpath(a.csv, ROOT)}` ({len(df)} model, split test eval_visual, shared_data v1 seed 42). "
            f"Độ nhạy: đổi từng trọng số ±0,05 → hạng 1 vẫn là **{base_rank[0]}** ở {n_same_top}/{len(sens)} cấu hình "
            f"(chi tiết `results/weighted_scoring_sensitivity.json`).\n")
    with open(os.path.join(ROOT, "results", "weighted_scoring.md"), "w", encoding="utf-8") as f:
        f.write(md + note)
    res.to_json(os.path.join(ROOT, "results", "weighted_scoring.json"), orient="records", force_ascii=False, indent=1)
    with open(os.path.join(ROOT, "results", "weighted_scoring_sensitivity.json"), "w", encoding="utf-8") as f:
        json.dump({"base_rank": base_rank, "delta": 0.05, "configs": sens}, f, ensure_ascii=False, indent=1)
    res_b = score_table(df, criteria=CRITERIA_B)
    res_b.to_json(os.path.join(ROOT, "results", "weighted_scoring_scenario_B.json"), orient="records", force_ascii=False, indent=1)
    with open(os.path.join(ROOT, "results", "weighted_scoring.md"), "a", encoding="utf-8") as f:
        f.write("\n### Kịch bản B (đề xuất, chưa chốt): thêm tiêu chí Tầng category 0,10, Độ chính xác instance còn 0,25\n\n"
                + to_markdown(res_b, CRITERIA_B) + "\n")
    print(to_markdown(res_b, CRITERIA_B))
    print(df.drop(columns=["source_file"]).to_string())
    print(md + note)


if __name__ == "__main__":
    main()
