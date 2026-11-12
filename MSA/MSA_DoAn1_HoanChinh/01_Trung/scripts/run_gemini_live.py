# repo: scripts/run_gemini_live.py
"""US_41 – Đo THẬT nhánh Gemini end-to-end (Router -> Agent -> Gemini -> hậu kiểm) trên các câu router chuyển sang gemini_*.

Chạy:  MSA_GEMINI_KEY_FILE=<file .env> PYTHONPATH=src python scripts/run_gemini_live.py --model gemini-3.5-flash-lite --max-a 40 --max-b 10
- Cấu hình A: không đặt thinkingConfig (mặc định của model).
- Cấu hình B: thinkingBudget=1024 (bật suy nghĩ) trên tập con – so sánh token/latency.
- Cache: chạy lại 10 câu đầu của A qua cache (0 lời gọi API) để đo latency khi trúng cache.
Ghi: results/gemini_fallback_live.json (+ từng câu trả lời).
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from eval_router import SETS, load, session_of  # noqa: E402
from msa.agent.gemini_client import GeminiRestClient  # noqa: E402
from msa.agent.router import Agent, Router, find_store_facts  # noqa: E402

GEMINI = {"gemini_chitchat", "gemini_ood"}
CACHE = os.path.join(ROOT, "results", "cache", "gemini_cache.sqlite")


class Recorder:
    """Bọc client để giữ lại output thô (token thinking...) của lần gọi gần nhất."""

    def __init__(self, client: GeminiRestClient):
        self.c, self.last = client, None

    def generate(self, prompt: str, system: str | None = None, **kw):
        self.last = self.c.generate(prompt, system=system, **kw)
        return self.last


def pct(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (k - lo), 1)


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if not r["error"] and not r["cached"]]
    lat = [r["latency_ms_e2e"] for r in ok]
    tin = [r["tokens_in"] for r in ok]
    tout = [r["tokens_out"] for r in ok]
    tth = [r["tokens_thinking"] for r in ok]
    return dict(
        n_rows=len(rows), n_ok_api=len(ok), n_error=sum(1 for r in rows if r["error"]), n_cached=sum(1 for r in rows if r["cached"]),
        latency_ms_p50=pct(lat, 0.5), latency_ms_p95=pct(lat, 0.95), latency_ms_mean=round(statistics.mean(lat), 1) if lat else None,
        tokens_in_mean=round(statistics.mean(tin), 1) if tin else None, tokens_out_mean=round(statistics.mean(tout), 1) if tout else None,
        tokens_thinking_mean=round(statistics.mean(tth), 1) if tth else None,
        tokens_total_mean=round(statistics.mean([a + b + c for a, b, c in zip(tin, tout, tth)]), 1) if ok else None,
        store_fact_raw=sum(1 for r in ok if r["store_facts_raw"]), store_fact_after_postcheck=sum(1 for r in ok if r["store_facts_final"]),
        store_fact_raw_ids=[r["id"] for r in ok if r["store_facts_raw"]],
        finish_reasons={fr: sum(1 for r in ok if r["finish_reason"] == fr) for fr in {r["finish_reason"] for r in ok}},
    )


def run(items: list[dict], client: GeminiRestClient, use_cache: bool, sleep_s: float, label: str) -> list[dict]:
    rec = Recorder(client)
    agent = Agent(router=Router(), llm=rec)
    rows = []
    for ex in items:
        rec.last = None
        orig = rec.generate
        rec.generate = (lambda p, system=None, _o=orig, **kw: _o(p, system=system, use_cache=use_cache))  # type: ignore
        t0 = time.perf_counter()
        resp = agent.handle(ex["text"], None, session_of(ex))
        e2e = (time.perf_counter() - t0) * 1000
        rec.generate = orig  # type: ignore
        raw = rec.last or {}
        rows.append(dict(id=ex["id"], set=ex["_set"], gold=ex["route"], route=resp["route"], text=ex["text"], config=label,
                         answer_raw=raw.get("answer", ""), answer_final=resp["answer"], source=resp["source"],
                         cached=bool(raw.get("cached")), error=raw.get("error"), tokens_in=raw.get("tokens_in", 0),
                         tokens_out=raw.get("tokens_out", 0), tokens_thinking=raw.get("tokens_thinking", 0) or 0,
                         latency_ms_api=raw.get("latency_ms"), latency_ms_e2e=round(e2e, 1), finish_reason=raw.get("finish_reason"),
                         model_version=raw.get("model_version"), attempts=raw.get("attempts"),
                         store_facts_raw=find_store_facts(raw.get("answer", "")), store_facts_final=find_store_facts(resp["answer"])))
        r = rows[-1]
        print(f"[{label}] {r['id']} {r['route']} lat={r['latency_ms_e2e']} tok={r['tokens_in']}/{r['tokens_out']}/{r['tokens_thinking']} err={r['error']} facts={r['store_facts_raw']}", flush=True)
        if r["error"] and "429" in str(r["error"]):
            print("Dừng: 429 (hết quota).")
            break
        if not r["cached"]:
            time.sleep(sleep_s)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-3.5-flash-lite")
    ap.add_argument("--max-a", type=int, default=40)
    ap.add_argument("--max-b", type=int, default=10)
    ap.add_argument("--budget-b", type=int, default=1024)
    ap.add_argument("--sleep", type=float, default=4.0)
    a = ap.parse_args()
    router = Router()
    route_stats, pool = {}, []
    for name, path in SETS.items():
        if not os.path.exists(path):
            continue
        data = load(path)
        preds = [router.route_obj(ex.get("text"), b"i" if ex.get("has_image") else None, session_of(ex)).route for ex in data]
        g = [dict(ex, _set=name) for ex, p in zip(data, preds) if p in GEMINI]
        route_stats[name] = dict(n=len(data), routed_gemini=len(g), fallback_rate=round(len(g) / len(data), 3),
                                 routed_clarify=sum(p == "clarify" for p in preds))
        pool.extend(g)
    items_a = pool[: a.max_a]
    cA = GeminiRestClient(model=a.model, thinking_budget=None, cache_path=CACHE, prompt_version="trung-v1")
    rows_a = run(items_a, cA, use_cache=False, sleep_s=a.sleep, label="A_default")
    ok_ids = [r["id"] for r in rows_a if not r["error"]]
    items_b = [x for x in items_a if x["id"] in ok_ids][: a.max_b]
    cB = GeminiRestClient(model=a.model, thinking_budget=a.budget_b, cache_path=CACHE, prompt_version="trung-v1")
    rows_b = run(items_b, cB, use_cache=False, sleep_s=a.sleep, label=f"B_thinking{a.budget_b}")
    rows_c = run(items_b, cA, use_cache=True, sleep_s=0, label="C_cache")  # cùng khoá với A -> trúng cache
    sA, sB = summarize(rows_a), summarize(rows_b)
    total_turns = sum(v["n"] for v in route_stats.values())
    total_g = sum(v["routed_gemini"] for v in route_stats.values())
    fr = total_g / total_turns
    res = dict(
        config=dict(model=a.model, router="router_v1_rule (results/router_v1_frozen.py.txt)", prompt_version="trung-v1",
                    system_prompt="GEMINI_SYSTEM_PROMPT trong src/msa/agent/router.py", max_output_tokens=512, temperature=0.4,
                    sleep_s=a.sleep, date=time.strftime("%Y-%m-%d %H:%M"), hardware="2 CPU, 7 GB RAM (cloud sandbox) + mạng qua proxy",
                    note="gemini-3.5-flash bị 429 (free tier 20 request/ngày/model, đã hết trong ngày) -> đo trên gemini-3.5-flash-lite"),
        routing=dict(per_set=route_stats, total_turns=total_turns, total_routed_gemini=total_g, fallback_rate_all=round(fr, 3)),
        A_default=sA, B_thinking=sB,
        C_cache=dict(n=len(rows_c), hits=sum(r["cached"] for r in rows_c), latency_ms_p50=pct([r["latency_ms_e2e"] for r in rows_c], 0.5)),
        tokens_per_100_turns=dict(
            A_default=round(fr * 100 * sA["tokens_total_mean"], 0) if sA["tokens_total_mean"] else None,
            B_thinking=round(fr * 100 * sB["tokens_total_mean"], 0) if sB["tokens_total_mean"] else None,
            cong_thuc="fallback_rate × 100 × token_tb_mỗi_lời_gọi (in+out+thinking); chưa trừ cache",
            don_gia="[cần xác minh – điền theo bảng giá Google hiện hành] chi_phí = tokens_in×giá_in + (tokens_out+thinking)×giá_out",
        ),
        api_calls_made=cA.calls_api + cB.calls_api,
        rows=rows_a + rows_b + rows_c,
    )
    json.dump(res, open(os.path.join(ROOT, "results", "gemini_fallback_live.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
