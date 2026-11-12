# repo: scripts/summarize_reviews.py
"""US_36 – Tóm tắt offline ưu/nhược của từng sản phẩm từ review → product_review_summary.json.

Hai cách:
  baseline : luật từ khoá tiếng Việt theo 8 khía cạnh (chất liệu, độ bền, êm/thoải mái, size/form, màu sắc,
             đường may, giao hàng/đóng gói, giá) – có xử lý phủ định đơn giản, lọc review spam/quảng cáo.
             Mỗi ý kèm số review nhắc tới + comment_id minh chứng → không thể "bịa" ngoài review.
  llm      : Gemini tóm tắt (gộp 5 SP/lời gọi), bắt buộc trích chỉ số review; kiểm tự động chồng lấp token.

    python src/scripts/summarize_reviews.py baseline                  # toàn bộ SP ViMRHP trong phạm vi
    python src/scripts/summarize_reviews.py llm --n 20 --model gemini-3.5-flash-lite
"""
from __future__ import annotations
import os

import argparse
import json
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SRC = Path((os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/vimrhp_fashion_products.jsonl"))
OUT = ROOT / "results" / "product_review_summary.json"
OUT_LLM = ROOT / "results" / "product_review_summary_llm20.json"
OUT_OF_SCOPE = {"DongHo"}
GROUP = {"GiayDepNam": "footwear", "GiayDepNu": "footwear", "ThoiTrangNam": "clothing", "ThoiTrangNu": "clothing",
         "PhuKienNu": "accessory"}

# (khía cạnh, nhãn hiển thị, mẫu tích cực, mẫu tiêu cực) – mẫu tiêu cực kiểm TRƯỚC để "không chỉ thừa" không bị đếm nhầm
ASPECTS: list[tuple[str, str, str, str]] = [
    ("material", "Chất liệu/vải",
     r"vải (đẹp|tốt|mát|mềm|mịn|dày)|chất (đẹp|tốt|ổn|xịn|mát|mềm)|dày dặn|mềm mịn|chất lượng (tốt|ổn|cao)",
     r"vải (mỏng tanh|xấu|kém|thô|cứng)|chất (kém|xấu|tệ)|xù lông|mỏng tanh|bai dão|ra màu"),
    ("durability", "Độ bền",
     r"(?<!không )(?<!ko )(?<!k )bền(?! (không|ko|k|hay|chưa|ko)\b)|chắc chắn|cứng cáp|chắc tay",
     r"rách|bung keo|bong keo|hỏng|gãy|tróc|sứt|(?<!biết )(không|ko|k) bền(?! (không|ko|k|hay)\b)|nhanh hỏng|vỡ"),
    ("comfort", "Êm/thoải mái",
     r"(?<!không )(?<!ko )(?<!k )êm|thoải mái|nhẹ chân|thoáng mát|không đau chân|ko đau chân|mát",
     r"đau chân|cấn chân|bí chân|nóng|cọ chân|trầy chân|khó chịu"),
    ("fit", "Size/form",
     r"đúng size|chuẩn size|vừa (vặn|chân|người|khít|y)|form (đẹp|chuẩn)|fom (đẹp|chuẩn)|chuẩn form|đúng form",
     r"(hơi |khá |bị |quá )?(rộng(?! rãi)|chật|nhỏ|bé)( quá| xíu)?\b|lùi (1 )?size|tăng (1 )?size|lên (1 )?size|không vừa|ko vừa|"
     r"k vừa|hơi ngắn|bị ngắn"),
    ("color", "Màu sắc/giống hình",
     r"đúng màu|màu (đẹp|chuẩn|tươi)|như hình|giống hình|y hình|giống ảnh|như ảnh|đúng mẫu|đúng mô tả",
     r"phai màu|lệch màu|khác màu|không giống hình|ko giống hình|nhạt hơn|đậm hơn|không đúng mô tả|k đúng mô tả"),
    ("stitching", "Đường may/hoàn thiện",
     r"đường may (đẹp|chắc|kỹ|khéo)|không (có )?chỉ thừa|ko (có )?chỉ thừa|k (có )?chỉ thừa|may (đẹp|kỹ|chắc)",
     r"(?<!quá )(nhiều |còn |bị )chỉ thừa|đường may (xấu|ẩu)|may ẩu|keo lem|lỗi"),
    ("shipping", "Giao hàng/đóng gói",
     r"giao (hàng )?(nhanh|siêu nhanh|cực nhanh)|ship nhanh|đóng gói (cẩn thận|kỹ|kĩ|chắc)|gói (hàng )?cẩn thận",
     r"giao (hàng )?(chậm|lâu)|ship (chậm|lâu)|giao (sai|thiếu)|bị móp|hộp móp"),
    ("price", "Giá",
     r"giá (rẻ|tốt|hợp lý|hợp lí|ổn|hời)|đáng tiền|rẻ|hạt dẻ|xứng đáng",
     r"\bđắt\b|không đáng tiền|ko đáng tiền|phí tiền"),
]
SPAM_RX = re.compile(r"\[QC\]|voucher|soạn \w+ gửi|\bsoan\b|nhận xu|mục nhận xét này chỉ để|ưu đãi|ib |inbox|"
                     r"book lịch|đặt lịch|zalo|nhà thuốc|https?://", re.I)


def is_spam(text: str) -> bool:
    return bool(SPAM_RX.search(text or ""))


def aspect_hits(text: str) -> dict[str, str]:
    """Trả {aspect: 'pos'|'neg'} cho 1 review (neg ưu tiên nếu cả hai)."""
    t = (text or "").lower()
    hits = {}
    for key, _, pos, neg in ASPECTS:
        if re.search(neg, t):
            # "không chỉ thừa" là tích cực: nếu mẫu tích cực khớp đúng đoạn đó thì không tính neg
            if key == "stitching" and re.search(pos, t) and not re.search(r"(nhiều|còn|bị) chỉ thừa", t):
                hits[key] = "pos"
            else:
                hits[key] = "neg"
        elif re.search(pos, t):
            hits[key] = "pos"
    return hits


def snippet_around(text: str, pattern: str, n: int = 120) -> str:
    """Cắt đoạn review quanh chỗ khớp mẫu để minh chứng dễ kiểm."""
    t = re.sub(r"\s+", " ", text or "").strip()
    m = re.search(pattern, t.lower())
    if not m or len(t) <= n:
        return snippet(t, n)
    a = max(0, m.start() - n // 2)
    return ("…" if a else "") + t[a:a + n].strip() + ("…" if a + n < len(t) else "")


def snippet(text: str, n: int = 110) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def summarize_product(p: dict, min_mentions: int = 2) -> dict:
    revs = [r for r in p["reviews"] if (r.get("text") or "").strip()]
    clean = [r for r in revs if not is_spam(r["text"])]
    stats: dict[str, dict] = {k: {"pos": [], "neg": []} for k, *_ in ASPECTS}
    for r in clean:
        for k, pol in aspect_hits(r["text"]).items():
            stats[k][pol].append(r)
    label = {k: lab for k, lab, *_ in ASPECTS}
    pat = {k: (pos, neg) for k, _, pos, neg in ASPECTS}
    pros, cons = [], []
    for k, s in stats.items():
        npos, nneg = len(s["pos"]), len(s["neg"])
        if npos >= min_mentions and npos > nneg:
            pros.append(dict(aspect=k, label=label[k], mentions=npos, opposite_mentions=nneg,
                             evidence=[{"comment_id": r["comment_id"], "text": snippet_around(r["text"], pat[k][0])}
                                       for r in s["pos"][:2]]))
        if nneg >= min_mentions or (nneg >= 1 and nneg >= 0.2 * (npos + nneg)):
            cons.append(dict(aspect=k, label=label[k], mentions=nneg, opposite_mentions=npos,
                             evidence=[{"comment_id": r["comment_id"], "text": snippet_around(r["text"], pat[k][1])}
                                       for r in s["neg"][:2]]))
    pros.sort(key=lambda x: -x["mentions"])
    cons.sort(key=lambda x: -x["mentions"])
    ratings = [r["rating"] for r in revs if r.get("rating")]
    return dict(product_id=p["product_id"], title=p["title"], vimrhp_subcategory=p["vimrhp_subcategory"],
                product_type=GROUP.get(p["vimrhp_subcategory"], "unknown"), n_reviews=len(revs),
                n_spam_filtered=len(revs) - len(clean), avg_rating=round(statistics.mean(ratings), 2) if ratings else None,
                rating_dist={str(k): ratings.count(k) for k in range(1, 6)}, pros=pros, cons=cons,
                text_vi=render_text(pros, cons, len(clean)), method="keyword_baseline_v1")


def render_text(pros: list[dict], cons: list[dict], n: int) -> str:
    """Câu tóm tắt tiếng Việt sinh từ thống kê (không có thông tin ngoài review)."""
    if not pros and not cons:
        return f"Chưa đủ nhận xét cụ thể về sản phẩm (dựa trên {n} đánh giá)."
    parts = []
    if pros:
        parts.append("Ưu điểm: " + "; ".join(f"{x['label'].lower()} ({x['mentions']} đánh giá khen)" for x in pros[:4]))
    if cons:
        parts.append("Lưu ý: " + "; ".join(f"{x['label'].lower()} ({x['mentions']} đánh giá phàn nàn/nhắc)" for x in cons[:3]))
    return ". ".join(parts) + f". (Tổng hợp từ {n} đánh giá.)"


def load_products(include_out_of_scope: bool = False) -> list[dict]:
    ps = [json.loads(l) for l in SRC.open(encoding="utf-8")]
    return [p for p in ps if include_out_of_scope or p["vimrhp_subcategory"] not in OUT_OF_SCOPE]


def run_baseline(out: Path = OUT) -> dict:
    prods = load_products()
    res = {p["product_id"]: summarize_product(p) for p in prods}
    meta = dict(source="ViMRHP (HF trucmtnguyen/ViMRHP, CC BY-NC-ND 4.0) – shared_data v1", n_products=len(res),
                excluded_subcategories=sorted(OUT_OF_SCOPE), method="keyword_baseline_v1",
                n_with_pros=sum(bool(v["pros"]) for v in res.values()),
                n_with_cons=sum(bool(v["cons"]) for v in res.values()),
                n_empty=sum(not v["pros"] and not v["cons"] for v in res.values()),
                spam_reviews_filtered=sum(v["n_spam_filtered"] for v in res.values()),
                reviews_total=sum(v["n_reviews"] for v in res.values()))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"_meta": meta, "products": res}, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


# ------------------------------------------------------------------ LLM
LLM_SYSTEM = (
    "Bạn tóm tắt đánh giá khách hàng cho cửa hàng thời trang. CHỈ dùng thông tin có trong các review được cung cấp, "
    "không suy đoán, không thêm giá/size/chất liệu nếu review không nói. Bỏ qua review quảng cáo/spam lạc đề. "
    "Mỗi ý phải ghi chỉ số review minh chứng. Trả JSON đúng schema."
)


def llm_prompt(batch: list[dict], max_reviews: int = 12) -> str:
    blocks = []
    for p in batch:
        revs = [r for r in p["reviews"] if (r.get("text") or "").strip()][:max_reviews]
        lines = [f"### {p['product_id']} | {p['title']}"]
        lines += [f"[{i}] ({r['rating']}★) {snippet(r['text'], 220)}" for i, r in enumerate(revs)]
        blocks.append("\n".join(lines))
    return ("\n\n".join(blocks) +
            '\n\nVới mỗi sản phẩm trả: {"<product_id>": {"pros": [{"point": "≤ 15 từ", "reviews": [chỉ số]}], '
            '"cons": [{"point": "...", "reviews": [...]}]}}. Tối đa 4 ưu, 3 nhược; không có nhược thì để [].')


def run_llm(n: int, model: str, per_call: int = 5, seed: int = 42) -> dict:
    from msa_td.gemini_client import GeminiClient
    rng = random.Random(seed)
    prods = load_products()
    by_g: dict[str, list[dict]] = {}
    for p in prods:
        by_g.setdefault(p["vimrhp_subcategory"], []).append(p)
    pick: list[dict] = []
    for g in sorted(by_g):
        pick += rng.sample(by_g[g], n // len(by_g))
    pick += rng.sample([p for p in prods if p not in pick], n - len(pick))
    client = GeminiClient(model=model, cache_path=str(ROOT / "results" / "gemini_cache.sqlite"),
                          budget_file=str(ROOT / "results" / "gemini_budget.json"), max_retries=1)
    res, calls = {}, []
    for i in range(0, len(pick), per_call):
        batch = pick[i:i + per_call]
        r = client.generate(llm_prompt(batch), system=LLM_SYSTEM, temperature=0.0, max_output_tokens=4000,
                            response_json=True)
        calls.append({k: r.get(k) for k in ("latency_ms", "tokens_in", "tokens_out", "tokens_thinking", "error", "model")})
        try:
            d = json.loads(r["answer"])
        except (json.JSONDecodeError, TypeError):
            d = {}
        for p in batch:
            s = d.get(p["product_id"], {})
            revs = [x for x in p["reviews"] if (x.get("text") or "").strip()][:12]
            for side in ("pros", "cons"):
                for pt in s.get(side, []):
                    idx = [j for j in pt.get("reviews", []) if isinstance(j, int) and 0 <= j < len(revs)]
                    pt["evidence"] = [{"idx": j, "comment_id": revs[j]["comment_id"], "text": snippet(revs[j]["text"], 160)}
                                      for j in idx]
                    pt["invalid_refs"] = [j for j in pt.get("reviews", []) if j not in idx]
                    pt["auto_overlap"] = overlap(pt.get("point", ""), " ".join(revs[j]["text"] for j in idx))
            res[p["product_id"]] = dict(title=p["title"], vimrhp_subcategory=p["vimrhp_subcategory"],
                                        pros=s.get("pros", []), cons=s.get("cons", []), method=f"llm:{model}",
                                        baseline=summarize_product(p)["text_vi"])
    out = dict(_meta=dict(model=model, n=len(res), calls=calls, seed=seed, per_call=per_call), products=res)
    OUT_LLM.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out["_meta"]


def overlap(point: str, evidence: str) -> float:
    """Tỉ lệ từ (≥ 2 ký tự) của ý tóm tắt xuất hiện trong review minh chứng."""
    toks = [t for t in re.findall(r"[0-9a-zà-ỹđ]+", point.lower()) if len(t) >= 2]
    ev = set(re.findall(r"[0-9a-zà-ỹđ]+", evidence.lower()))
    return round(sum(t in ev for t in toks) / len(toks), 3) if toks else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["baseline", "llm"])
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--model", default="gemini-3.5-flash-lite")
    a = ap.parse_args()
    print(json.dumps(run_baseline() if a.mode == "baseline" else run_llm(a.n, a.model), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
