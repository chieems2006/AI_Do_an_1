# repo: scripts/bench_common_subset.py
"""US_24 – So sánh công bằng trên tập câu CHUNG mà mọi model đều đã chạy (vd. q001–q018). Không gọi API."""
import json
import statistics
from pathlib import Path

RES = Path(__file__).resolve().parents[2] / "results"
TAGS = ["gemini35flashlite", "gemma4_26b_api", "qwen25_05b"]


def main() -> dict:
    load = lambda p: [json.loads(l) for l in p.open(encoding="utf-8")]
    qa = {t: {r["qid"]: r for r in load(RES / f"bench_llm_qa_{t}.jsonl")} for t in TAGS}
    judge = {r["qid"]: r["scores"] for r in load(RES / "bench_llm_judge.jsonl")}
    common = sorted(set.intersection(*(set(v) for v in qa.values())) & set(judge))
    out = {"qids": common, "n": len(common), "models": {}}
    for t in TAGS:
        js = [judge[q][t] for q in common if t in judge[q]]
        lat = [qa[t][q]["latency_ms"] / 1000 for q in common]
        un = [q for q in common if not qa[t][q]["answerable"]]
        out["models"][t] = dict(
            faithfulness=round(statistics.mean(float(j["faithfulness"]) for j in js), 3),
            hallucination_rate=round(sum(bool(j["hallucination"]) for j in js) / len(js), 3),
            correctness=round(statistics.mean(float(j["correctness"]) for j in js), 3),
            correct_refusal_unanswerable=f"{sum(bool(judge[q][t].get('refused')) for q in un)}/{len(un)}",
            latency_s_median=round(statistics.median(lat), 1))
    (RES / "bench_llm_common_subset.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1))
