# repo: scripts/fill_docs.py
"""Chèn các bảng sinh từ kết quả THẬT (make_tables.py) vào tài liệu, giữa cặp marker <!-- NAME --> ... <!-- /NAME -->."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "scripts"))
import make_tables as T  # noqa: E402


def put(doc: str, name: str, content: str) -> None:
    p = ROOT / doc if doc.endswith("README.md") else ROOT / "docs" / doc; s = p.read_text(encoding="utf-8")
    s2 = re.sub(rf"<!-- {name} -->.*?<!-- /{name} -->", lambda m: f"<!-- {name} -->\n{content}\n<!-- /{name} -->", s, flags=re.S)
    p.write_text(s2, encoding="utf-8")


def e2e() -> str:
    p = ROOT / "results" / "e2e_visual-only.json"
    if not p.exists():
        return "CHƯA ĐO"
    d = json.loads(p.read_text(encoding="utf-8")); v = d["visual_only"]
    return ("Chạy THẬT `--agent visual-only` (index `indexes/best` → FashionCLIP, τ_v và gate như `config.json`), 18 kịch bản visual:\n\n"
            "| Chỉ số | Giá trị |\n|---|---|\n"
            f"| TSR phần visual | **{v['tsr']:.3f}** ({round(v['tsr'] * v['n'])}/{v['n']}) |\n| Latency p50 / p95 (ms, gồm đọc ảnh + embed + gate + search) | {v['latency_ms_p50']} / {v['latency_ms_p95']} |\n"
            f"| Lỗi | {', '.join(f'{k}: {n}' for k, n in v['errors'].items()) or 'không'} |\n"
            f"| 42 kịch bản text | route `not_ready` (chưa ghép) → TSR toàn hệ thống trong file = {d['task_success_rate']} **không có ý nghĩa**, CHƯA ĐO |\n\n"
            "Khung đo đã kiểm thử bằng `--agent fake` (`results/e2e_fake.json`, chỉ để test, không phải số liệu).")


def main():
    R = T.load()
    hw = next((r.get("hardware") for r in R.values() if r.get("hardware")), {})
    head = (f"Phần cứng: {hw.get('cpu')} – {hw.get('n_cpu')} CPU, torch {hw.get('torch')} ({hw.get('torch_threads')} luồng), fp32; máy dùng chung (latency có nhiễu). "
            "Split test của `eval/eval_visual.csv`; nguồn số: `results/bench/<model>.json`, `results/bench_image_embed.csv`.\n\n")
    a = head + "**Bảng A (chính)**\n\n" + T.table_a(R) + "\n\n**Bảng A2 (theo nhóm)**\n\n" + T.table_a2(R)
    put("US_19_khao_sat_embedding_anh.md", "BANG_A_RESULTS", a)
    put("US_22_benchmark_embedding.md", "BANG_A_RESULTS", a)
    put("US_22_benchmark_embedding.md", "GATE_RESULTS", T.table_gate(R))
    put("US_22_benchmark_embedding.md", "OOD_RESULTS", T.table_ood(R))
    put("US_29_build_index.md", "BUILD_RESULTS", T.table_build())
    put("US_45_cai_tien_va_do_truoc_sau.md", "IMPR_RESULTS", T.table_impr())
    put("US_44_baseline_e2e.md", "E2E_RESULTS", e2e())
    rows = ["| Model | Macro R@5 | R@1 | R@10 | MRR@10 | CTE@5 | cat Hit@5 | cat P@5 | Embed truy vấn ms (median) |", "|---|---|---|---|---|---|---|---|---|"]
    ok = sorted([(m, r) for m, r in R.items() if r["status"] == "ok"], key=lambda x: -x[1]["test"]["macro_R@5"])
    for m, r in ok:
        t = r["test"]
        rows.append(f"| {m} | {t['macro_R@5']:.3f} | {t['R@1']:.3f} | {t['R@10']:.3f} | {t['MRR@10']:.3f} | {t['CTE@5']:.3f} | {t['cat_Hit@5']:.3f} | {t['cat_P@5']:.3f} | {r.get('query_embed_ms_median')} |")
    for m in T.ORDER:
        if m not in R or R[m]["status"] != "ok":
            rows.append(f"| {m} | CHƯA ĐO | | | | | | | |")
    put("README.md", "README_TABLE", "\n".join(rows))
    print("ok")


if __name__ == "__main__":
    main()
