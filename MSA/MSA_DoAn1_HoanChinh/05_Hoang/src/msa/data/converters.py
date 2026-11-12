# repo: src/msa/data/converters.py
"""Bộ chuyển đổi dataset công khai → schema sản phẩm chuẩn (mục 5.1) – US_06/US_48 (Owner: Hoàng).

Nguồn hỗ trợ:
- Fashion Product Images (small, HF `ashraq/fashion-product-images-small`) – parquet có ảnh nhúng. ĐÃ CHẠY THẬT.
- ViMRHP (HF `trucmtnguyen/ViMRHP`, CC BY-NC-ND 4.0) – JSON review Shopee tiếng Việt. ĐÃ CHẠY THẬT.
- Amazon Reviews 2023 meta (HF `McAuley-Lab/Amazon-Reviews-2023`, JSONL rất lớn → đọc luồng N dòng). ĐÃ CHẠY THẬT (luồng).
- Amazon Berkeley Objects listings – [cần xác minh] định dạng; chỉ test trên mẫu tự tạo.
- Clothing Dataset (Grigorev, CC0) – [cần xác minh] định dạng CSV; chỉ test trên mẫu tự tạo.
Mapping product_type/sub_category ở đây khớp bản tạm của shared_data; taxonomy chính thức do Trung (US_49) chốt.
"""
from __future__ import annotations

import glob
import hashlib
import io
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd

SEED = 42
SCHEMA_FIELDS = ["product_id", "title", "category", "brand", "price", "currency", "colors", "sizes", "description",
                 "specs", "image_paths", "rating", "rating_count", "reviews", "source", "source_url", "license",
                 "product_type", "sub_category", "gender", "size_system", "view_type", "variant_id", "language"]
PRODUCT_TYPES = {"footwear", "clothing", "headwear", "accessory"}
SUB_CATEGORIES = {
    "footwear": {"sneaker", "leather_shoe", "sandal", "boot", "heel_flat*", "unknown"},
    "clothing": {"top", "bottom", "dress", "outerwear", "unknown"},
    "headwear": {"cap", "beanie", "bucket", "wide_brim", "wide_brim*", "unknown"},
    "accessory": {"bag", "belt", "eyewear", "unknown"},
}
SIZE_SYSTEMS = {"EU", "US", "UK", "VN", "alpha", "free", "numeric_waist", "none"}
QUOTA_MIN = {"footwear": 1200, "clothing": 2000, "accessory": 500, "headwear": 300}

# ---------------- Fashion Product Images ----------------
FPI_MAP = {  # articleType -> (product_type, sub_category tạm) – giống shared_data/scripts/prep_shared_data.py
    "Casual Shoes": ("footwear", "sneaker"), "Sports Shoes": ("footwear", "sneaker"),
    "Formal Shoes": ("footwear", "leather_shoe"), "Heels": ("footwear", "heel_flat*"), "Flats": ("footwear", "heel_flat*"),
    "Sandals": ("footwear", "sandal"), "Sports Sandals": ("footwear", "sandal"), "Flip Flops": ("footwear", "sandal"),
    "Tshirts": ("clothing", "top"), "Shirts": ("clothing", "top"), "Tops": ("clothing", "top"), "Sweatshirts": ("clothing", "top"),
    "Sweaters": ("clothing", "top"), "Kurtas": ("clothing", "top"), "Jackets": ("clothing", "outerwear"),
    "Blazers": ("clothing", "outerwear"), "Rain Jacket": ("clothing", "outerwear"), "Jeans": ("clothing", "bottom"),
    "Shorts": ("clothing", "bottom"), "Trousers": ("clothing", "bottom"), "Track Pants": ("clothing", "bottom"),
    "Skirts": ("clothing", "bottom"), "Capris": ("clothing", "bottom"), "Leggings": ("clothing", "bottom"),
    "Dresses": ("clothing", "dress"), "Jumpsuit": ("clothing", "dress"),
    "Caps": ("headwear", "cap"), "Hat": ("headwear", "wide_brim*"), "Headband": ("headwear", "unknown"),
    "Handbags": ("accessory", "bag"), "Backpacks": ("accessory", "bag"), "Clutches": ("accessory", "bag"),
    "Duffel Bag": ("accessory", "bag"), "Laptop Bag": ("accessory", "bag"), "Messenger Bag": ("accessory", "bag"),
    "Belts": ("accessory", "belt"), "Sunglasses": ("accessory", "eyewear"),
}
FPI_QUOTA = {"footwear": 1400, "clothing": 2200, "accessory": 700, "headwear": 10_000}  # headwear: lấy hết
FPI_SOURCE = {"name": "Fashion Product Images (small)", "url": "https://huggingface.co/datasets/ashraq/fashion-product-images-small",
              "origin": "Kaggle paramaggarwal/fashion-product-images-dataset (gốc Myntra)",
              "license": "[cần xác minh] – HF card không ghi rõ; bản Kaggle gốc cần đọc Data Card", "credibility": "Mức 2"}


