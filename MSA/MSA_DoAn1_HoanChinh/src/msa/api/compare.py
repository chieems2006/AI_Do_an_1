# repo: src/msa/api/compare.py
"""So sánh 2-3 sản phẩm theo bảng thuộc tính (US_38 – Owner: Hoàng, Support: Trung).

Nguyên tắc: MỌI ô lấy trực tiếp từ DB (catalog); ô thiếu = "chưa có thông tin"; không để LLM tự nghĩ thuộc tính.
Chỉ so sánh trong cùng product_type. "Điểm nổi bật" (ưu/nhược) suy ra bằng luật từ chính các ô trong bảng.
"""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

MISSING = "chưa có thông tin"
ATTRIBUTES = [  # (khoá, nhãn tiếng Việt, hàm lấy giá trị từ bản ghi)
    ("title", "Tên sản phẩm", lambda r: r.get("title")),
    ("brand", "Thương hiệu", lambda r: r.get("brand")),
    ("price", "Giá", lambda r: r.get("price")),
    ("currency", "Tiền tệ", lambda r: r.get("currency")),
    ("sub_category", "Loại", lambda r: r.get("sub_category")),
    ("colors", "Màu", lambda r: r.get("colors")),
    ("sizes", "Size", lambda r: r.get("sizes")),
    ("size_system", "Hệ size", lambda r: None if r.get("size_system") in (None, "none") else r.get("size_system")),
    ("gender", "Giới tính", lambda r: r.get("gender")),
    ("material", "Chất liệu", lambda r: (r.get("specs") or {}).get("material")),
    ("usage", "Mục đích dùng", lambda r: (r.get("specs") or {}).get("usage")),
    ("season", "Mùa", lambda r: (r.get("specs") or {}).get("season")),
    ("year", "Năm", lambda r: (r.get("specs") or {}).get("year")),
    ("rating", "Điểm đánh giá", lambda r: r.get("rating")),
    ("rating_count", "Số lượt đánh giá", lambda r: r.get("rating_count")),
    ("description", "Mô tả", lambda r: r.get("description")),
    ("source", "Nguồn dữ liệu", lambda r: r.get("source")),
]


class CompareError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    if isinstance(v, (list, tuple, str)) and len(v) == 0:
        return True
    return False


def cell(v: Any) -> Any:
    """Giá trị hiển thị: thiếu → MISSING, list → nối bằng ', ', còn lại giữ nguyên kiểu."""
    if _is_missing(v):
        return MISSING
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v)
    return v


def compare_products(catalog: pd.DataFrame, product_ids: list[str]) -> dict:
    """Trả {"product_type", "columns": [product_id...], "rows": [{key, label, values{pid: cell}}], "highlights": [...]}"""
    ids = list(dict.fromkeys(product_ids or []))
    if not 2 <= len(ids) <= 3:
        raise CompareError("bad_count", "Cần chọn từ 2 đến 3 sản phẩm khác nhau để so sánh.")
    idx = catalog.set_index("product_id", drop=False)
    missing = [i for i in ids if i not in idx.index]
    if missing:
        raise CompareError("not_found", f"Không tìm thấy sản phẩm: {', '.join(missing)}.")
    recs = {i: idx.loc[i].to_dict() for i in ids}
    types = {r["product_type"] for r in recs.values()}
    if len(types) > 1:
        raise CompareError("mixed_types", "Chỉ so sánh được các sản phẩm cùng nhóm (ví dụ giày với giày). "
                                          f"Các sản phẩm bạn chọn thuộc nhiều nhóm: {', '.join(sorted(types))}.")
    rows = [{"key": k, "label": lab, "values": {i: cell(get(recs[i])) for i in ids}} for k, lab, get in ATTRIBUTES]
    return {"product_type": types.pop(), "columns": ids, "rows": rows, "highlights": highlights(rows, ids)}


def highlights(rows: list[dict], ids: list[str]) -> list[dict]:
    """Ưu/nhược suy ra bằng luật CHỈ từ ô có trong bảng (giá thấp nhất, rating cao nhất, nhiều lượt đánh giá nhất...)."""
    by = {r["key"]: r["values"] for r in rows}
    out = []

    def num(v):
        return v if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)) else None
    for key, better, text in (("price", min, "Giá thấp nhất"), ("rating", max, "Điểm đánh giá cao nhất"),
                              ("rating_count", max, "Nhiều lượt đánh giá nhất")):
        vals = {i: num(by[key][i]) for i in ids}
        vals = {i: v for i, v in vals.items() if v is not None}
        if len(vals) >= 2 and len(set(vals.values())) > 1:
            best = better(vals.values())
            for i, v in vals.items():
                if v == best:
                    out.append({"product_id": i, "attribute": key, "text": f"{text} ({v})"})
    for key, lab in (("price", "giá"), ("material", "chất liệu"), ("sizes", "size")):
        for i in ids:
            if by[key][i] == MISSING:
                out.append({"product_id": i, "attribute": key, "text": f"Chưa có thông tin {lab}"})
    return out
