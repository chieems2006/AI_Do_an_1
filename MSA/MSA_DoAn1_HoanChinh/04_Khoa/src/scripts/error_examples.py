# repo: scripts/error_examples.py
"""Phân tích lỗi Visual Search từ results/per_query/<model>.csv (split test, số THẬT).

    python src/scripts/error_examples.py --model clip_b32 [--n 10]
-> results/errors_<model>.md (bảng lỗi theo biến đổi/nhóm + 10 ví dụ) và results/errors_<model>.png (ảnh truy vấn | top-3)
"""
from __future__ import annotations
import os

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SHARED = Path(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))


def main(model: str, n: int = 10):
    pq = pd.read_csv(ROOT / "results" / "per_query" / f"{model}.csv", keep_default_na=False)
    ev = pd.read_csv(ROOT / "eval" / "eval_visual.csv", keep_default_na=False)
    cat = pd.read_parquet(SHARED / "catalog_fpi.parquet", columns=["product_id", "title", "product_type", "sub_category", "image_paths"]).set_index("product_id")
    d = pq.merge(ev[["query_id", "query_image", "transform", "gt_product_ids", "sub_category", "article_type"]], on="query_id")
    d = d[d.split == "test"]
    inst = d[d.tier == "instance"].copy()
    inst["tf"] = inst["transform"].str.split("(").str[0]
    inst["miss5"] = inst["R@5"] < 1
    lines = [f"# Phân tích lỗi – `{model}` (split test, đo thật)\n",
             "## Recall@5 theo kiểu biến đổi (tầng instance)\n", "| Biến đổi | n | Recall@5 | Recall@1 | CTE@5 |", "|---|---|---|---|---|"]
    for tf, g in inst.groupby("tf"):
        lines.append(f"| {tf} | {len(g)} | {g['R@5'].mean():.3f} | {g['R@1'].mean():.3f} | {g['CTE@5'].mean():.3f} |")
    lines += ["\n## Recall@5 theo sub_category (instance)\n", "| sub_category | n | Recall@5 |", "|---|---|---|"]
    for s, g in inst.groupby("sub_category"):
        lines.append(f"| {s} | {len(g)} | {g['R@5'].mean():.3f} |")
    # ví dụ lỗi: ưu tiên đa dạng biến đổi/nhóm
    miss = inst[inst.miss5].sort_values(["tf", "product_type"])
    ex = miss.groupby("tf").head(2).head(n - 3)
    catq = d[(d.tier == "category") & (d["P@5"] == 0)].head(3)
    ex = pd.concat([ex, catq])
    lines += ["\n## Ví dụ lỗi điển hình\n", "| # | query_id | Nhóm | Biến đổi | SP đúng (title) | Top-1 trả về (title, nhóm) | Hạng SP đúng | Nhận xét |", "|---|---|---|---|---|---|---|---|"]
    rows_img = []
    for i, r in enumerate(ex.itertuples(), 1):
        gt = r.gt_product_ids.split("|")[0]
        top = r.top5_ids.split("|")
        t1 = cat.loc[top[0]] if top and top[0] in cat.index else None
        gtt = cat.loc[gt].title if gt in cat.index else "?"
        same_type = t1 is not None and t1.product_type == r.product_type
        note = ("cùng nhóm, khác SP" if same_type else "SAI NHÓM") if r.tier == "instance" else "category: top-5 không cùng articleType+màu"
        lines.append(f"| {i} | {r.query_id} | {r.product_type} | {r.transform if r.tier == 'instance' else 'held-out/LOO'} | {gtt if r.tier == 'instance' else r.article_type} | "
                     f"{t1.title if t1 is not None else '?'} ({t1.product_type if t1 is not None else '?'}) | {r.rank if r.rank else '>10'} | {note} |")
        rows_img.append([ROOT / r.query_image] + [SHARED / cat.loc[p].image_paths[0] for p in top[:3] if p in cat.index])
    (ROOT / "results" / f"errors_{model}.md").write_text("\n".join(lines), encoding="utf-8")
    W, H = 90, 120
    canvas = Image.new("RGB", (W * 4 + 10, H * len(rows_img)), "white")
    for ri, row in enumerate(rows_img):
        for ci, p in enumerate(row):
            canvas.paste(Image.open(p).convert("RGB").resize((W, H)), (ci * W + (10 if ci else 0), ri * H))
        ImageDraw.Draw(canvas).text((2, ri * H + 2), str(ri + 1), fill="red")
    canvas.save(ROOT / "results" / f"errors_{model}.png")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--n", type=int, default=10)
    a = ap.parse_args(); main(a.model, a.n)
