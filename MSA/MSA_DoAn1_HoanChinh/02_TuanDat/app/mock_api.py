# repo: app/mock_api.py
"""API giả lập (khi FastAPI của Hoàng chưa chạy) – trả response đúng hợp đồng 5.2 từ dữ liệu THẬT đã làm sạch.

Không gọi model: tìm kiếm = khớp từ khoá tiêu đề; ảnh = trả ngẫu nhiên có seed cùng product_type (đánh dấu rõ là MOCK);
QA = đọc product_review_summary.json; chat = câu trả lời mẫu gắn source="gemini" để kiểm nhãn UI.
"""
from __future__ import annotations
import os

import json
import random
import re
import time
import uuid
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "results" / "catalog_clean.parquet"
SUMMARY = ROOT / "results" / "product_review_summary.json"
IMAGE_ROOT = Path(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))
VI2EN = {"giày": "shoe", "giay": "shoe", "dép": "sandal", "dep": "sandal", "áo": "shirt", "ao": "shirt",
         "thun": "tshirt", "quần": "jean", "quan": "jean", "váy": "dress", "đầm": "dress", "mũ": "cap", "nón": "cap",
         "túi": "bag", "tui": "bag", "kính": "sunglass", "thắt lưng": "belt", "đen": "black", "trắng": "white",
         "xanh": "blue", "đỏ": "red", "nâu": "brown", "nam": "men", "nữ": "women", "balo": "backpack"}


def _resp(route: str, answer: str, items: list[dict] | None = None, source: str = "internal",
          confidence: float = 0.0, citations: list | None = None, t0: float | None = None) -> dict:
    return {"route": route, "confidence": confidence, "source": source, "answer": answer, "items": items or [],
            "citations": citations or [], "latency_ms": round((time.perf_counter() - (t0 or time.perf_counter())) * 1000, 1),
            "request_id": str(uuid.uuid4()), "mock": True}


class MockAPI:
    def __init__(self, catalog: Path = CATALOG, summary: Path = SUMMARY, seed: int = 42):
        self.df = pd.read_parquet(catalog) if Path(catalog).exists() else pd.DataFrame()
        self.summ = json.loads(Path(summary).read_text(encoding="utf-8"))["products"] if Path(summary).exists() else {}
        self.rng = random.Random(seed)

    def _item(self, r: pd.Series, score: float | None) -> dict:
        return {"product_id": r.product_id, "title": r.title, "price": r.price, "currency": r.currency,
                "score": score, "image": list(r.image_paths)[0] if len(r.image_paths) else None,
                "source_url": r.source_url, "product_type": r.product_type, "sub_category": r.sub_category,
                "brand": r.brand, "colors": list(r.colors) if r.colors is not None else []}

    def search_text(self, query: str, k: int = 8) -> dict:
        t0 = time.perf_counter()
        q = query.lower()
        toks = [VI2EN.get(w, w) for w in re.findall(r"\w+", q)] + [v for kk, v in VI2EN.items() if " " in kk and kk in q]
        if self.df.empty:
            return _resp("search", "Chưa có catalog.", t0=t0)
        title = self.df.title.str.lower()
        score = sum(title.str.contains(re.escape(t)).astype(int) for t in toks if len(t) >= 3) if toks else 0
        top = self.df.assign(match_score=score).sort_values("match_score", ascending=False).head(k)
        top = top[top.match_score > 0]
        items = [self._item(r, round(r.match_score / max(1, len(toks)), 2)) for r in top.itertuples()]
        msg = f"(MOCK) Tìm thấy {len(items)} sản phẩm khớp từ khoá." if items else "(MOCK) Không tìm thấy sản phẩm phù hợp."
        return _resp("search", msg, items, confidence=0.5 if items else 0.1, t0=t0)

    def search_image(self, image_bytes: bytes | None, k: int = 6, product_type: str | None = None) -> dict:
        t0 = time.perf_counter()
        if not image_bytes:
            return _resp("clarify", "Bạn gửi giúp mình ảnh sản phẩm nhé.", t0=t0)
        g = self.df if not product_type else self.df[self.df.product_type == product_type]
        s = g.sample(min(k, len(g)), random_state=self.rng.randint(0, 9999))
        items = [self._item(r, None) for r in s.itertuples()]
        return _resp("visual", "(MOCK – chưa nối VisualSearcher, kết quả ngẫu nhiên, không có điểm tương đồng)",
                     items, t0=t0)

    def qa(self, question: str, product_id: str | None) -> dict:
        t0 = time.perf_counter()
        s = self.summ.get(product_id or "")
        if not s:
            return _resp("qa", "Xin lỗi, hiện chưa có thông tin về điều này trong dữ liệu sản phẩm.", t0=t0)
        cites = [{"product_id": product_id, "field": "review", "chunk_id": str(e["comment_id"])}
                 for x in s["pros"][:2] + s["cons"][:1] for e in x["evidence"][:1]]
        return _resp("qa", s["text_vi"], citations=cites, confidence=0.6, t0=t0)

    def compare(self, product_ids: list[str]) -> dict:
        t0 = time.perf_counter()
        rows = self.df[self.df.product_id.isin(product_ids)]
        items = [self._item(r, None) for r in rows.itertuples()]
        for it in items:
            s = self.summ.get(it["product_id"])
            if s:
                it["pros"] = [x["label"] for x in s["pros"][:3]]
                it["cons"] = [x["label"] for x in s["cons"][:2]]
        if len(items) < 2:
            return _resp("clarify", "Cần ít nhất 2 mã sản phẩm có trong catalog để so sánh.", items, t0=t0)
        return _resp("compare", f"(MOCK) So sánh {len(items)} sản phẩm.", items[:3], t0=t0)

    def chat(self, text: str) -> dict:
        t0 = time.perf_counter()
        return _resp("gemini_chitchat", "(MOCK Gemini) Chào bạn! Mình là trợ lý mua sắm thời trang, bạn cần tìm gì?",
                     source="gemini", confidence=0.9, t0=t0)
