# repo: scripts/recheck_store_facts.py
"""Chấm lại hậu kiểm I18 (regex) trên câu trả lời Gemini ĐÃ LƯU trong results/gemini_fallback_live.json – không gọi API.
Chạy: PYTHONPATH=src python scripts/recheck_store_facts.py"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from msa.agent.router import find_store_facts  # noqa: E402

d = json.load(open(os.path.join(ROOT, "results", "gemini_fallback_live.json"), encoding="utf-8"))
out = {}
for cfg in ("A_default", "B_thinking1024"):
    rows = [r for r in d["rows"] if r["config"] == cfg and not r["error"] and not r["cached"]]
    flagged = [dict(id=r["id"], text=r["text"], facts=find_store_facts(r["answer_raw"]), answer=r["answer_raw"]) for r in rows]
    flagged = [f for f in flagged if f["facts"]]
    out[cfg] = dict(n=len(rows), flagged_regex_v2=len(flagged), flagged=flagged)
out["kiem_tay_A"] = dict(
    nguoi_kiem="tác nhân AI (vai Trung) – nhóm cần kiểm lại",
    neu_gia_size_ton_kho_khuyen_mai=0,
    khang_dinh_cua_hang_co_hang_ngoai_danh_muc=["trs_038 (đồng hồ Casio)", "r038 (khuyên tai nam châm)"],
    regex_v1_bat_nham=["r064 (ký hiệu $ trong công thức toán)"],
)
out["ghi_chu"] = ("regex v1: 1 cờ sai (r064) và bỏ sót 2 câu khẳng định cửa hàng có bán đồng hồ/khuyên tai. "
                  "regex v2: '$' phải đứng trước số + thêm mẫu 'danh_muc'. Unsupported-store-fact (kiểm tay) = 2/40 = 0.05 trên cấu hình A.")
json.dump(out, open(os.path.join(ROOT, "results", "gemini_store_fact_recheck.json"), "w"), ensure_ascii=False, indent=1)
print({k: (v["n"], v["flagged_regex_v2"]) for k, v in out.items() if isinstance(v, dict) and "n" in v})
