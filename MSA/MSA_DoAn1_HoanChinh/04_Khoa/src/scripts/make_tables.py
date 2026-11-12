# repo: scripts/make_tables.py
"""Sinh bảng Markdown từ kết quả THẬT (results/bench/*.json, results/improvements_*.json, results/build_index_*.json)
để dán vào tài liệu (Bảng A, A2, gate, OOD, trước/sau). Không có số -> ghi CHƯA ĐO.

    python src/scripts/make_tables.py  -> results/tables.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ORDER = ["resnet50", "clip_b32", "clip_b16", "openclip_b32_laion2b", "siglip_b16", "fashionclip", "marqo_fashionsiglip", "dinov2_s"]


def f(v, nd=3):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "–"
    if isinstance(v, (int, float)):
        return f"{v:.{nd}f}" if isinstance(v, float) else str(v)
    return str(v)


def load():
    out = {}
    for m in ORDER:
        p = ROOT / "results" / "bench" / f"{m}.json"
        if p.exists():
            out[m] = json.loads(p.read_text())
    return out


def table_a(R):
    lines = ["| Model | R@1 | R@5 | R@10 | MRR@10 | NDCG@10 | Macro R@5 | CTE@5 | cat Hit@5 | cat P@5 | Embed truy vấn ms (median / p95, bs=1) | Embed catalog ms/ảnh (bs=32) | FAISS search ms (median) | RSS sau nạp (MB) | Peak RSS (MB) | Trọng số visual fp32 (MB) | Index (MB) |",
             "|---|" + "---|" * 16]
    for m in ORDER:
        r = R.get(m)
        if not r:
            lines.append(f"| {m} | CHƯA ĐO |" + " |" * 15); continue
        if r["status"] != "ok":
            lines.append(f"| {m} | LỖI: {r.get('error', '')[:80]} |" + " |" * 15); continue
        t = r["test"]
        lines.append(f"| {m} | {f(t['R@1'])} | {f(t['R@5'])} | {f(t['R@10'])} | {f(t['MRR@10'])} | {f(t['NDCG@10'])} | {f(t['macro_R@5'])} | {f(t['CTE@5'])} | {f(t['cat_Hit@5'])} | {f(t['cat_P@5'])} | "
                     f"{f(r.get('query_embed_ms_median'), 1)} / {f(r.get('query_embed_ms_p95'), 1)} | {f(r.get('catalog_embed_ms_per_img_batch'), 1)} | {f(r.get('faiss_search_ms_median'), 3)} | {f(r.get('rss_after_load_mb'), 0)} | {f(r.get('peak_rss_mb'), 0)} | {f(r.get('weights_fp32_visual_mb'), 0)} | {f(r.get('index_size_mb'), 1)} |")
    return "\n".join(lines)


def table_a2(R):
    lines = ["| Model | R@5 giày | R@5 quần áo | R@5 mũ | R@5 phụ kiện | Macro R@5 | CTE@5 | R@5 (hard_cross_type) | CTE@5 (hard) | cat P@5 giày | cat P@5 quần áo | cat P@5 mũ | cat P@5 phụ kiện | cat SubP@5 | R@5 ảnh ngoài đời |",
             "|---|" + "---|" * 14]
    for m in ORDER:
        r = R.get(m)
        if not r or r["status"] != "ok":
            continue
        t = r["test"]
        lines.append(f"| {m} | {f(t['R@5_footwear'])} | {f(t['R@5_clothing'])} | {f(t['R@5_headwear'])} | {f(t['R@5_accessory'])} | {f(t['macro_R@5'])} | {f(t['CTE@5'])} | {f(t['R@5_hard'])} | {f(t['CTE@5_hard'])} | "
                     f"{f(t['cat_P@5_footwear'])} | {f(t['cat_P@5_clothing'])} | {f(t['cat_P@5_headwear'])} | {f(t['cat_P@5_accessory'])} | {f(t['cat_SubP@5'])} | CHƯA ĐO |")
    return "\n".join(lines)


def table_gate(R):
    lines = ["| Model | Gate | Độ chính xác gate (test) | τ chọn trên val | R@5 trước → sau | Macro R@5 trước → sau | CTE@5 trước → sau | R@5 hard trước → sau | cat P@5 trước → sau | cat CTE@5 trước → sau |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for m in ORDER:
        r = R.get(m)
        if not r or r["status"] != "ok":
            continue
        t = r["test"]
        for mode, g in r.get("gate", {}).items():
            s = g["test"]
            lines.append(f"| {m} | {mode} | {f(g['acc_test'])} | {g['tau_chosen_on_val']} | {f(t['R@5'])} → {f(s['R@5'])} | {f(t['macro_R@5'])} → {f(s['macro_R@5'])} | {f(t['CTE@5'])} → {f(s['CTE@5'])} | {f(t['R@5_hard'])} → {f(s['R@5_hard'])} | {f(t['cat_P@5'])} → {f(s['cat_P@5'])} | {f(t['cat_CTE@5'])} → {f(s['cat_CTE@5'])} |")
    return "\n".join(lines)


def table_ood(R):
    lines = ["| Model | top-1 cos instance (p05/p50) | top-1 cos category (p05/p50) | top-1 cos OOD (p50/p95) | AUROC category vs OOD | τ_v (p05 val) | Giữ in-scope (test) | Loại OOD (test) | Loại OOD @ τ_v=0,25 | Giữ in-scope @ 0,25 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for m in ORDER:
        r = R.get(m)
        if not r or r["status"] != "ok":
            continue
        o = r["ood"]
        j = lambda a: "/".join(f(x) for x in a)  # noqa: E731
        lines.append(f"| {m} | {j(o['top1_inscope_instance_p05_p50'])} | {j(o['top1_inscope_category_p05_p50'])} | {j(o['top1_ood_p50_p95'])} | {f(o['auroc_category_vs_ood'])} | {f(o['tau_v_val_p05'])} | {f(o['test_inscope_category_kept'])} | {f(o['test_ood_rejected'])} | {f(o['test_ood_rejected_at_default_0.25'])} | {f(o['test_inscope_category_kept_at_default_0.25'])} |")
    return "\n".join(lines)


def table_impr():
    out = []
    for p in sorted((ROOT / "results").glob("improvements_*.json")):
        d = json.loads(p.read_text()); rows = d["rows"]; b = rows["baseline"]
        out.append(f"\n**Model: `{d['model']}`** – split test\n")
        out.append("| Biến thể | R@1 | R@5 | MRR@10 | Macro R@5 | CTE@5 | R@5 hard | cat Hit@5 | cat P@5 | ΔR@5 | ΔMacro R@5 | ΔMRR | Δcat P@5 | Ghi chú |")
        out.append("|---|" + "---|" * 13)
        for k, r in rows.items():
            note = ", ".join(f"{a}={r[a]}" for a in ("lambda_chosen_on_val", "tau_chosen_on_val", "gate_acc_test") if a in r)
            d5 = lambda key: f"{float(r[key]) - float(b[key]):+.3f}"  # noqa: E731
            out.append(f"| {k} | {f(r['R@1'])} | {f(r['R@5'])} | {f(r['MRR@10'])} | {f(r['macro_R@5'])} | {f(r['CTE@5'])} | {f(r['R@5_hard'])} | {f(r['cat_Hit@5'])} | {f(r['cat_P@5'])} | {d5('R@5')} | {d5('macro_R@5')} | {d5('MRR@10')} | {d5('cat_P@5')} | {note} |")
    return "\n".join(out) if out else "CHƯA ĐO"


def table_build():
    out = ["| Model | Số SP | Dim | Embed catalog (s) | Từ cache? | Build tổng (s) | File index (MB) | Truy vấn e2e ms median / p95 (embed+gate+search) | Search-only ms median | Số lần đo |", "|---|---|---|---|---|---|---|---|---|---|"]
    for p in sorted((ROOT / "results").glob("build_index_*.json")):
        r = json.loads(p.read_text())
        out.append(f"| {r['model']} | {r['n_items']} | {r['dim']} | {r['embed_s']} | {r['embed_from_cache']} | {r['build_total_s']} | {r['index_file_mb']} | {r['query_e2e_ms_median']} / {r['query_e2e_ms_p95']} | {r['search_only_ms_median']} | {r['n_latency_measurements']} |")
    return "\n".join(out)


def main():
    R = load()
    hw = next((r.get("hardware") for r in R.values() if r.get("hardware")), {})
    md = [f"Phần cứng: {hw.get('cpu', '?')} – {hw.get('n_cpu', '?')} CPU, torch {hw.get('torch', '?')} ({hw.get('torch_threads', '?')} luồng); máy DÙNG CHUNG với 4 tác nhân khác nên latency có nhiễu do tải nền.",
          "Dữ liệu: shared_data v1 (prep_shared_data.py seed 42); eval: eval/eval_visual.csv (split test: 240 instance + 120 category); seed 42.",
          "\n### Bảng A – kết quả chính (split test)\n", table_a(R), "\n### Bảng A2 – theo nhóm (split test)\n", table_a2(R),
          "\n### Type gate I19 (split test, τ chọn trên val)\n", table_gate(R), "\n### Ngưỡng τ_v / ngoài phạm vi (split test)\n", table_ood(R),
          "\n### Build index (US_29)\n", table_build(), "\n### Cải tiến trước/sau (US_45)\n", table_impr()]
    s = "\n".join(md)
    (ROOT / "results" / "tables.md").write_text(s, encoding="utf-8")
    print(s)


if __name__ == "__main__":
    main()
