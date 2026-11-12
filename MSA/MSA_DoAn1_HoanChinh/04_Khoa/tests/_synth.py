"""Sinh catalog ảnh giả (hình khối màu trên nền trắng) cho test – không cần dữ liệu thật."""
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

TYPES = ["footwear", "clothing", "headwear", "accessory"]


def make_catalog(tmp: Path, n_per_type: int = 6, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    (tmp / "imgs").mkdir(parents=True, exist_ok=True)
    rows = []
    for ti, t in enumerate(TYPES):
        for i in range(n_per_type):
            im = Image.new("RGB", (60, 80), "white")
            d = ImageDraw.Draw(im)
            col = tuple(int(c) for c in rng.integers(0, 220, 3))
            x0, y0 = int(rng.integers(2, 15)), int(rng.integers(2, 25))
            shape = [d.rectangle, d.ellipse, d.polygon, d.line][ti]
            if ti == 2:
                d.polygon([(x0, y0 + 40), (x0 + 30, y0), (x0 + 40, y0 + 45)], fill=col)
            elif ti == 3:
                d.line([(x0, y0), (x0 + 40, y0 + 45)], fill=col, width=8)
            else:
                shape([x0, y0, x0 + 30 + i, y0 + 40], fill=col)
            pid = f"p_{t[:3]}_{i}"
            rel = f"imgs/{pid}.jpg"; im.save(tmp / rel)
            rows.append(dict(product_id=pid, title=f"{t} {i}", product_type=t, sub_category="unknown", image_paths=[rel]))
    return pd.DataFrame(rows)
