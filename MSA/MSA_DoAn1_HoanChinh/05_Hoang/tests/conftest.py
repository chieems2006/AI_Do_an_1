"""Fixture dùng chung: catalog tổng hợp (synthetic) + ảnh sinh bằng PIL; mặc định mock Gemini."""
import io
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MSA_LLM_MOCK", "1")
os.environ.setdefault("MSA_QA_BACKEND", "stub")  # test API của Hoàng kiểm ReviewQAStub; RAG thật có test tích hợp ở tests/
os.environ.pop("GEMINI_API_KEY", None)

TYPES = {"footwear": ["sneaker", "sandal", "leather_shoe"], "clothing": ["top", "bottom", "dress"],
         "headwear": ["cap", "beanie"], "accessory": ["bag", "belt", "eyewear"]}
COLORS = ["Black", "White", "Red", "Navy Blue", "Grey", "Brown", "Pink", "Green"]
RGB = {"Black": (10, 10, 10), "White": (245, 245, 245), "Red": (200, 20, 30), "Navy Blue": (20, 30, 110),
       "Grey": (128, 128, 128), "Brown": (120, 70, 30), "Pink": (240, 150, 180), "Green": (30, 150, 50)}
SHAPE = {"footwear": "ellipse", "clothing": "rect", "headwear": "pie", "accessory": "poly"}


def make_image(color: str, ptype: str, size=(96, 96), seed=0) -> Image.Image:
    rnd = random.Random(seed)
    im = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(im)
    box = (10 + rnd.randint(0, 6), 15, size[0] - 10, size[1] - 12)
    fill = RGB[color]
    getattr(d, {"ellipse": "ellipse", "rect": "rectangle", "pie": "pieslice", "poly": "polygon"}[SHAPE[ptype]])(
        *([[(10, 80), (48, 10), (86, 80)]] if SHAPE[ptype] == "poly" else [box]),
        **({"start": 180, "end": 360} if SHAPE[ptype] == "pie" else {}), fill=fill)
    return im


def to_bytes(im: Image.Image, fmt="JPEG", **kw) -> bytes:
    b = io.BytesIO()
    im.save(b, format=fmt, **kw)
    return b.getvalue()


@pytest.fixture(scope="session")
def synth():
    """Catalog giả 64 SP (4 nhóm) có giá/size/màu/rating để kiểm bộ lọc & so sánh; ảnh sinh theo màu + hình."""
    rows, images, types = [], {}, {}
    i = 0
    for pt, subs in TYPES.items():
        for j in range(16):
            sub, col, col2 = subs[j % len(subs)], COLORS[j % len(COLORS)], COLORS[(j + 3) % len(COLORS)]
            pid = f"syn_{i:03d}"
            size_sys = {"footwear": "EU", "clothing": "alpha", "headwear": "free", "accessory": "none"}[pt]
            sizes = {"EU": ["39", "40", "41", "42"][: 1 + j % 4], "alpha": ["S", "M", "L", "XL"][j % 4:],
                     "free": ["free"], "none": []}[size_sys]
            rows.append(dict(product_id=pid, title=f"{sub} {col} mẫu {j}", category=f"{pt}/{sub}", brand=f"Brand{j % 3}",
                             price=None if j == 15 else float(100_000 + 50_000 * j), currency=None if j == 15 else "VND",
                             colors=[col] + ([col2] if j % 5 == 0 else []), sizes=sizes,
                             description=None if j % 4 == 0 else f"Mô tả {sub} {j}",
                             specs={"material": None if j % 3 == 0 else ["da", "vải", "cotton"][j % 3],
                                    "usage": ["Casual", "Sports", "Formal"][j % 3], "season": "Summer", "year": 2020 + j % 4},
                             image_paths=[f"images/{pid}/0.jpg"], rating=None if j % 6 == 0 else round(3 + (j % 5) * 0.4, 1),
                             rating_count=j * 3, reviews=[{"review_id": f"r{i}_{k}", "rating": 5,
                                                           "text": t} for k, t in enumerate(
                                 ["Giao hàng nhanh, đóng gói cẩn thận", f"Chất liệu {['da', 'vải', 'cotton'][j % 3]} mềm, mặc thoải mái",
                                  "Form chuẩn, nên chọn đúng size"])],
                             source="synthetic", source_url=None, license="synthetic", product_type=pt, sub_category=sub,
                             gender=["Men", "Women", "Unisex"][j % 3], size_system=size_sys, view_type="studio",
                             variant_id=None, language="vi"))
            images[pid] = make_image(col, pt, seed=i)
            types[pid] = pt
            i += 1
    return {"df": pd.DataFrame(rows), "images": images, "types": types}


@pytest.fixture()
def client(synth, tmp_path):
    from fastapi.testclient import TestClient
    from msa.api.main import State, create_app
    from msa.api.searchers import DummyVisualSearcher
    from msa.llm_gateway import LLMGateway
    gw = LLMGateway(mock=True, cache_path=str(tmp_path / "c.sqlite"), log_path=str(tmp_path / "llm.jsonl"))
    st = State(catalog=synth["df"], visual=DummyVisualSearcher(synth["images"], synth["types"]), gateway=gw,
               log_dir=str(tmp_path / "logs"))
    return TestClient(create_app(st)), tmp_path
