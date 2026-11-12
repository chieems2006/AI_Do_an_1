"""US_08 – test 03_clean.py trên catalog + ảnh giả sinh trong test."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clean", ROOT / "src" / "scripts" / "03_clean.py")
clean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clean)


def _img(path: Path, seed: int, size=(60, 80), blank=False):
    rng = np.random.default_rng(seed)
    arr = np.full((size[1], size[0], 3), 200, np.uint8) if blank else rng.integers(0, 255, (size[1], size[0], 3), np.uint8)
    Image.fromarray(arr).save(path)


def _row(pid, title, art, img, brand=None, color="Black"):
    return dict(product_id=pid, title=title, category=f"X/Y/{art}", brand=brand or title.split()[0], price=None,
                currency=None, colors=[color], sizes=[], description="<b>Mô  tả</b>&nbsp;tốt", specs={"articleType": art},
                image_paths=[img], rating=None, rating_count=None, reviews=[], source="fashion_product_images_small",
                source_url="u", license="l", product_type="x", sub_category="x", gender="Men", size_system="none",
                view_type="studio", variant_id=None, language="en")


def _make(tmp: Path):
    (tmp / "img").mkdir()
    rows = []
    for i in range(6):
        _img(tmp / "img" / f"{i}.jpg", i)
        rows.append(_row(f"fpi_{i}", f"Nike Men Black Shoe {i}", "Casual Shoes", f"img/{i}.jpg"))
    # 6 = bản sao y hệt ảnh 0 (MD5 trùng)
    (tmp / "img" / "6.jpg").write_bytes((tmp / "img" / "0.jpg").read_bytes())
    rows.append(_row("fpi_6", "Nike Men Black Shoe 0", "Casual Shoes", "img/6.jpg"))
    _img(tmp / "img" / "7.jpg", 7, blank=True)                     # ảnh trơn
    rows.append(_row("fpi_7", "Puma Men Blue Tshirt", "Tshirts", "img/7.jpg"))
    _img(tmp / "img" / "8.jpg", 8, size=(20, 20))                    # quá nhỏ
    rows.append(_row("fpi_8", "Puma Men Red Tshirt", "Tshirts", "img/8.jpg"))
    (tmp / "img" / "9.jpg").write_bytes(b"not an image")             # hỏng
    rows.append(_row("fpi_9", "Puma Men Grey Tshirt", "Tshirts", "img/9.jpg"))
    rows.append(_row("fpi_10", "Puma Men Missing Tshirt", "Tshirts", "img/nope.jpg"))  # thiếu file
    _img(tmp / "img" / "11.jpg", 11)
    rows.append(_row("fpi_11", "Proline Men Grey Beanie", "Caps", "img/11.jpg"))
    _img(tmp / "img" / "12.jpg", 12)
    rows.append(_row("fpi_12", "Some Headband", "Headband", "img/12.jpg"))
    pd.DataFrame(rows).to_parquet(tmp / "cat.parquet")
    return tmp


def test_pipeline(tmp_path):
    _make(tmp_path)
    r = clean.run(tmp_path / "cat.parquet", tmp_path, tmp_path / "out", ROOT / "data" / "category_map.csv",
                  cap=None, quota={"footwear": 1}, sample_per_type=5)
    st = r["images"]["status"]
    assert st["blank"] == 1 and st["too_small"] == 1 and st["unreadable"] == 1 and st["missing"] == 1
    assert r["exact_md5_duplicates"] == 1
    out = pd.read_parquet(tmp_path / "out" / "catalog_clean.parquet")
    assert "fpi_6" not in set(out.product_id)                     # bản trùng bị xoá
    assert "fpi_12" not in set(out.product_id)                    # headband → unknown → loại
    assert out.set_index("product_id").at["fpi_11", "sub_category"] == "beanie"   # tinh chỉnh theo tiêu đề
    assert (out.product_type != "unknown").all()                  # 100% có category
    assert out.description.iloc[0] == "Mô tả tốt"                 # bỏ HTML + gộp khoảng trắng
    assert json.loads((tmp_path / "out" / "clean_report.json").read_text(encoding="utf-8"))["after"]["n"] == len(out)
    assert (tmp_path / "out" / "label_check_sample.csv").exists()


def test_helpers():
    assert clean.infer_brand("Red Tape Men Black Shoes") == "Red Tape"
    assert clean.infer_brand("United Colors of Benetton Women Bag") == "United Colors of Benetton"
    assert clean.normalize_color("Navy Blue") == "blue" and clean.normalize_color("đen") == "black"
    assert clean.normalize_color("Xyz") == "other"
    assert clean.normalize_sizes(["s", "M", "2XL"], "clothing") == ("alpha", ["S", "M", "XXL"])
    assert clean.normalize_sizes(["40", "39"], "footwear") == ("EU", ["39", "40"])
    assert clean.normalize_sizes([], "footwear") == ("none", [])
    assert clean.refine_sub_category("Flying Machine Men Black Hat", "headwear", "cap") == "wide_brim"
    assert clean.refine_sub_category("Nike Cap", "headwear", "cap") == "cap"


def test_hamming_pairs():
    pairs = clean.hamming_pairs(["ffffffffffffffff", "fffffffffffffffe", "0000000000000000"], ["a", "b", "c"], 2)
    assert pairs == [("a", "b", 1)]


def test_cap_respects_quota():
    df = pd.DataFrame({"product_type": ["c"] * 10 + ["c"] * 2, "sub_category": ["top"] * 10 + ["dress"] * 2,
                       "product_id": range(12)})
    out, info = clean.cap_leaves(df, 3, {"c": 8})
    assert len(out) == 8 and info["dropped"] == 4
    out2, _ = clean.cap_leaves(df, 3, {"c": 0})
    assert len(out2) == 5
