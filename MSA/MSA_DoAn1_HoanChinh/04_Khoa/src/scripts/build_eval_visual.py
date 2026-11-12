# repo: scripts/build_eval_visual.py
"""US_15 – Sinh bộ đánh giá Visual Search `eval_visual.csv` từ dữ liệu THẬT (shared_data v1).

Hai tầng truy vấn:
1. `instance` – ảnh studio "khác góc" XẤP XỈ bằng biến đổi có kiểm soát ảnh gốc của SP
   (crop lệch, xoay, đổi sáng/màu, lật+scale, dán lên nền, hạ chất lượng, tổ hợp). GT = product_id gốc
   (ảnh gốc vẫn nằm trong index). Đây KHÔNG thay thế ảnh chụp ngoài đời.
2. `category` – truy vấn là ảnh của SP KHÁC (held-out: có trong 44.072 dòng FPI gốc nhưng không nằm
   trong catalog; riêng mũ không còn SP held-out nên dùng leave-one-out: chính ảnh SP trong catalog,
   loại bản thân khỏi kết quả qua cột `exclude_ids`). GT = mọi SP catalog cùng articleType + cùng màu gốc.

`hard_cross_type` được gán bằng tiêu chí độc lập với các model benchmark: trong không gian pixel thô
(thumbnail 16x16 RGB, trừ trung bình, cosine), ≥ 2/5 láng giềng gần nhất của ảnh gốc thuộc product_type khác.

Chạy:  python src/scripts/build_eval_visual.py  (seed 42) -> eval/eval_visual.csv + eval/queries/*.jpg
"""
from __future__ import annotations
import os

import argparse
import glob
import io
import json
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SHARED = Path(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))
RAW_GLOB = (os.environ.get("MSA_RAW_DIR", "/home/claude/realdata") + "/fpi/data/*.parquet")
TYPES = ["footwear", "clothing", "headwear", "accessory"]

TRANSFORMS = ["crop_offset", "rotate", "color_jitter", "hflip_scale", "background", "lowres_jpeg", "combo"]