def read_fpi_metadata(parquet_files: Iterable[str]) -> pd.DataFrame:
    """Đọc metadata FPI (bỏ cột ảnh cho nhẹ)."""
    import pyarrow.parquet as pq
    fs = sorted(parquet_files)
    return pd.concat([pq.read_table(f, columns=[c for c in pq.read_schema(f).names if c != "image"]).to_pandas() for f in fs],
                     ignore_index=True)


def select_fpi(meta: pd.DataFrame, product_types: set[str] | None = None, quota: dict | None = None,
               seed: int = SEED) -> pd.DataFrame:
    """Lọc articleType theo FPI_MAP, chọn theo quota phân tầng articleType (mỗi loại ≥ 40) – tất định theo seed.
    quota=None → lấy toàn bộ dòng map được."""
    df = meta[meta.articleType.isin(FPI_MAP)].copy()
    df["product_type"] = df.articleType.map(lambda a: FPI_MAP[a][0])
    df["sub_category"] = df.articleType.map(lambda a: FPI_MAP[a][1])
    if product_types:
        df = df[df.product_type.isin(product_types)]
    if quota is None:
        return df.sort_values("id").reset_index(drop=True)
    picked = []
    for pt, g in df.groupby("product_type"):
        q = quota[pt]
        if len(g) <= q:
            picked.append(g)
            continue
        per = (g.articleType.value_counts(normalize=True) * q).clip(lower=40).round().astype(int)
        parts = [g[g.articleType == a].sample(min(n, (g.articleType == a).sum()), random_state=seed) for a, n in per.items()]
        picked.append(pd.concat(parts).sample(frac=1, random_state=seed).head(q))
    return pd.concat(picked).reset_index(drop=True)


def fpi_row_to_schema(r) -> dict:
    """Một dòng FPI → bản ghi schema chuẩn. Ảnh lưu `data/images/<product_id>/0.jpg`."""
    pid = f"fpi_{int(r.id)}"
    return dict(product_id=pid, title=r.productDisplayName, category=f"{r.masterCategory}/{r.subCategory}/{r.articleType}",
                brand=(r.productDisplayName or "").split(" ")[0] or None, price=None, currency=None,
                colors=[r.baseColour] if isinstance(r.baseColour, str) and r.baseColour else [], sizes=[], description=None,
                specs={"season": r.season, "usage": r.usage, "year": None if pd.isna(r.year) else int(r.year),
                       "articleType": r.articleType},
                image_paths=[f"images/{pid}/0.jpg"], rating=None, rating_count=None, reviews=[],
                source="fashion_product_images_small", source_url=FPI_SOURCE["url"], license=FPI_SOURCE["license"],
                product_type=r.product_type, sub_category=r.sub_category, gender=r.gender, size_system="none",
                view_type="studio", variant_id=None, language="en")


def extract_fpi_images(parquet_files: Iterable[str], ids: set[int], out_dir: str | os.PathLike) -> dict[str, str]:
    """Ghi ảnh nhúng của các id cần lấy ra `out_dir/<product_id>/0.jpg`; trả {product_id: sha1 ảnh}."""
    import pyarrow.parquet as pq
    hashes = {}
    for f in sorted(parquet_files):
        for b in pq.ParquetFile(f).iter_batches(batch_size=2000, columns=["id", "image"]):
            for r in b.to_pylist():
                if r["id"] in ids:
                    pid = f"fpi_{r['id']}"
                    d = Path(out_dir) / pid
                    d.mkdir(parents=True, exist_ok=True)
                    data = r["image"]["bytes"]
                    (d / "0.jpg").write_bytes(data)
                    hashes[pid] = hashlib.sha1(data).hexdigest()
    return hashes


