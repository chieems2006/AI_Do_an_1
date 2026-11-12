# repo: scripts/llm_gateway_live.py
"""US_50 – Gọi THẬT 10 request mẫu tới Gemini qua LLMGateway, đo latency/token theo 3 cấu hình thinking,
rồi lặp lại để đo cache hit. Kết quả: results/llm_gateway_live.json (không chứa key).

Lệnh: python src/scripts/llm_gateway_live.py --env-file <đường dẫn .env chứa GEMINI_API_KEY> [--rpm 3]
Ngân sách: ~30 lời gọi API (+ retry khi 429). Free tier đo được: 5 request/phút/project/model.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung
from msa.eval.metrics import latency_summary  # noqa: E402
from msa.llm_gateway import LLMGateway, load_env_file  # noqa: E402

SYSTEM = ("Bạn là trợ lý mua sắm thời trang của cửa hàng (giày dép, quần áo, mũ, phụ kiện). Trả lời tiếng Việt, "
          "ngắn gọn (tối đa 3 câu). KHÔNG nêu giá, size, tồn kho hay thông số của sản phẩm cụ thể vì bạn không có dữ liệu "
          "cửa hàng; nếu người dùng hỏi những điều đó, hãy mời họ dùng chức năng tìm kiếm/so sánh của cửa hàng.")
PROMPTS = [  # (id, nhóm route kỳ vọng, câu) – câu do tác nhân viết (origin=agent_written)
    ("p01", "chitchat", "Chào bạn, bạn là ai vậy?"),
    ("p02", "chitchat", "Cảm ơn nhé, bạn tư vấn dễ thương ghê!"),
    ("p03", "chitchat", "Hôm nay mình buồn quá, mặc gì cho vui lên được không?"),
    ("p04", "ood", "Thủ đô của nước Úc là thành phố nào?"),
    ("p05", "ood", "Viết giúp mình một đoạn code Python sắp xếp danh sách."),
    ("p06", "ood", "Giá vàng hôm nay bao nhiêu?"),
    ("p07", "hard", "Đi đám cưới buổi tối ở ngoài trời thì nam nên phối áo và giày thế nào?"),
    ("p08", "hard", "Da mình ngăm, nên chọn mũ lưỡi trai màu gì cho hợp?"),
    ("p09", "hard", "Giày da nên bảo quản thế nào vào mùa nồm ẩm ở miền Bắc?"),
    ("p10", "guardrail", "Đôi sneaker trắng của shop giá bao nhiêu và còn size 42 không?"),
]
CONFIGS = {"default": {}, "budget0": {"thinking_budget": 0}, "level_low": {"thinking_level": "low"}}


def summarize(recs: list[dict]) -> dict:
    ok = [r for r in recs if r["source"] in ("gemini", "cache") and not r["error"]]
    n = len(recs)

    def mean(k):
        return sum(r[k] for r in ok) / len(ok) if ok else None
    s = {"n": n, "n_success": len(ok), "n_fallback": sum(r["source"] == "fallback" for r in recs),
         "n_cache_hit": sum(bool(r["cached"]) for r in recs), "total_retries": sum(r["retries"] for r in recs),
         "latency_ms_end_to_end": latency_summary([r["latency_ms"] for r in ok]),
         "api_latency_ms": latency_summary([r["api_latency_ms"] for r in ok if r.get("api_latency_ms") is not None
                                            and not r["cached"]]),
         "mean_tokens_in": mean("tokens_in"), "mean_tokens_out": mean("tokens_out"),
         "mean_tokens_thinking": mean("tokens_thinking")}
    if ok:
        s["tokens_per_100_requests"] = {k: round(100 * mean(k)) for k in ("tokens_in", "tokens_out", "tokens_thinking")}
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", required=False)
    ap.add_argument("--rpm", type=float, default=3.0)
    ap.add_argument("--configs", default="default,budget0,level_low")
    ap.add_argument("--out", default=str(ROOT / "results" / "llm_gateway_live.json"))
    a = ap.parse_args()
    if a.env_file:
        load_env_file(a.env_file)
    cache_path = ROOT / "results" / "cache" / "llm_live_cache.sqlite"
    if cache_path.exists():
        cache_path.unlink()  # đo sạch: cache rỗng lúc bắt đầu
    gw = LLMGateway(cache_path=str(cache_path), rpm=a.rpm, max_retries=5, mock=False,
                    log_path=str(ROOT / "results" / "logs" / "llm_live_calls.jsonl"))
    out = {"model": gw.model, "rpm_limit_client": a.rpm, "system_prompt": SYSTEM, "started": time.strftime("%Y-%m-%d %H:%M:%S"),
           "prompts": [{"id": i, "kind": k, "text": t, "origin": "agent_written"} for i, k, t in PROMPTS],
           "passes": {}}
    keep = ("source", "cached", "tokens_in", "tokens_out", "tokens_thinking", "latency_ms", "api_latency_ms", "wait_ms",
            "error", "retries", "finish_reason", "model_version")
    for cfg in a.configs.split(","):
        recs = []
        for pid, kind, text in PROMPTS:
            r = gw.generate(text, system=SYSTEM, **CONFIGS[cfg])
            rec = {"id": pid, "kind": kind, **{k: r.get(k) for k in keep}, "answer": r["answer"][:400]}
            recs.append(rec)
            print(cfg, json.dumps({k: rec[k] for k in ("id", "source", "tokens_in", "tokens_out", "tokens_thinking",
                                                       "latency_ms", "api_latency_ms", "wait_ms", "retries", "error")}, ensure_ascii=False), flush=True)
        out["passes"][cfg] = {"generation_config": CONFIGS[cfg], "records": recs, "summary": summarize(recs)}
    # Lặp lại cấu hình đầu tiên → phải trúng cache (0 lời gọi API)
    first = a.configs.split(",")[0]
    calls_before = gw.stats.api_calls
    recs = []
    for pid, kind, text in PROMPTS:
        r = gw.generate(text, system=SYSTEM, **CONFIGS[first])
        recs.append({"id": pid, "kind": kind, **{k: r.get(k) for k in keep}})
    out["passes"][f"{first}_repeat_cache"] = {"records": recs, "summary": summarize(recs),
                                               "api_calls_during_pass": gw.stats.api_calls - calls_before}
    out["gateway_stats"] = gw.stats.as_dict()
    out["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v["summary"] for k, v in out["passes"].items()}, ensure_ascii=False, indent=1))
    print(json.dumps(out["gateway_stats"], ensure_ascii=False))


if __name__ == "__main__":
    main()
