"""Kiểm US_49: cây taxonomy, luật map FPI/ViMRHP trên ví dụ thật, category_map.csv phủ 100% nhãn."""
import os

import pandas as pd
import pytest

from msa.data.taxonomy import TAXONOMY, is_valid_leaf, map_fpi, map_vimrhp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_tree_has_4_types_and_unique_leaves():
    assert set(TAXONOMY) == {"footwear", "clothing", "headwear", "accessory"}
    leaves = [x for v in TAXONOMY.values() for x in v]
    assert len(leaves) == len(set(leaves))
    assert "heel_flat" in TAXONOMY["footwear"] and "beanie" in TAXONOMY["headwear"]


@pytest.mark.parametrize("args,expected", [
    (("Footwear", "Shoes", "Heels", "Catwalk Women Brown Heels"), ("footwear", "heel_flat", "keep")),
    (("Footwear", "Shoes", "Flats", "Carlton London Women Tan Brown Boots"), ("footwear", "boot", "keep")),
    (("Footwear", "Shoes", "Sports Shoes", "ADIDAS Men Red Pre L Boot Sports Shoes"), ("footwear", "sneaker", "keep")),
    (("Footwear", "Shoes", "Sports Shoes", "Nike Men Air Max Conquer ACG Brown Sports Boot"), ("footwear", "boot", "keep")),
    (("Accessories", "Headwear", "Hat", "Timberland Unisex Casual Black Skull Caps"), ("headwear", "beanie", "keep")),
    (("Accessories", "Headwear", "Caps", "Quiksilver Men Grey Firsty Fishtails Cap"), ("headwear", "cap", "keep")),
    (("Accessories", "Headwear", "Headband", "Nike Unisex Black Headband"), ("out_of_scope", "unknown", "exclude")),
    (("Accessories", "Watches", "Watches", "Titan Men Watch"), ("out_of_scope", "unknown", "exclude")),
    (("Accessories", "Belts", "Tshirts", "Mr.Men Men's Funny Coral Pink T-shirt"), ("clothing", "top", "keep")),
    (("Free Items", "Free Gifts", "Handbags", "x"), ("accessory", "bag", "keep")),
    (("Apparel", "Apparel Set", "Kurta Sets", "x"), ("clothing", "unknown", "unknown")),
])
def test_map_fpi(args, expected):
    assert map_fpi(*args).as_tuple()[:3] == expected


@pytest.mark.parametrize("sub,title,expected", [
    ("ThoiTrangNu", "Áo Khoác Lông 2 lớp nam nữ có mũ tai gấu khóa kép", ("clothing", "outerwear")),
    ("PhuKienNu", "Khăn lau kính Nano, khăn giấy chống bám hơi nước", ("out_of_scope", "unknown")),
    ("GiayDepNu", "GIÀY SANDAL CAO GÓT NỮ ĐẾ NHỌN 7-9 PHÂN", ("footwear", "heel_flat")),
    ("PhuKienNu", "Mũ lưỡi trai LOULI SAIGON thêu chữ HAMPTONS", ("headwear", "cap")),
    ("PhuKienNu", "Mũ chống nắng nửa đầu Hàn Quốc, nón vành rộng", ("headwear", "wide_brim")),
    ("DongHo", "Đồng hồ nam Casio A168", ("out_of_scope", "unknown")),
    ("GiayDepNam", "[ VÂN NHÁM ] Dép YZ Slide Vân Nhám bản giới hạn 2023", ("footwear", "sandal")),
    ("ThoiTrangNam", "Áo Hoodie Unisex Nam Nữ, Họa Tiết Năm Sinh", ("clothing", "top")),
    ("ThoiTrangNu", "Set Bộ Áo Thun Nữ Form Rộng Tay Lỡ + Quần Short", ("clothing", "unknown")),
    ("PhuKienNu", "[FREESHIP] SET TẤT TRƠN ULZZANG", ("out_of_scope", "unknown")),
    ("PhuKienNu", "Thắt lưng nam da cao cấp", ("accessory", "belt")),
])
def test_map_vimrhp(sub, title, expected):
    r = map_vimrhp(sub, title)
    assert (r.product_type, r.sub_category) == expected


def test_category_map_csv_covers_all_and_valid():
    p = os.path.join(ROOT, "data", "category_map.csv")
    if not os.path.exists(p):
        pytest.skip("chưa chạy scripts/build_category_map.py")
    df = pd.read_csv(p)
    assert set(df.action) <= {"keep", "unknown", "exclude"}
    assert not df.rule_id.astype(str).str.contains("chua_co_trong_bang").any()
    for r in df[df.action != "exclude"].itertuples():
        assert is_valid_leaf(r.product_type, r.sub_category), r
    assert (df[df.action == "exclude"].product_type == "out_of_scope").all()
    fpi = df[df.source == "fashion_product_images"]
    assert fpi.n_rows_source.astype(int).sum() == 44072  # mọi dòng gốc FPI đều có nhãn được map