# ---------------- ViMRHP (Shopee VN, tiếng Việt) ----------------
VIMRHP_SOURCE = {"name": "ViMRHP – Fashion (Shopee VN reviews)", "url": "https://huggingface.co/datasets/trucmtnguyen/ViMRHP",
                 "paper": "ViMRHP: A Vietnamese Benchmark Dataset for Multimodal Review Helpfulness Prediction (NLDB 2025, arXiv 2505.07416)",
                 "license": "CC BY-NC-ND 4.0 (theo dataset card) – chỉ dùng nội bộ học thuật, không phát hành lại bản đã chỉnh",
                 "credibility": "Mức 1"}
# Từ khoá tiếng Việt → (product_type, sub_category); chọn từ khoá xuất hiện SỚM NHẤT trong tên SP
# (ví dụ "Áo khoác ... có mũ" → áo khoác, không phải mũ).
VI_KEYWORDS: list[tuple[str, str, str]] = [
    ("giày cao gót", "footwear", "heel_flat*"), ("giày búp bê", "footwear", "heel_flat*"), ("guốc", "footwear", "heel_flat*"),
    ("sandal", "footwear", "sandal"), ("dép", "footwear", "sandal"), ("boot", "footwear", "boot"), ("bốt", "footwear", "boot"),
    ("giày tây", "footwear", "leather_shoe"), ("giày da", "footwear", "leather_shoe"), ("giày lười", "footwear", "leather_shoe"),
    ("sneaker", "footwear", "sneaker"), ("giày thể thao", "footwear", "sneaker"), ("giày", "footwear", "unknown"),
    ("áo khoác", "clothing", "outerwear"), ("hoodie", "clothing", "outerwear"), ("cardigan", "clothing", "outerwear"),
    ("blazer", "clothing", "outerwear"), ("áo", "clothing", "top"), ("quần", "clothing", "bottom"), ("chân váy", "clothing", "bottom"),
    ("váy", "clothing", "dress"), ("đầm", "clothing", "dress"), ("bộ đồ", "clothing", "unknown"), ("set", "clothing", "unknown"),
    ("mũ bucket", "headwear", "bucket"), ("nón bucket", "headwear", "bucket"), ("mũ len", "headwear", "beanie"),
    ("beanie", "headwear", "beanie"), ("mũ lưỡi trai", "headwear", "cap"), ("nón lưỡi trai", "headwear", "cap"),
    ("mũ", "headwear", "unknown"), ("nón", "headwear", "unknown"),
    ("túi", "accessory", "bag"), ("balo", "accessory", "bag"), ("ba lô", "accessory", "bag"), ("ví", "accessory", "bag"),
    ("thắt lưng", "accessory", "belt"), ("dây nịt", "accessory", "belt"), ("kính", "accessory", "eyewear"),
]
VIMRHP_GROUP_TYPE = {"GiayDepNu": "footwear", "GiayDepNam": "footwear", "ThoiTrangNu": "clothing",
                     "ThoiTrangNam": "clothing", "PhuKienNu": "accessory", "DongHo": None}


