# repo: scripts/03_clean.py
"""US_08 – Làm sạch, khử trùng lặp, phân loại catalog sản phẩm.

Các bước (mỗi bước ghi số trước/sau vào báo cáo):
 1. Chuẩn hoá text: Unicode NFC, bỏ thẻ HTML / entity, gộp khoảng trắng (title, brand, description).
 2. Kiểm ảnh: thiếu file, không mở được (PIL verify), quá nhỏ (< min_side), ảnh gần như một màu (std < blank_std).
 3. Khử trùng lặp: MD5 (trùng tuyệt đối) + perceptual hash (pHash, Hamming ≤ ngưỡng) CHỈ trong cùng
    product_type + brand (sheet 1 mục H) – biến thể khác màu được giữ lại và gán variant_id chung.
 4. Áp category_map.csv (source, source_label → product_type, sub_category); không map được → unknown và loại khỏi index.
 5. Chuẩn hoá màu về ~14 màu chung; chuẩn hoá size theo size_system của nhóm.
 6. Giới hạn tối đa mỗi nhóm lá (cap) nhưng không để product_type rơi dưới quota.
 7. Lấy mẫu 100 SP/nhóm để kiểm nhãn (CSV cho 2 người) + kiểm tự động bằng từ khoá tiêu đề.

Chạy thật:
    python src/scripts/03_clean.py --catalog /home/claude/work/shared_data/catalog_fpi.parquet \
        --image-root /home/claude/work/shared_data --out results
"""
from __future__ import annotations
import os

import argparse
import hashlib
import html
import json
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QUOTA = {"footwear": 1200, "clothing": 2000, "accessory": 500, "headwear": 300}

# ---------------------------------------------------------------- text
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def normalize_text(s: Any) -> Any:
    """NFC + bỏ HTML + gộp khoảng trắng. Giữ None/NaN nguyên trạng."""
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return s
    s = html.unescape(str(s))
    s = _TAG.sub(" ", s)
    s = unicodedata.normalize("NFC", s)
    s = s.replace("​", " ").replace("\xa0", " ")
    return _WS.sub(" ", s).strip()


_GENDER = {"men", "women", "unisex", "boys", "girls", "kids", "kids-unisex", "men's", "women's", "girl's", "boy's", "kids-boys", "kids-girls"}


def infer_brand(title: str | None) -> str | None:
    """Lấy brand = các từ đứng trước từ chỉ giới tính (FPI: 'Red Tape Men Black Shoes' -> 'Red Tape').

    Bản prep_shared_data lấy từ đầu tiên nên 'Red Tape' và 'Red Chief' bị gộp thành 'Red'.
    """
    if not title:
        return None
    toks = title.split()
    for i, t in enumerate(toks):
        if t.lower() in _GENDER and i > 0:
            return " ".join(toks[:i])
    return toks[0]


def title_jaccard(a: str | None, b: str | None) -> float:
    """Jaccard trên tập từ (chữ thường, bỏ 's) – dùng xác nhận cặp trùng."""
    ta = set(re.sub(r"'s\b", "", (a or "").lower()).split())
    tb = set(re.sub(r"'s\b", "", (b or "").lower()).split())
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0


# ---------------------------------------------------------------- màu / size
COLOR_MAP = {
    "black": "black", "charcoal": "black",
    "white": "white", "off white": "white", "cream": "white",
    "grey": "grey", "grey melange": "grey", "steel": "grey", "silver": "grey", "metallic": "grey",
    "blue": "blue", "navy blue": "blue", "turquoise blue": "blue", "teal": "blue",
    "red": "red", "maroon": "red", "burgundy": "red", "rust": "red",
    "pink": "pink", "magenta": "pink", "peach": "pink",
    "purple": "purple", "lavender": "purple",
    "green": "green", "olive": "green", "sea green": "green", "lime green": "green", "fluorescent green": "green",
    "yellow": "yellow", "mustard": "yellow", "gold": "yellow",
    "orange": "orange",
    "brown": "brown", "tan": "brown", "coffee brown": "brown", "mushroom brown": "brown", "bronze": "brown",
    "copper": "brown", "taupe": "brown",
    "beige": "beige", "khaki": "beige",
    "multi": "multi",
    # tiếng Việt (cho dữ liệu crawl/ViMRHP)
    "đen": "black", "trắng": "white", "xám": "grey", "ghi": "grey", "xanh dương": "blue", "xanh navy": "blue",
    "đỏ": "red", "hồng": "pink", "tím": "purple", "xanh lá": "green", "vàng": "yellow", "cam": "orange",
    "nâu": "brown", "be": "beige", "kem": "white",
}


