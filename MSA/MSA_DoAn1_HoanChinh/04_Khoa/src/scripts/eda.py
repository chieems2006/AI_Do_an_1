# repo: scripts/eda.py
"""US_09 – EDA trên dữ liệu THẬT (shared_data v1): catalog FPI 4.593 SP, 44.072 dòng FPI gốc, ViMRHP 509 SP/11.009 review.

Chạy:  python src/scripts/eda.py   -> docs/US_09_eda/{*.png, eda_stats.json, eda_report.md}
"""
from __future__ import annotations
import os

import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SHARED = Path(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))
RAW_GLOB = (os.environ.get("MSA_RAW_DIR", "/home/claude/realdata") + "/fpi/data/*.parquet")
OUT = ROOT / "docs" / "US_09_eda"
VI_CHARS = set("ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")
COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3", "#8C8C8C"]


def has_vi(text: str) -> bool:
    """Heuristic ngôn ngữ: có ít nhất một ký tự có dấu tiếng Việt."""
    return any(c in VI_CHARS for c in str(text).lower())


def words(s) -> int:
    return len(str(s).split()) if s is not None else 0


def save(fig, name: str, charts: list):
    fig.tight_layout(); fig.savefig(OUT / name, dpi=110); plt.close(fig); charts.append(name)


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    charts: list[str] = []
    st: dict = {"data_version": "shared_data v1 (prep_shared_data.py seed 42)"}

    # ------------------------------------------------------------- catalog FPI
    cat = pd.read_parquet(SHARED / "catalog_fpi.parquet")
    cat["article_type"] = cat.specs.map(lambda s: s.get("articleType"))
    cat["season"] = cat.specs.map(lambda s: s.get("season"))
    cat["usage"] = cat.specs.map(lambda s: s.get("usage"))
    cat["year"] = cat.specs.map(lambda s: s.get("year"))
    cat["colour"] = cat.colors.map(lambda a: a[0] if len(a) else None)
    st["catalog"] = {
        "n": len(cat), "by_type": cat.product_type.value_counts().to_dict(),
        "by_sub": cat.groupby(["product_type", "sub_category"]).size().rename(lambda x: x).to_dict(),
        "n_article_types": int(cat.article_type.nunique()),
        "by_gender": cat.gender.value_counts().to_dict(),
        "top_colours": cat.colour.value_counts().head(15).to_dict(), "n_colours": int(cat.colour.nunique()),
        "by_season": cat.season.value_counts(dropna=False).to_dict(), "by_usage": cat.usage.value_counts(dropna=False).to_dict(),
        "year_min_max": [float(np.nanmin(cat.year.astype(float))), float(np.nanmax(cat.year.astype(float)))],
        "brands_n": int(cat.brand.nunique()),
    }
    st["catalog"]["by_sub"] = {f"{a}/{b}": int(n) for (a, b), n in cat.groupby(["product_type", "sub_category"]).size().items()}
    # thiếu trường
    def missing(col):
        v = cat[col]
        return int(sum(1 for x in v if x is None or (isinstance(x, float) and np.isnan(x)) or (hasattr(x, "__len__") and not isinstance(x, str) and len(x) == 0) or (isinstance(x, str) and not x.strip())))
    st["catalog"]["missing_rate"] = {c: round(missing(c) / len(cat), 4) for c in ["title", "brand", "price", "description", "colors", "sizes", "rating", "reviews", "season", "usage"]}
    # tên
    cat["title_words"] = cat.title.map(words)
    st["catalog"]["title_words"] = {"mean": round(cat.title_words.mean(), 2), "median": float(cat.title_words.median()), "min": int(cat.title_words.min()), "max": int(cat.title_words.max())}
    dup = cat.title.str.lower().str.strip().duplicated(keep=False)
    st["catalog"]["dup_title_rows"] = int(dup.sum()); st["catalog"]["dup_title_groups"] = int(cat[dup].title.str.lower().nunique())
    st["catalog"]["lang_title_vi_rate"] = round(cat.title.map(has_vi).mean(), 4)
    # ảnh
    sizes, fbytes, white = Counter(), [], []
    for p in cat.image_paths.map(lambda a: SHARED / a[0]):
        im = Image.open(p); sizes[im.size] += 1; fbytes.append(p.stat().st_size)
        a = np.asarray(im.convert("L"), dtype=np.uint8); white.append(float((a > 240).mean()))
    st["catalog"]["image_sizes"] = {f"{w}x{h}": n for (w, h), n in sizes.most_common()}
    st["catalog"]["image_kb"] = {"mean": round(np.mean(fbytes) / 1024, 2), "p05": round(np.percentile(fbytes, 5) / 1024, 2), "p95": round(np.percentile(fbytes, 95) / 1024, 2)}
    cat["white_ratio"] = white
    st["catalog"]["white_bg_ratio"] = {"mean": round(float(np.mean(white)), 3), "p05": round(float(np.percentile(white, 5)), 3), "p50": round(float(np.median(white)), 3),
                                       "share_lt_0.2": round(float((np.array(white) < 0.2).mean()), 4)}
    st["catalog"]["white_bg_by_type"] = cat.groupby("product_type").white_ratio.mean().round(3).to_dict()
    # hình người mẫu (ước lượng thô): quần áo thường có người mặc -> tỉ lệ nền trắng thấp hơn
    # ------------------------------------------------------------- FPI gốc 44.072 dòng
    import pyarrow.parquet as pq

    raw = pd.concat([pq.read_table(f, columns=[c for c in pq.read_schema(f).names if c != "image"]).to_pandas() for f in sorted(glob.glob(RAW_GLOB))])
    st["fpi_raw"] = {"n": len(raw), "by_master": raw.masterCategory.value_counts().to_dict(), "n_article_types": int(raw.articleType.nunique()),
                     "top_article_types": raw.articleType.value_counts().head(25).to_dict(), "by_gender": raw.gender.value_counts().to_dict(),
                     "missing": {c: int(raw[c].isna().sum()) for c in raw.columns},
                     "headwear_rows": raw[raw.articleType.isin(["Caps", "Hat", "Headband"])].articleType.value_counts().to_dict(),
                     "footwear_boot_rows": int(raw.productDisplayName.str.contains(r"\bboots?\b", case=False, na=False).sum()),
                     "beanie_rows_by_name": int(raw.productDisplayName.str.contains("beanie", case=False, na=False).sum()),
                     "bucket_rows_by_name": int(raw.productDisplayName.str.contains("bucket", case=False, na=False).sum())}
    st["fpi_raw"]["catalog_coverage"] = round(len(cat) / len(raw), 4)

    # ------------------------------------------------------------- ViMRHP
    vi = [json.loads(l) for l in open(SHARED / "vimrhp_fashion_products.jsonl", encoding="utf-8")]
    vdf = pd.DataFrame(vi)
    revs = pd.DataFrame([dict(pid=p["product_id"], sub=p["vimrhp_subcategory"], **r) for p in vi for r in p.get("reviews", [])])
    revs["n_words"] = revs.text.map(words)
    revs["n_chars"] = revs.text.map(lambda s: len(str(s)))
    revs["is_vi"] = revs.text.map(has_vi)
    revs["template"] = revs.text.str.contains(r"Đúng với mô tả:|Chất liệu:|Màu sắc:", regex=True, na=False)
    vdf["n_reviews"] = vdf.reviews.map(len)
    vdf["title_words"] = vdf.title.map(words)
    st["vimrhp"] = {
        "n_products": len(vdf), "n_reviews": len(revs), "by_sub": vdf.vimrhp_subcategory.value_counts().to_dict(),
        "in_scope_products_excl_DongHo": int((vdf.vimrhp_subcategory != "DongHo").sum()),
        "reviews_per_product": {"mean": round(vdf.n_reviews.mean(), 2), "median": float(vdf.n_reviews.median()), "min": int(vdf.n_reviews.min()), "max": int(vdf.n_reviews.max())},
        "rating_dist": {int(k): int(v) for k, v in revs.rating.value_counts().sort_index().items()},
        "rating_mean": round(revs.rating.mean(), 3),
        "review_words": {"mean": round(revs.n_words.mean(), 2), "median": float(revs.n_words.median()), "p95": float(revs.n_words.quantile(0.95))},
        "review_vi_rate": round(revs.is_vi.mean(), 4),
        "review_empty_or_lt3_words": round(float((revs.n_words < 3).mean()), 4),
        "review_template_rate": round(float(revs.template.mean()), 4),
        "review_dup_text_rate": round(float(revs.text.str.strip().str.lower().duplicated().mean()), 4),
        "title_words": {"mean": round(vdf.title_words.mean(), 2), "median": float(vdf.title_words.median())},
        "has_image_url_rate": round(float(vdf.image_urls.map(lambda a: len(a) > 0).mean()), 4),
        "fields": sorted(vdf.columns.tolist()),
        "missing_fields_vs_schema": ["description", "price", "sizes", "specs", "colors"],
    }
    st["vimrhp"]["rating_by_sub"] = revs.groupby("sub").rating.mean().round(3).to_dict()

    # ------------------------------------------------------------- biểu đồ
    # 1. phân bố nhóm/sub_category catalog
    fig, ax = plt.subplots(figsize=(9, 4.5))
    s = cat.groupby(["product_type", "sub_category"]).size().sort_values()
    ax.barh([f"{a}/{b}" for a, b in s.index], s.values, color=[COLORS[["footwear", "clothing", "headwear", "accessory"].index(a)] for a, _ in s.index])
    for i, v in enumerate(s.values):
        ax.text(v + 10, i, str(v), va="center", fontsize=8)
    ax.set_title("Catalog FPI (4.593 SP): số SP theo product_type / sub_category"); ax.set_xlabel("Số sản phẩm")
    save(fig, "01_catalog_type_sub.png", charts)
    # 2. articleType FPI gốc top 25 (đánh dấu loại có trong catalog)
    fig, ax = plt.subplots(figsize=(9, 6))
    top = raw.articleType.value_counts().head(25)[::-1]
    incat = set(cat.article_type)
    ax.barh(top.index, top.values, color=["#55A868" if a in incat else "#BBBBBB" for a in top.index])
    ax.set_title("FPI gốc 44.072 dòng: top-25 articleType (xanh = có trong catalog)"); ax.set_xlabel("Số dòng")
    save(fig, "02_fpi_raw_article_types.png", charts)
    # 3. giới tính theo nhóm
    fig, ax = plt.subplots(figsize=(8, 4))
    g = pd.crosstab(cat.product_type, cat.gender)
    g.plot(kind="bar", stacked=True, ax=ax, color=COLORS[: g.shape[1]]); ax.set_title("Giới tính theo product_type (catalog)"); ax.set_ylabel("Số SP"); ax.tick_params(axis="x", rotation=0)
    save(fig, "03_gender_by_type.png", charts)
    # 4. màu top 15
    fig, ax = plt.subplots(figsize=(8, 4.5))
    c = cat.colour.value_counts().head(15)[::-1]
    ax.barh(c.index, c.values, color="#4C72B0"); ax.set_title("Top-15 màu gốc (baseColour) trong catalog"); ax.set_xlabel("Số SP")
    save(fig, "04_colours_top15.png", charts)
    # 5. season / usage
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    cat.season.fillna("NA").value_counts().plot(kind="bar", ax=axs[0], color="#DD8452"); axs[0].set_title("Mùa (season)"); axs[0].tick_params(axis="x", rotation=0)
    cat.usage.fillna("NA").value_counts().plot(kind="bar", ax=axs[1], color="#8172B3"); axs[1].set_title("Mục đích dùng (usage)"); axs[1].tick_params(axis="x", rotation=30)
    save(fig, "05_season_usage.png", charts)
    # 6. ảnh: tỉ lệ nền trắng theo nhóm + kích thước file
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for i, t in enumerate(["footwear", "clothing", "headwear", "accessory"]):
        axs[0].hist(cat[cat.product_type == t].white_ratio, bins=30, alpha=0.55, label=t, color=COLORS[i])
    axs[0].set_title("Tỉ lệ pixel gần trắng (>240) mỗi ảnh"); axs[0].legend(); axs[0].set_xlabel("tỉ lệ")
    axs[1].hist(np.array(fbytes) / 1024, bins=40, color="#55A868"); axs[1].set_title(f"Dung lượng ảnh (KB) – mọi ảnh {list(st['catalog']['image_sizes'])[0]}"); axs[1].set_xlabel("KB")
    save(fig, "06_image_whitebg_filesize.png", charts)
    # 7. độ dài tên SP (catalog vs ViMRHP) + độ dài review
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    axs[0].hist(cat.title_words, bins=range(0, 20), alpha=0.6, label="FPI (EN)"); axs[0].hist(vdf.title_words, bins=range(0, 40), alpha=0.6, label="ViMRHP (VI)")
    axs[0].set_title("Số từ trong tên sản phẩm"); axs[0].legend()
    axs[1].hist(revs.n_words.clip(upper=150), bins=50, color="#C44E52"); axs[1].set_title("ViMRHP: số từ mỗi review (cắt ở 150)"); axs[1].set_xlabel("số từ")
    save(fig, "07_title_review_length.png", charts)
    # 8. rating ViMRHP
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    rd = revs.rating.value_counts().sort_index(); axs[0].bar(rd.index.astype(str), rd.values, color="#DD8452"); axs[0].set_title("ViMRHP: phân bố rating (11.009 review)")
    for i, v in enumerate(rd.values):
        axs[0].text(i, v, str(v), ha="center", va="bottom", fontsize=8)
    vs = vdf.vimrhp_subcategory.value_counts(); axs[1].bar(vs.index, vs.values, color=["#BBBBBB" if x == "DongHo" else "#4C72B0" for x in vs.index]); axs[1].set_title("ViMRHP: số SP theo nhóm (xám = ngoài phạm vi)"); axs[1].tick_params(axis="x", rotation=30)
    save(fig, "08_vimrhp_rating_sub.png", charts)
    # 9. lưới ảnh mẫu mỗi nhóm
    fig, axs = plt.subplots(4, 8, figsize=(10, 6))
    for r, t in enumerate(["footwear", "clothing", "headwear", "accessory"]):
        smp = cat[cat.product_type == t].sample(8, random_state=42)
        for cidx, p in enumerate(smp.image_paths):
            axs[r, cidx].imshow(Image.open(SHARED / p[0])); axs[r, cidx].axis("off")
        axs[r, 0].set_title(t, fontsize=8, loc="left")
    fig.suptitle("Ảnh mẫu FPI (60×80 px gốc) – seed 42")
    save(fig, "09_sample_images.png", charts)
    st["charts"] = charts
    (OUT / "eda_stats.json").write_text(json.dumps(st, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(st, ensure_ascii=False, indent=1, default=str)[:6000])
    return st


if __name__ == "__main__":
    main()
