# repo: scripts/build_eval_qa.py
"""US_16 – Xây eval/eval_qa.jsonl trên dữ liệu THẬT ViMRHP (review Shopee tiếng Việt).

Quy trình:
1. Chọn SP (seed 42, cân đối 5 nhóm con, bỏ DongHo, bỏ SP không phải thời trang như keo dán giày).
2. Gửi theo lô (3 SP/lời gọi) cho Gemini kèm review thật (đánh số R1..Rn) → mỗi SP 3 câu answerable
   + 1 câu answerable=false. Ánh xạ R-index → comment_id thật, kiểm bằng chứng.
3. Gộp các câu do tác nhân viết tay (eval/eval_qa_handwritten.jsonl).
4. `--check`: kiểm mọi ràng buộc nghiệm thu US_16.

Lưu ý: CHƯA có người thật duyệt (reviewed_by=[]) – nhóm cần duyệt ≥ 30% bởi 2 người.

Dùng:
    MSA_ENV_FILE=<file .env> PYTHONPATH=src python src/scripts/build_eval_qa.py --generate
    PYTHONPATH=src python src/scripts/build_eval_qa.py --check
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung

from msa.rag.data import load_vimrhp  # noqa: E402

OUT = ROOT / "eval" / "eval_qa.jsonl"
RAW = ROOT / "eval" / "raw" / "eval_qa_gemini_raw.jsonl"
HANDWRITTEN = ROOT / "eval" / "eval_qa_handwritten.jsonl"
CORRECTIONS = ROOT / "eval" / "eval_qa_corrections.jsonl"  # sửa nhãn sau kiểm tra (khớp product_id + question)
TYPES = {"size_giay", "size_ao_quan", "chat_lieu", "do_ben", "gia", "form", "giao_hang", "so_sanh", "ngoai_pham_vi"}
ORIGINS = {"llm_gemini", "viet_tay_tac_nhan"}
FIELDS = {"id", "product_id", "question", "answer", "answerable", "evidence_review_ids", "type", "origin",
          "reviewed_by", "split"}
TYPES_BY_GROUP = {
    "footwear": "size_giay, chat_lieu, do_ben, form, giao_hang, so_sanh",
    "clothing": "size_ao_quan, chat_lieu, do_ben, form, giao_hang, so_sanh",
    "accessory": "chat_lieu, do_ben, form, giao_hang, so_sanh",
}
NON_FASHION = re.compile(r"keo dán|xi đánh|lót giày|dây giày", re.I)
SYSTEM = (
    "Bạn là người xây bộ đánh giá hỏi đáp sản phẩm cho trợ lý mua sắm thời trang tiếng Việt. "
    "Chỉ dùng thông tin trong các đánh giá (review) được cung cấp. Không suy đoán, không bịa."
)
PROMPT_TMPL = """Dưới đây là {n} sản phẩm thật, mỗi sản phẩm kèm các review khách hàng đánh số R1, R2, ...

{blocks}

Với MỖI sản phẩm, tạo đúng 4 câu hỏi mà người mua có thể hỏi trợ lý:
- 3 câu answerable=true: đáp án được các review hỗ trợ RÕ RÀNG. Mỗi câu một loại khác nhau, chọn trong: {{types_hint}}.
  Đáp án 1-2 câu, tiếng Việt, mở đầu kiểu "Theo đánh giá của khách, ...", chỉ nêu điều review nói (nếu review trái chiều thì nói rõ).
  "evidence" = danh sách mã review (vd ["R2","R7"]) chứa thông tin của đáp án (1-3 mã, phải đúng).
  Loại "so_sanh" = so với hình/mô tả/giá tiền (vd "có giống hình không", "có đáng tiền không").
- 1 câu answerable=false: hỏi thông tin KHÔNG có trong bất kỳ review nào của SP đó (vd giá bán chính xác bao nhiêu tiền,
  còn hàng size/màu cụ thể không, chính sách đổi trả/bảo hành, xuất xứ/nhà máy, kích thước cm/trọng lượng chính xác).
  type ∈ {{gia, ngoai_pham_vi, size_giay, size_ao_quan}}; answer = "Hiện cửa hàng chưa có thông tin về <điều được hỏi>."; evidence = [].
Câu hỏi tự nhiên như người mua thật: đa số có dấu, khoảng 1/4 viết không dấu hoặc teencode (ko, k, sz, bn, đc). Có thể nhắc tên ngắn của SP.