def normalize_color(c: str | None) -> str:
    """Đưa màu về ~14 nhóm chung; không nhận ra → 'other'."""
    if not c:
        return "unknown"
    k = unicodedata.normalize("NFC", str(c)).strip().lower()
    return COLOR_MAP.get(k, "other")


DEFAULT_SIZE_SYSTEM = {"footwear": "EU", "clothing": "alpha", "headwear": "free", "accessory": "none"}
_ALPHA = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL"]


def normalize_sizes(sizes: Any, product_type: str) -> tuple[str, list[str]]:
    """Trả (size_system, sizes chuẩn hoá). Danh sách rỗng → ('none', [])."""
    vals = [str(x).strip().upper() for x in (list(sizes) if sizes is not None else []) if str(x).strip()]
    if not vals:
        return "none", []
    vals = [v.replace("2XL", "XXL").replace("3XL", "XXXL") for v in vals]
    if all(v in _ALPHA for v in vals):
        return "alpha", sorted(set(vals), key=_ALPHA.index)
    if all(v in {"FREE", "FREESIZE", "FREE SIZE", "ONE SIZE"} for v in vals):
        return "free", ["FREE"]
    nums = [re.sub(r"[^0-9.]", "", v) for v in vals]
    if all(nums) and product_type == "footwear":
        f = [float(n) for n in nums]
        system = "EU" if min(f) >= 30 else "US"
        return system, sorted(set(nums), key=float)
    if all(nums) and product_type == "clothing":
        return "numeric_waist", sorted(set(nums), key=float)
    return DEFAULT_SIZE_SYSTEM.get(product_type, "none"), vals


# ---------------------------------------------------------------- ảnh
def check_image(path: Path, min_side: int = 32, blank_std: float = 3.0) -> dict:
    """Kiểm 1 ảnh: trả dict{status, w, h, mode, std, md5, phash}. status ∈ ok|missing|unreadable|too_small|blank."""
    from PIL import Image
    import imagehash

    out: dict[str, Any] = dict(status="ok", w=None, h=None, mode=None, std=None, md5=None, phash=None)
    if not path.exists():
        out["status"] = "missing"
        return out
    raw = path.read_bytes()
    out["md5"] = hashlib.md5(raw).hexdigest()
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
            out.update(w=im.width, h=im.height, mode=im.mode)
            g = np.asarray(im.convert("L"), dtype=np.float32)
            out["std"] = float(g.std())
            out["phash"] = str(imagehash.phash(im.convert("RGB")))
    except Exception:  # noqa: BLE001 – mọi lỗi giải mã đều là ảnh lỗi
        out["status"] = "unreadable"
        return out
    if min(out["w"], out["h"]) < min_side:
        out["status"] = "too_small"
    elif out["std"] < blank_std:
        out["status"] = "blank"
    return out


def hamming_pairs(hashes: list[str], ids: list[str], max_dist: int) -> list[tuple[str, str, int]]:
    """Tìm mọi cặp (id_a, id_b, dist) có Hamming ≤ max_dist giữa các pHash 64-bit (hex)."""
    if len(hashes) < 2:
        return []
    arr = np.array([int(h, 16) for h in hashes], dtype=np.uint64)
    out = []
    for i in range(0, len(arr), 512):
        x = arr[i:i + 512, None] ^ arr[None, :]
        d = np.unpackbits(x.view(np.uint8), axis=-1).reshape(x.shape[0], x.shape[1], 64).sum(-1)
        rows, cols = np.nonzero(d <= max_dist)
        for r, c in zip(rows, cols):
            a = i + r
            if a < c:
                out.append((ids[a], ids[c], int(d[r, c])))
    return out


