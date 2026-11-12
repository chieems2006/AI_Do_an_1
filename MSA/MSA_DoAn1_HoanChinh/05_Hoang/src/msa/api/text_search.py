# repo: src/msa/api/text_search.py
"""Tìm sản phẩm bằng văn bản + bộ lọc (US_37 – Owner: Hoàng, Support: Trung).

- Xếp hạng TF-IDF (word 1-2gram) trên văn bản sản phẩm đã làm giàu từ khoá tiếng Việt (vì catalog FPI tiếng Anh).
- Bộ lọc cứng: product_type, sub_category, màu (theo HỌ màu, nhận tiếng Việt/Anh), giới tính, khoảng giá, size.
- Re-rank: điểm TF-IDF + thưởng nhỏ khi màu/nhóm trong câu truy vấn khớp thuộc tính có cấu trúc.
- `parse_filters_vi(query)` trích bộ lọc từ câu tiếng Việt (loại, màu, giới tính, "dưới 500k") – tuỳ chọn.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

COLOR_FAMILY = {  # màu gốc (EN, chữ thường) → họ màu
    "black": "black", "white": "white", "off white": "white", "cream": "beige", "beige": "beige", "khaki": "beige",
    "nude": "beige", "skin": "beige", "tan": "brown", "brown": "brown", "coffee brown": "brown", "bronze": "brown",
    "mushroom brown": "brown", "copper": "brown", "taupe": "brown", "grey": "grey", "grey melange": "grey", "charcoal": "grey",
    "steel": "grey", "silver": "silver", "metallic": "silver", "gold": "gold", "red": "red", "maroon": "red", "burgundy": "red",
    "rust": "red", "pink": "pink", "rose": "pink", "peach": "pink", "magenta": "pink", "fuchsia": "pink", "blue": "blue",
    "navy blue": "blue", "turquoise blue": "blue", "teal": "blue", "sea green": "green", "green": "green",
    "olive": "green", "lime green": "green", "fluorescent green": "green", "yellow": "yellow", "mustard": "yellow",
    "orange": "orange", "coral": "orange", "purple": "purple", "lavender": "purple", "mauve": "purple", "multi": "multi",
}
VI_COLOR = {"đen": "black", "trắng": "white", "be": "beige", "kem": "beige", "nâu": "brown", "xám": "grey", "ghi": "grey",
            "bạc": "silver", "vàng gold": "gold", "đỏ": "red", "đô": "red", "hồng": "pink", "xanh dương": "blue",
            "xanh navy": "blue", "xanh lam": "blue", "navy": "blue", "xanh lá": "green", "xanh rêu": "green", "vàng": "yellow",
            "cam": "orange", "tím": "purple", "nhiều màu": "multi"}
FAMILY_VI = {"black": "đen", "white": "trắng", "beige": "be kem", "brown": "nâu", "grey": "xám ghi", "silver": "bạc",
             "gold": "vàng gold", "red": "đỏ", "pink": "hồng", "blue": "xanh dương navy", "green": "xanh lá",
             "yellow": "vàng", "orange": "cam", "purple": "tím", "multi": "nhiều màu"}
SUB_VI = {"sneaker": "giày thể thao sneaker", "leather_shoe": "giày da giày tây", "sandal": "dép sandal xăng đan",
          "boot": "giày boot bốt", "heel_flat*": "giày cao gót giày búp bê", "top": "áo áo thun áo sơ mi",
          "bottom": "quần quần jean quần short", "dress": "váy đầm", "outerwear": "áo khoác", "cap": "mũ lưỡi trai nón",
          "beanie": "mũ len", "bucket": "mũ bucket", "wide_brim": "mũ rộng vành", "wide_brim*": "mũ rộng vành",
          "bag": "túi túi xách balo", "belt": "thắt lưng dây nịt", "eyewear": "kính kính mắt kính râm"}
TYPE_VI = {"footwear": "giày dép", "clothing": "quần áo", "headwear": "mũ nón", "accessory": "phụ kiện"}
GENDER_VI = {"Men": "nam", "Women": "nữ", "Unisex": "nam nữ unisex", "Boys": "bé trai", "Girls": "bé gái"}
QUERY_TYPE_KW = [("giày", "footwear"), ("dép", "footwear"), ("sandal", "footwear"), ("sneaker", "footwear"),
                 ("áo", "clothing"), ("quần", "clothing"), ("váy", "clothing"), ("đầm", "clothing"),
                 ("mũ", "headwear"), ("nón", "headwear"), ("túi", "accessory"), ("balo", "accessory"),
                 ("thắt lưng", "accessory"), ("kính", "accessory")]


def _n(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").lower().strip()


def color_family(c: str) -> str | None:
    """Màu (EN hoặc VI) → họ màu; không biết → None."""
    c = _n(c)
    if c in COLOR_FAMILY:
        return COLOR_FAMILY[c]
    if c in VI_COLOR:
        return VI_COLOR[c]
    if c in FAMILY_VI:
        return c
    return None


@dataclass
class Filters:
    product_type: str | None = None
    sub_category: str | None = None
    colors: list[str] = field(default_factory=list)
    gender: str | None = None
    include_unisex: bool = True
    price_min: float | None = None
    price_max: float | None = None
    size: str | None = None

    def active(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v not in (None, [], True)}


def parse_filters_vi(query: str) -> Filters:
    """Trích bộ lọc đơn giản từ câu tiếng Việt: loại (từ khoá đầu tiên), màu, nam/nữ, 'dưới/trên Nk'."""
    q = _n(query)
    f = Filters()
    best = None
    for kw, pt in QUERY_TYPE_KW:
        m = re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", q)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), pt)
    f.product_type = best[1] if best else None
    for kw in sorted(VI_COLOR, key=len, reverse=True):
        if re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", q):
            fam = VI_COLOR[kw]
            if fam not in f.colors:
                f.colors.append(fam)
            q = re.sub(rf"(?<!\w){re.escape(kw)}(?!\w)", " ", q)
    if re.search(r"(?<!\w)nữ(?!\w)", q) and not re.search(r"(?<!\w)nam(?!\w)", q):
        f.gender = "Women"
    elif re.search(r"(?<!\w)nam(?!\w)", q) and not re.search(r"(?<!\w)nữ(?!\w)", q):
        f.gender = "Men"

    def money(num: str, unit: str | None) -> float:
        v = float(num.replace(",", ".").replace(".", "")) if unit is None else float(num.replace(",", "."))
        return v * {"k": 1e3, "nghìn": 1e3, "ngàn": 1e3, "tr": 1e6, "triệu": 1e6}.get(unit or "", 1)
    m = re.search(r"(dưới|tối đa|không quá)\s*([\d.,]+)\s*(k|nghìn|ngàn|tr|triệu)?", q)
    if m:
        f.price_max = money(m.group(2), m.group(3))
    m = re.search(r"(trên|từ|ít nhất)\s*([\d.,]+)\s*(k|nghìn|ngàn|tr|triệu)?", q)
    if m:
        f.price_min = money(m.group(2), m.group(3))
    return f


def doc_text(r) -> str:
    """Văn bản để index: tiêu đề + thuộc tính + từ khoá tiếng Việt suy ra từ thuộc tính có cấu trúc."""
    specs = r.specs if isinstance(r.specs, dict) else {}
    fams = {color_family(c) for c in (r.colors or [])} - {None}
    parts = [r.title or "", r.category or "", r.sub_category or "", r.product_type or "", " ".join(r.colors or []),
             r.gender or "", str(specs.get("usage") or ""), str(specs.get("season") or ""),
             SUB_VI.get(r.sub_category, ""), TYPE_VI.get(r.product_type, ""), GENDER_VI.get(r.gender, ""),
             " ".join(FAMILY_VI[f] for f in fams)]
    return _n(" ".join(parts))


class TextSearcher:
    """TF-IDF + bộ lọc metadata + re-rank nhẹ."""

    def __init__(self, catalog: pd.DataFrame):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.df = catalog.reset_index(drop=True)
        self.docs = [doc_text(r) for r in self.df.itertuples()]
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b")
        self.X = self.vec.fit_transform(self.docs)
        self.fam = [frozenset(color_family(c) for c in (cs or [])) - {None} for cs in self.df.colors]

    def mask(self, f: Filters) -> np.ndarray:
        d = self.df
        m = np.ones(len(d), bool)
        if f.product_type:
            m &= (d.product_type == f.product_type).to_numpy()
        if f.sub_category:
            m &= (d.sub_category == f.sub_category).to_numpy()
        if f.colors:
            want = {color_family(c) or _n(c) for c in f.colors}
            m &= np.array([bool(fs & want) for fs in self.fam])
        if f.gender:
            ok = {f.gender} | ({"Unisex"} if f.include_unisex else set())
            m &= d.gender.isin(ok).to_numpy()
        if f.price_min is not None or f.price_max is not None:
            p = pd.to_numeric(d.price, errors="coerce")
            pm = p.notna()  # SP không có giá bị loại khi người dùng lọc giá
            if f.price_min is not None:
                pm &= p >= f.price_min
            if f.price_max is not None:
                pm &= p <= f.price_max
            m &= pm.to_numpy()
        if f.size:
            s = _n(str(f.size))
            m &= np.array([s in {_n(str(x)) for x in (sz or [])} for sz in d.sizes])
        return m

    def search(self, query: str, k: int = 10, filters: Filters | None = None) -> list[dict]:
        f = filters or Filters()
        m = self.mask(f)
        if not m.any():
            return []
        q = _n(query or "")
        sims = (self.X @ self.vec.transform([q]).T).toarray().ravel() if q else np.zeros(len(self.df))
        qf = parse_filters_vi(q) if q else Filters()
        bonus = np.zeros(len(self.df))
        if qf.colors:
            bonus += 0.05 * np.array([bool(fs & set(qf.colors)) for fs in self.fam])
        if qf.product_type:
            bonus += 0.05 * (self.df.product_type == qf.product_type).to_numpy()
        score = np.where(m, sims + bonus, -np.inf)
        idx = np.argsort(-score, kind="stable")[: min(k, int(m.sum()))]
        out = []
        for i in idx:
            r = self.df.iloc[i]
            out.append({"product_id": r.product_id, "title": r.title, "price": None if pd.isna(r.price) else r.price,
                        "score": round(float(score[i]), 6), "image": (r.image_paths or [None])[0],
                        "product_type": r.product_type, "sub_category": r.sub_category, "colors": list(r.colors or []),
                        "gender": r.gender, "sizes": list(r.sizes or [])})
        return out
