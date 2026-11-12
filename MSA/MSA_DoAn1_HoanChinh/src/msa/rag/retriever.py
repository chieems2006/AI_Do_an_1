# repo: src/msa/rag/retriever.py
"""US_33/34 – Bộ truy xuất cho RAG: TF-IDF (char n-gram), BM25 (âm tiết), Dense (embedder cắm được), Hybrid (RRF).

Mọi retriever có `search(query, k=5, product_id=None) -> list[dict]` (chunk + "score"), lọc theo product_id
nếu có (người dùng đang ở trang 1 sản phẩm). Văn bản được bỏ dấu khi so khớp từ vựng để chịu được câu
không dấu / teencode.
"""
from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Protocol

import numpy as np

TEENCODE = {"ko": "không", "k": "không", "kh": "không", "khg": "không", "hong": "không", "bn": "bao nhiêu",
            "sz": "size", "đc": "được", "dc": "được", "mn": "mọi người", "vs": "với", "j": "gì", "r": "rồi",
            "sp": "sản phẩm", "tks": "cảm ơn", "z": "vậy", "v": "vậy", "ntn": "như thế nào", "mk": "mình",
            "mik": "mình", "bt": "bình thường", "bth": "bình thường"}


def strip_accents(s: str) -> str:
    """Bỏ dấu tiếng Việt (đ → d)."""
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def normalize_query(q: str) -> str:
    """Viết lại teencode phổ biến (query rewriting đơn giản, I-cải tiến RAG)."""
    toks = re.findall(r"\w+|\S", unicodedata.normalize("NFC", q.lower()))
    return " ".join(TEENCODE.get(t, t) for t in toks)


def tokenize(s: str) -> list[str]:
    """Tách âm tiết sau khi bỏ dấu."""
    return re.findall(r"[a-z0-9]+", strip_accents(s))


class Embedder(Protocol):
    def encode_queries(self, texts: list[str]) -> np.ndarray: ...
    def encode_passages(self, texts: list[str]) -> np.ndarray: ...


class DummyEmbedder:
    """Embedder giả (hashing âm tiết, L2-normalized) – dùng cho test, không cần tải model."""

    name = "dummy-hash-256"

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _enc(self, texts: list[str]) -> np.ndarray:
        m = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for tok in tokenize(t):
                m[i, int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim] += 1.0
        n = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.maximum(n, 1e-9)

    encode_queries = _enc
    encode_passages = _enc


class STEmbedder:
    """Bọc sentence-transformers; tự thêm tiền tố 'query: '/'passage: ' cho họ E5."""

    def __init__(self, model_name: str = "intfloat/multilingual-e5-small", batch_size: int = 32,
                 cache_dir: Path | None = None):
        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(2)
        self.name = model_name
        self.model = SentenceTransformer(model_name, device="cpu")
        self.batch_size = batch_size
        self.e5 = "e5" in model_name.lower()
        self.cache_dir = cache_dir

    def _enc(self, texts: list[str], prefix: str) -> np.ndarray:
        texts = [prefix + t for t in texts] if self.e5 else texts
        return self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                 show_progress_bar=False, convert_to_numpy=True).astype(np.float32)

    def encode_queries(self, texts: list[str]) -> np.ndarray:
        return self._enc(texts, "query: ")

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        if self.cache_dir is not None:
            h = hashlib.md5(("\n".join(texts) + self.name).encode()).hexdigest()[:16]
            p = Path(self.cache_dir) / f"emb_{self.name.replace('/', '_')}_{h}.npy"
            if p.exists():
                return np.load(p)
            v = self._enc(texts, "passage: ")
            p.parent.mkdir(parents=True, exist_ok=True)
            np.save(p, v)
            return v
        return self._enc(texts, "passage: ")


