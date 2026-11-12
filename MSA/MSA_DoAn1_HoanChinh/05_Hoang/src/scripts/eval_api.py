# repo: scripts/eval_api.py
"""Đo THẬT API trên catalog Data v1 (US_30, US_37, US_38): gọi endpoint qua TestClient (in-process, không tính mạng).

- /search/image: truy vấn = ảnh FPI KHÔNG nằm trong catalog (held-out, cùng articleType đã map; 20 ảnh/nhóm cho
  footwear, clothing, accessory). Headwear: catalog đã lấy HẾT mũ của FPI → không có ảnh held-out; dùng leave-one-out
  (ảnh catalog, loại chính nó khỏi kết quả) và báo tách riêng. Đo latency p50/p95, cross_type_error@5,
  sub_category precision@5, độ chính xác type gate. Lưu ý: KHÔNG có ground truth "cùng sản phẩm" → không tính Recall@K.
- /search/text: 15 truy vấn lọc thật, kiểm tự động mọi kết quả thoả bộ lọc.
- /compare: 20 nhóm (2-3 SP cùng nhóm, seed 42), so từng ô với dữ liệu GỐC (parquet FPI / JSON ViMRHP) → % khớp.
Lệnh: python src/scripts/eval_api.py   → results/api_eval.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MSA_LOG_DIR", str(ROOT / "results" / "logs" / "api_eval"))
from fastapi.testclient import TestClient  # noqa: E402

from msa.api.main import State, create_app  # noqa: E402
from msa.api.searchers import ClipFaissSearcher  # noqa: E402
from msa.api.text_search import color_family  # noqa: E402
from msa.data import converters as C  # noqa: E402
from msa.eval.metrics import cross_type_error_at_k, latency_summary  # noqa: E402

RAW = Path(os.environ.get("MSA_RAW_DIR", "/home/claude/realdata"))
SEED = 42


def heldout_queries(cat: pd.DataFrame, per_type: int = 20) -> list[dict]:
    import pyarrow.parquet as pq
    fs = sorted(glob.glob(str(RAW / "fpi" / "data" / "*.parquet")))
    meta = C.read_fpi_metadata(fs)
    m = meta[meta.articleType.isin(C.FPI_MAP)].copy()
    m["product_type"] = m.articleType.map(lambda a: C.FPI_MAP[a][0])
    m["sub_category"] = m.articleType.map(lambda a: C.FPI_MAP[a][1])
    in_cat = {int(p[4:]) for p in cat.product_id if p.startswith("fpi_")}
    m = m[~m.id.isin(in_cat)]
    picks = []
    for pt, g in m.groupby("product_type"):
        picks.append(g.sample(min(per_type, len(g)), random_state=SEED))
    q = pd.concat(picks)
    ids = set(q.id)
    imgs = {}
    for f in fs:
        for b in pq.ParquetFile(f).iter_batches(batch_size=2000, columns=["id", "image"]):
            for r in b.to_pylist():
                if r["id"] in ids:
                    imgs[r["id"]] = r["image"]["bytes"]
    return [{"qid": f"heldout_{r.id}", "bytes": imgs[r.id], "product_type": r.product_type, "sub_category": r.sub_category,
             "exclude": None} for r in q.itertuples()]


def loo_headwear(cat: pd.DataFrame, n: int = 20) -> list[dict]:
    hw = cat[(cat.product_type == "headwear") & cat.product_id.str.startswith("fpi_")].sample(n, random_state=SEED)
    return [{"qid": f"loo_{r.product_id}", "bytes": (ROOT / "data" / r.image_paths[0]).read_bytes(),
             "product_type": "headwear", "sub_category": r.sub_category, "exclude": r.product_id} for r in hw.itertuples()]


def eval_image(client, searcher, cat, queries, k=5) -> dict:
    sub_of = cat.set_index("product_id").sub_category
    per = []
    for q in queries:
        t = time.perf_counter()
        r = client.post("/search/image", files={"file": (f"{q['qid']}.jpg", q["bytes"], "image/jpeg")},
                        data={"k": str(k + 1)})
        lat = (time.perf_counter() - t) * 1000
        b = r.json()
        items = [i for i in b["items"] if i["product_id"] != q["exclude"]][:k]
        from PIL import Image
        img = Image.open(io.BytesIO(q["bytes"])).convert("RGB")
        gate_t, gate_c = searcher.type_gate(img)
        nogate = [i for i in searcher.search(img, k=k + 1, use_gate=False) if i["product_id"] != q["exclude"]][:k]
        per.append({"qid": q["qid"], "status": r.status_code, "product_type": q["product_type"], "latency_ms": lat,
                    "server_latency_ms": b["latency_ms"], "top1_score": b["confidence"], "n_items": len(items),
                    "cte5": cross_type_error_at_k([i["product_type"] for i in items], q["product_type"], k),
                    "cte5_no_gate": cross_type_error_at_k([i["product_type"] for i in nogate], q["product_type"], k),
                    "subcat_p5": float(np.mean([sub_of[i["product_id"]] == q["sub_category"] for i in items])) if items else 0.0,
                    "gate_type": gate_t, "gate_conf": gate_c, "gate_correct": gate_t == q["product_type"],
                    "below_tau_v": b.get("error", {}).get("code") == "not_product" if b.get("error") else False})
    df = pd.DataFrame(per)

    def agg(d):
        return {"n": int(len(d)), "latency_ms_client": latency_summary(d.latency_ms), "latency_ms_server": latency_summary(d.server_latency_ms),
                "cross_type_error@5": float(d.cte5.mean()), "cross_type_error@5_no_gate": float(d.cte5_no_gate.mean()),
                "subcategory_precision@5": float(d.subcat_p5.mean()), "type_gate_accuracy": float(d.gate_correct.mean()),
                "top1_score_mean": float(d.top1_score.mean()), "n_below_tau_v": int(d.below_tau_v.sum()),
                "pct_under_1500ms": float((d.latency_ms < 1500).mean())}
    return {"overall": agg(df), "by_type": {t: agg(g) for t, g in df.groupby("product_type")}, "per_query": per}


TEXT_QUERIES = [
    ("giày thể thao", {"product_type": "footwear"}),
    ("sneaker", {"sub_category": "sneaker", "colors": ["trắng"]}),
    ("giày nữ", {"product_type": "footwear", "gender": "Women"}),
    ("dép", {"sub_category": "sandal", "colors": ["đen"]}),
    ("giày da công sở", {"sub_category": "leather_shoe", "colors": ["nâu"]}),
    ("áo thun nam", {"sub_category": "top", "gender": "Men", "include_unisex": False}),
    ("quần jean", {"sub_category": "bottom", "colors": ["xanh dương"]}),
    ("váy", {"sub_category": "dress", "gender": "Women"}),
    ("áo khoác", {"sub_category": "outerwear"}),
    ("mũ lưỡi trai", {"product_type": "headwear", "colors": ["đen"]}),
    ("mũ", {"product_type": "headwear", "gender": "Men"}),
    ("túi xách", {"sub_category": "bag", "gender": "Women", "colors": ["hồng"]}),
    ("thắt lưng", {"sub_category": "belt", "colors": ["đen", "nâu"]}),
    ("kính râm", {"sub_category": "eyewear", "gender": "Unisex", "include_unisex": True}),
    ("balo", {"product_type": "accessory", "colors": ["xám"]}),
]


def eval_text(client, cat) -> dict:
    by = cat.set_index("product_id")
    per = []
    for q, f in TEXT_QUERIES:
        t = time.perf_counter()
        b = client.post("/search/text", json={"query": q, "k": 20, "filters": f}).json()
        lat = (time.perf_counter() - t) * 1000
        viol = 0
        for it in b["items"]:
            r = by.loc[it["product_id"]]
            ok = (not f.get("product_type") or r.product_type == f["product_type"]) and \
                 (not f.get("sub_category") or r.sub_category == f["sub_category"]) and \
                 (not f.get("colors") or bool({color_family(c) for c in r.colors} & {color_family(c) for c in f["colors"]})) and \
                 (not f.get("gender") or r.gender in ({f["gender"]} | ({"Unisex"} if f.get("include_unisex", True) else set())))
            viol += not ok
        per.append({"query": q, "filters": f, "n_items": len(b["items"]), "violations": viol, "latency_ms": lat,
                    "server_latency_ms": b["latency_ms"], "top3": [i["title"] for i in b["items"][:3]]})
    return {"n_queries": len(per), "queries_all_correct": sum(p["violations"] == 0 for p in per),
            "queries_with_results": sum(p["n_items"] > 0 for p in per), "total_items": sum(p["n_items"] for p in per),
            "total_violations": sum(p["violations"] for p in per),
            "latency_ms_client": latency_summary([p["latency_ms"] for p in per]), "per_query": per,
            "note": "Catalog thật chưa có giá/size → không đo được bộ lọc giá/size trên dữ liệu thật (đã test trên dữ liệu tổng hợp)."}


def raw_truth() -> tuple[dict, dict]:
    meta = C.read_fpi_metadata(sorted(glob.glob(str(RAW / "fpi" / "data" / "*.parquet")))).set_index("id")
    vim = {}
    for fp in sorted(glob.glob(str(RAW / "vimrhp" / "Annotation" / "Fashion-*.json"))):
        for r in json.load(open(fp, encoding="utf-8")):
            v = vim.setdefault(f"shopee_{r['ProductId']}", {"title": r["ProductName"], "ratings": []})
            v["ratings"].append(r["Rating"])
    return meta, vim


def eval_compare(client, cat) -> dict:
    meta, vim = raw_truth()
    rng = random.Random(SEED)
    groups = []  # 16 nhóm SP FPI + 4 nhóm SP Shopee (ViMRHP), xen kẽ 2 và 3 SP, cùng product_type
    for src, n in (("fpi_", 16), ("shopee_", 4)):
        sub = cat[cat.product_id.str.startswith(src)]
        types = sorted(sub.product_type.unique())
        for i in range(n):
            ids = sub[sub.product_type == types[i % len(types)]].product_id.tolist()
            groups.append(rng.sample(ids, 2 if len(groups) % 2 == 0 else 3))
    per, n_cells, n_match, lats = [], 0, 0, []
    for ids in groups:
        t = time.perf_counter()
        b = client.post("/compare", json={"product_ids": ids}).json()
        lats.append((time.perf_counter() - t) * 1000)
        rows = {r["key"]: r["values"] for r in b["table"]["rows"]}
        mism = []
        for p in ids:
            if p.startswith("fpi_"):
                m = meta.loc[int(p[4:])]
                exp = {"title": m.productDisplayName, "colors": m.baseColour, "gender": m.gender, "usage": m.usage,
                       "season": m.season, "year": int(m.year) if m.year == m.year else "chưa có thông tin",
                       "price": "chưa có thông tin", "sizes": "chưa có thông tin"}
            else:
                v = vim[p]
                exp = {"title": v["title"], "rating": round(sum(v["ratings"]) / len(v["ratings"]), 3),
                       "rating_count": len(v["ratings"]), "price": "chưa có thông tin", "material": "chưa có thông tin"}
            for k, e in exp.items():
                got = rows[k][p]
                ok = (got == e) or (isinstance(e, float) and isinstance(got, (int, float)) and abs(got - e) < 1e-6)
                n_cells += 1
                n_match += ok
                if not ok:
                    mism.append({"product_id": p, "field": k, "got": got, "expected": e})
        per.append({"ids": ids, "mismatches": mism})
    return {"n_groups": len(groups), "n_cells_checked": n_cells, "n_cells_match": n_match,
            "match_rate": n_match / n_cells, "groups_100pct": sum(not p["mismatches"] for p in per),
            "latency_ms_client": latency_summary(lats), "per_group": per}


def main() -> None:
    import torch
    torch.set_num_threads(2)
    t0 = time.time()
    cat = C.read_catalog(ROOT / "data" / "processed" / "catalog_v1.parquet")
    vs = ClipFaissSearcher(cat, ROOT / "data", ROOT / "results" / "cache")
    st = State(catalog=cat, visual=vs, log_dir=str(ROOT / "results" / "logs" / "api_eval"))
    client = TestClient(create_app(st))
    client.post("/search/text", json={"query": "warmup"})  # khởi tạo TF-IDF ngoài phép đo
    queries = heldout_queries(cat) + loo_headwear(cat)
    client.post("/search/image", files={"file": ("w.jpg", queries[0]["bytes"], "image/jpeg")})  # warm-up
    img = eval_image(client, vs, cat, queries)
    out = {"data_version": "Data v1 (scripts 01/01b/02, seed 42)", "catalog_size": int(len(cat)),
           "visual_index_size": int(len(vs.index.ids)), "visual_model": ClipFaissSearcher.MODEL, "tau_v": 0.25,
           "torch_threads": 2, "cpu": os.cpu_count(),
           "note": "Latency đo trong tiến trình (TestClient) trên máy 2 CPU dùng chung với tác nhân khác.",
           "search_image": {**{k: v for k, v in img.items() if k != "per_query"}}, "search_text": eval_text(client, cat),
           "compare": eval_compare(client, cat), "elapsed_s": round(time.time() - t0, 1)}
    out["search_image"]["heldout_vs_loo"] = "footwear/clothing/accessory = ảnh held-out (không trong catalog); headwear = leave-one-out"
    json.dump(out, open(ROOT / "results" / "api_eval.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    pd.DataFrame(img["per_query"]).to_csv(ROOT / "results" / "api_eval_image_per_query.csv", index=False)
    print(json.dumps({"image": out["search_image"]["overall"], "image_by_type": {t: {k: v for k, v in d.items() if "latency" not in k}
                                                                                for t, d in out["search_image"]["by_type"].items()},
                      "text": {k: v for k, v in out["search_text"].items() if k != "per_query"},
                      "compare": {k: v for k, v in out["compare"].items() if k != "per_group"}}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
