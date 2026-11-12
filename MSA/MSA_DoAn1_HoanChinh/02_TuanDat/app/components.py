# repo: app/components.py
"""US_31/US_43 – Logic hiển thị thuần Python (không phụ thuộc Gradio) để test được.

- Card sản phẩm: ảnh, tên, giá, độ tương đồng, link nguồn (thiếu trường → hiển thị rõ "Chưa có ...", không bịa).
- Nhãn nguồn: "Trả lời bởi Gemini" (source=gemini/cache-của-gemini) / "Từ dữ liệu cửa hàng" (source=internal).
- Bảng so sánh 2-3 sản phẩm.
- Kiểm response theo hợp đồng mục 5.2.
"""
from __future__ import annotations

import base64
import html
import mimetypes
from pathlib import Path
from typing import Any

ROUTES = {"visual", "qa", "search", "compare", "gemini_chitchat", "gemini_ood", "clarify"}
SOURCES = {"internal", "gemini", "cache", "fallback"}  # "fallback": QUYET_DINH_CAN_CHOT mục D (Tác nhân 2)
LABEL_GEMINI = "Trả lời bởi Gemini"
LABEL_STORE = "Từ dữ liệu cửa hàng"
LABEL_SYSTEM = "Thông báo hệ thống"  # thông điệp dự phòng khi Gemini lỗi – KHÔNG phải dữ liệu cửa hàng
CARD_FIELDS = ("image", "title", "price", "score", "link")


def validate_response(resp: dict) -> list[str]:
    """Trả danh sách lỗi so với schema response chung (rỗng = hợp lệ)."""
    errs = []
    for k in ("route", "confidence", "source", "answer", "items", "citations", "latency_ms", "request_id"):
        if k not in resp:
            errs.append(f"thiếu trường {k}")
    if resp.get("route") not in ROUTES:
        errs.append(f"route không hợp lệ: {resp.get('route')}")
    if resp.get("source") not in SOURCES:
        errs.append(f"source không hợp lệ: {resp.get('source')}")
    if not isinstance(resp.get("items", []), list):
        errs.append("items phải là list")
    return errs


def source_label(resp: dict) -> str:
    """Nhãn nguồn hiển thị. 'cache' được coi là Gemini nếu route là gemini_* hoặc resp có cached_from='gemini'."""
    src = resp.get("source")
    if src == "fallback":
        return LABEL_SYSTEM
    if src == "gemini" or (src == "cache" and (str(resp.get("route", "")).startswith("gemini")
                                               or resp.get("cached_from") == "gemini")):
        return LABEL_GEMINI + (" (bộ nhớ đệm)" if src == "cache" else "")
    return LABEL_STORE


def format_price(price: Any, currency: str | None = "VND") -> str:
    """1250000 → '1.250.000 ₫'. None/NaN/≤0 → 'Chưa có giá' (catalog FPI không có giá)."""
    try:
        v = float(price)
    except (TypeError, ValueError):
        return "Chưa có giá"
    if v != v or v <= 0:
        return "Chưa có giá"
    if (currency or "VND").upper() in ("VND", "₫", "VNĐ"):
        return f"{int(round(v)):,}".replace(",", ".") + " ₫"
    return f"{v:,.2f} {currency}"


def format_score(score: Any) -> str:
    """Cosine/điểm 0..1 → 'Tương đồng 87%'; thiếu → 'Chưa có điểm'."""
    try:
        v = float(score)
    except (TypeError, ValueError):
        return "Chưa có điểm"
    if v != v:
        return "Chưa có điểm"
    return f"Tương đồng {max(0.0, min(1.0, v)) * 100:.0f}%"


def image_src(path_or_url: str | None, image_root: str | Path | None = None) -> str | None:
    """URL giữ nguyên; đường dẫn cục bộ → data URI base64 (Gradio HTML không đọc file trực tiếp)."""
    if not path_or_url:
        return None
    if str(path_or_url).startswith(("http://", "https://", "data:")):
        return str(path_or_url)
    p = Path(image_root or ".") / str(path_or_url)
    if not p.exists():
        return None
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def card_fields(item: dict, image_root: str | Path | None = None) -> dict[str, str]:
    """Giá trị hiển thị của 5 trường card (dùng cho cả HTML và test 'hiển thị đúng 100% trường')."""
    src = image_src(item.get("image"), image_root)
    return {
        "image": src or "",
        "title": str(item.get("title") or "(Không có tên)"),
        "price": format_price(item.get("price"), item.get("currency") or "VND"),
        "score": format_score(item.get("score")),
        "link": str(item.get("source_url") or item.get("url") or ""),
    }


