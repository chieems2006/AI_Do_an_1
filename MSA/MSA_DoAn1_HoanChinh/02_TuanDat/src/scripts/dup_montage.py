# repo: scripts/dup_montage.py
"""Vẽ lưới ví dụ cặp ảnh nghi trùng từ results/dup_pairs.csv (US_08) để người kiểm bằng mắt.

    python src/scripts/dup_montage.py --dist 0 --n 48 --out results/figures/dup_d0.png
"""
from __future__ import annotations
import os

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]


def montage(pairs: pd.DataFrame, image_dir: Path, out: Path, cols: int = 8) -> Path:
    def load(pid: str) -> Image.Image:
        return Image.open(image_dir / f"{pid.split('_', 1)[1]}.jpg").convert("RGB").resize((90, 120))
    rows = (len(pairs) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * 200, max(rows, 1) * 140), "white")
    dr = ImageDraw.Draw(canvas)
    for i, r in enumerate(pairs.itertuples()):
        x, y = (i % cols) * 200, (i // cols) * 140
        canvas.paste(load(r.id_a), (x, y))
        canvas.paste(load(r.id_b), (x + 95, y))
        dr.text((x, y + 122), f"#{i} d={r.dist} {r.action}", fill="red")
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default=str(ROOT / "results" / "dup_pairs.csv"))
    ap.add_argument("--image-dir", default=(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/fpi_images"))
    ap.add_argument("--dist", type=int, default=0)
    ap.add_argument("--n", type=int, default=48)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    p = pd.read_csv(a.pairs)
    s = p[p.dist == a.dist]
    s = s.sample(min(a.n, len(s)), random_state=a.seed).sort_values("action")
    s.to_csv(Path(a.out).with_suffix(".csv"), index=False)
    print(montage(s, Path(a.image_dir), Path(a.out)))


if __name__ == "__main__":
    main()
