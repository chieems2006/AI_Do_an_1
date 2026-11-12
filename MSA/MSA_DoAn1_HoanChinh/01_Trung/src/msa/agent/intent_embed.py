# repo: src/msa/agent/intent_embed.py
"""Bộ phân loại ý định bằng embedding (tuỳ chọn, dùng làm tín hiệu phụ cho Router).
Prototype k-NN: nhúng câu mẫu đã gán nhãn (mặc định: eval_router_seed.jsonl của Trung – KHÔNG dùng tập test),
dự đoán nhãn của láng giềng gần nhất (cosine). Model: intfloat/multilingual-e5-small (prefix 'query: ')."""
from __future__ import annotations

import json
import os

import numpy as np

DEFAULT_PROTOS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                              "eval", "eval_router_seed.jsonl")


class PrototypeIntentEmbedder:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small", protos_path: str = DEFAULT_PROTOS, k: int = 3):
        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(2)
        self.name = model_name
        self.model = SentenceTransformer(model_name, device="cpu")
        rows = [json.loads(line) for line in open(protos_path, encoding="utf-8") if line.strip()]
        # bỏ câu có ảnh (visual do luật quyết định) và câu rỗng
        rows = [r for r in rows if r.get("text") and not r.get("has_image")]
        self.labels = [r["route"] for r in rows]
        self.k = k
        self.P = self._emb([r["text"] for r in rows])

    def _emb(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.encode([f"query: {t}" for t in texts], normalize_embeddings=True, batch_size=16))

    def predict(self, text: str) -> tuple[str, float]:
        v = self._emb([text])[0]
        sims = self.P @ v
        idx = np.argsort(-sims)[: self.k]
        votes: dict[str, float] = {}
        for i in idx:
            votes[self.labels[i]] = votes.get(self.labels[i], 0.0) + float(sims[i])
        lab = max(votes, key=votes.get)
        # quy đổi về thang điểm luật: (cos trung bình của nhãn thắng - 0.8) * 5, chặn [0, 1]
        score = float(np.clip((votes[lab] / sum(1 for i in idx if self.labels[i] == lab) - 0.8) * 5, 0, 1))
        return lab, score
