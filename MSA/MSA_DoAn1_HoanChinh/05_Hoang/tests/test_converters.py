"""US_06/US_48 – converter → schema chuẩn trên mẫu tổng hợp (+ kiểm trên dữ liệu thật nếu đã chạy scripts)."""
import json
from pathlib import Path

import pandas as pd
import pytest
from msa.data import converters as C

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("title,exp", [
    ("Áo Khoác Lông 2 lớp nam nữ có mũ tai gấu", ("clothing", "outerwear")),
    ("GIÀY CAO GÓT NỮ BÍT MŨI QUAI NGỌC", ("footwear", "heel_flat*")),
    ("Dép lê quai ngang nam nữ", ("footwear", "sandal")),
    ("Mũ lưỡi trai thêu chữ unisex", ("headwear", "cap")),
    ("Túi tote vải canvas", ("accessory", "bag")),
    ("Quần short kaki nam", ("clothing", "bottom")),
    ("Chân váy xếp ly", ("clothing", "bottom")),
    ("Khuyên tai bạc 925", (None, "unknown")),
])
def test_classify_vi_title(title, exp):
    assert C.classify_vi_title(title) == exp


def test_vimrhp_converter(tmp_path):
    recs = [{"ProductId": 1, "ProductName": "Dép sandal nữ", "SubCategory": "GiayDepNu", "CommentId": 11, "Rating": 4,
             "Comment": "đẹp", "ProductUrl": "https://shopee.vn/x?y=1", "ShopId": 9},
            {"ProductId": 1, "ProductName": "Dép sandal nữ", "SubCategory": "GiayDepNu", "CommentId": 10, "Rating": 2,
             "Comment": "tạm"},
            {"ProductId": 2, "ProductName": "Đồng hồ nam", "SubCategory": "DongHo", "CommentId": 12, "Rating": 5, "Comment": "x"}]
    p = tmp_path / "Fashion-train.json"
    p.write_text(json.dumps(recs, ensure_ascii=False), encoding="utf-8")
    df = C.convert_vimrhp([str(p)])
    assert len(df) == 1 and df.iloc[0].product_type == "footwear" and df.iloc[0].rating == 3.0
    assert [r["review_id"] for r in df.iloc[0].reviews] == ["10", "11"] and df.iloc[0].source_url == "https://shopee.vn/x"
    assert C.validate_schema(df) == []


def test_amazon_mapping():
    assert C.classify_amazon_categories(["Clothing, Shoes & Jewelry", "Men", "Accessories", "Hats & Caps", "Baseball Caps"]) == ("headwear", "cap")
    assert C.classify_amazon_categories(["Clothing, Shoes & Jewelry", "Women", "Shoes", "Boots"]) == ("footwear", "boot")
    assert C.classify_amazon_categories(["Clothing, Shoes & Jewelry", "Women", "Jewelry", "Rings"])[0] is None
    assert C.classify_amazon_categories(["Clothing, Shoes & Jewelry", "Women", "Clothing", "Swimsuits"])[0] is None
    rec = C.amazon_meta_to_schema({"parent_asin": "B01", "title": "Cap", "price": 9.5, "store": "X",
                                   "categories": ["Clothing, Shoes & Jewelry", "Men", "Accessories", "Hats & Caps", "Skullies & Beanies"],
                                   "images": [{"large": "u"}]})
    assert rec["product_id"] == "amz_B01" and rec["sub_category"] == "beanie" and rec["currency"] == "USD"


def test_abo_and_clothing_cc0_mappers():
    abo = {"item_id": "B0X", "item_name": [{"language_tag": "en_US", "value": "Boot"}], "product_type": [{"value": "BOOT"}],
           "color": [{"language_tag": "en_US", "value": "Black"}]}
    r = C.abo_listing_to_schema(abo)
    assert r["product_type"] == "footwear" and r["colors"] == ["Black"]
    assert C.abo_listing_to_schema({"item_id": "1", "product_type": [{"value": "LAMP"}]}) is None
    assert C.clothing_cc0_row_to_schema({"image": "abc", "label": "Hat", "kids": "False"})["product_type"] == "headwear"
    assert C.clothing_cc0_row_to_schema({"image": "abc", "label": "Skip", "kids": "False"}) is None
    assert C.clothing_cc0_row_to_schema({"image": "abc", "label": "Dress", "kids": "True"}) is None


def _fpi_meta(n=200):
    types = list(C.FPI_MAP)
    return pd.DataFrame({"id": range(n), "gender": "Men", "masterCategory": "M", "subCategory": "S",
                         "articleType": [types[i % len(types)] for i in range(n)], "baseColour": "Black", "season": "Summer",
                         "year": 2012.0, "usage": "Casual", "productDisplayName": [f"Brand P{i}" for i in range(n)]})


def test_fpi_select_deterministic_and_hash():
    m = _fpi_meta()
    q = {"footwear": 30, "clothing": 40, "accessory": 20, "headwear": 100}
    a, b = C.select_fpi(m, quota=q, seed=42), C.select_fpi(m, quota=q, seed=42)
    assert a.id.tolist() == b.id.tolist()
    df = pd.DataFrame([C.fpi_row_to_schema(r) for r in a.itertuples()])
    assert C.validate_schema(df) == []
    assert C.catalog_hash(df) == C.catalog_hash(df.sample(frac=1, random_state=1))  # không phụ thuộc thứ tự dòng


def test_write_read_roundtrip(tmp_path):
    m = _fpi_meta(40)
    df = pd.DataFrame([C.fpi_row_to_schema(r) for r in C.select_fpi(m).itertuples()])
    C.write_catalog(df, tmp_path / "c.parquet")
    assert C.catalog_hash(C.read_catalog(tmp_path / "c.parquet")) == C.catalog_hash(df)


def test_validate_schema_detects_errors():
    df = pd.DataFrame([{**{f: None for f in C.SCHEMA_FIELDS}, "product_id": "x", "title": "t", "product_type": "car",
                        "sub_category": "x", "size_system": "none"}] * 2)
    errs = " ".join(C.validate_schema(df))
    assert "trùng product_id" in errs and "product_type sai" in errs


@pytest.mark.realdata
def test_real_data_v1_counts():
    p = ROOT / "data" / "counts_data_v1.json"
    if not p.exists():
        pytest.skip("chưa chạy scripts 01/01b/02")
    rep = json.loads(p.read_text(encoding="utf-8"))
    assert rep["schema_valid_100pct"] and rep["counts"]["by_type"]["footwear"] + rep["counts"]["by_type"]["accessory"] >= 1700
