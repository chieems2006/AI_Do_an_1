# repo: scripts/make_bench_contexts.py
"""US_24 – Chọn sản phẩm ViMRHP và dựng ngữ cảnh (review THẬT) cố định cho benchmark LLM.

Ngữ cảnh = tối đa N review của 1 SP (ưu tiên review dài + hữu ích), mỗi review cắt ≤ L ký tự, đánh số [R1]..[Rn].
Câu hỏi/đáp án tham chiếu do tác nhân (AI) viết tay sau khi đọc ngữ cảnh → eval/bench_qa_questions.py.

    python src/scripts/make_bench_contexts.py   # ghi eval/bench_contexts.jsonl
"""
from __future__ import annotations
import os

import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = Path((os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/vimrhp_fashion_products.jsonl"))
OUT = ROOT / "eval" / "bench_contexts.jsonl"
SEED = 42
PLAN = {"GiayDepNam": 7, "GiayDepNu": 7, "ThoiTrangNam": 7, "ThoiTrangNu": 7, "PhuKienNu": 8}
PHUKIEN_IN_SCOPE = re.compile(r"thắt lưng|dây lưng|kính|túi|balo|ba lô|mũ|nón", re.I)
ATTR = re.compile(r"chất|size|form|màu|đế|êm|bền|vải|da|rộng|chật|nhỏ|to|dày|mỏng|nóng|mát|phai|đường may|keo|nặng|nhẹ", re.I)


def build(n_reviews: int = 6, max_chars: int = 260) -> list[dict]:
    rng = random.Random(SEED)
    prods = [json.loads(l) for l in SRC.open(encoding="utf-8")]
    out = []
    for sub, k in PLAN.items():
        cands = [p for p in prods if p["vimrhp_subcategory"] == sub and len(p["reviews"]) >= 10]
        if sub == "PhuKienNu":
            cands = [p for p in cands if PHUKIEN_IN_SCOPE.search(p["title"])]
        # điểm thông tin = số review có nhắc thuộc tính
        cands.sort(key=lambda p: -sum(bool(ATTR.search(r["text"] or "")) for r in p["reviews"]))
        top = cands[: k * 3]
        rng.shuffle(top)
        for p in sorted(top[:k], key=lambda p: p["product_id"]):
            revs = sorted(p["reviews"], key=lambda r: -(len(r["text"] or "") * (1 + (r.get("helpfulness") or 0))))
            ctx = []
            for i, r in enumerate(revs[:n_reviews], 1):
                t = re.sub(r"\s+", " ", r["text"] or "").strip()
                t = t if len(t) <= max_chars else t[:max_chars].rsplit(" ", 1)[0] + "…"
                ctx.append({"rid": f"R{i}", "comment_id": r["comment_id"], "rating": r["rating"], "text": t})
            out.append({"product_id": p["product_id"], "title": p["title"], "vimrhp_subcategory": sub,
                        "n_reviews_total": len(p["reviews"]), "context": ctx})
    return out


def context_text(item: dict) -> str:
    """Định dạng ngữ cảnh đưa vào prompt (giống nhau cho mọi LLM)."""
    lines = [f"Sản phẩm: {item['title']}", "Đánh giá của khách hàng:"]
    lines += [f"[{c['rid']}] ({c['rating']}★) {c['text']}" for c in item["context"]]
    return "\n".join(lines)


if __name__ == "__main__":
    items = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"{len(items)} sản phẩm -> {OUT}")