def _norm(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").lower()


def classify_vi_title(title: str) -> tuple[str | None, str]:
    """Phân loại tên SP tiếng Việt theo từ khoá xuất hiện sớm nhất (khớp nguyên từ). Không khớp → (None, 'unknown')."""
    t = _norm(title)
    best = None
    for kw, pt, sub in VI_KEYWORDS:
        m = re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", t)
        if m and (best is None or m.start() < best[0] or (m.start() == best[0] and len(kw) > best[1])):
            best = (m.start(), len(kw), pt, sub)
    return (best[2], best[3]) if best else (None, "unknown")


def convert_vimrhp(json_files: Iterable[str]) -> pd.DataFrame:
    """Gộp review ViMRHP theo ProductId → bản ghi schema chuẩn (không có giá/mô tả/size; ảnh chỉ là URL Shopee).
    product_type: theo từ khoá tên SP; nếu không khớp thì theo nhóm ViMRHP. Loại DongHo (ngoài phạm vi)."""
    rows: dict = {}
    for fp in sorted(json_files):
        for r in json.load(open(fp, encoding="utf-8")):
            grp = r.get("SubCategory")
            if VIMRHP_GROUP_TYPE.get(grp) is None:
                continue
            pid = f"shopee_{r['ProductId']}"
            p = rows.get(pid)
            if p is None:
                pt, sub = classify_vi_title(r["ProductName"])
                group_pt = VIMRHP_GROUP_TYPE[grp]
                p = rows[pid] = dict(
                    product_id=pid, title=r["ProductName"], category=f"Shopee/{grp}", brand=None, price=None, currency=None,
                    colors=[], sizes=[], description=None,
                    specs={"vimrhp_subcategory": grp, "shop_id": r.get("ShopId"), "image_urls": r.get("ProductImage") or [],
                           "type_rule": "title_keyword" if pt else "group_default"},
                    image_paths=[], rating=None, rating_count=0, reviews=[], source="vimrhp_shopee",
                    source_url=(r.get("ProductUrl") or "").split("?")[0], license=VIMRHP_SOURCE["license"],
                    product_type=pt or group_pt, sub_category=sub if pt else "unknown",
                    gender="Women" if grp.endswith("Nu") else ("Men" if grp.endswith("Nam") else None),
                    size_system="none", view_type="unknown", variant_id=None, language="vi")
            p["reviews"].append({"review_id": str(r["CommentId"]), "rating": r.get("Rating"), "text": r.get("Comment"),
                                 "detail_rating": r.get("DetailRating"), "date": r.get("CommentDate")})
    for p in rows.values():
        rs = [x["rating"] for x in p["reviews"] if isinstance(x["rating"], (int, float))]
        p["rating_count"] = len(rs)
        p["rating"] = round(sum(rs) / len(rs), 3) if rs else None
        p["reviews"].sort(key=lambda x: x["review_id"])
    return pd.DataFrame(sorted(rows.values(), key=lambda d: d["product_id"]), columns=SCHEMA_FIELDS)


# ---------------- Amazon Reviews 2023 (meta) ----------------
AMAZON_SOURCE = {"name": "Amazon Reviews 2023 – meta Clothing_Shoes_and_Jewelry (McAuley Lab)",
                 "url": "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023",
                 "paper": "Hou et al., Bridging Language and Items for Retrieval and Recommendation (arXiv 2403.03952)",
                 "license": "[cần xác minh] – điều khoản dùng cho nghiên cứu theo trang dataset", "credibility": "Mức 1"}
AMAZON_HF_META_URL = ("https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/meta_categories/"
                      "meta_Clothing_Shoes_and_Jewelry.jsonl")
AMAZON_RULES: list[tuple[str, str, str]] = [  # (đoạn đường dẫn category, product_type, sub_category) – thứ tự ưu tiên
    ("Baseball Caps", "headwear", "cap"), ("Skullies & Beanies", "headwear", "beanie"), ("Bucket Hats", "headwear", "bucket"),
    ("Sun Hats", "headwear", "wide_brim"), ("Fedoras", "headwear", "wide_brim"), ("Cowboy Hats", "headwear", "wide_brim"),
    ("Hats & Caps", "headwear", "unknown"),
    ("Sunglasses", "accessory", "eyewear"), ("Eyewear", "accessory", "eyewear"), ("Belts", "accessory", "belt"),
    ("Handbags & Wallets", "accessory", "bag"), ("Backpacks", "accessory", "bag"), ("Luggage", "accessory", "bag"),
    ("Boots", "footwear", "boot"), ("Sandals", "footwear", "sandal"), ("Slippers", "footwear", "sandal"),
    ("Athletic", "footwear", "sneaker"), ("Fashion Sneakers", "footwear", "sneaker"), ("Oxfords", "footwear", "leather_shoe"),
    ("Loafers & Slip-Ons", "footwear", "leather_shoe"), ("Pumps", "footwear", "heel_flat*"), ("Flats", "footwear", "heel_flat*"),
    ("Shoes", "footwear", "unknown"),
    ("Coats, Jackets & Vests", "clothing", "outerwear"), ("Dresses", "clothing", "dress"), ("Jeans", "clothing", "bottom"),
    ("Pants", "clothing", "bottom"), ("Shorts", "clothing", "bottom"), ("Skirts", "clothing", "bottom"),
    ("Tops, Tees & Blouses", "clothing", "top"), ("Shirts", "clothing", "top"), ("Fashion Hoodies & Sweatshirts", "clothing", "top"),
    ("Sweaters", "clothing", "top"),
]


def classify_amazon_categories(cats: list[str]) -> tuple[str | None, str]:
    """Map đường dẫn categories Amazon → (product_type, sub_category). Loại Jewelry/Watches/Costumes/trẻ em → (None, ...)."""
    if not cats:
        return None, "unknown"
    # bỏ gốc "Clothing, Shoes & Jewelry" rồi mới loại nhánh trang sức/đồng hồ/hoá trang/em bé
    if any(x in seg for seg in cats[1:] for x in ("Jewelry", "Watches", "Costumes", "Baby", "Novelty")):
        return None, "unknown"
    segs = cats[1:]
    if any("Headband" in seg for seg in segs):  # băng đô không thuộc taxonomy mũ
        return None, "unknown"
    for frag, pt, sub in AMAZON_RULES:  # chỉ so trên các nút con (gốc chứa chữ "Shoes" gây map sai)
        if any(frag in seg for seg in segs):
            return pt, sub
    return None, "unknown"


def amazon_meta_to_schema(d: dict) -> dict | None:
    """Một dòng meta Amazon 2023 → schema chuẩn (ảnh là URL – môi trường hiện chặn m.media-amazon.com)."""
    pt, sub = classify_amazon_categories(d.get("categories") or [])
    if pt is None:
        return None
    asin = d.get("parent_asin") or d.get("asin")
    det = d.get("details") or {}
    return dict(product_id=f"amz_{asin}", title=d.get("title"), category=" > ".join(d.get("categories") or []),
                brand=d.get("store"), price=d.get("price") if isinstance(d.get("price"), (int, float)) else None,
                currency="USD" if isinstance(d.get("price"), (int, float)) else None, colors=[], sizes=[],
                description=" ".join(d.get("description") or []) or None,
                specs={"features": d.get("features") or [], "details": {k: str(v) for k, v in det.items()},
                       "image_urls": [i.get("large") or i.get("hi_res") for i in d.get("images") or []]},
                image_paths=[], rating=d.get("average_rating"), rating_count=d.get("rating_number"), reviews=[],
                source="amazon_reviews_2023", source_url=f"https://www.amazon.com/dp/{asin}", license=AMAZON_SOURCE["license"],
                product_type=pt, sub_category=sub, gender=None, size_system="US" if pt == "footwear" else "none",
                view_type="unknown", variant_id=None, language="en")


def stream_jsonl_http(url: str, max_lines: int, timeout: float = 60.0) -> Iterator[dict]:
    """Đọc luồng N dòng đầu của 1 file JSONL lớn qua HTTP (không tải cả file)."""
    import httpx
    with httpx.stream("GET", url, follow_redirects=True, timeout=timeout) as r:
        r.raise_for_status()
        for i, line in enumerate(r.iter_lines()):
            if i >= max_lines:
                break
            if line.strip():
                yield json.loads(line)


# ---------------- ABO & Clothing Dataset (chưa chạy thật) ----------------
ABO_SOURCE = {"name": "Amazon Berkeley Objects (ABO) listings", "url": "https://amazon-berkeley-objects.s3.amazonaws.com/index.html",
              "license": "CC BY 4.0 [cần xác minh]", "credibility": "Mức 1",
              "status": "KHÔNG truy cập được S3 từ môi trường hiện tại – converter chỉ test trên mẫu tự tạo"}
CLOTHING_CC0_SOURCE = {"name": "Clothing Dataset (Alexey Grigorev)", "url": "https://github.com/alexeygrigorev/clothing-dataset",
                       "license": "CC0 [cần xác minh]", "credibility": "Mức 2",
                       "status": "Chưa tải trong lượt này – converter chỉ test trên mẫu tự tạo"}
ABO_TYPE_MAP = {"SHOES": ("footwear", "unknown"), "BOOT": ("footwear", "boot"), "SANDAL": ("footwear", "sandal"),
                "HANDBAG": ("accessory", "bag"), "BACKPACK": ("accessory", "bag"), "SUNGLASSES": ("accessory", "eyewear"),
                "HAT": ("headwear", "unknown"), "SHIRT": ("clothing", "top"), "PANTS": ("clothing", "bottom"),
                "DRESS": ("clothing", "dress"), "COAT": ("clothing", "outerwear")}  # [cần xác minh] tên product_type ABO
CLOTHING_CC0_MAP = {"T-Shirt": ("clothing", "top"), "Shirt": ("clothing", "top"), "Longsleeve": ("clothing", "top"),
                    "Polo": ("clothing", "top"), "Top": ("clothing", "top"), "Hoodie": ("clothing", "top"),
                    "Pants": ("clothing", "bottom"), "Shorts": ("clothing", "bottom"), "Skirt": ("clothing", "bottom"),
                    "Dress": ("clothing", "dress"), "Outwear": ("clothing", "outerwear"), "Blazer": ("clothing", "outerwear"),
                    "Body": ("clothing", "unknown"), "Hat": ("headwear", "unknown"), "Shoes": ("footwear", "unknown")}


def _abo_val(d: dict, key: str, lang_prefix: str = "en") -> str | None:
    for x in d.get(key) or []:
        if str(x.get("language_tag", "en")).startswith(lang_prefix):
            return x.get("value")
    return None


def abo_listing_to_schema(d: dict) -> dict | None:
    """Một dòng listings ABO → schema chuẩn. [cần xác minh] tên trường theo README ABO (item_id, item_name[...], product_type[...])."""
    ptype = ((d.get("product_type") or [{}])[0]).get("value", "")
    if ptype not in ABO_TYPE_MAP:
        return None
    pt, sub = ABO_TYPE_MAP[ptype]
    color = _abo_val(d, "color")
    return dict(product_id=f"abo_{d['item_id']}", title=_abo_val(d, "item_name"), category=f"ABO/{ptype}",
                brand=_abo_val(d, "brand"), price=None, currency=None, colors=[color] if color else [], sizes=[],
                description=" ".join(x.get("value", "") for x in d.get("bullet_point") or [] if
                                     str(x.get("language_tag", "en")).startswith("en")) or None,
                specs={"main_image_id": d.get("main_image_id")}, image_paths=[], rating=None, rating_count=None,
                reviews=[], source="abo", source_url=ABO_SOURCE["url"], license=ABO_SOURCE["license"], product_type=pt,
                sub_category=sub, gender=None, size_system="none", view_type="studio", variant_id=None, language="en")


def clothing_cc0_row_to_schema(row: dict) -> dict | None:
    """Một dòng images.csv của Clothing Dataset (image, sender_id, label, kids) → schema; bỏ 'Skip', 'Not sure', đồ trẻ em."""
    lab = row.get("label")
    if lab not in CLOTHING_CC0_MAP or str(row.get("kids")).lower() in ("true", "1"):
        return None
    pt, sub = CLOTHING_CC0_MAP[lab]
    return dict(product_id=f"cds_{row['image']}", title=None, category=f"ClothingDataset/{lab}", brand=None, price=None,
                currency=None, colors=[], sizes=[], description=None, specs={"sender_id": row.get("sender_id")},
                image_paths=[f"images/cds_{row['image']}/0.jpg"], rating=None, rating_count=None, reviews=[],
                source="clothing_dataset_cc0", source_url=CLOTHING_CC0_SOURCE["url"], license=CLOTHING_CC0_SOURCE["license"],
                product_type=pt, sub_category=sub, gender=None, size_system="none", view_type="real_life", variant_id=None,
                language="en")


# ---------------- Kiểm tra & tái lập ----------------
def validate_schema(df: pd.DataFrame) -> list[str]:
    """Trả danh sách lỗi schema (rỗng = hợp lệ 100%)."""
    errs = []
    miss = [c for c in SCHEMA_FIELDS if c not in df.columns]
    if miss:
        errs.append(f"thiếu cột: {miss}")
        return errs
    if df.product_id.duplicated().any():
        errs.append(f"trùng product_id: {int(df.product_id.duplicated().sum())}")
    bad_pt = df[~df.product_type.isin(PRODUCT_TYPES)]
    if len(bad_pt):
        errs.append(f"product_type sai: {len(bad_pt)}")
    bad_sub = df[[s not in SUB_CATEGORIES.get(p, set()) for p, s in zip(df.product_type, df.sub_category)]]
    if len(bad_sub):
        errs.append(f"sub_category sai: {len(bad_sub)}")
    if (~df.size_system.isin(SIZE_SYSTEMS)).any():
        errs.append("size_system sai")
    if df.title.isna().any():
        errs.append(f"title rỗng: {int(df.title.isna().sum())}")
    return errs


def _jsonable(v):
    if hasattr(v, "tolist"):
        return v.tolist()
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, float) and v != v:
        return None
    return v