# ---------------------------------------------------------------- category
def load_category_map(path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    m = pd.read_csv(path)
    return {(r.source, r.source_label): (r.product_type, r.sub_category) for r in m.itertuples()}


def source_label(row: pd.Series) -> str:
    specs = row.get("specs")
    if isinstance(specs, dict) and specs.get("articleType"):
        return str(specs["articleType"])
    cat = str(row.get("category") or "")
    return cat.split("/")[-1] if cat else ""


# Từ khoá tiêu đề để kiểm nhãn tự động (tiếng Anh cho FPI); khớp ≥ 1 từ khoá của lá → coi là nhất quán.
TITLE_KEYWORDS = {
    "sneaker": ["shoe", "sneaker", "trainer", "running", "casual"],
    "leather_shoe": ["shoe", "formal", "loafer", "derby", "oxford", "leather"],
    "heel_flat": ["heel", "flat", "pump", "wedge", "bellie", "ballerina", "sandal", "shoe"],
    "sandal": ["sandal", "flip", "slipper", "floater", "chappal"],
    "top": ["tshirt", "t-shirt", "shirt", "top", "kurta", "sweater", "sweatshirt", "tee", "polo", "kurti", "tunic",
            "jersey"],
    "bottom": ["jean", "short", "trouser", "pant", "skirt", "capri", "legging", "track", "chino", "dungree",
               "dungaree"],
    "dress": ["dress", "jumpsuit"],
    "outerwear": ["jacket", "blazer", "coat"],
    "cap": ["cap"],
    "beanie": ["beanie", "skull cap"],
    "bucket": ["bucket"],
    "wide_brim": ["hat", "fedora", "panama"],
    "bag": ["bag", "backpack", "clutch", "handbag", "duffel", "messenger", "tote", "sling", "purse"],
    "belt": ["belt"],
    "eyewear": ["sunglass", "glasses", "eyewear", "aviator", "wayfarer"],
}


# Tinh chỉnh lá theo tiêu đề – phát hiện khi chạy thật: articleType "Caps"/"Hat" của FPI có lẫn beanie / skull cap.
TITLE_REFINE: list[tuple[str, str, str]] = [
    ("headwear", r"\bbeanie|\bskull ?caps?\b", "beanie"),
    ("headwear", r"\bbucket\b", "bucket"),
    ("headwear", r"\b(fedora|panama|sun ?hat|wide ?brim)\b", "wide_brim"),
    # FPI: "Flying Machine Men Black Hat" (fedora), "Wildcraft Unisex Beige Hat" (mũ vành) – đã xem ảnh thật
    ("headwear", r"\bhats?\b", "wide_brim"),
]


def refine_sub_category(title: str | None, product_type: str, sub: str) -> str:
    """Áp TITLE_REFINE (regex, không phân biệt hoa thường); không khớp → giữ nguyên."""
    t = (title or "").lower()
    for pt, pat, new in TITLE_REFINE:
        if pt == product_type and re.search(pat, t):
            return new
    return sub


def title_label_consistent(title: str, sub: str) -> bool | None:
    kws = TITLE_KEYWORDS.get(sub)
    if not kws:
        return None
    t = (title or "").lower()
    return any(k in t for k in kws)


# ---------------------------------------------------------------- cap theo lá
def cap_leaves(df: pd.DataFrame, cap: int | None, quota: dict[str, int], seed: int = 42) -> tuple[pd.DataFrame, dict]:
    """Giữ tối đa `cap` SP/lá; nếu product_type rơi dưới quota thì trả lại SP từ các lá lớn nhất cho đủ quota."""
    if not cap:
        return df, {"cap": None, "dropped": 0}
    kept, dropped_info = [], {}
    for pt, g in df.groupby("product_type"):
        parts, pool = [], []
        for sub, gs in g.groupby("sub_category"):
            gs = gs.sample(frac=1, random_state=seed)
            parts.append(gs.head(cap))
            if len(gs) > cap:
                pool.append(gs.iloc[cap:])
        cur = pd.concat(parts)
        need = quota.get(pt, 0) - len(cur)
        if need > 0 and pool:
            extra = pd.concat(pool).sample(frac=1, random_state=seed).head(need)
            cur = pd.concat([cur, extra])
        dropped_info[pt] = int(len(g) - len(cur))
        kept.append(cur)
    out = pd.concat(kept)
    return out, {"cap": cap, "dropped_by_type": dropped_info, "dropped": int(len(df) - len(out))}


# ---------------------------------------------------------------- pipeline
def counts(df: pd.DataFrame) -> dict:
    return {
        "n": int(len(df)),
        "by_type": {k: int(v) for k, v in df.product_type.value_counts().sort_index().items()},
        "by_leaf": {f"{a}/{b}": int(n) for (a, b), n in df.groupby(["product_type", "sub_category"]).size().items()},
    }


def run(catalog: Path, image_root: Path, out_dir: Path, category_map: Path, phash_max_dist: int = 4,
        min_side: int = 32, blank_std: float = 3.0, cap: int | None = 800, quota: dict | None = None,
        sample_per_type: int = 100, seed: int = 42, drop_title_jaccard: float = 0.6, fix_brand: bool = True) -> dict:
    t_start = time.time()
    quota = quota or DEFAULT_QUOTA
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(catalog)
    report: dict[str, Any] = {"input": str(catalog), "config": dict(phash_max_dist=phash_max_dist, min_side=min_side,
                              blank_std=blank_std, cap=cap, quota=quota, seed=seed, sample_per_type=sample_per_type,
                              drop_title_jaccard=drop_title_jaccard, fix_brand=fix_brand)}
    report["before"] = counts(df)

    # 1. text
    changed = 0
    for col in ["title", "brand", "description"]:
        if col in df:
            new = df[col].map(normalize_text)
            changed += int(((new != df[col]) & df[col].notna()).sum())
            df[col] = new
    report["text_fields_changed"] = changed
    if fix_brand:
        new_brand = df.title.map(infer_brand)
        report["brand_fixed"] = int((new_brand != df.brand).sum())
        report["brand_unique_before_after"] = [int(df.brand.nunique()), int(new_brand.nunique())]
        df["brand"] = new_brand
    report["missing_rate"] = {c: round(float(df[c].isna().mean() if df[c].dtype == object else 0), 4)
                              for c in ["title", "brand", "price", "description", "rating"] if c in df}

    # 2. ảnh
    infos = []
    for pid, paths in zip(df.product_id, df.image_paths):
        p = image_root / list(paths)[0] if len(paths) else Path("/nonexistent")
        infos.append(dict(product_id=pid, path=str(p), **check_image(p, min_side, blank_std)))
    img = pd.DataFrame(infos)
    report["images"] = {
        "checked": int(len(img)),
        "status": {k: int(v) for k, v in img.status.value_counts().items()},
        "size_wh": {f"{w}x{h}": int(n) for (w, h), n in img.groupby(["w", "h"]).size().items()},
        "mode": {k: int(v) for k, v in img["mode"].value_counts().items()},
        "bad_rate": round(float((img.status != "ok").mean()), 4),
    }
    img[img.status != "ok"].to_csv(out_dir / "bad_images.csv", index=False)
    df = df.merge(img[["product_id", "status", "md5", "phash", "std"]], on="product_id", how="left")
    n0 = len(df)
    df = df[df.status == "ok"].copy()
    report["removed_bad_images"] = int(n0 - len(df))

    # 3. khử trùng
    md5_dups = df[df.duplicated("md5", keep="first")]
    report["exact_md5_duplicates"] = int(len(md5_dups))
    # thống kê toàn cục (tham khảo, KHÔNG dùng để xoá) ở nhiều ngưỡng
    all_pairs = hamming_pairs(df.phash.tolist(), df.product_id.tolist(), max_dist=max(phash_max_dist, 8))
    meta = df.set_index("product_id")
    report["phash_pairs_global_by_threshold"] = {
        str(t): int(sum(1 for *_, d in all_pairs if d <= t)) for t in [0, 2, 4, 6, 8]}
    report["phash_pairs_global_cross_type_le_thr"] = int(sum(
        1 for a, b, d in all_pairs if d <= phash_max_dist and meta.at[a, "product_type"] != meta.at[b, "product_type"]))
    # cặp dùng để quyết định: cùng product_type + brand, d ≤ ngưỡng
    rows = []
    for a, b, d in all_pairs:
        if d > phash_max_dist:
            continue
        ra, rb = meta.loc[a], meta.loc[b]
        same_group = ra.product_type == rb.product_type and ra.brand == rb.brand
        ca, cb = [normalize_color(x) for x in list(ra.colors)[:1]], [normalize_color(x) for x in list(rb.colors)[:1]]
        same_color = ca == cb
        jac = title_jaccard(ra.title, rb.title)
        md5_eq = ra.md5 == rb.md5
        # Quy tắc (sau khi kiểm ảnh thật, xem docs/US_08): pHash trên ảnh 60x80 va chạm nhiều giữa SP khác nhau,
        # nên chỉ XOÁ khi MD5 trùng, hoặc pHash = 0 + cùng type/brand/màu + tiêu đề gần giống (Jaccard ≥ ngưỡng).
        if md5_eq or (d == 0 and same_group and same_color and jac >= drop_title_jaccard):
            action = "drop_b"
        elif same_group and same_color:
            action = "review"        # nghi trùng – đưa người kiểm, không tự xoá
        elif same_group:
            action = "variant"       # cùng kiểu khác màu → giữ, gán variant_id
        else:
            action = "keep_both_diff_group"
        rows.append(dict(id_a=a, id_b=b, dist=d, same_type_brand=same_group, same_color=same_color,
                         title_a=ra.title, title_b=rb.title, title_jaccard=round(jac, 3), md5_equal=md5_eq, action=action))
    pairs = pd.DataFrame(rows, columns=["id_a", "id_b", "dist", "same_type_brand", "same_color", "title_a", "title_b",
                                        "title_jaccard", "md5_equal", "action"])
    pairs.to_csv(out_dir / "dup_pairs.csv", index=False)
    drop_ids = set(md5_dups.product_id) | set(pairs.loc[pairs.action == "drop_b", "id_b"])
    report["dedupe"] = {
        "pairs_le_thr_total": int(len(pairs)),
        "pairs_same_type_brand": int(pairs.same_type_brand.sum()) if len(pairs) else 0,
        "pairs_action": {k: int(v) for k, v in pairs.action.value_counts().items()} if len(pairs) else {},
        "removed_duplicates": int(len(drop_ids)),
    }
    # variant_id: nhóm các cặp 'variant' bằng union-find
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.get(x, x) != x:
            x = parent[x]
        return x
    for r in pairs[pairs.action == "variant"].itertuples():
        parent[find(r.id_b)] = find(r.id_a)
    df["variant_id"] = df.product_id.map(lambda x: f"var_{find(x)}" if x in parent or x in parent.values() else None)
    df = df[~df.product_id.isin(drop_ids)].copy()
    report["variant_groups"] = int(df.variant_id.dropna().nunique())

    # 4. category map
    cmap = load_category_map(category_map)
    labels = df.apply(source_label, axis=1)
    mapped = [cmap.get((s, l)) for s, l in zip(df.source, labels)]
    df["source_label"] = labels
    df["product_type"] = [m[0] if m else "unknown" for m in mapped]
    df["sub_category"] = [m[1] if m else "unknown" for m in mapped]
    refined = [refine_sub_category(t, pt, sc) for t, pt, sc in zip(df.title, df.product_type, df.sub_category)]
    chg = df.sub_category != pd.Series(refined, index=df.index)
    report["title_refined"] = {f"{a}->{b}": int(n) for (a, b), n in
                               Counter(zip(df.sub_category[chg], pd.Series(refined, index=df.index)[chg])).items()}
    df["sub_category"] = refined
    report["unmapped_labels"] = sorted({l for l, m in zip(labels, mapped) if m is None})
    unk = df[(df.product_type == "unknown") | (df.sub_category == "unknown")]
    report["removed_unknown_category"] = int(len(unk))
    report["removed_unknown_labels"] = {k: int(v) for k, v in unk.source_label.value_counts().items()}
    df = df[(df.product_type != "unknown") & (df.sub_category != "unknown")].copy()

    # 5. màu / size
    df["colors_norm"] = df.colors.map(lambda cs: sorted({normalize_color(c) for c in (list(cs) if cs is not None else [])}))
    ss = [normalize_sizes(s, pt) for s, pt in zip(df.sizes, df.product_type)]
    df["size_system"] = [a for a, _ in ss]
    df["sizes"] = [b for _, b in ss]
    report["color_norm_dist"] = dict(Counter(c for cs in df.colors_norm for c in cs).most_common())
    report["size_system_dist"] = {k: int(v) for k, v in df.size_system.value_counts().items()}

    report["before_cap"] = counts(df)
    # 6. cap theo lá
    df, cap_info = cap_leaves(df, cap, quota, seed)
    report["cap"] = cap_info
    report["after"] = counts(df)
    report["quota_check"] = {pt: {"quota": q, "have": report["after"]["by_type"].get(pt, 0),
                                  "ok": report["after"]["by_type"].get(pt, 0) >= q} for pt, q in quota.items()}
    report["category_coverage"] = round(float((df.product_type.isin(quota) & (df.sub_category != "unknown")).mean()), 4)

    # 7. mẫu kiểm nhãn
    samples = []
    for pt, g in df.groupby("product_type"):
        s = g.sample(min(sample_per_type, len(g)), random_state=seed)
        samples.append(s)
    smp = pd.concat(samples)
    smp = smp.assign(auto_title_consistent=[title_label_consistent(t, s) for t, s in zip(smp.title, smp.sub_category)],
                     image=smp.image_paths.map(lambda p: list(p)[0]), label_ok_annotator_1="", label_ok_annotator_2="",
                     correct_sub_category="")
    smp[["product_id", "title", "image", "source_label", "product_type", "sub_category", "auto_title_consistent",
         "label_ok_annotator_1", "label_ok_annotator_2", "correct_sub_category"]].to_csv(out_dir / "label_check_sample.csv", index=False)
    auto = {}
    for pt, g in smp.groupby("product_type"):
        v = g.auto_title_consistent.dropna()
        auto[pt] = {"n": int(len(g)), "inconsistent": int((~v.astype(bool)).sum()),
                    "inconsistent_rate": round(float((~v.astype(bool)).mean()), 4) if len(v) else None}
    report["label_check_auto_title"] = auto
    report["label_check_human"] = "CHƯA ĐO – 2 người điền label_ok_annotator_1/2 trong results/label_check_sample.csv"

    df = df.drop(columns=["status", "md5", "std"]).rename(columns={"phash": "image_phash"})
    df.to_parquet(out_dir / "catalog_clean.parquet", index=False, compression="zstd")
    report["runtime_s"] = round(time.time() - t_start, 1)
    (out_dir / "clean_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str))
    (out_dir / "clean_report.md").write_text(render_md(report), encoding="utf-8")
    return report


def render_md(r: dict) -> str:
    """Bảng trước/sau dạng markdown sinh tự động từ clean_report.json."""
    lines = ["# Báo cáo làm sạch (sinh tự động bởi 03_clean.py)", "",
             f"Đầu vào: `{r['input']}` – cấu hình: `{json.dumps(r['config'], ensure_ascii=False)}`", "",
             "| Bước | Số SP | Ghi chú |", "|---|---|---|",
             f"| Ban đầu | {r['before']['n']} | |",
             f"| Loại ảnh lỗi | -{r['removed_bad_images']} | trạng thái ảnh: {r['images']['status']} |",
             f"| Khử trùng lặp | -{r['dedupe']['removed_duplicates']} | MD5 trùng: {r['exact_md5_duplicates']}; cặp pHash ≤ ngưỡng cùng type+brand: {r['dedupe']['pairs_same_type_brand']} |",
             f"| Loại category unknown | -{r['removed_unknown_category']} | {r['removed_unknown_labels']} |",
             f"| Cap mỗi lá | -{r['cap']['dropped']} | cap={r['cap']['cap']} |",
             f"| **Sau làm sạch** | **{r['after']['n']}** | |", "",
             "| Nhóm lá | Trước | Sau |", "|---|---|---|"]
    keys = sorted(set(r["before"]["by_leaf"]) | set(r["after"]["by_leaf"]))
    for k in keys:
        lines.append(f"| {k} | {r['before']['by_leaf'].get(k, 0)} | {r['after']['by_leaf'].get(k, 0)} |")
    lines += ["", "| product_type | Quota | Sau | Đạt? |", "|---|---|---|---|"]
    for pt, q in r["quota_check"].items():
        lines.append(f"| {pt} | {q['quota']} | {q['have']} | {'Đạt' if q['ok'] else 'THIẾU'} |")
    lines += ["", f"Cặp pHash toàn cục theo ngưỡng Hamming: {r['phash_pairs_global_by_threshold']}",
              f"Kiểm nhãn tự động theo từ khoá tiêu đề (mẫu 100/nhóm): {r['label_check_auto_title']}", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalog", default=(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/catalog_fpi.parquet"))
    ap.add_argument("--image-root", default=os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))
    ap.add_argument("--category-map", default=str(ROOT / "data" / "category_map.csv"))
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--phash-max-dist", type=int, default=4)
    ap.add_argument("--min-side", type=int, default=32)
    ap.add_argument("--cap", type=int, default=800)
    ap.add_argument("--drop-title-jaccard", type=float, default=0.6)
    a = ap.parse_args()
    r = run(Path(a.catalog), Path(a.image_root), Path(a.out), Path(a.category_map), a.phash_max_dist, a.min_side,
            cap=a.cap, drop_title_jaccard=a.drop_title_jaccard)
    print(render_md(r))


if __name__ == "__main__":
    main()