# ----------------------------------------------------------------------------- biến đổi
def _bg_texture(size, rng: np.random.Generator) -> Image.Image:
    """Nền không trắng: màu ngẫu nhiên + nhiễu (giả lập bàn/sàn)."""
    w, h = size
    base = rng.integers(60, 200, size=3)
    noise = rng.normal(0, 18, size=(h, w, 1))
    arr = np.clip(base[None, None, :] + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").filter(ImageFilter.GaussianBlur(1))


def _paste_on_bg(im: Image.Image, rng: np.random.Generator, scale: float) -> Image.Image:
    """Tách nền trắng thô (ngưỡng) rồi dán vật thể đã thu nhỏ lên nền có texture."""
    w, h = im.size
    small = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BICUBIC)
    a = np.asarray(small).astype(int)
    mask = Image.fromarray(((a.min(axis=2) < 235) * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(3))
    bg = _bg_texture((w, h), rng)
    ox = int(rng.integers(0, w - small.size[0] + 1))
    oy = int(rng.integers(0, h - small.size[1] + 1))
    bg.paste(small, (ox, oy), mask)
    return bg


def apply_transform(im: Image.Image, name: str, rng: np.random.Generator) -> tuple[Image.Image, str]:
    """Áp một biến đổi có kiểm soát; trả về ảnh + chuỗi mô tả tham số (để tái lập/giải thích)."""
    im = im.convert("RGB")
    w, h = im.size
    if name == "crop_offset":
        f = float(rng.uniform(0.70, 0.85))
        cw, ch = int(w * f), int(h * f)
        x0 = int(rng.integers(0, w - cw + 1)); y0 = int(rng.integers(0, h - ch + 1))
        return im.crop((x0, y0, x0 + cw, y0 + ch)).resize((w, h), Image.BICUBIC), f"crop_offset(f={f:.2f},x0={x0},y0={y0})"
    if name == "rotate":
        ang = float(rng.choice([-1, 1]) * rng.uniform(8, 15))
        return im.rotate(ang, resample=Image.BICUBIC, fillcolor=(255, 255, 255)), f"rotate({ang:.1f}deg)"
    if name == "color_jitter":
        b, c, s = (float(rng.uniform(0.7, 1.3)) for _ in range(3))
        out = ImageEnhance.Color(ImageEnhance.Contrast(ImageEnhance.Brightness(im).enhance(b)).enhance(c)).enhance(s)
        return out, f"color_jitter(b={b:.2f},c={c:.2f},s={s:.2f})"
    if name == "hflip_scale":
        sc = float(rng.uniform(0.75, 0.9))
        small = ImageOps.mirror(im).resize((int(w * sc), int(h * sc)), Image.BICUBIC)
        canvas = Image.new("RGB", (w, h), (255, 255, 255)); canvas.paste(small, ((w - small.size[0]) // 2, (h - small.size[1]) // 2))
        return canvas, f"hflip_scale(s={sc:.2f})"
    if name == "background":
        sc = float(rng.uniform(0.7, 0.85))
        return _paste_on_bg(im, rng, sc), f"background(scale={sc:.2f})"
    if name == "lowres_jpeg":
        f = float(rng.uniform(0.4, 0.6)); q = int(rng.integers(20, 40))
        small = im.resize((max(1, int(w * f)), max(1, int(h * f))), Image.BILINEAR).resize((w, h), Image.BILINEAR)
        buf = io.BytesIO(); small.save(buf, "JPEG", quality=q)
        return Image.open(io.BytesIO(buf.getvalue())).convert("RGB"), f"lowres_jpeg(f={f:.2f},q={q})"
    if name == "combo":
        ang = float(rng.choice([-1, 1]) * rng.uniform(5, 10))
        b = float(rng.uniform(0.75, 1.25))
        out = ImageEnhance.Brightness(im.rotate(ang, resample=Image.BICUBIC, fillcolor=(255, 255, 255))).enhance(b)
        sc = float(rng.uniform(0.7, 0.85))
        return _paste_on_bg(out, rng, sc), f"combo(rotate={ang:.1f},b={b:.2f},bg_scale={sc:.2f})"
    raise ValueError(name)


# ----------------------------------------------------------------------------- tiện ích
def pixel_thumbs(paths: list[str]) -> np.ndarray:
    """Thumbnail 16x16 RGB trừ trung bình, L2-normalize – không gian pixel thô (độc lập model)."""
    out = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        s = max(im.size); c = Image.new("RGB", (s, s), (255, 255, 255)); c.paste(im, ((s - im.size[0]) // 2, (s - im.size[1]) // 2))
        a = np.asarray(c.resize((16, 16), Image.BILINEAR), dtype=np.float32).reshape(-1) / 255.0
        out.append(a - a.mean())
    x = np.stack(out)
    return x / np.clip(np.linalg.norm(x, axis=1, keepdims=True), 1e-9, None)


def hard_cross_flags(cat: pd.DataFrame, img_paths: list[str], k: int = 5, min_other: int = 2) -> np.ndarray:
    x = pixel_thumbs(img_paths)
    sims = x @ x.T
    np.fill_diagonal(sims, -9)
    nn = np.argsort(-sims, axis=1)[:, :k]
    types = cat["product_type"].to_numpy()
    other = (types[nn] != types[:, None]).sum(axis=1)
    return other >= min_other


def load_catalog() -> pd.DataFrame:
    cat = pd.read_parquet(SHARED / "catalog_fpi.parquet")
    cat["article_type"] = cat["specs"].map(lambda s: s.get("articleType"))
    cat["raw_id"] = cat["product_id"].str.replace("fpi_", "", regex=False).astype(int)
    cat["img"] = cat["image_paths"].map(lambda a: str(SHARED / a[0]))
    return cat.reset_index(drop=True)


def load_raw_meta() -> pd.DataFrame:
    import pyarrow.parquet as pq

    fs = sorted(glob.glob(RAW_GLOB))
    return pd.concat([pq.read_table(f, columns=["id", "masterCategory", "subCategory", "articleType", "baseColour", "gender", "productDisplayName"]).to_pandas() for f in fs])


def read_raw_images(ids: set[int]) -> dict[int, bytes]:
    import pyarrow.parquet as pq

    out = {}
    for f in sorted(glob.glob(RAW_GLOB)):
        for b in pq.ParquetFile(f).iter_batches(batch_size=2000, columns=["id", "image"]):
            for r in b.to_pylist():
                if r["id"] in ids:
                    out[r["id"]] = r["image"]["bytes"]
    return out


# ----------------------------------------------------------------------------- build
def build(n_inst: int = 100, n_cat: int = 50, val_frac: float = 0.4, seed: int = 42, out_dir: Path = ROOT / "eval") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    random.seed(seed)
    cat = load_catalog()
    raw = load_raw_meta()
    col = dict(zip(raw["id"], raw["baseColour"]))
    cat["base_colour"] = cat["raw_id"].map(col)
    cat["hard"] = hard_cross_flags(cat, cat["img"].tolist())
    qdir = out_dir / "queries"; qdir.mkdir(parents=True, exist_ok=True)
    rows = []

    # ---- tầng instance
    for t in TYPES:
        sub = cat[cat.product_type == t]
        hard = sub[sub.hard]; easy = sub[~sub.hard]
        n_h = min(len(hard), max(8, n_inst // 4))
        pick = pd.concat([hard.sample(n_h, random_state=seed), easy.sample(min(len(easy), n_inst - n_h), random_state=seed)])
        pick = pick.sample(frac=1, random_state=seed).reset_index(drop=True)
        n_val = int(round(len(pick) * val_frac))
        for i, r in pick.iterrows():
            tr = TRANSFORMS[i % len(TRANSFORMS)]
            im, desc = apply_transform(Image.open(r.img), tr, rng)
            qid = f"vq_inst_{t[:4]}_{i:03d}"
            path = qdir / f"{qid}.jpg"; im.save(path, "JPEG", quality=95)
            rows.append(dict(query_id=qid, query_image=str(path.relative_to(ROOT)), gt_product_ids=r.product_id,
                             product_type=t, sub_category=r.sub_category, article_type=r.article_type,
                             base_colour=r.base_colour, split="val" if i < n_val else "test", tier="instance",
                             source="fpi_catalog_transformed", hard_cross_type=bool(r.hard), transform=desc,
                             exclude_ids="", origin="synthetic_transform_of_real_catalog_image (tác nhân Khoa sinh, seed 42)"))

    # ---- tầng category (held-out SP khác cùng articleType+màu; mũ dùng leave-one-out)
    at2type = cat.groupby("article_type")[["product_type", "sub_category"]].agg(lambda s: s.mode().iloc[0])
    key_groups = cat.groupby(["article_type", "base_colour"])["product_id"].apply(list).to_dict()
    in_cat = set(cat.raw_id)
    held = raw[raw.articleType.isin(at2type.index) & ~raw.id.isin(in_cat)].copy()
    held["key_n"] = [len(key_groups.get((a, c), [])) for a, c in zip(held.articleType, held.baseColour)]
    held = held[held.key_n >= 1]
    held["product_type"] = held.articleType.map(at2type["product_type"])
    held["sub_category"] = held.articleType.map(at2type["sub_category"])
    picks = []
    for t in TYPES:
        h = held[held.product_type == t]
        if len(h) >= n_cat:
            picks.append(("heldout", t, h.sample(n_cat, random_state=seed)))
        else:  # mũ: không còn SP held-out -> leave-one-out trên catalog
            c = cat[cat.product_type == t].copy()
            c["key_n"] = [len(key_groups.get((a, b), [])) for a, b in zip(c.article_type, c.base_colour)]
            c = c[c.key_n >= 2]
            picks.append(("loo", t, c.sample(min(n_cat, len(c)), random_state=seed)))
    need = set(int(i) for kind, _, d in picks if kind == "heldout" for i in d["id"])
    raw_bytes = read_raw_images(need)
    for kind, t, d in picks:
        d = d.reset_index(drop=True)
        n_val = int(round(len(d) * val_frac))
        for i, r in d.iterrows():
            qid = f"vq_cat_{t[:4]}_{i:03d}"
            path = qdir / f"{qid}.jpg"
            if kind == "heldout":
                Image.open(io.BytesIO(raw_bytes[int(r.id)])).convert("RGB").save(path, "JPEG", quality=95)
                gts = key_groups[(r.articleType, r.baseColour)]; excl = ""; at, bc, sc = r.articleType, r.baseColour, r.sub_category
                src = "fpi_heldout_other_product"; org = "real_image_of_heldout_FPI_product (không có trong catalog)"
            else:
                Image.open(r.img).convert("RGB").save(path, "JPEG", quality=95)
                gts = [p for p in key_groups[(r.article_type, r.base_colour)] if p != r.product_id]; excl = r.product_id
                at, bc, sc = r.article_type, r.base_colour, r.sub_category
                src = "fpi_catalog_leave_one_out"; org = "real_catalog_image, loại chính nó khỏi kết quả (leave-one-out)"
            rows.append(dict(query_id=qid, query_image=str(path.relative_to(ROOT)), gt_product_ids="|".join(gts),
                             product_type=t, sub_category=sc, article_type=at, base_colour=bc,
                             split="val" if i < n_val else "test", tier="category", source=src, hard_cross_type=False,
                             transform="none", exclude_ids=excl, origin=org))
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "eval_visual.csv", index=False)
    stats = {
        "n_queries": len(df), "by_tier": df.tier.value_counts().to_dict(),
        "by_split_tier_type": {f"{a}/{b}/{c}": int(n) for (a, b, c), n in df.groupby(["tier", "split", "product_type"]).size().items()},
        "hard_cross_type": int(df.hard_cross_type.sum()),
        "hard_cross_type_test": int(df[(df.split == "test")].hard_cross_type.sum()),
        "catalog_hard_flag_rate_by_type": cat.groupby("product_type").hard.mean().round(4).to_dict(),
        "transform_counts": df[df.tier == "instance"]["transform"].str.split("(").str[0].value_counts().to_dict(),
        "category_gt_size_median": float(df[df.tier == "category"].gt_product_ids.str.count(r"\|").add(1).median()),
        "seed": seed, "data_version": "shared_data v1 (prep_shared_data.py seed 42)",
    }
    (out_dir / "eval_visual_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1))
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    return df


def build_ood(n_per: int = 30, seed: int = 42, out_dir: Path = ROOT / "eval") -> pd.DataFrame:
    """Truy vấn NGOÀI PHẠM VI (ảnh thật FPI không thuộc 4 nhóm: Personal Care, Watches) để hiệu chỉnh τ_v."""
    raw = load_raw_meta()
    pools = {"personal_care": raw[raw.masterCategory == "Personal Care"], "watches": raw[raw.articleType == "Watches"]}
    picks = {k: v.sample(n_per, random_state=seed) for k, v in pools.items()}
    imgs = read_raw_images({int(i) for d in picks.values() for i in d.id})
    qdir = out_dir / "queries"; qdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for k, d in picks.items():
        for i, r in enumerate(d.itertuples()):
            qid = f"vq_ood_{k[:5]}_{i:03d}"; path = qdir / f"{qid}.jpg"
            Image.open(io.BytesIO(imgs[int(r.id)])).convert("RGB").save(path, "JPEG", quality=95)
            rows.append(dict(query_id=qid, query_image=str(path.relative_to(ROOT)), gt_product_ids="", product_type="ood",
                             sub_category=k, article_type=r.articleType, split="val" if i < int(n_per * 0.4) else "test",
                             tier="ood", source="fpi_out_of_scope", origin="real_image_FPI_out_of_scope"))
    df = pd.DataFrame(rows); df.to_csv(out_dir / "eval_visual_ood.csv", index=False)
    print("OOD:", df.groupby(["sub_category", "split"]).size().to_dict())
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-inst", type=int, default=100)
    ap.add_argument("--n-cat", type=int, default=50)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    build(a.n_inst, a.n_cat, seed=a.seed)
    build_ood(seed=a.seed)
