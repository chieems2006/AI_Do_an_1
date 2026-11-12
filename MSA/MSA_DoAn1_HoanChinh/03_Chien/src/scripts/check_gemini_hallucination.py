# repo: scripts/check_gemini_hallucination.py
"""US_51 / R13 / I18 – Hậu kiểm phản hồi Gemini: phát hiện giá, size, tồn kho, chính sách cửa hàng bị "bịa".

Phản hồi nhánh Gemini KHÔNG có ngữ cảnh DB, nên mọi con số giá/size cụ thể, khẳng định còn/hết hàng,
chính sách đổi trả/bảo hành/phí ship đều bị coi là vi phạm (trừ khi xuất hiện trong `context` được cấp).
Câu phủ định ("mình chưa có thông tin về giá", "không biết còn hàng không") không bị tính.

Dùng:
    python src/scripts/check_gemini_hallucination.py "Đôi này giá 350k, còn size 42 nhé"
    python src/scripts/check_gemini_hallucination.py --file results/gemini_fallback_check.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

NEG = re.compile(r"(không|chưa|ko|k\b|chẳng|khó|cần kiểm tra|kiểm tra|tra giúp|không thể|không có thông tin|"
                 r"chưa có thông tin|không rõ|không biết|hỏi|xem giúp|nếu)", re.I)
RULES: dict[str, list[str]] = {
    "gia": [
        r"\d[\d.,]*\s*(k|nghìn|ngàn|ngan|đ|đồng|dong|vnđ|vnd|triệu|tr)\b",
        r"\$\s*\d", r"\d[\d.,]*\s*(usd|\$)",
        r"giá\s*(chỉ|từ|khoảng|là|:)?\s*\d",
        r"(giảm|sale|khuyến mãi|off)\s*\d+\s*%",
    ],
    "size": [
        r"\b(size|sz|cỡ|số)\s*(\d{2}(\.\d)?|xxs|xs|s|m|l|xl|xxl|xxxl|\d?xl)\b",
        r"\b\d{2}(\.\d)?\s*(eu|us|uk)\b",
        r"\b(eu|us|uk)\s*\d{1,2}\b",
    ],
    "ton_kho": [
        r"còn\s*hàng", r"hết\s*hàng", r"sẵn\s*hàng", r"có\s*sẵn", r"tồn\s*kho",
        r"còn\s*(size|sz|màu|cỡ)", r"còn\s*\d+\s*(sản phẩm|chiếc|đôi|cái|bộ)", r"chỉ\s*còn",
    ],
    "chinh_sach": [
        r"đổi\s*trả\s*(trong|miễn phí|\d)", r"bảo\s*hành\s*\d", r"(miễn phí|free)\s*(ship|vận chuyển|giao hàng)",
        r"freeship", r"giao\s*(hàng)?\s*trong\s*\d+\s*(giờ|ngày|h)\b", r"phí\s*(ship|vận chuyển)\s*\d",
    ],
}
COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in RULES.items()}


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "")


def check_text(text: str, context: str = "", neg_window: int = 30) -> dict:
    """Trả {violation: bool, hits: [{loai, khop, vi_tri}]}. Bỏ qua khớp nằm trong ngữ cảnh DB hoặc sau từ phủ định."""
    text, ctx = _nfc(text), _nfc(context).lower()
    hits = []
    for kind, pats in COMPILED.items():
        for p in pats:
            for m in p.finditer(text):
                frag = m.group(0)
                if ctx and frag.lower() in ctx:
                    continue
                before = text[max(0, m.start() - neg_window):m.start()]
                if kind in ("ton_kho", "chinh_sach", "size") and NEG.search(before):
                    continue
                hits.append({"loai": kind, "khop": frag, "vi_tri": m.start()})
    return {"violation": bool(hits), "hits": hits}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--file", help="JSON có danh sách 'rows' với trường 'response'")
    a = ap.parse_args()
    if a.file:
        data = json.load(open(a.file, encoding="utf-8"))
        rows = data["rows"] if isinstance(data, dict) else data
        bad = [r for r in rows if check_text(r.get("response", "")).get("violation")]
        print(json.dumps({"n": len(rows), "vi_pham": len(bad), "ids": [r.get("id") for r in bad]}, ensure_ascii=False))
        return 1 if bad else 0
    print(json.dumps(check_text(a.text or sys.stdin.read()), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
