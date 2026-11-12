"""Tác nhân 1 – chuẩn bị dữ liệu dùng chung (bản tạm) từ nguồn thật.
- Fashion Product Images (small, HF ashraq/fashion-product-images-small) -> catalog 4 nhóm + ảnh
- ViMRHP Fashion (HF trucmtnguyen/ViMRHP, CC BY-NC-ND 4.0) -> sản phẩm + review tiếng Việt
Mapping product_type/sub_category ở đây là TẠM; taxonomy chính thức do Trung (US_49) chốt.
"""
import glob, io, json, os, collections
import pandas as pd, pyarrow.parquet as pq
SEED = 42
OUT = os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data")
RAW = os.environ.get("MSA_RAW_DIR", "/home/claude/realdata")

MAP = {  # articleType -> (product_type, sub_category tạm)
 "Casual Shoes": ("footwear","sneaker"), "Sports Shoes": ("footwear","sneaker"),
 "Formal Shoes": ("footwear","leather_shoe"), "Heels": ("footwear","heel_flat*"), "Flats": ("footwear","heel_flat*"),
 "Sandals": ("footwear","sandal"), "Sports Sandals": ("footwear","sandal"), "Flip Flops": ("footwear","sandal"),
 "Tshirts": ("clothing","top"), "Shirts": ("clothing","top"), "Tops": ("clothing","top"), "Sweatshirts": ("clothing","top"),
 "Sweaters": ("clothing","top"), "Kurtas": ("clothing","top"), "Jackets": ("clothing","outerwear"), "Blazers": ("clothing","outerwear"),
 "Rain Jacket": ("clothing","outerwear"), "Jeans": ("clothing","bottom"), "Shorts": ("clothing","bottom"), "Trousers": ("clothing","bottom"),
 "Track Pants": ("clothing","bottom"), "Skirts": ("clothing","bottom"), "Capris": ("clothing","bottom"), "Leggings": ("clothing","bottom"),
 "Dresses": ("clothing","dress"), "Jumpsuit": ("clothing","dress"),
 "Caps": ("headwear","cap"), "Hat": ("headwear","wide_brim*"), "Headband": ("headwear","unknown"),
 "Handbags": ("accessory","bag"), "Backpacks": ("accessory","bag"), "Clutches": ("accessory","bag"), "Duffel Bag": ("accessory","bag"),
 "Laptop Bag": ("accessory","bag"), "Messenger Bag": ("accessory","bag"), "Belts": ("accessory","belt"), "Sunglasses": ("accessory","eyewear"),
}
QUOTA = {"footwear": 1400, "clothing": 2200, "accessory": 700, "headwear": 10_000}  # headwear: lấy hết

def main():
    fs = sorted(glob.glob(f"{RAW}/fpi/data/*.parquet"))
    df = pd.concat([pq.read_table(f, columns=[c for c in pq.read_schema(f).names if c != "image"]).to_pandas() for f in fs])
    df = df[df.articleType.isin(MAP)].copy()
    df["product_type"] = df.articleType.map(lambda a: MAP[a][0]); df["sub_category"] = df.articleType.map(lambda a: MAP[a][1])
    picked = []
    for pt, g in df.groupby("product_type"):
        q = QUOTA[pt]
        if len(g) <= q: picked.append(g); continue
        # phân tầng theo articleType, tỉ lệ thuận nhưng mỗi loại tối thiểu 40
        per = (g.articleType.value_counts(normalize=True) * q).clip(lower=40).round().astype(int)
        parts = [g[g.articleType == a].sample(min(n, (g.articleType == a).sum()), random_state=SEED) for a, n in per.items()]
        picked.append(pd.concat(parts).sample(frac=1, random_state=SEED).head(q))
    cat = pd.concat(picked)
    ids = set(cat.id.astype(int))
    os.makedirs(f"{OUT}/fpi_images", exist_ok=True)
    for f in fs:
        for b in pq.ParquetFile(f).iter_batches(batch_size=2000, columns=["id", "image"]):
            for r in b.to_pylist():
                if r["id"] in ids:
                    open(f"{OUT}/fpi_images/{r['id']}.jpg", "wb").write(r["image"]["bytes"])
    rows = []
    for r in cat.itertuples():
        rows.append(dict(product_id=f"fpi_{r.id}", title=r.productDisplayName, category=f"{r.masterCategory}/{r.subCategory}/{r.articleType}",
            brand=(r.productDisplayName or "").split(" ")[0], price=None, currency=None, colors=[r.baseColour] if r.baseColour else [],
            sizes=[], description=None, specs={"season": r.season, "usage": r.usage, "year": r.year, "articleType": r.articleType},
            image_paths=[f"fpi_images/{r.id}.jpg"], rating=None, rating_count=None, reviews=[], source="fashion_product_images_small",
            source_url="https://huggingface.co/datasets/ashraq/fashion-product-images-small", license="[cần xác minh] – bản gốc Kaggle paramaggarwal/fashion-product-images-dataset",
            product_type=r.product_type, sub_category=r.sub_category, gender=r.gender, size_system="none", view_type="studio", variant_id=None, language="en"))
    out = pd.DataFrame(rows); out.to_parquet(f"{OUT}/catalog_fpi.parquet", index=False)
    # ViMRHP Fashion
    rev = []
    for s in ["train", "dev", "test"]:
        rev += json.load(open(f"{RAW}/vimrhp/Annotation/Fashion-{s}.json"))
    prods = {}
    for r in rev:
        p = prods.setdefault(r["ProductId"], dict(product_id=f"shopee_{r['ProductId']}", title=r["ProductName"], vimrhp_subcategory=r["SubCategory"],
            image_urls=r.get("ProductImage") or [], source_url=(r.get("ProductUrl") or "").split("?")[0], reviews=[]))
        p["reviews"].append(dict(comment_id=r["CommentId"], rating=r["Rating"], text=r["Comment"], detail_rating=r.get("DetailRating"),
            date=r.get("CommentDate"), helpfulness=r.get("Helpfulness_Score")))
    with open(f"{OUT}/vimrhp_fashion_products.jsonl", "w") as f:
        for p in prods.values(): f.write(json.dumps(p, ensure_ascii=False) + "\n")
    stats = dict(fpi_by_type=out.product_type.value_counts().to_dict(), fpi_by_sub={f"{a}/{b}": int(n) for (a, b), n in out.groupby(["product_type", "sub_category"]).size().items()},
        fpi_total=len(out), fpi_source_rows_total=int(sum(pq.ParquetFile(f).metadata.num_rows for f in fs)),
        vimrhp_products=len(prods), vimrhp_reviews=len(rev), vimrhp_by_sub=collections.Counter(p["vimrhp_subcategory"] for p in prods.values()))
    json.dump(stats, open(f"{OUT}/stats.json", "w"), ensure_ascii=False, indent=1, default=str); print(json.dumps(stats, ensure_ascii=False, indent=1, default=str))

if __name__ == "__main__":
    main()
