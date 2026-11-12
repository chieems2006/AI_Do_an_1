# repo: scripts/tau_v_analysis.py
"""Phân tích ngưỡng τ_v (top-1 cosine) từ cache embedding + per_query (số THẬT). -> results/tau_v_analysis.json
Hai cách chọn trên VAL: (a) p05 top-1 của truy vấn category (giữ 95 % SP khác cùng loại);
(b) max top-1 của truy vấn OOD val + 0,01 (vừa đủ loại hết OOD val). Báo cáo tỉ lệ giữ/loại trên TEST."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[2]
out = {}
ood = pd.read_csv(ROOT / "eval" / "eval_visual_ood.csv", keep_default_na=False)
for f in sorted((ROOT / "results" / "bench").glob("*.json")):
    m = f.stem; pq = pd.read_csv(ROOT / "results" / "per_query" / f"{m}.csv")
    Xc = np.load(ROOT / "cache" / f"{m}_catalog.npy"); Xo = np.load(ROOT / "cache" / f"{m}_ood.npy")
    s_ood = (Xo @ Xc.T).max(1); ov, ot = s_ood[ood.split == "val"], s_ood[ood.split == "test"]
    t = pq[pq.split == "test"]; v = pq[pq.split == "val"]
    taus = {"a_p05_category_val": float(np.percentile(v[v.tier == "category"].top1_score, 5)), "b_max_ood_val+0.01": float(ov.max() + 0.01), "default_0.25": 0.25}
    out[m] = {k: {"tau": round(tau, 4), "test_instance_kept": round(float((t[t.tier == "instance"].top1_score >= tau).mean()), 4),
                  "test_category_kept": round(float((t[t.tier == "category"].top1_score >= tau).mean()), 4),
                  "test_ood_rejected": round(float((ot < tau).mean()), 4)} for k, tau in taus.items()}
(ROOT / "results" / "tau_v_analysis.json").write_text(json.dumps(out, indent=1))
for m, d in out.items(): print(m, json.dumps(d))
