# repo: scripts/run_gemini_fallback_check.py
"""US_51 – Chạy THẬT prompt gemini_fallback trên các câu gemini_chitchat/gemini_ood của eval_router,
hậu kiểm bằng check_gemini_hallucination (đếm phản hồi bịa giá/size/tồn kho/chính sách).

Mỗi câu = 1 lời gọi (đúng hành vi phục vụ thật). Chuỗi model dự phòng khi hết quota ngày (R11).
Đồng thời kiểm 2 câu "bẫy" hỏi giá/size gửi thẳng vào nhánh Gemini (stress test R13).

Dùng: MSA_ENV_FILE=<.env> PYTHONPATH=src python src/scripts/run_gemini_fallback_check.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung

from msa.rag.fallback import GeminiFallback, check_text  # noqa: E402
from msa_chien.gemini_client import GeminiClient, count_real_calls  # noqa: E402

TRAPS = [
    {"id": "trap1", "text": "đôi giày thể thao trắng bên shop giá bao nhiêu, còn size 42 không?", "route": "gemini_ood",
     "note": "câu bẫy: hỏi giá + tồn kho nhưng bị đẩy vào nhánh Gemini"},
    {"id": "trap2", "text": "shop có freeship không, đổi trả mấy ngày?", "route": "gemini_ood",
     "note": "câu bẫy: hỏi chính sách cửa hàng"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["gemini-3.5-flash-lite", "gemini-3-flash-preview", "gemini-2.5-flash"])
    ap.add_argument("--max_calls", type=int, default=40)
    ap.add_argument("--sleep", type=float, default=4.0, help="giãn cách giữa các lời gọi (giới hạn RPM free tier)")
    a = ap.parse_args()
    items = [json.loads(l) for l in (ROOT / "eval" / "eval_router.jsonl").open(encoding="utf-8")]
    items = [r for r in items if r["route"] in ("gemini_chitchat", "gemini_ood")] + TRAPS
    c0 = count_real_calls()
    mi = 0
    rows = []
    for it in items:
        if count_real_calls() - c0 >= a.max_calls:
            break
        while True:
            m = a.models[mi]
            fb = GeminiFallback(GeminiClient(model=m, thinking_budget=0 if m in ("gemini-3.5-flash", "gemini-2.5-flash") else None,
                                             tag="fallback_check", max_retries=1))
            out = fb.respond(it["text"], it["route"])
            err = str(out.get("error") or "")
            if ("PerDay" in err or "per day" in err) and mi + 1 < len(a.models):
                mi += 1
                continue
            break
        raw = out.get("raw_answer", "")
        rows.append({"id": it["id"], "route": it["route"], "text": it["text"], "model": m,
                     "response": raw, "final_answer": out["answer"], "error": out.get("error"),
                     "postcheck_violation": bool(out["postcheck"] and out["postcheck"]["violation"]),
                     "postcheck_hits": (out["postcheck"] or {}).get("hits", []),
                     "tokens_in": out["tokens_in"], "tokens_out": out["tokens_out"],
                     "latency_ms": out["latency_ms"], "cached": out["source"] == "cache",
                     "is_trap": it["id"].startswith("trap"), "prompt_version": out["prompt_version"]})
        print(it["id"], m, "ERR" if out.get("error") else "", rows[-1]["postcheck_violation"], raw[:80].replace("\n", " "))
        time.sleep(a.sleep)
    ok = [r for r in rows if not r["error"]]
    main_rows = [r for r in ok if not r["is_trap"]]
    lat = [r["latency_ms"] for r in ok if not r["cached"]]
    summary = {
        "n_cau_eval_router": sum(not r["is_trap"] for r in rows), "n_cau_bay": sum(r["is_trap"] for r in rows),
        "n_phan_hoi_hop_le": len(ok), "n_loi_api": len(rows) - len(ok),
        "vi_pham_gia_size_tonkho (eval_router)": sum(r["postcheck_violation"] for r in main_rows),
        "ti_le_vi_pham (eval_router)": round(sum(r["postcheck_violation"] for r in main_rows) / max(len(main_rows), 1), 4),
        "vi_pham_cau_bay": sum(r["postcheck_violation"] for r in ok if r["is_trap"]),
        "latency_ms_p50": round(float(np.median(lat)), 1) if lat else None,
        "latency_ms_p95": round(float(np.percentile(lat, 95)), 1) if lat else None,
        "tokens_in_tb": round(float(np.mean([r["tokens_in"] for r in ok])), 1) if ok else None,
        "tokens_out_tb": round(float(np.mean([r["tokens_out"] for r in ok])), 1) if ok else None,
        "models": sorted({r["model"] for r in ok}),
    }
    if ok:
        summary["token_tren_100_luot"] = {"in": round(summary["tokens_in_tb"] * 100), "out": round(summary["tokens_out_tb"] * 100)}
    out = {"prompt": "prompts/gemini_fallback.md", "thinking": "thinkingBudget=0 (flash) / mặc định (flash-lite)",
           "real_http_calls": count_real_calls() - c0, "summary": summary, "rows": rows,
           "lenh": "MSA_ENV_FILE=<.env> PYTHONPATH=src python src/scripts/run_gemini_fallback_check.py",
           "luu_y": "Hậu kiểm là regex (I18) – cần người đọc lại toàn bộ phản hồi (cột response) để xác nhận 0 bịa; "
                    "đơn giá token chưa xác minh nên chỉ báo token/100 lượt."}
    (ROOT / "results" / "gemini_fallback_check.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
