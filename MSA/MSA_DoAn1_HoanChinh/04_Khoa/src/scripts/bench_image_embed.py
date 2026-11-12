# repo: scripts/bench_image_embed.py
"""US_22 – Benchmark embedding ảnh trên catalog THẬT (4.593 SP FPI) + eval_visual.

Mỗi model chạy trong MỘT tiến trình riêng (để đo RAM sạch):
    python src/scripts/bench_image_embed.py --model clip_b32
Gộp kết quả:
    python src/scripts/bench_image_embed.py --aggregate
Kết quả: results/bench/<model>.json, results/per_query/<model>.csv, results/bench_image_embed.{csv,json}
Cache embedding: cache/<model>_{catalog,queries,ood}.npy (+ _ids.json) – chạy lại sẽ dùng cache.

Mọi model: cùng tiền xử lý hình học (common_preprocess), cùng FAISS IndexFlatIP (cosine trên vector L2-norm), cùng K.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung
from msa.eval import visual_metrics as M  # noqa: E402

SHARED = Path(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))
TYPES = ["footwear", "clothing", "headwear", "accessory"]
DATA_VERSION = "shared_data v1 (prep_shared_data.py seed 42)"
SEED = 42
K_LIST = (1, 5, 10)

# Prompt zero-shot cho type gate (I19) – nhiều prompt/nhóm, lấy max cosine
TYPE_PROMPTS = {
    "footwear": ["a photo of shoes", "a photo of sneakers", "a photo of sandals", "a photo of flip flops",
                 "a photo of high heels", "a photo of formal leather shoes", "a photo of boots"],
    "clothing": ["a photo of a t-shirt", "a photo of a shirt", "a photo of a dress", "a photo of jeans",
                 "a photo of trousers", "a photo of shorts", "a photo of a jacket", "a photo of a person wearing clothes",
                 "a photo of a kurta", "a photo of a skirt"],
    "headwear": ["a photo of a cap", "a photo of a baseball cap", "a photo of a hat", "a photo of a beanie",
                 "a photo of a bucket hat", "a photo of a headband"],
    "accessory": ["a photo of a handbag", "a photo of a backpack", "a photo of a bag", "a photo of a belt",
                  "a photo of sunglasses", "a photo of a wallet", "a photo of a clutch"],
}


def rss_mb() -> float:
    import psutil

    return psutil.Process().memory_info().rss / 1e6


def peak_rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e3  # Linux: KB


def hardware() -> dict:
    cpu = ""
    try:
        for line in open("/proc/cpuinfo", encoding="utf-8"):
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip(); break
    except OSError:
        pass
    import torch

    return {"cpu": cpu, "n_cpu": os.cpu_count(), "torch_threads": torch.get_num_threads(), "python": platform.python_version(),
            "torch": torch.__version__, "platform": platform.platform()}


def load_catalog() -> pd.DataFrame:
    cat = pd.read_parquet(SHARED / "catalog_fpi.parquet", columns=["product_id", "product_type", "sub_category", "image_paths", "specs"])
    cat["img"] = cat["image_paths"].map(lambda a: str(SHARED / a[0]))
    cat["article_type"] = cat["specs"].map(lambda s: s.get("articleType"))
    return cat.reset_index(drop=True)


def cached_embed(emb, name: str, kind: str, paths: list[str], ids: list[str], batch: int = 32) -> tuple[np.ndarray, float]:
    """Embed có cache .npy; trả về (X, ms/ảnh khi embed theo batch – NaN nếu lấy từ cache)."""
    f = ROOT / "cache" / f"{name}_{kind}.npy"
    fid = ROOT / "cache" / f"{name}_{kind}_ids.json"
    ftime = ROOT / "cache" / f"{name}_{kind}_timing.json"
    if f.exists() and fid.exists() and json.loads(fid.read_text(encoding="utf-8")) == ids:
        tm = json.loads(ftime.read_text(encoding="utf-8")) if ftime.exists() else {}
        return np.load(f), float(tm.get("ms_per_img", float("nan")))
    # Embed theo khối 512 ảnh, lưu từng khối (part) để CHẠY TIẾP được nếu tiến trình bị ngắt/OOM
    total_s, n_done, parts = 0.0, 0, []
    for pi, s in enumerate(range(0, len(paths), 512)):
        fp = ROOT / "cache" / f"{name}_{kind}_part{pi:02d}.npy"
        fpt = ROOT / "cache" / f"{name}_{kind}_part{pi:02d}.json"
        meta = {"ids": ids[s : s + 512]}
        if fp.exists() and fpt.exists() and json.loads(fpt.read_text(encoding="utf-8")).get("ids") == meta["ids"]:
            parts.append(np.load(fp)); total_s += json.loads(fpt.read_text(encoding="utf-8"))["seconds"]; n_done += len(meta["ids"]); continue
        t = time.perf_counter()
        Xp = emb.embed(paths[s : s + 512], batch_size=batch)
        meta["seconds"] = time.perf_counter() - t
        np.save(fp, Xp.astype(np.float32)); fpt.write_text(json.dumps(meta), encoding="utf-8")
        parts.append(Xp); total_s += meta["seconds"]; n_done += len(meta["ids"])
        print(f"[{name}/{kind}] {n_done}/{len(paths)} ảnh, {total_s:.0f}s (tổng thời gian embed các khối)", flush=True)
    X = np.concatenate(parts) if parts else np.zeros((0, 1), np.float32)
    ms = total_s * 1000 / max(1, len(paths))
    np.save(f, X.astype(np.float32)); fid.write_text(json.dumps(ids), encoding="utf-8")
    ftime.write_text(json.dumps({"ms_per_img": ms, "total_s": total_s, "n": len(paths)}), encoding="utf-8")
    for pi in range((len(paths) + 511) // 512):  # dọn các khối tạm
        for ext in (".npy", ".json"):
            (ROOT / "cache" / f"{name}_{kind}_part{pi:02d}{ext}").unlink(missing_ok=True)
    return X, ms


def search(index, Q: np.ndarray, k: int):
    D, I = index.search(np.ascontiguousarray(Q, dtype=np.float32), k)
    return D, I


def eval_rankings(qdf: pd.DataFrame, I: np.ndarray, D: np.ndarray, cat: pd.DataFrame, k_eval: int = 10) -> pd.DataFrame:
    """Tính độ đo từng truy vấn. I đã lấy dư để loại exclude_ids."""
    pids = cat["product_id"].to_numpy(); ptypes = cat["product_type"].to_numpy(); psubs = cat["sub_category"].to_numpy()
    rows = []
    for qi, q in enumerate(qdf.itertuples()):
        excl = set(str(q.exclude_ids).split("|")) if isinstance(q.exclude_ids, str) and q.exclude_ids else set()
        keep = [(j, s) for j, s in zip(I[qi], D[qi]) if j >= 0 and pids[j] not in excl][:k_eval]
        ranked = [pids[j] for j, _ in keep]; rtypes = [ptypes[j] for j, _ in keep]; rsubs = [psubs[j] for j, _ in keep]
        rel = set(str(q.gt_product_ids).split("|"))
        r = dict(query_id=q.query_id, tier=q.tier, split=q.split, product_type=q.product_type, hard=bool(q.hard_cross_type),
                 top1_score=float(keep[0][1]) if keep else float("nan"), top5_ids="|".join(ranked[:5]))
        for k in K_LIST:
            r[f"R@{k}"] = M.recall_at_k(ranked, rel, k) if q.tier == "instance" else M.hit_at_k(ranked, rel, k)
        r["MRR@10"] = M.mrr(ranked, rel, 10)
        r["NDCG@10"] = M.ndcg_at_k(ranked, rel, 10)
        r["P@5"] = M.precision_at_k(ranked, rel, 5)
        r["CTE@5"] = M.cross_type_error_at_k(rtypes, q.product_type, 5)
        r["SubP@5"] = sum(1 for s in rsubs[:5] if s == q.sub_category) / 5.0
        r["rank"] = next((i + 1 for i, p in enumerate(ranked) if p in rel), 0)
        rows.append(r)
    return pd.DataFrame(rows)


def summarize(pq: pd.DataFrame, prefix: str = "") -> dict:
    out = {}
    inst = pq[(pq.tier == "instance")]
    catq = pq[(pq.tier == "category")]
    for k in K_LIST:
        out[f"{prefix}R@{k}"] = inst[f"R@{k}"].mean()
    out[f"{prefix}MRR@10"] = inst["MRR@10"].mean()
    out[f"{prefix}NDCG@10"] = inst["NDCG@10"].mean()
    for t in TYPES:
        out[f"{prefix}R@5_{t}"] = inst[inst.product_type == t]["R@5"].mean()
    out[f"{prefix}macro_R@5"] = float(np.mean([out[f"{prefix}R@5_{t}"] for t in TYPES]))
    out[f"{prefix}CTE@5"] = inst["CTE@5"].mean()
    out[f"{prefix}R@5_hard"] = inst[inst.hard]["R@5"].mean() if inst.hard.any() else float("nan")
    out[f"{prefix}CTE@5_hard"] = inst[inst.hard]["CTE@5"].mean() if inst.hard.any() else float("nan")
    out[f"{prefix}cat_Hit@5"] = catq["R@5"].mean()
    out[f"{prefix}cat_P@5"] = catq["P@5"].mean()
    out[f"{prefix}cat_SubP@5"] = catq["SubP@5"].mean()
    out[f"{prefix}cat_CTE@5"] = catq["CTE@5"].mean()
    for t in TYPES:
        out[f"{prefix}cat_P@5_{t}"] = catq[catq.product_type == t]["P@5"].mean()
    return {k: (None if pd.isna(v) else round(float(v), 4)) for k, v in out.items()}


# ----------------------------------------------------------------------------- type gate
def gate_scores(emb, Xcat: np.ndarray, cat: pd.DataFrame, Q: np.ndarray, mode: str) -> np.ndarray:
    """Trả về ma trận xác suất (n_query, 4) theo TYPES. mode = 'zeroshot' (text prompt) | 'centroid'."""
    if mode == "zeroshot":
        S = []
        for t in TYPES:
            T = emb.embed_text(TYPE_PROMPTS[t])
            S.append((Q @ T.T).max(axis=1))
        S = np.stack(S, 1) * 100.0
    else:
        C = np.stack([Xcat[cat.product_type.to_numpy() == t].mean(0) for t in TYPES])
        C = C / np.linalg.norm(C, axis=1, keepdims=True)
        S = (Q @ C.T) * 50.0
    S = S - S.max(1, keepdims=True)
    P = np.exp(S); return P / P.sum(1, keepdims=True)


def gated_search(Xcat: np.ndarray, cat: pd.DataFrame, Q: np.ndarray, P: np.ndarray, tau: float, kk: int):
    """Lọc catalog theo nhóm dự đoán nếu conf ≥ tau; ngược lại tìm toàn bộ."""
    import faiss

    types = cat.product_type.to_numpy()
    full = faiss.IndexFlatIP(Xcat.shape[1]); full.add(Xcat)
    sub_idx = {}
    for t in TYPES:
        ids = np.where(types == t)[0]
        ix = faiss.IndexFlatIP(Xcat.shape[1]); ix.add(Xcat[ids]); sub_idx[t] = (ix, ids)
    D = np.full((len(Q), kk), -1.0, dtype=np.float32); I = np.full((len(Q), kk), -1, dtype=np.int64)
    for i in range(len(Q)):
        j = int(P[i].argmax())
        if P[i, j] >= tau:
            ix, ids = sub_idx[TYPES[j]]
            d, ii = ix.search(Q[i : i + 1], min(kk, len(ids)))
            n = d.shape[1]; D[i, :n] = d[0]; I[i, :n] = ids[ii[0]]
        else:
            d, ii = full.search(Q[i : i + 1], kk); D[i] = d[0]; I[i] = ii[0]
    return D, I


# ----------------------------------------------------------------------------- run one model
def run_model(name: str, batch: int = 32, lat_n: int = 20, lat_rep: int = 3) -> dict:
    sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung
    from msa.embed.image_embedders import get_embedder, set_threads

    set_threads(2)
    import faiss
    import torch

    torch.manual_seed(SEED); np.random.seed(SEED)
    (ROOT / "results" / "bench").mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "per_query").mkdir(parents=True, exist_ok=True)
    res: dict = {"model": name, "data_version": DATA_VERSION, "seed": SEED, "eval_file": "eval/eval_visual.csv",
                 "preprocess": "RGB -> pad vuông nền trắng -> resize bicubic về input_size -> chuẩn hoá mean/std của model",
                 "index": "faiss.IndexFlatIP (cosine, vector L2-normalized)", "status": "running"}
    out_json = ROOT / "results" / "bench" / f"{name}.json"
    try:
        rss0 = rss_mb(); t0 = time.perf_counter()
        emb = get_embedder(name)
        res["load_s"] = round(time.perf_counter() - t0, 2)
        res["rss_after_load_mb"] = round(rss_mb(), 1); res["rss_model_delta_mb"] = round(rss_mb() - rss0, 1)
        res.update({f"info_{k}": v for k, v in emb.info().items()})
        res["weights_fp32_visual_mb"] = round(getattr(emb, "n_params_visual", 0) * 4 / 1e6, 1)
        res["weights_fp32_total_mb"] = round(getattr(emb, "n_params", 0) * 4 / 1e6, 1)
        res["hardware"] = hardware()

        cat = load_catalog()
        qdf = pd.read_csv(ROOT / "eval" / "eval_visual.csv", keep_default_na=False)
        ood = pd.read_csv(ROOT / "eval" / "eval_visual_ood.csv", keep_default_na=False)
        Xcat, ms_cat = cached_embed(emb, name, "catalog", cat.img.tolist(), cat.product_id.tolist(), batch)
        res["catalog_embed_ms_per_img_batch"] = None if np.isnan(ms_cat) else round(ms_cat, 2)
        res["catalog_embed_total_s"] = None if np.isnan(ms_cat) else round(ms_cat * len(cat) / 1000, 1)
        Q, _ = cached_embed(emb, name, "queries", [str(ROOT / p) for p in qdf.query_image], qdf.query_id.tolist(), batch)
        QO, _ = cached_embed(emb, name, "ood", [str(ROOT / p) for p in ood.query_image], ood.query_id.tolist(), batch)

        # ---- index + truy vấn
        t = time.perf_counter(); index = faiss.IndexFlatIP(Xcat.shape[1]); index.add(Xcat)
        res["index_build_ms"] = round((time.perf_counter() - t) * 1000, 2)
        res["index_size_mb"] = round(Xcat.nbytes / 1e6, 2); res["n_catalog"] = int(len(Xcat))
        D, I = search(index, Q, 20)
        pq = eval_rankings(qdf, I, D, cat)
        pq.to_csv(ROOT / "results" / "per_query" / f"{name}.csv", index=False)
        res["test"] = summarize(pq[pq.split == "test"]); res["val"] = summarize(pq[pq.split == "val"])
        res["all"] = summarize(pq)

        # ---- latency (median của lat_rep lần trên lat_n ảnh, batch=1)
        paths = [str(ROOT / p) for p in qdf.query_image[:lat_n]]
        emb.embed(paths[:2], batch_size=1)  # warmup
        per = []
        for _ in range(lat_rep):
            for p in paths:
                t = time.perf_counter(); emb.embed([p], batch_size=1); per.append((time.perf_counter() - t) * 1000)
        res["query_embed_ms_median"] = round(statistics.median(per), 2)
        res["query_embed_ms_p95"] = round(float(np.percentile(per, 95)), 2)
        res["latency_n_measurements"] = len(per)
        sp = []
        for _ in range(lat_rep):
            for i in range(min(200, len(Q))):
                t = time.perf_counter(); index.search(Q[i : i + 1], 10); sp.append((time.perf_counter() - t) * 1000)
        res["faiss_search_ms_median"] = round(statistics.median(sp), 4)
        res["faiss_search_ms_p95"] = round(float(np.percentile(sp, 95)), 4)

        # ---- OOD (ngoài phạm vi) – phân biệt bằng top-1 cosine
        Do, _ = search(index, QO, 1)
        ins = pq[(pq.tier == "instance") & (pq.split == "test")]["top1_score"].to_numpy()
        ins_cat = pq[(pq.tier == "category") & (pq.split == "test")]["top1_score"].to_numpy()
        oo = Do[ood.split.to_numpy() == "test", 0]
        res["ood"] = {
            "top1_inscope_instance_p05_p50": [round(float(np.percentile(ins, 5)), 4), round(float(np.median(ins)), 4)],
            "top1_inscope_category_p05_p50": [round(float(np.percentile(ins_cat, 5)), 4), round(float(np.median(ins_cat)), 4)],
            "top1_ood_p50_p95": [round(float(np.median(oo)), 4), round(float(np.percentile(oo, 95)), 4)],
            "auroc_category_vs_ood": round(M.auroc(ins_cat.tolist(), oo.tolist()), 4),
        }
        # ngưỡng chọn trên VAL: giữ 95% truy vấn category trong phạm vi
        val_cat = pq[(pq.tier == "category") & (pq.split == "val")]["top1_score"].to_numpy()
        tau_v = float(np.percentile(val_cat, 5))
        res["ood"]["tau_v_val_p05"] = round(tau_v, 4)
        res["ood"]["test_inscope_category_kept"] = round(float((ins_cat >= tau_v).mean()), 4)
        res["ood"]["test_ood_rejected"] = round(float((oo < tau_v).mean()), 4)
        res["ood"]["test_ood_rejected_at_default_0.25"] = round(float((oo < 0.25).mean()), 4)
        res["ood"]["test_inscope_category_kept_at_default_0.25"] = round(float((ins_cat >= 0.25).mean()), 4)

        # ---- type gate (I19): zero-shot nếu có text tower, centroid cho mọi model
        res["gate"] = {}
        modes = (["zeroshot"] if emb.has_text else []) + ["centroid"]
        qtypes = qdf.product_type.to_numpy()
        for mode in modes:
            P = gate_scores(emb, Xcat, cat, Q, mode)
            pred = np.array(TYPES)[P.argmax(1)]
            g = {"acc_test": round(float((pred == qtypes)[qdf.split == "test"].mean()), 4),
                 "acc_val": round(float((pred == qtypes)[qdf.split == "val"].mean()), 4)}
            best = None
            for tau in (0.0, 0.5, 0.7, 0.9):
                Dg, Ig = gated_search(Xcat, cat, Q, P, tau, 20)
                pg = eval_rankings(qdf, Ig, Dg, cat)
                sv = summarize(pg[pg.split == "val"])
                if best is None or sv["R@5"] > best[1]["R@5"] + 1e-9:
                    best = (tau, sv, pg)
            tau, _, pg = best
            g["tau_chosen_on_val"] = tau
            g["test"] = summarize(pg[pg.split == "test"])
            pg.to_csv(ROOT / "results" / "per_query" / f"{name}__gate_{mode}.csv", index=False)
            res["gate"][mode] = g
        res["peak_rss_mb"] = round(peak_rss_mb(), 1)
        res["status"] = "ok"
    except Exception as ex:  # ghi lỗi thật, không bịa số
        import traceback

        res["status"] = "error"; res["error"] = f"{type(ex).__name__}: {ex}"[:800]; res["trace"] = traceback.format_exc()[-2000:]
    out_json.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: res.get(k) for k in ("model", "status", "error", "catalog_embed_total_s", "query_embed_ms_median")}, ensure_ascii=False))
    if res["status"] == "ok":
        print("TEST:", json.dumps(res["test"], ensure_ascii=False))
    return res


def aggregate() -> pd.DataFrame:
    rows = []
    for f in sorted((ROOT / "results" / "bench").glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        row = {"model": r["model"], "display": r.get("info_display"), "status": r["status"], "error": r.get("error", ""),
               "dim": r.get("info_dim"), "has_text": r.get("info_has_text"), "params_visual_M": round(r.get("info_n_params_visual", 0) / 1e6, 1) if r.get("info_n_params_visual") else None,
               "weights_fp32_visual_mb": r.get("weights_fp32_visual_mb"), "weights_fp32_total_mb": r.get("weights_fp32_total_mb"),
               "rss_after_load_mb": r.get("rss_after_load_mb"), "peak_rss_mb": r.get("peak_rss_mb"),
               "catalog_embed_ms_per_img_batch32": r.get("catalog_embed_ms_per_img_batch"), "catalog_embed_total_s": r.get("catalog_embed_total_s"),
               "query_embed_ms_median_bs1": r.get("query_embed_ms_median"), "query_embed_ms_p95_bs1": r.get("query_embed_ms_p95"),
               "faiss_search_ms_median": r.get("faiss_search_ms_median"), "index_size_mb": r.get("index_size_mb")}
        if r["status"] == "ok":
            row.update({f"test_{k}": v for k, v in r["test"].items()})
            row.update({f"ood_{k}": (v if not isinstance(v, list) else "/".join(map(str, v))) for k, v in r["ood"].items()})
            for mode, g in r.get("gate", {}).items():
                row[f"gate_{mode}_acc_test"] = g["acc_test"]; row[f"gate_{mode}_tau"] = g["tau_chosen_on_val"]
                for k in ("R@1", "R@5", "macro_R@5", "MRR@10", "CTE@5", "R@5_hard", "cat_P@5", "cat_CTE@5"):
                    row[f"gate_{mode}_test_{k}"] = g["test"][k]
        rows.append(row)
    df = pd.DataFrame(rows)
    if "test_macro_R@5" in df:
        df = df.sort_values("test_macro_R@5", ascending=False)
    df.to_csv(ROOT / "results" / "bench_image_embed.csv", index=False)
    (ROOT / "results" / "bench_image_embed.json").write_text(df.to_json(orient="records", force_ascii=False, indent=1), encoding="utf-8")
    print(df[[c for c in ["model", "status", "test_R@1", "test_R@5", "test_R@10", "test_MRR@10", "test_macro_R@5", "test_CTE@5", "test_cat_P@5", "query_embed_ms_median_bs1"] if c in df]].to_string())
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--batch", type=int, default=32)
    a = ap.parse_args()
    if a.aggregate:
        aggregate()
    else:
        run_model(a.model, batch=a.batch)
