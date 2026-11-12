# repo: src/msa/rag/data.py
"""Nạp dữ liệu ViMRHP (shared_data v1) cho RAG/eval: bỏ đồng hồ, khử review trùng trong cùng SP."""
from __future__ import annotations
import os

import json
from pathlib import Path

VIMRHP_PATH = Path((os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/vimrhp_fashion_products.jsonl"))
# nhóm con ViMRHP → product_type theo schema 5.1 (DongHo ngoài phạm vi)
SUB2TYPE = {"ThoiTrangNu": "clothing", "ThoiTrangNam": "clothing", "GiayDepNu": "footwear",
            "GiayDepNam": "footwear", "PhuKienNu": "accessory"}
EXCLUDED_SUBS = {"DongHo"}
DATA_VERSION = "shared_data v1 (prep_shared_data.py seed 42)"


def load_vimrhp(path: Path | str = VIMRHP_PATH) -> list[dict]:
    """Trả danh sách SP: {product_id, title, vimrhp_subcategory, product_type, source_url, reviews[]}.

    - Loại nhóm DongHo.
    - Khử review trùng `comment_id` trong cùng một SP (dữ liệu gốc có 86 bản trùng).
    - `review_id` = str(comment_id) – dùng làm evidence_review_ids.
    """
    out = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            sub = r.get("vimrhp_subcategory")
            if sub in EXCLUDED_SUBS:
                continue
            seen, revs = set(), []
            for rv in r.get("reviews", []):
                rid = str(rv["comment_id"])
                if rid in seen:
                    continue
                seen.add(rid)
                revs.append({**rv, "review_id": rid})
            out.append({"product_id": r["product_id"], "title": r["title"], "vimrhp_subcategory": sub,
                        "product_type": SUB2TYPE.get(sub, "unknown"), "source_url": r.get("source_url"),
                        "reviews": revs})
    return out
