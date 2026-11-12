# repo: src/msa/api/recommend.py
"""US_39 (stretch) – Gợi ý "nên chọn cái nào" CHỈ dựa trên bảng so sánh đã có (Owner: Hoàng, Support: Chiến).

1) Chấm điểm bằng luật trên các ô của bảng (ngân sách, màu, giới tính, mục đích dùng).
2) (Tuỳ chọn) nhờ LLM diễn giải – prompt chỉ chứa bảng; `check_grounded` kiểm mọi con số/thuộc tính trong câu trả lời
   phải có trong bảng hoặc trong nhu cầu người dùng; vi phạm → bỏ câu LLM, dùng giải thích theo luật.
"""
from __future__ import annotations

import json
import re

from .compare import MISSING
from .text_search import color_family, parse_filters_vi

USAGE_KW = {"đi bộ": "Sports", "thể thao": "Sports", "chạy": "Sports", "tập": "Sports", "gym": "Sports",
            "đi làm": "Formal", "công sở": "Formal", "đám cưới": "Formal", "dự tiệc": "Party", "đi chơi": "Casual",
            "hằng ngày": "Casual", "hàng ngày": "Casual", "du lịch": "Travel"}

PROMPT = """Bạn là trợ lý mua sắm. Dưới đây là BẢNG SO SÁNH (JSON) lấy từ cơ sở dữ liệu cửa hàng và NHU CẦU của khách.
Chỉ được dùng thông tin có trong bảng. Ô "chưa có thông tin" nghĩa là không biết – không được đoán.
Không nêu thêm thuộc tính, con số, giá, size, chất liệu nào ngoài bảng. Trả lời tiếng Việt, tối đa 4 câu,
nêu sản phẩm nên chọn (theo product_id) và lý do dựa trên ô của bảng.

NHU CẦU: {needs}
BẢNG: {table}
GỢI Ý THEO LUẬT (tham khảo): {rule_pick}"""


def parse_needs(text: str) -> dict:
    f = parse_filters_vi(text or "")
    t = (text or "").lower()
    usage = next((u for kw, u in USAGE_KW.items() if kw in t), None)
    return {"budget_max": f.price_max, "colors": f.colors, "gender": f.gender, "usage": usage, "text": text}


def rule_recommend(table: dict, needs: dict) -> dict:
    """Chấm điểm từng sản phẩm; mỗi lý do trích nguyên giá trị ô của bảng."""
    by = {r["key"]: r["values"] for r in table["rows"]}
    scores, reasons = {}, {}
    for pid in table["columns"]:
        s, why = 0.0, []
        price = by["price"][pid]
        if needs.get("budget_max") is not None:
            if isinstance(price, (int, float)):
                if price <= needs["budget_max"]:
                    s += 2
                    why.append(f"giá {price} nằm trong ngân sách")
                else:
                    s -= 2
                    why.append(f"giá {price} vượt ngân sách")
            else:
                why.append("chưa có thông tin giá")
        if needs.get("colors"):
            cols = by["colors"][pid]
            fams = {color_family(c.strip()) for c in str(cols).split(",")} if cols != MISSING else set()
            if fams & set(needs["colors"]):
                s += 1
                why.append(f"có màu {cols}")
        if needs.get("gender") and by["gender"][pid] in (needs["gender"], "Unisex"):
            s += 1
            why.append(f"giới tính {by['gender'][pid]}")
        if needs.get("usage") and by["usage"][pid] == needs["usage"]:
            s += 1.5
            why.append(f"mục đích dùng {by['usage'][pid]}")
        r = by["rating"][pid]
        if isinstance(r, (int, float)):
            s += 0.2 * r
            why.append(f"điểm đánh giá {r}")
        scores[pid], reasons[pid] = s, why
    best = max(table["columns"], key=lambda p: (scores[p], -table["columns"].index(p)))
    tie = sum(1 for p in table["columns"] if scores[p] == scores[best]) > 1
    text = (f"Nên cân nhắc {best} ({by['title'][best]}): " + ("; ".join(reasons[best]) or "các sản phẩm tương đương theo dữ liệu hiện có")
            + "." + (" Lưu ý: các lựa chọn đang ngang điểm theo dữ liệu hiện có." if tie else ""))
    return {"pick": best, "scores": scores, "reasons": reasons, "tie": tie, "answer": text}


def _table_strings(table: dict) -> str:
    return json.dumps(table, ensure_ascii=False).lower()


def check_grounded(answer: str, table: dict, needs_text: str = "") -> tuple[bool, list[str]]:
    """Mọi con số (≥ 2 chữ số hoặc có dấu thập phân) và mọi product_id dạng xxx_123 trong câu trả lời phải có trong bảng
    hoặc nhu cầu. Trả (ok, danh sách vi phạm)."""
    src = _table_strings(table) + " " + (needs_text or "").lower()
    bad = []
    for num in re.findall(r"\d+(?:[.,]\d+)?", answer):
        if (len(num) >= 2 or "." in num or "," in num) and num.lower() not in src and num.replace(",", ".") not in src:
            bad.append(num)
    for pid in re.findall(r"\b[a-z]+_\d+\b", answer.lower()):
        if pid not in table["columns"]:
            bad.append(pid)
    rows = {r["key"]: r["values"] for r in table["rows"]}
    low = answer.lower()
    for key, kw in (("material", "chất liệu"), ("sizes", "size"), ("price", "giá")):
        all_missing = all(v == MISSING for v in rows.get(key, {}).values())
        m = re.search(rf"{kw}\s*(?:là|:|bằng)?\s*([^\s,.;]+)", low)
        if all_missing and m and not m.group(1).startswith("chưa") and m.group(1) not in src:
            bad.append(f"khẳng định {kw} '{m.group(1)}' khi bảng không có")
    return (not bad), bad


def recommend(table: dict, needs_text: str, gateway=None) -> dict:
    needs = parse_needs(needs_text)
    rule = rule_recommend(table, needs)
    out = {"pick": rule["pick"], "answer": rule["answer"], "source": "internal", "grounded": True, "violations": [],
           "rule": rule}
    if gateway is None:
        return out
    res = gateway.generate(PROMPT.format(needs=needs_text, table=json.dumps(table, ensure_ascii=False),
                                         rule_pick=rule["pick"]), temperature=0)
    if res.get("source") == "fallback":
        return out
    ok, bad = check_grounded(res["answer"], table, needs_text)
    if ok:
        out.update(answer=res["answer"], source=res["source"])
    else:
        out.update(grounded=False, violations=bad, llm_answer_rejected=res["answer"])
    return out