def render_card_html(item: dict, image_root: str | Path | None = None) -> str:
    f = card_fields(item, image_root)
    img = (f'<img src="{html.escape(f["image"])}" alt="{html.escape(f["title"])}" class="msa-img"/>'
           if f["image"] else '<div class="msa-noimg">Không có ảnh</div>')
    link = (f'<a href="{html.escape(f["link"])}" target="_blank" rel="noopener">Xem nguồn</a>'
            if f["link"] else "<span>Không có link</span>")
    pid = html.escape(str(item.get("product_id", "")))
    return (f'<div class="msa-card" data-product-id="{pid}">{img}'
            f'<div class="msa-title">{html.escape(f["title"])}</div>'
            f'<div class="msa-price">{html.escape(f["price"])}</div>'
            f'<div class="msa-score">{html.escape(f["score"])}</div>'
            f'<div class="msa-link">{link}</div></div>')


CSS = """
.msa-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.msa-card{border:1px solid #ddd;border-radius:8px;padding:8px;font-size:13px;background:#fff;color:#222}
.msa-img{width:100%;height:150px;object-fit:contain;background:#fafafa}
.msa-noimg{height:150px;display:flex;align-items:center;justify-content:center;background:#f2f2f2;color:#888}
.msa-title{font-weight:600;margin:4px 0}.msa-price{color:#c0392b}.msa-score{color:#555}
.msa-badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;margin-bottom:4px}
.msa-badge.gemini{background:#e8f0fe;color:#1a56c4}.msa-badge.store{background:#e6f4ea;color:#137333}
"""


def render_cards(items: list[dict], image_root: str | Path | None = None) -> str:
    if not items:
        return ""
    return '<div class="msa-grid">' + "".join(render_card_html(i, image_root) for i in items) + "</div>"


def render_compare_table(items: list[dict], fields: list[tuple[str, str]] | None = None) -> str:
    """Bảng so sánh 2-3 SP (markdown). Ô thiếu → 'Chưa có thông tin'."""
    fields = fields or [("title", "Tên"), ("price", "Giá"), ("product_type", "Nhóm"), ("sub_category", "Loại"),
                        ("colors", "Màu"), ("brand", "Thương hiệu"), ("pros", "Ưu điểm (review)"),
                        ("cons", "Lưu ý (review)")]
    items = items[:3]
    if len(items) < 2:
        return "_Cần ít nhất 2 sản phẩm để so sánh._"

    def cell(it: dict, k: str) -> str:
        v = it.get(k)
        if k == "price":
            return format_price(v, it.get("currency") or "VND")
        if v is None or v == "" or (isinstance(v, (list, tuple)) and not len(v)):
            return "Chưa có thông tin"
        if isinstance(v, (list, tuple)):
            v = ", ".join(map(str, v))
        return str(v).replace("|", "/").replace("\n", " ")
    head = "| Thuộc tính | " + " | ".join(f"SP{i + 1}" for i in range(len(items))) + " |"
    sep = "|---" * (len(items) + 1) + "|"
    rows = [f"| {lab} | " + " | ".join(cell(it, k) for it in items) + " |" for k, lab in fields]
    return "\n".join([head, sep, *rows])


def render_answer(resp: dict) -> str:
    """Văn bản chat kèm nhãn nguồn (markdown)."""
    label = source_label(resp)
    badge = "[AI ngoài] " if label.startswith(LABEL_GEMINI) else "[Cửa hàng] "
    cites = resp.get("citations") or []
    cite_txt = ""
    if cites:
        cite_txt = "\n\n_Nguồn: " + ", ".join(f"{c.get('product_id')}·{c.get('field')}" for c in cites[:5]) + "_"
    return f"**{badge}{label}**\n\n{resp.get('answer', '')}{cite_txt}"


def render_response(resp: dict, image_root: str | Path | None = None) -> tuple[str, str, str]:
    """→ (markdown chat, HTML card, markdown bảng so sánh)."""
    items = resp.get("items") or []
    cmp_md = render_compare_table(items) if resp.get("route") == "compare" else ""
    return render_answer(resp), render_cards(items, image_root), cmp_md
