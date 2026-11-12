# repo: src/msa/api/searchers.py
"""Bộ tìm kiếm ảnh cho API (/search/image). Giao diện khớp mục 5.3 (Khoa là Owner của msa.search.visual):
`search(image, k=10, product_type=None) -> list[dict{product_id, score, product_type}]`, `type_gate(image) -> (product_type, conf)`.

- `ClipFaissSearcher`: CLIP ViT-B/32 (HF `openai/clip-vit-base-patch32`, chạy CPU) + FAISS IndexFlatIP trên catalog thật.
  Product-type gate zero-shot bằng prompt văn bản; lọc FAISS theo nhóm.
- `DummyVisualSearcher`: embedding = histogram màu (cho test, không cần model).
- `get_visual_searcher()`: ưu tiên module của Khoa nếu import được (MSA_VISUAL_BACKEND=khoa), mặc định clip.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol, Sequence

import numpy as np
from PIL import Image

PRODUCT_TYPE_PROMPTS = {  # zero-shot gate – prompt tiếng Anh vì CLIP gốc huấn luyện tiếng Anh
    "footwear": ["a photo of a shoe", "a photo of sneakers", "a photo of sandals", "a photo of high heels", "a photo of boots"],
    "clothing": ["a photo of a t-shirt", "a photo of a shirt", "a photo of trousers", "a photo of a dress", "a photo of a jacket"],
    "headwear": ["a photo of a cap", "a photo of a hat", "a photo of a beanie"],
    "accessory": ["a photo of a handbag", "a photo of a backpack", "a photo of a belt", "a photo of sunglasses"],
}


class VisualSearcherProto(Protocol):
    def search(self, image: Image.Image, k: int = 10, product_type: str | None = None) -> list[dict]: ...

    def type_gate(self, image: Image.Image) -> tuple[str | None, float]: ...


class _FlatIndex:
    """FAISS IndexFlatIP theo từng product_type (+ toàn bộ). Fallback numpy nếu thiếu faiss."""

    def __init__(self, emb: np.ndarray, ids: Sequence[str], types: Sequence[str]):
        self.ids, self.types = np.asarray(ids), np.asarray(types)
        self.emb = np.ascontiguousarray(emb.astype("float32"))
        try:
            import faiss
            self.faiss = faiss
        except ImportError:  # pragma: no cover
            self.faiss = None
        self.sub: dict[str | None, tuple] = {None: self._make(np.arange(len(self.ids)))}
        for t in sorted(set(types)):
            self.sub[t] = self._make(np.where(self.types == t)[0])

    def _make(self, rows: np.ndarray):
        if self.faiss is None:
            return rows, self.emb[rows]
        idx = self.faiss.IndexFlatIP(self.emb.shape[1])
        idx.add(self.emb[rows])
        return rows, idx

    def search(self, q: np.ndarray, k: int, product_type: str | None) -> list[dict]:
        rows, idx = self.sub.get(product_type, (np.array([], int), None))
        if len(rows) == 0:
            return []
        k = min(k, len(rows))
        q = np.ascontiguousarray(q.reshape(1, -1).astype("float32"))
        if self.faiss is None:
            s = (idx @ q[0])
            top = np.argsort(-s)[:k]
            D, I = s[top][None], top[None]
        else:
            D, I = idx.search(q, k)
        return [{"product_id": str(self.ids[rows[i]]), "score": float(d), "product_type": str(self.types[rows[i]])}
                for d, i in zip(D[0], I[0]) if i >= 0]


class DummyVisualSearcher:
    """Searcher giả cho test: vector = histogram màu RGB 4×4×4 chuẩn hoá L2 (tất định, không cần model)."""

    def __init__(self, images: dict[str, Image.Image], types: dict[str, str]):
        ids = sorted(images)
        self.index = _FlatIndex(np.stack([self.embed(images[i]) for i in ids]), ids, [types[i] for i in ids])

    @staticmethod
    def embed(img: Image.Image) -> np.ndarray:
        a = np.asarray(img.convert("RGB").resize((32, 32))).reshape(-1, 3) // 64
        h = np.bincount(a[:, 0] * 16 + a[:, 1] * 4 + a[:, 2], minlength=64).astype("float32")
        return h / (np.linalg.norm(h) + 1e-9)

    def type_gate(self, image: Image.Image) -> tuple[str | None, float]:
        res = self.index.search(self.embed(image), 1, None)
        return (res[0]["product_type"], res[0]["score"]) if res else (None, 0.0)

    def search(self, image: Image.Image, k: int = 10, product_type: str | None = None) -> list[dict]:
        return self.index.search(self.embed(image), k, product_type)


class ClipFaissSearcher:
    """CLIP ViT-B/32 + FAISS trên catalog thật. Embedding catalog cache ở `cache_dir` (npy + ids json)."""

    MODEL = "openai/clip-vit-base-patch32"

    def __init__(self, catalog_df, images_root: str | os.PathLike, cache_dir: str | os.PathLike,
                 gate_min_conf: float = 0.5, batch_size: int = 32):
        import torch
        from transformers import CLIPModel, CLIPProcessor
        torch.set_num_threads(int(os.environ.get("MSA_TORCH_THREADS", 2)))
        self.torch = torch
        self.model = CLIPModel.from_pretrained(self.MODEL).eval()
        self.proc = CLIPProcessor.from_pretrained(self.MODEL)
        self.gate_min_conf = gate_min_conf
        df = catalog_df[catalog_df.image_paths.map(len) > 0]
        root = Path(images_root)
        df = df[[(root / p[0]).exists() for p in df.image_paths]]
        ids, types = df.product_id.tolist(), df.product_type.tolist()
        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        f_emb, f_ids = cache / "clip_b32_catalog.npy", cache / "clip_b32_catalog_ids.json"
        if f_emb.exists() and f_ids.exists() and json.loads(f_ids.read_text(encoding="utf-8")) == ids:
            emb = np.load(f_emb)
        else:
            embs = []
            for i in range(0, len(ids), batch_size):
                ims = [Image.open(root / p[0]).convert("RGB") for p in df.image_paths.iloc[i:i + batch_size]]
                embs.append(self.embed(ims))
            emb = np.concatenate(embs)
            np.save(f_emb, emb)
            f_ids.write_text(json.dumps(ids), encoding="utf-8")
        self.index = _FlatIndex(emb, ids, types)
        # vector văn bản cho type gate (trung bình các prompt mỗi nhóm)
        self.gate_types = list(PRODUCT_TYPE_PROMPTS)
        tv = []
        for t in self.gate_types:
            e = self._embed_text(PRODUCT_TYPE_PROMPTS[t]).mean(0)
            tv.append(e / np.linalg.norm(e))
        self.gate_vecs = np.stack(tv)

    @staticmethod
    def _as_array(out) -> "np.ndarray":
        """transformers mới có thể trả ModelOutput thay vì tensor → lấy pooler/embeds."""
        if hasattr(out, "detach"):
            return out.detach().numpy()
        for k in ("image_embeds", "text_embeds", "pooler_output"):
            v = getattr(out, k, None)
            if v is not None:
                return v.detach().numpy()
        raise TypeError(type(out))

    def _embed_text(self, texts: list[str]) -> np.ndarray:
        with self.torch.no_grad():
            t = self.proc(text=texts, return_tensors="pt", padding=True)
            e = self._as_array(self.model.get_text_features(**t))
        return e / np.linalg.norm(e, axis=1, keepdims=True)

    def embed(self, images: list[Image.Image]) -> np.ndarray:
        """Ảnh → vector 512 chiều L2-normalized."""
        with self.torch.no_grad():
            x = self.proc(images=[im.convert("RGB") for im in images], return_tensors="pt")
            e = self._as_array(self.model.get_image_features(**x))
        return (e / np.linalg.norm(e, axis=1, keepdims=True)).astype("float32")

    def type_gate(self, image: Image.Image) -> tuple[str | None, float]:
        """Zero-shot: softmax(100·cos) giữa ảnh và vector prompt mỗi nhóm."""
        v = self.embed([image])[0]
        logits = 100 * self.gate_vecs @ v
        p = np.exp(logits - logits.max())
        p /= p.sum()
        i = int(p.argmax())
        return self.gate_types[i], float(p[i])

    def search(self, image: Image.Image, k: int = 10, product_type: str | None = None, use_gate: bool = True) -> list[dict]:
        v = self.embed([image])[0]
        pt = product_type
        if pt is None and use_gate:
            logits = 100 * self.gate_vecs @ v
            p = np.exp(logits - logits.max())
            p /= p.sum()
            if p.max() >= self.gate_min_conf:
                pt = self.gate_types[int(p.argmax())]
        return self.index.search(v, k, pt)


def get_visual_searcher(catalog_df, images_root, cache_dir) -> VisualSearcherProto:
    """Chọn backend theo MSA_VISUAL_BACKEND: 'khoa' (msa.search.visual.VisualSearcher nếu có) | 'clip' (mặc định)."""
    backend = os.environ.get("MSA_VISUAL_BACKEND", "clip")
    if backend == "khoa":
        try:
            from msa.search.visual import VisualSearcher  # type: ignore
            return VisualSearcher()
        except Exception:  # pragma: no cover – chưa ghép module của Khoa
            pass
    return ClipFaissSearcher(catalog_df, images_root, cache_dir)
