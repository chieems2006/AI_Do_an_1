# repo: src/msa/data/schema_adapters.py
"""US_05 – Đưa bản ghi từng nguồn về schema chuẩn (product.schema.json) và validate."""
from __future__ import annotations

import json
import math
import os
from typing import Any, Iterable

from msa.data.taxonomy import map_vimrhp

from msa.paths import SCHEMA_PATH as _SCHEMA_PATH

SCHEMA_PATH = str(_SCHEMA_PATH)  # 01_Trung/src/schema/product.schema.json


def load_schema() -> dict:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


def to_plain(v: Any) -> Any:
    """numpy/pandas -> kiểu JSON thuần (list, None thay NaN)."""
    if v is None:
        return None
    if hasattr(v, "tolist") and not isinstance(v, (str, bytes)):
        v = v.tolist()
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, dict):
        return {k: to_plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [to_plain(x) for x in v]
    return v


def fpi_row_to_record(row: dict) -> dict:
    """Bản ghi catalog_fpi (pandas row dict) -> dict JSON thuần đúng schema (không đổi giá trị)."""
    rec = {k: to_plain(v) for k, v in row.items() if not k.startswith("taxonomy_")}
    if isinstance(rec.get("specs"), dict) and rec["specs"].get("year") is not None:
        rec["specs"]["year"] = int(rec["specs"]["year"])
    return rec


def vimrhp_to_record(p: dict) -> dict:
    """Sản phẩm ViMRHP (jsonl của shared_data) -> schema chuẩn. Không có giá/mô tả/size => null/rỗng (không bịa)."""
    r = map_vimrhp(p.get("vimrhp_subcategory"), p.get("title"))
    reviews = [dict(review_id=str(x["comment_id"]), rating=x.get("rating"), text=x.get("text") or "",
                    date=x.get("date"), helpfulness=x.get("helpfulness"), detail_rating=x.get("detail_rating"))
               for x in p.get("reviews", [])]
    ratings = [x["rating"] for x in reviews if x["rating"] is not None]
    return dict(
        product_id=p["product_id"], title=p["title"], category=p.get("vimrhp_subcategory"), brand=None, price=None, currency=None,
        colors=[], sizes=[], description=None,
        specs={"image_urls": p.get("image_urls", []), "taxonomy_rule": r.rule_id},
        image_paths=[], rating=round(sum(ratings) / len(ratings), 3) if ratings else None,
        rating_count=len(ratings), reviews=reviews, source="vimrhp_shopee", source_url=p.get("source_url") or "https://shopee.vn",
        license="CC BY-NC-ND 4.0 (ViMRHP, NLDB 2025) – chỉ dùng nội bộ học thuật, không phát hành lại bản đã chỉnh",
        product_type=r.product_type, sub_category=r.sub_category, gender=None,
        size_system="none", view_type="unknown", variant_id=None, language="vi",
    )


def validate_records(records: Iterable[dict], schema: dict | None = None) -> tuple[int, int, list[tuple[str, str]]]:
    """Trả (số hợp lệ, số lỗi, danh sách (product_id, thông điệp lỗi đầu tiên))."""
    from jsonschema import Draft202012Validator

    v = Draft202012Validator(schema or load_schema())
    ok = bad = 0
    errs: list[tuple[str, str]] = []
    for rec in records:
        e = next(iter(v.iter_errors(rec)), None)
        if e is None:
            ok += 1
        else:
            bad += 1
            errs.append((str(rec.get("product_id")), f"{'/'.join(map(str, e.path))}: {e.message[:120]}"))
    return ok, bad, errs