class _Base:
    """Phần chung: giữ chunks, chỉ số theo product_id, trả kết quả."""

    name = "base"

    def __init__(self, chunks: list[dict], rewrite: bool = False):
        self.chunks = chunks
        self.rewrite = rewrite
        self.by_pid: dict[str, list[int]] = defaultdict(list)
        for i, c in enumerate(chunks):
            self.by_pid[c["product_id"]].append(i)

    def _q(self, q: str) -> str:
        return normalize_query(q) if self.rewrite else q

    def _scores(self, query: str, idx: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def search(self, query: str, k: int = 5, product_id: str | None = None) -> list[dict]:
        if product_id is not None:
            idx = np.array(self.by_pid.get(product_id, []), dtype=int)
        else:
            idx = np.arange(len(self.chunks))
        if len(idx) == 0:
            return []
        s = self._scores(self._q(query), idx)
        order = np.argsort(-s, kind="stable")[:k]
        return [{**self.chunks[int(idx[o])], "score": float(s[o])} for o in order]


class TfidfRetriever(_Base):
    """TF-IDF char n-gram (2-4, char_wb) trên văn bản bỏ dấu; cosine."""

    name = "tfidf_char"

    def __init__(self, chunks: list[dict], rewrite: bool = False):
        super().__init__(chunks, rewrite)
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), preprocessor=strip_accents,
                                   sublinear_tf=True, min_df=1)
        self.X = self.vec.fit_transform([c["text"] for c in chunks])

    def _scores(self, query: str, idx: np.ndarray) -> np.ndarray:
        qv = self.vec.transform([query])
        return (self.X[idx] @ qv.T).toarray().ravel()


class BM25Retriever(_Base):
    """BM25 Okapi trên âm tiết bỏ dấu (k1=1.5, b=0.75)."""

    name = "bm25"

    def __init__(self, chunks: list[dict], rewrite: bool = False, k1: float = 1.5, b: float = 0.75):
        super().__init__(chunks, rewrite)
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(c["text"])) for c in chunks]
        self.dl = np.array([sum(d.values()) for d in self.docs], dtype=float)
        self.avgdl = float(self.dl.mean()) if len(self.dl) else 1.0
        df: Counter = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def _scores(self, query: str, idx: np.ndarray) -> np.ndarray:
        qt = tokenize(query)
        out = np.zeros(len(idx))
        for j, i in enumerate(idx):
            d, dl = self.docs[i], self.dl[i]
            s = 0.0
            for t in qt:
                f = d.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out[j] = s
        return out


class DenseRetriever(_Base):
    """Dense retrieval với embedder cắm được (cosine trên vector L2-normalized; FAISS Flat nếu có)."""

    def __init__(self, chunks: list[dict], embedder: Embedder, rewrite: bool = False):
        super().__init__(chunks, rewrite)
        self.embedder = embedder
        self.name = f"dense:{getattr(embedder, 'name', 'custom')}"
        self.E = embedder.encode_passages([c["text"] for c in chunks])

    def _scores(self, query: str, idx: np.ndarray) -> np.ndarray:
        q = self.embedder.encode_queries([query])[0]
        return self.E[idx] @ q


class HybridRetriever(_Base):
    """Kết hợp nhiều retriever bằng Reciprocal Rank Fusion (k=60); score trả về = điểm của retriever đầu."""

    def __init__(self, retrievers: list[_Base], rrf_k: int = 60, pool: int = 50):
        super().__init__(retrievers[0].chunks)
        self.rs, self.rrf_k, self.pool = retrievers, rrf_k, pool
        self.name = "hybrid_rrf(" + "+".join(r.name for r in retrievers) + ")"

    def search(self, query: str, k: int = 5, product_id: str | None = None) -> list[dict]:
        fused: dict[str, float] = defaultdict(float)
        first: dict[str, dict] = {}
        for ri, r in enumerate(self.rs):
            for rank, c in enumerate(r.search(query, k=self.pool, product_id=product_id)):
                fused[c["chunk_id"]] += 1.0 / (self.rrf_k + rank + 1)
                if ri == 0 or c["chunk_id"] not in first:
                    first.setdefault(c["chunk_id"], c)
        top = sorted(fused, key=lambda x: -fused[x])[:k]
        return [{**first[cid], "rrf": fused[cid]} for cid in top]