Trả về JSON đúng dạng:
[{{"product_id": "...", "questions": [{{"question": "...", "answer": "...", "answerable": true, "type": "...", "evidence": ["R1"]}}]}}]"""


def select_products(products: list[dict], per_sub: int = 9, seed: int = 42, min_reviews: int = 10) -> list[dict]:
    """Chọn SP cân đối theo nhóm con ViMRHP (seed cố định)."""
    rng = random.Random(seed)
    by = collections.defaultdict(list)
    for p in products:
        if len(p["reviews"]) >= min_reviews and not NON_FASHION.search(p["title"]):
            by[p["vimrhp_subcategory"]].append(p)
    out = []
    for sub in sorted(by):
        out += rng.sample(sorted(by[sub], key=lambda x: x["product_id"]), min(per_sub, len(by[sub])))
    return out


def product_block(p: dict, max_reviews: int = 25, max_chars: int = 300) -> tuple[str, dict[str, str]]:
    """Khối text của 1 SP + ánh xạ R-index → review_id."""
    lines = [f"### product_id: {p['product_id']}", f"Tên: {p['title']}", f"Nhóm: {p['product_type']}"]
    rmap = {}
    for i, rv in enumerate(p["reviews"][:max_reviews], 1):
        txt = re.sub(r"\s+", " ", rv["text"]).strip()[:max_chars]
        lines.append(f"R{i} ({rv['rating']}★): {txt}")
        rmap[f"R{i}"] = rv["review_id"]
    return "\n".join(lines), rmap


def split_of(pid: str) -> str:
    """Chia val/test theo product_id (không lẫn SP giữa 2 tập)."""
    return "val" if int(hashlib.md5(pid.encode()).hexdigest(), 16) % 2 == 0 else "test"


def done_products() -> set[str]:
    """SP đã sinh thành công (có trong raw, parse được JSON)."""
    done = set()
    if RAW.exists():
        for line in RAW.open(encoding="utf-8"):
            rec = json.loads(line)
            try:
                for item in json.loads(rec["result"]["answer"]):
                    done.add(item.get("product_id"))
            except Exception:
                pass
    return done


def generate(batch_size: int = 7, per_sub: int = 12, max_calls: int = 8,
             model: str = "gemini-3.5-flash-lite", thinking_budget: int | None = None) -> list[dict]:
    """Sinh thêm câu cho các SP chưa làm (nối vào raw); dừng khi hết quota ngày. Trả về toàn bộ câu từ raw.

    Lịch sử lượt này: 6 lô đầu (3 SP/lô) sinh bằng gemini-3.5-flash (thinkingBudget=0) trước khi hết quota
    free tier 20 request/ngày/model; phần còn lại dùng gemini-3.5-flash-lite (cùng họ Flash, quota riêng).
    """
    from msa_chien.gemini_client import GeminiClient, count_real_calls

    products = load_vimrhp()
    done = done_products()
    todo = [p for p in select_products(products, per_sub=per_sub) if p["product_id"] not in done]
    llm = GeminiClient(model=model, thinking_budget=thinking_budget, tag="eval_qa_gen", max_retries=2)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    c0, n_batches = count_real_calls(), 0
    for b in range(0, len(todo), batch_size):
        if count_real_calls() - c0 >= max_calls:
            break
        batch = todo[b:b + batch_size]
        blocks = [product_block(p)[0] for p in batch]
        groups = sorted({p["product_type"] for p in batch})
        hint = "; ".join(f"SP nhóm {g}: {TYPES_BY_GROUP[g]}" for g in groups)
        prompt = PROMPT_TMPL.format(n=len(batch), blocks="\n\n".join(blocks)).replace("{types_hint}", hint)
        res = llm.generate(prompt, system=SYSTEM, temperature=0.4, json_mode=True, max_output_tokens=12000)
        with RAW.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"batch": [p["product_id"] for p in batch], "model": model, "result": res},
                               ensure_ascii=False) + "\n")
        n_batches += 1
        if res.get("error"):
            print("Lỗi lô", b, str(res["error"])[:200])
            if "per day" in str(res["error"]) or "PerDay" in str(res["error"]):
                break
    print(f"{n_batches} lô, {count_real_calls() - c0} request HTTP thật")
    return rows_from_raw(products)


def finalize(llm_rows: list[dict]) -> list[dict]:
    """Lọc câu lỗi, gộp câu viết tay, đánh id."""
    good = [r for r in llm_rows if not r.pop("_bad_evidence", False) and r["type"] in TYPES and r["question"]
            and (not r["answerable"] or r["evidence_review_ids"])]
    hand = [json.loads(l) for l in HANDWRITTEN.open(encoding="utf-8")] if HANDWRITTEN.exists() else []
    for h in hand:
        h.setdefault("reviewed_by", [])
        h["origin"] = "viet_tay_tac_nhan"
        h["split"] = split_of(h["product_id"])
    rows = good + hand
    if CORRECTIONS.exists():
        fixes = {(c["product_id"], c["question"]): c for c in (json.loads(l) for l in CORRECTIONS.open(encoding="utf-8"))}
        for r in rows:
            c = fixes.get((r["product_id"], r["question"]))
            if c:
                r.update(c["set"])
    for i, r in enumerate(rows, 1):
        r["id"] = f"qa{i:03d}"
    key_order = ["id", "product_id", "question", "answer", "answerable", "evidence_review_ids", "type", "origin",
                 "reviewed_by", "split"]
    return [{k: r[k] for k in key_order} for r in rows]


def check(rows: list[dict], products: list[dict] | None = None) -> list[str]:
    """Kiểm ràng buộc US_16; trả danh sách lỗi (rỗng = đạt)."""
    errs = []
    if len(rows) < 150:
        errs.append(f"chỉ có {len(rows)} < 150 câu")
    if len({r["id"] for r in rows}) != len(rows):
        errs.append("trùng id")
    n_un = sum(not r["answerable"] for r in rows)
    if rows and n_un / len(rows) <= 0.15:
        errs.append(f"tỉ lệ answerable=false {n_un / len(rows):.2%} ≤ 15%")
    revs = {p["product_id"]: {rv["review_id"] for rv in p["reviews"]} for p in products} if products else None
    for r in rows:
        if set(r) != FIELDS:
            errs.append(f"{r.get('id')}: sai trường")
            continue
        if r["type"] not in TYPES:
            errs.append(f"{r['id']}: type lạ {r['type']}")
        if r["origin"] not in ORIGINS:
            errs.append(f"{r['id']}: origin lạ")
        if r["answerable"] and not r["evidence_review_ids"]:
            errs.append(f"{r['id']}: answerable nhưng không có evidence")
        if not r["answerable"] and r["evidence_review_ids"]:
            errs.append(f"{r['id']}: answerable=false nhưng có evidence")
        if revs is not None:
            if r["product_id"] not in revs:
                errs.append(f"{r['id']}: product_id không có trong ViMRHP (đã bỏ DongHo)")
            elif not set(r["evidence_review_ids"]) <= revs[r["product_id"]]:
                errs.append(f"{r['id']}: evidence không thuộc review của SP")
    if {r["origin"] for r in rows} != ORIGINS and rows:
        errs.append("thiếu một trong hai origin (llm_gemini / viet_tay_tac_nhan)")
    return errs


def summary(rows: list[dict]) -> dict:
    return {"n": len(rows), "answerable_false": sum(not r["answerable"] for r in rows),
            "ti_le_khong_dap_an": round(sum(not r["answerable"] for r in rows) / max(len(rows), 1), 3),
            "by_type": dict(collections.Counter(r["type"] for r in rows)),
            "by_origin": dict(collections.Counter(r["origin"] for r in rows)),
            "by_split": dict(collections.Counter(r["split"] for r in rows)),
            "n_products": len({r["product_id"] for r in rows}),
            "reviewed_by_2_nguoi": sum(len(r["reviewed_by"]) >= 2 for r in rows)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generate", action="store_true", help="gọi Gemini sinh câu (tốn lời gọi)")
    ap.add_argument("--rebuild", action="store_true", help="dựng lại từ raw đã lưu + câu viết tay (không gọi API)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    products = load_vimrhp()
    if a.generate:
        rows = finalize(generate())
    elif a.rebuild:
        rows = finalize(rows_from_raw(products))
    else:
        rows = [json.loads(l) for l in OUT.open(encoding="utf-8")]
    if a.generate or a.rebuild:
        with OUT.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    errs = check(rows, products)
    print(json.dumps({**summary(rows), "errors": errs[:20], "n_errors": len(errs)}, ensure_ascii=False, indent=1))
    print("CHÚ Ý: chưa có người thật duyệt – nhóm cần duyệt ≥ 30% bởi 2 người (điền reviewed_by).")
    return 1 if errs else 0


def rows_from_raw(products: list[dict]) -> list[dict]:
    """Dựng lại câu từ file raw (không gọi API) – để tái lập."""
    pmap = {p["product_id"]: p for p in products}
    rows = []
    for line in RAW.open(encoding="utf-8"):
        rec = json.loads(line)
        try:
            data = json.loads(rec["result"]["answer"])
        except Exception:
            continue
        for item in data:
            pid = item.get("product_id")
            if pid not in pmap:
                continue
            _, rm = product_block(pmap[pid])
            for q in item.get("questions", []):
                ev = [rm[e] for e in q.get("evidence", []) if e in rm]
                rows.append({"product_id": pid, "question": q.get("question", "").strip(),
                             "answer": q.get("answer", "").strip(), "answerable": bool(q.get("answerable")),
                             "evidence_review_ids": ev if q.get("answerable") else [], "type": q.get("type"),
                             "origin": "llm_gemini", "reviewed_by": [], "split": split_of(pid),
                             "_bad_evidence": len(ev) != len(q.get("evidence", []))})
    return rows


if __name__ == "__main__":
    sys.exit(main())
