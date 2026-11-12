# repo: src/msa/search/visual.py
"""Tìm sản phẩm tương tự bằng ảnh (US_29/US_30) – Owner: Khoa.

- `VisualSearcher.search(image, k=10, product_type=None) -> list[dict{product_id, score, product_type}]`
- `VisualSearcher.type_gate(image) -> (product_type, conf)`: zero-shot bằng text prompt (model có text tower)
  hoặc nearest-centroid (mọi model).
- `VisualSearcher.query(image, k)`: bọc cho Agent – áp type gate + ngưỡng τ_v; nếu top-1 < τ_v trả về
  `no_match=True` và câu gợi ý mô tả bằng chữ (theo hợp đồng mục 5.2/5.3).
Index lưu dạng: `<dir>/index.faiss`, `<dir>/embeddings.npy`, `<dir>/meta.parquet` (product_id, product_type,
sub_category, title, image), `<dir>/config.json`.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from msa.embed.image_embedders import ImageEmbedder, ImageLike, get_embedder

TYPES = ["footwear", "clothing", "headwear", "accessory"]
TYPE_PROMPTS = {
    "footwear": ["a photo of shoes", "a photo of sneakers", "a photo of sandals", "a photo of flip flops",
                 "a photo of high heels", "a photo of formal leather shoes", "a photo of boots"],
    "clothing": ["a photo of a t-shirt", "a photo of a shirt", "a photo of a dress", "a photo of jeans",
                 "a photo of trousers", "a photo of shorts", "a photo of a jacket", "a photo of a person wearing clothes",
                 "a photo of a kurta", "a photo of a skirt"],
    "headwear": ["a photo of a cap", "a photo of a baseball cap", "a photo of a hat", "a photo of a beanie",
                 "a photo of a bucket hat", "a photo of a headband"],
    "accessory": ["a photo of a handbag", "a photo of a backpack", "a photo of a bag", "a photo of a belt",
                  "a photo of sunglasses", "a photo of a wallet", "a photo of a clutch"],
}
NO_MATCH_MSG = ("Mình chưa thấy sản phẩm nào đủ giống ảnh bạn gửi trong cửa hàng. "
                "Bạn có thể mô tả bằng chữ (loại sản phẩm, màu, kiểu dáng, khoảng giá) để mình tìm giúp nhé?")


def _faiss():
    import faiss  # import lười

    return faiss


class VisualSearcher:
    """Tìm kiếm ảnh trên FAISS IndexFlatIP (cosine) với lọc theo product_type."""

    def __init__(self, embedder: ImageEmbedder, embeddings: np.ndarray, meta: pd.DataFrame,
                 tau_v: float = 0.25, gate_mode: str = "auto", gate_tau: float = 0.0):
        assert len(embeddings) == len(meta), "embeddings và meta lệch số dòng"
        self.embedder = embedder
        self.X = np.ascontiguousarray(embeddings, dtype=np.float32)
        self.meta = meta.reset_index(drop=True)
        self.tau_v = tau_v
        self.gate_tau = gate_tau
        self.gate_mode = ("zeroshot" if embedder.has_text else "centroid") if gate_mode == "auto" else gate_mode
        faiss = _faiss()
        self.index = faiss.IndexFlatIP(self.X.shape[1]); self.index.add(self.X)
        self._types = self.meta["product_type"].to_numpy()
        self._sub = {}
        for t in TYPES:
            ids = np.where(self._types == t)[0]
            if len(ids):
                ix = faiss.IndexFlatIP(self.X.shape[1]); ix.add(self.X[ids]); self._sub[t] = (ix, ids)
        self._centroids = None
        self._type_text = None

    # ------------------------------------------------------------------ load/save
    @classmethod
    def load(cls, index_dir: str | Path, embedder: ImageEmbedder | None = None, **kw) -> "VisualSearcher":
        d = Path(index_dir)
        cfg = json.loads((d / "config.json").read_text(encoding="utf-8"))
        emb = embedder or get_embedder(cfg["model"])
        X = np.load(d / "embeddings.npy")
        meta = pd.read_parquet(d / "meta.parquet")
        kw.setdefault("tau_v", cfg.get("tau_v", 0.25))
        kw.setdefault("gate_tau", cfg.get("gate_tau", 0.0))
        return cls(emb, X, meta, **kw)

    # ------------------------------------------------------------------ core
    def embed_query(self, image: ImageLike) -> np.ndarray:
        return self.embedder.embed([image])[0]

    def _search_vec(self, q: np.ndarray, k: int, product_type: str | None) -> list[dict]:
        q = np.ascontiguousarray(q.reshape(1, -1), dtype=np.float32)
        if product_type and product_type in self._sub:
            ix, ids = self._sub[product_type]
            D, I = ix.search(q, min(k, len(ids))); I = ids[I[0]]; D = D[0]
        else:
            D, I = self.index.search(q, min(k, len(self.X))); D, I = D[0], I[0]
        out = []
        for s, j in zip(D, I):
            if j < 0:
                continue
            m = self.meta.iloc[int(j)]
            out.append({"product_id": m["product_id"], "score": float(s), "product_type": m["product_type"],
                        "sub_category": m.get("sub_category"), "title": m.get("title"), "image": m.get("image")})
        return out

    def search(self, image: ImageLike, k: int = 10, product_type: str | None = None) -> list[dict]:
        """Top-k SP giống ảnh nhất; `product_type` để lọc cứng theo nhóm."""
        return self._search_vec(self.embed_query(image), k, product_type)

    def type_probs(self, q: np.ndarray) -> np.ndarray:
        if self.gate_mode == "zeroshot":
            if self._type_text is None:
                self._type_text = {t: self.embedder.embed_text(TYPE_PROMPTS[t]) for t in TYPES}
            s = np.array([(self._type_text[t] @ q).max() for t in TYPES]) * 100.0
        else:
            if self._centroids is None:
                C = np.stack([self.X[self._types == t].mean(0) if (self._types == t).any() else np.zeros(self.X.shape[1]) for t in TYPES])
                self._centroids = C / np.clip(np.linalg.norm(C, axis=1, keepdims=True), 1e-9, None)
            s = (self._centroids @ q) * 50.0
        s = s - s.max(); p = np.exp(s)
        return p / p.sum()

    def type_gate(self, image: ImageLike) -> tuple[str, float]:
        """Dự đoán product_type của ảnh + độ tin cậy (softmax)."""
        p = self.type_probs(self.embed_query(image))
        j = int(p.argmax())
        return TYPES[j], float(p[j])

    def query(self, image: ImageLike, k: int = 10, use_gate: bool = True, product_type: str | None = None) -> dict:
        """Giao diện cho Agent: trả về dict theo hợp đồng response (route=visual)."""
        t0 = time.perf_counter()
        q = self.embed_query(image)
        gate = None
        if product_type is None and use_gate:
            p = self.type_probs(q); j = int(p.argmax()); gate = (TYPES[j], float(p[j]))
            if gate[1] >= self.gate_tau:
                product_type = gate[0]
        items = self._search_vec(q, k, product_type)
        top1 = items[0]["score"] if items else 0.0
        no_match = top1 < self.tau_v
        return {"route": "visual", "confidence": float(top1), "source": "internal",
                "answer": NO_MATCH_MSG if no_match else f"Đây là {len(items)} sản phẩm giống ảnh của bạn nhất.",
                "items": [] if no_match else items, "no_match": no_match,
                "type_gate": {"product_type": gate[0], "conf": gate[1]} if gate else None,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2)}


def build_meta(cat: pd.DataFrame, image_root: str | Path) -> pd.DataFrame:
    """Meta tối thiểu cho index từ catalog theo schema 5.1."""
    root = Path(image_root)
    return pd.DataFrame({
        "product_id": cat["product_id"].values, "product_type": cat["product_type"].values,
        "sub_category": cat["sub_category"].values, "title": cat["title"].values,
        "image": [str(root / a[0]) for a in cat["image_paths"]],
    })
