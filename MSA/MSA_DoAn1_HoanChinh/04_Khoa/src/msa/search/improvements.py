# repo: src/msa/search/improvements.py
"""Cải tiến Visual Search (US_45) – Owner: Khoa.

- I1 `bbox_crop`: cắt sát vật thể theo nền trắng (ảnh studio FPI nền trắng) rồi chừa lề; fallback center-crop
  khi không tìm được vùng vật thể. (rembg/YOLO không dùng ở lượt này để tiết kiệm CPU – ghi trong tài liệu.)
- I2 `embed_tta_hflip`: embedding truy vấn = trung bình (ảnh, ảnh lật ngang) rồi L2-normalize.
- I3 `LinearAdapter`: ánh xạ tuyến tính W (ridge kéo về ma trận đơn vị) từ embedding ảnh truy vấn "nhiễu"
  sang embedding ảnh catalog, học trên cặp (ảnh biến đổi, ảnh gốc) của các SP KHÔNG nằm trong tập test.
- I19 type gate: xem `msa.search.visual.VisualSearcher.type_probs` (zero-shot text / centroid).
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image, ImageOps

from msa.embed.image_embedders import ImageEmbedder, ImageLike, l2n, load_image


def bbox_crop(img: ImageLike, thr: int = 240, margin: float = 0.06, min_frac: float = 0.05, center_frac: float = 0.85) -> Image.Image:
    """I1 – cắt theo bounding box các pixel không-trắng (< thr). Nếu vùng vật thể quá nhỏ/không có -> center-crop."""
    im = load_image(img)
    a = np.asarray(im.convert("L"))
    ys, xs = np.where(a < thr)
    w, h = im.size
    if len(xs) < min_frac * w * h * 0.1:
        cw, ch = int(w * center_frac), int(h * center_frac)
        return im.crop(((w - cw) // 2, (h - ch) // 2, (w - cw) // 2 + cw, (h - ch) // 2 + ch))
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    mx, my = int((x1 - x0) * margin), int((y1 - y0) * margin)
    box = (max(0, x0 - mx), max(0, y0 - my), min(w, x1 + mx), min(h, y1 + my))
    if (box[2] - box[0]) * (box[3] - box[1]) < min_frac * w * h:
        return im
    return im.crop(box)


def embed_with_crop(emb: ImageEmbedder, images: Sequence[ImageLike], batch_size: int = 32) -> np.ndarray:
    return emb.embed([bbox_crop(i) for i in images], batch_size=batch_size)


def embed_tta_hflip(emb: ImageEmbedder, images: Sequence[ImageLike], batch_size: int = 32) -> np.ndarray:
    """I2 – TTA lật ngang: mean(emb(x), emb(flip(x)))."""
    ims = [load_image(i) for i in images]
    a = emb.embed(ims, batch_size=batch_size)
    b = emb.embed([ImageOps.mirror(i) for i in ims], batch_size=batch_size)
    return l2n(a + b)


class LinearAdapter:
    """I3 – W = argmin ||A W - B||² + λ||W - I||²  (nghiệm đóng), áp lên embedding truy vấn rồi L2-normalize."""

    def __init__(self, lam: float = 1.0):
        self.lam = lam
        self.W: np.ndarray | None = None

    def fit(self, A: np.ndarray, B: np.ndarray) -> "LinearAdapter":
        A = np.asarray(A, dtype=np.float64); B = np.asarray(B, dtype=np.float64)
        d = A.shape[1]
        I = np.eye(d)
        self.W = np.linalg.solve(A.T @ A + self.lam * I, A.T @ B + self.lam * I)
        return self

    def transform(self, Q: np.ndarray) -> np.ndarray:
        if self.W is None:
            raise RuntimeError("Adapter chưa fit")
        return l2n(np.asarray(Q, dtype=np.float64) @ self.W)

    def save(self, path: str | Path) -> None:
        np.savez(path, W=self.W, lam=self.lam)

    @classmethod
    def load(cls, path: str | Path) -> "LinearAdapter":
        z = np.load(path)
        a = cls(float(z["lam"])); a.W = z["W"]
        return a
