# repo: src/msa/rag/ingest.py
"""US_33 – Kho tri thức: chunk dữ liệu theo từng sản phẩm/trường, gắn metadata truy ngược được.

Mỗi chunk: {chunk_id, product_id, field, text, source, source_url, review_id, rating, title}
- `field` ∈ {title, description, specs, review, detail_rating}
- `chunk_id` = "<product_id>::<field>::<n|review_id>" – duy nhất, truy ngược product_id và nguồn.
Hỗ trợ cả ViMRHP (chỉ có tên + review + DetailRating) lẫn schema 5.1 (description/specs/reviews).

Dùng: PYTHONPATH=src python -m msa.rag.ingest --out data/kb/chunks.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

MAX_CHARS = 500  # mô tả dài được cắt theo câu thành đoạn ≤ 500 ký tự


def clean_text(s: str) -> str:
    """Chuẩn hoá Unicode NFC, gộp khoảng trắng."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip()


def split_sentences(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Cắt văn bản dài thành các đoạn ≤ max_chars theo ranh giới câu."""
    sents = re.split(r"(?<=[.!?。\n])\s+", text)
    out, cur = [], ""
    for s in sents:
        s = s.strip()
        if not s:
            continue
        if cur and len(cur) + len(s) + 1 > max_chars:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return [o[:max_chars * 2] for o in out]


def _parse_detail(detail: str) -> dict[str, float]:
    out = {}
    for line in (detail or "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            try:
                out[k.strip()] = float(v.strip())
            except ValueError:
                pass
    return out


DETAIL_VI = {"product_quality": "chất lượng sản phẩm", "seller_service": "dịch vụ người bán",
             "delivery_service": "giao hàng"}


def chunk_product(p: dict[str, Any], source: str | None = None) -> list[dict]:
    """Sinh chunk cho 1 sản phẩm (dict theo schema 5.1 hoặc bản ghi ViMRHP đã nạp bằng load_vimrhp)."""
    pid = p["product_id"]
    src = source or p.get("source") or ("vimrhp" if str(pid).startswith("shopee_") else "unknown")
    base = {"product_id": pid, "source": src, "source_url": p.get("source_url"), "title": p.get("title", "")}
    chunks: list[dict] = []

    def add(field: str, key: str, text: str, **extra: Any) -> None:
        text = clean_text(text)
        if text:
            chunks.append({**base, "chunk_id": f"{pid}::{field}::{key}", "field": field, "text": text,
                           "review_id": extra.get("review_id"), "rating": extra.get("rating")})

    add("title", "0", p.get("title", ""))
    if p.get("description"):
        for i, part in enumerate(split_sentences(clean_text(p["description"]))):
            add("description", str(i), part)
    specs = p.get("specs")
    if isinstance(specs, str):
        try:
            specs = json.loads(specs)
        except Exception:
            specs = {"thông số": specs}
    if isinstance(specs, dict) and specs:
        add("specs", "0", "; ".join(f"{k}: {v}" for k, v in specs.items() if v not in (None, "")))
    details: list[dict[str, float]] = []
    for j, rv in enumerate(p.get("reviews") or []):
        if isinstance(rv, str):
            add("review", str(j), rv)
            continue
        rid = str(rv.get("review_id") or rv.get("comment_id") or j)
        add("review", rid, rv.get("text", ""), review_id=rid, rating=rv.get("rating"))
        d = _parse_detail(rv.get("detail_rating", ""))
        if d:
            details.append(d)
    if details:
        parts = []
        for k, vi in DETAIL_VI.items():
            vals = [d[k] for d in details if k in d]
            if vals:
                parts.append(f"{vi} {sum(vals) / len(vals):.1f}/5")
        stars = [rv.get("rating") for rv in p.get("reviews") or [] if isinstance(rv, dict) and rv.get("rating")]
        txt = f"Điểm đánh giá chi tiết trung bình từ {len(details)} lượt: " + ", ".join(parts)
        if stars:
            txt += f". Số sao trung bình {sum(stars) / len(stars):.1f}/5"
        add("detail_rating", "0", txt)
    return chunks


def build_chunks(products: Iterable[dict]) -> list[dict]:
    """Chunk toàn bộ sản phẩm; bảo đảm chunk_id duy nhất."""
    out, seen = [], set()
    for p in products:
        for c in chunk_product(p):
            if c["chunk_id"] in seen:
                continue
            seen.add(c["chunk_id"])
            out.append(c)
    return out


def save_chunks(chunks: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def load_chunks(path: Path) -> list[dict]:
    return [json.loads(l) for l in Path(path).open(encoding="utf-8")]


def main() -> None:
    from msa.rag.data import load_vimrhp

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/kb/chunks.jsonl")
    a = ap.parse_args()
    chunks = build_chunks(load_vimrhp())
    save_chunks(chunks, Path(a.out))
    from collections import Counter
    print(json.dumps({"n_chunks": len(chunks), "by_field": Counter(c["field"] for c in chunks),
                      "n_products": len({c["product_id"] for c in chunks})}, ensure_ascii=False))


if __name__ == "__main__":
    main()
