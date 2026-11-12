# repo: scripts/run_improvements.py
"""US_45 – Đo TRƯỚC/SAU các cải tiến visual (I1 crop, I2 TTA, I3 adapter, I19 type gate) trên eval_visual (split test).

    python src/scripts/run_improvements.py --model clip_b16

Dùng embedding cache của bench (cache/<model>_*.npy); I1 cần embed lại catalog + truy vấn đã crop (cache riêng).
Siêu tham số chỉ chọn trên split val; số báo cáo là split test. Kết quả: results/improvements_<model>.{json,csv}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "src" / "scripts"))
import bench_image_embed as B  # noqa: E402
from build_eval_visual import TRANSFORMS, apply_transform  # noqa: E402
from msa.embed.image_embedders import get_embedder, l2n, set_threads  # noqa: E402
from msa.search.improvements import LinearAdapter, bbox_crop, embed_tta_hflip  # noqa: E402

KEYS = ["R@1", "R@5", "R@10", "MRR@10", "macro_R@5", "CTE@5", "R@5_hard", "cat_Hit@5", "cat_P@5", "cat_CTE@5",
        "R@5_footwear", "R@5_clothing", "R@5_headwear", "R@5_accessory"]


def evaluate(Xcat, Q, qdf, cat, split="test"):
    import faiss

    ix = faiss.IndexFlatIP(Xcat.shape[1]); ix.add(np.ascontiguousarray(Xcat, dtype=np.float32))
    D, I = ix.search(np.ascontiguousarray(Q, dtype=np.float32), 20)
    pq = B.eval_rankings(qdf, I, D, cat)
    return B.summarize(pq[pq.split == split]), pq


def cache_or(name: str, fn):
    f = ROOT / "cache" / f"{name}.npy"
    if f.exists():
        return np.load(f)
    X = fn(); np.save(f, X.astype(np.float32)); return X


def main(model: str, n_train: int = 800, with_crop: bool = False):
    set_threads(2)
    emb = get_embedder(model)
    cat = B.load_catalog()
    qdf = pd.read_csv(ROOT / "eval" / "eval_visual.csv", keep_default_na=False)
    Xcat = np.load(ROOT / "cache" / f"{model}_catalog.npy")
    Q = np.load(ROOT / "cache" / f"{model}_queries.npy")
    qpaths = [str(ROOT / p) for p in qdf.query_image]
    rows = {}
    base, _ = evaluate(Xcat, Q, qdf, cat)
    rows["baseline"] = base

    # ---- I2: TTA lật ngang (chỉ phía truy vấn)
    Qt = cache_or(f"{model}_queries_tta", lambda: embed_tta_hflip(emb, qpaths))
    rows["I2_tta_hflip"], _ = evaluate(Xcat, Qt, qdf, cat)

    # ---- I3: adapter tuyến tính học trên SP KHÔNG thuộc eval (không trùng test lẫn val)
    used = set("|".join(qdf.gt_product_ids).split("|")) | set(qdf.exclude_ids)
    pool = cat[~cat.product_id.isin(used)].sample(n_train, random_state=7).reset_index(drop=True)
    rng = np.random.default_rng(7)
    def make_train():
        ims = []
        for i, p in enumerate(pool.img):
            im, _ = apply_transform(Image.open(p), TRANSFORMS[i % len(TRANSFORMS)], rng); ims.append(im)
        return emb.embed(ims)
    A = cache_or(f"{model}_adapter_train_aug_seed7_n{n_train}", make_train)
    idx = cat.reset_index().set_index("product_id").loc[pool.product_id, "index"].to_numpy()
    Bt = Xcat[idx]
    best = None
    for lam in (0.1, 0.3, 1.0, 3.0, 10.0):
        ad = LinearAdapter(lam).fit(A, Bt)
        sv, _ = evaluate(Xcat, ad.transform(Q), qdf, cat, split="val")
        score = sv["R@5"] + sv["cat_P@5"]
        if best is None or score > best[0] + 1e-9:
            best = (score, lam, ad)
    _, lam, ad = best
    rows["I3_linear_adapter"], _ = evaluate(Xcat, ad.transform(Q), qdf, cat)
    rows["I3_linear_adapter"]["lambda_chosen_on_val"] = lam
    (ROOT / "results" / "adapters").mkdir(parents=True, exist_ok=True)
    ad.save(ROOT / "results" / "adapters" / f"{model}_linear_adapter.npz")

    # ---- I1: crop theo nền trắng (cả catalog và truy vấn)
    if with_crop:  # tốn 1 lượt embed lại toàn catalog -> chỉ chạy khi có --with-crop
        Xc = cache_or(f"{model}_catalog_crop", lambda: emb.embed([bbox_crop(p) for p in cat.img], batch_size=16))
        Qc = cache_or(f"{model}_queries_crop", lambda: emb.embed([bbox_crop(p) for p in qpaths]))
        rows["I1_bbox_crop"], _ = evaluate(Xc, Qc, qdf, cat)
    else:
        # I1 chỉ phía truy vấn (catalog giữ nguyên) – rẻ, đo được ngay
        Qc = cache_or(f"{model}_queries_crop", lambda: emb.embed([bbox_crop(p) for p in qpaths]))
        rows["I1_bbox_crop_query_only"], _ = evaluate(Xcat, Qc, qdf, cat)

    # ---- I19: type gate (lấy từ bench, τ chọn trên val)
    bj = json.loads((ROOT / "results" / "bench" / f"{model}.json").read_text(encoding="utf-8"))
    for mode, g in bj.get("gate", {}).items():
        rows[f"I19_type_gate_{mode}"] = {**g["test"], "tau_chosen_on_val": g["tau_chosen_on_val"], "gate_acc_test": g["acc_test"]}

    # ---- I19 biến thể: logistic regression trên embedding catalog (loại SP xuất hiện trong eval)
    from sklearn.linear_model import LogisticRegression

    tr = ~cat.product_id.isin(used)
    lr = LogisticRegression(max_iter=2000, C=10.0, class_weight="balanced").fit(Xcat[tr.to_numpy()], cat.product_type[tr])
    P = lr.predict_proba(Q)[:, [list(lr.classes_).index(t) for t in B.TYPES]]
    pred = np.array(B.TYPES)[P.argmax(1)]
    bestg = None
    for tau in (0.0, 0.5, 0.7, 0.9):
        Dg, Ig = B.gated_search(Xcat, cat, Q, P, tau, 20)
        pg = B.eval_rankings(qdf, Ig, Dg, cat)
        sv = B.summarize(pg[pg.split == "val"])
        if bestg is None or sv["R@5"] > bestg[1] + 1e-9:
            bestg = (tau, sv["R@5"], pg)
    rows["I19_type_gate_logreg"] = {**B.summarize(bestg[2][bestg[2].split == "test"]), "tau_chosen_on_val": bestg[0],
                                    "gate_acc_test": round(float((pred == qdf.product_type.to_numpy())[qdf.split == "test"].mean()), 4)}

    # ---- tổ hợp: TTA + adapter (adapter áp lên embedding TTA)
    rows["I2+I3"], _ = evaluate(Xcat, ad.transform(Qt), qdf, cat)

    df = pd.DataFrame(rows).T
    cols = [c for c in KEYS if c in df.columns] + [c for c in df.columns if c not in KEYS]
    df = df[cols]
    for c in KEYS:
        if c in df:
            df[f"Δ{c}"] = (df[c].astype(float) - float(base[c])).round(4)
    df.index.name = "variant"
    df.to_csv(ROOT / "results" / f"improvements_{model}.csv")
    out = {"model": model, "split": "test", "data_version": B.DATA_VERSION, "adapter_train": {"n": n_train, "seed": 7,
           "pool": "SP catalog không xuất hiện trong eval_visual (val+test)", "transforms": TRANSFORMS}, "rows": rows}
    (ROOT / "results" / f"improvements_{model}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print(df[["R@1", "R@5", "MRR@10", "macro_R@5", "CTE@5", "cat_P@5", "ΔR@5", "Δmacro_R@5", "Δcat_P@5"]].to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--n-train", type=int, default=800)
    ap.add_argument("--with-crop", action="store_true")
    a = ap.parse_args(); main(a.model, a.n_train, a.with_crop)