def _canon(v):
    """Chuẩn hoá giá trị để hash: NaN→None, float nguyên→int (24.0 ≡ 24 sau khi parquet ép kiểu), đệ quy."""
    v = _jsonable(v)
    if isinstance(v, dict):
        return {k: _canon(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    if isinstance(v, float):
        return int(v) if v.is_integer() else round(v, 6)
    return v


def catalog_hash(df: pd.DataFrame) -> str:
    """Hash nội dung catalog (sắp theo product_id, JSON sort_keys) – để kiểm 'chạy lại cho cùng kết quả'."""
    h = hashlib.sha256()
    for rec in df.sort_values("product_id").to_dict(orient="records"):
        h.update(json.dumps({k: _canon(v) for k, v in rec.items()}, ensure_ascii=False, sort_keys=True,
                            default=str).encode("utf-8"))
    return h.hexdigest()


def count_table(df: pd.DataFrame, types: set[str] | None = None) -> dict:
    """Bảng đếm theo product_type, (product_type, sub_category) và theo nguồn + kiểm quota tối thiểu (cho `types`)."""
    by_type = df.product_type.value_counts().to_dict()
    return {"total": int(len(df)), "by_type": {k: int(v) for k, v in by_type.items()},
            "by_sub": {f"{a}/{b}": int(n) for (a, b), n in df.groupby(["product_type", "sub_category"]).size().items()},
            "by_source": {k: int(v) for k, v in df.source.value_counts().items()},
            "quota_check": {pt: {"min": q, "have": int(by_type.get(pt, 0)), "ok": int(by_type.get(pt, 0)) >= q}
                            for pt, q in QUOTA_MIN.items() if types is None or pt in types}}


def write_catalog(df: pd.DataFrame, path: str | os.PathLike) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df = df[SCHEMA_FIELDS].copy()
    df["specs"] = df["specs"].map(lambda d: json.dumps(_jsonable(d), ensure_ascii=False, sort_keys=True, default=str))
    df["reviews"] = df["reviews"].map(lambda d: json.dumps(_jsonable(d), ensure_ascii=False, default=str))
    df.to_parquet(path, index=False)


def read_catalog(path: str | os.PathLike) -> pd.DataFrame:
    """Đọc catalog do write_catalog ghi (specs/reviews là JSON string) hoặc catalog shared (dict/array)."""
    df = pd.read_parquet(path)
    for c in ("specs", "reviews"):
        if c in df.columns:
            df[c] = df[c].map(lambda v: json.loads(v) if isinstance(v, str) else _jsonable(v))
    for c in ("colors", "sizes", "image_paths"):
        if c in df.columns:
            df[c] = df[c].map(lambda v: list(v) if v is not None and not isinstance(v, str) else ([] if v is None else [v]))
    return df


def append_sources_log(path: str | os.PathLike, entry: dict) -> None:
    """Ghi/ cập nhật log nguồn + license (`data/sources_log.json`), khoá theo tên nguồn."""
    p = Path(path)
    log = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    log[entry["name"]] = entry
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
