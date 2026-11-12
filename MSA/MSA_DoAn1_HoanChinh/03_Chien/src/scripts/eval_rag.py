# repo: scripts/eval_rag.py
"""Đo thật RAG trên ViMRHP + eval_qa.

1) `retrieval` (không gọi API): Hit@1/Hit@5/MRR@10 cho TF-IDF, BM25, BM25+rewrite, dense (e5-small, MiniLM),
   hybrid RRF; hai chế độ: lọc theo product_id (người dùng ở trang SP) và toàn kho. Phân tích điểm top-1
   của câu answerable vs answerable=false để hiệu chỉnh τ_r.
2) `e2e` (gọi Gemini, theo lô): faithfulness (giám khảo LLM + kiểm trích dẫn), refusal accuracy,
   hallucination rate, false-refusal rate.

Dùng:
    PYTHONPATH=src python src/scripts/eval_rag.py retrieval
    MSA_ENV_FILE=<.env> PYTHONPATH=src python src/scripts/eval_rag.py e2e --n 52 --batch 13
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung

from msa.rag.data import DATA_VERSION, load_vimrhp  # noqa: E402
from msa.rag.ingest import build_chunks  # noqa: E402
from msa.rag.retriever import (BM25Retriever, DenseRetriever, HybridRetriever, STEmbedder,  # noqa: E402
                               TfidfRetriever)

EVAL_QA = ROOT / "eval" / "eval_qa.jsonl"
RES = ROOT / "results"
CACHE = ROOT / "results" / "cache"


def gold_ids(r: dict) -> set[str]:
    return {f"{r['product_id']}::review::{rid}" for rid in r["evidence_review_ids"]}


def rank_metrics(ranked: list[list[str]], golds: list[set[str]]) -> dict:
    """Hit@1, Hit@5, MRR@10 (theo chunk bằng chứng đầu tiên trúng)."""
    h1 = h5 = mrr = 0.0
    for lst, g in zip(ranked, golds):
        pos = next((i for i, c in enumerate(lst[:10]) if c in g), None)
        if pos is not None:
            mrr += 1.0 / (pos + 1)
            h1 += pos < 1
            h5 += pos < 5
    n = max(len(golds), 1)
    return {"hit@1": round(h1 / n, 4), "hit@5": round(h5 / n, 4), "mrr@10": round(mrr / n, 4), "n": len(golds)}


def auc(pos: list[float], neg: list[float]) -> float:
    """AUC = P(điểm câu answerable > điểm câu không đáp án)."""
    if not pos or not neg:
        return float("nan")
    p, n = np.array(pos)[:, None], np.array(neg)[None, :]
    return float(((p > n).sum() + 0.5 * (p == n).sum()) / (p.size * n.size))


def run_retrieval(models: list[str]) -> dict:
    products = load_vimrhp()
    chunks = build_chunks(products)
    qa = [json.loads(l) for l in EVAL_QA.open(encoding="utf-8")]
    ans = [r for r in qa if r["answerable"]]
    unans = [r for r in qa if not r["answerable"]]
    import gc

    timings = {}
    e5 = models[0] if models else None
    factories = [("tfidf_char", lambda: TfidfRetriever(chunks)), ("bm25", lambda: BM25Retriever(chunks)),
                 ("bm25+rewrite", lambda: BM25Retriever(chunks, rewrite=True))]
    for m in models:
        factories.append((f"dense:{m}", lambda m=m: DenseRetriever(chunks, STEmbedder(m, cache_dir=CACHE))))
    if e5:
        factories.append((f"hybrid(bm25+dense:{e5})", lambda: HybridRetriever(
            [BM25Retriever(chunks), DenseRetriever(chunks, STEmbedder(e5, cache_dir=CACHE))])))
    out = {"data_version": DATA_VERSION, "n_chunks": len(chunks), "n_products": len(products),
           "n_answerable": len(ans), "n_unanswerable": len(unans), "hardware": f"{platform.machine()} 2 CPU (torch 2 threads)",
           "index_build_s": timings,
           "encode_corpus_lan_dau_s (lần chạy 05/11 00:0x, chưa có cache)": {"dense:intfloat/multilingual-e5-small": 674.8,
                                                                           "dense:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 160.1},
           "results": {}}
    for name, factory in factories:
        t = time.perf_counter()
        r = factory()
        timings[name] = round(time.perf_counter() - t, 1)
        res = {}
        for mode in ("theo_product_id", "toan_kho"):
            ranked, lat = [], []
            for q in ans:
                t = time.perf_counter()
                hits = r.search(q["question"], k=10, product_id=q["product_id"] if mode == "theo_product_id" else None)
                lat.append((time.perf_counter() - t) * 1000)
                ranked.append([h["chunk_id"] for h in hits])
            m = rank_metrics(ranked, [gold_ids(q) for q in ans])
            m["latency_ms_p50"] = round(float(np.median(lat)), 2)
            for split in ("val", "test"):
                idx = [i for i, q in enumerate(ans) if q["split"] == split]
                m[f"{split}"] = rank_metrics([ranked[i] for i in idx], [gold_ids(ans[i]) for i in idx])
            for origin in ("llm_gemini", "viet_tay_tac_nhan"):
                idx = [i for i, q in enumerate(ans) if q["origin"] == origin]
                m[f"origin_{origin}"] = rank_metrics([ranked[i] for i in idx], [gold_ids(ans[i]) for i in idx])
            res[mode] = m
        if not name.startswith("hybrid"):
            s_pos = [r.search(q["question"], k=1, product_id=q["product_id"])[0]["score"] for q in ans]
            s_neg = [r.search(q["question"], k=1, product_id=q["product_id"])[0]["score"] for q in unans]
            res["top1_score_theo_product_id"] = {
                "answerable_median": round(float(np.median(s_pos)), 4), "unanswerable_median": round(float(np.median(s_neg)), 4),
                "answerable_p10": round(float(np.percentile(s_pos, 10)), 4),
                "auc_tach_answerable": round(auc(s_pos, s_neg), 4),
                "ti_le_answerable_bi_chan_neu_tau_r_0.35": round(float(np.mean(np.array(s_pos) < 0.35)), 4)}
        out["results"][name] = res
        del r
        gc.collect()
        print(name, json.dumps({k: (v["hit@5"], v["mrr@10"]) for k, v in res.items() if "hit@5" in v}))
    return out


# ------------------------------------------------------------------ e2e
JUDGE_SYSTEM = ("Bạn là giám khảo nghiêm khắc đánh giá câu trả lời của trợ lý mua sắm. Chỉ dựa vào NGỮ CẢNH đã cho.")
JUDGE_TMPL = """Với mỗi mục dưới đây, đánh giá CÂU TRẢ LỜI so với NGỮ CẢNH (các đoạn review/tên SP).
- "faithfulness": tỉ lệ (0..1) nhận định trong câu trả lời được NGỮ CẢNH hỗ trợ. Câu từ chối kiểu "chưa có thông tin" → 1.0.
- "unsupported": true nếu có BẤT KỲ nhận định nào không có trong NGỮ CẢNH (bịa), ngược lại false.
- "relevant": true nếu câu trả lời đúng trọng tâm câu hỏi (câu từ chối hợp lý cũng tính true).
- "refusal": true nếu câu trả lời là từ chối/chưa có thông tin.
- "ly_do": ≤ 15 từ.

{items}

Trả về JSON: [{{"qid": "...", "faithfulness": 0.0, "unsupported": false, "relevant": true, "refusal": false, "ly_do": "..."}}]"""


def pick_e2e(qa: list[dict], n: int, seed: int = 42) -> list[dict]:
    """Chọn câu trên split test: ~70% answerable, ~30% không đáp án (cả hai origin)."""
    rng = random.Random(seed)
    test = [r for r in qa if r["split"] == "test"]
    a = [r for r in test if r["answerable"]]
    u = [r for r in test if not r["answerable"]]
    nu = max(int(round(n * 0.3)), 1)
    return rng.sample(a, n - nu) + rng.sample(u, nu)


def summarize(rows: list[dict]) -> dict:
    """Tính các độ đo e2e từ danh sách rows."""
    from msa.rag.pipeline import REFUSAL_RE

    ok = [r for r in rows if r["refuse_reason"] != "llm_error"]
    ans = [r for r in ok if r["answerable"]]
    un = [r for r in ok if not r["answerable"]]
    answered = [r for r in ok if not r["refused"]]
    jd = [r for r in ok if r["judge"]]
    summ = {
        "n_cau": len(rows), "n_loi_llm": len(rows) - len(ok), "n_answerable": len(ans), "n_khong_dap_an": len(un),
        "refusal_accuracy (answerable=false bị từ chối đúng)": round(sum(r["refused"] for r in un) / max(len(un), 1), 4),
        "false_refusal_rate (answerable bị từ chối)": round(sum(r["refused"] for r in ans) / max(len(ans), 1), 4),
        "citation_rate (câu trả lời có ≥1 trích dẫn hợp lệ)": round(sum(bool(r["citations"]) for r in answered) / max(len(answered), 1), 4),
        "cited_gold_rate (answerable được trả lời, trích trúng review bằng chứng)": round(
            sum(r["cited_gold"] for r in ans if not r["refused"]) / max(sum(not r["refused"] for r in ans), 1), 4),
        "faithfulness_judge_mean": round(float(np.mean([float(r["judge"].get("faithfulness", 0)) for r in jd])), 4) if jd else None,
        "hallucination_rate_judge (câu trả lời không từ chối có nhận định không có trong ngữ cảnh)": round(
            sum(bool(r["judge"].get("unsupported")) for r in jd if not r["refused"]) / max(sum(not r["refused"] for r in jd), 1), 4) if jd else None,
        "answer_relevancy_judge": round(sum(bool(r["judge"].get("relevant")) for r in jd) / max(len(jd), 1), 4) if jd else None,
        "n_duoc_cham": len(jd),
        "guard_triggered": sum(r["guard_triggered"] for r in rows),
        "refusal_regex_khop_tren_cau_tu_choi": sum(bool(REFUSAL_RE.search(r["answer"])) for r in ok if r["refused"]),
    }
    return summ


def run_e2e(n: int, batch: int, models: list[str], retriever_name: str, tau_r: float) -> dict:
    from msa_chien.gemini_client import GeminiClient, count_real_calls
    from msa.rag.pipeline import REFUSAL_RE, RAGPipeline

    products = load_vimrhp()
    titles = {p["product_id"]: p["title"] for p in products}
    chunks = build_chunks(products)
    qa = [json.loads(l) for l in EVAL_QA.open(encoding="utf-8")]
    items = pick_e2e(qa, n)
    if retriever_name == "bm25":
        retr = BM25Retriever(chunks, rewrite=True)
    elif retriever_name == "hybrid":
        retr = HybridRetriever([BM25Retriever(chunks), DenseRetriever(chunks, STEmbedder(
            "intfloat/multilingual-e5-small", cache_dir=CACHE))])
    else:
        retr = DenseRetriever(chunks, STEmbedder(retriever_name, cache_dir=CACHE))
    c0 = count_real_calls()
    llms = [GeminiClient(model=m, thinking_budget=0 if m in ("gemini-3.5-flash", "gemini-2.5-flash") else None, tag="rag_e2e", max_retries=2)
            for m in models]
    results, metas = {}, []
    li = 0
    for b in range(0, len(items), batch):
        chunk = items[b:b + batch]
        while li < len(llms):
            pipe = RAGPipeline(retr, llms[li], tau_r=tau_r, k=5, titles=titles)
            outs, meta = pipe.answer_batch([{"qid": q["id"], "question": q["question"], "product_id": q["product_id"]}
                                            for q in chunk])
            if meta.get("error") and ("PerDay" in str(meta["error"]) or "per day" in str(meta["error"])):
                li += 1
                continue
            break
        metas.append({**meta, "model": llms[min(li, len(llms) - 1)].model, "n": len(chunk)})
        for q, o in zip(chunk, outs):
            results[q["id"]] = {**o, "model": llms[min(li, len(llms) - 1)].model}
    # ---- giám khảo (LLM) theo lô
    judge_items = [(q, results[q["id"]]) for q in items if results[q["id"]].get("refuse_reason") != "llm_error"]
    judged = {}
    jl = 0
    for b in range(0, len(judge_items), 26):
        part = judge_items[b:b + 26]
        body = []
        for q, o in part:
            ctx = "\n".join(f"[C{i+1}] {t}" for i, t in enumerate(o.get("context_texts", [])))
            body.append(f"### qid: {q['id']}\nCÂU HỎI: {q['question']}\nNGỮ CẢNH:\n{ctx or '(trống)'}\n"
                        f"CÂU TRẢ LỜI: {o['answer']}")
        while jl < len(llms):
            res = llms[jl].generate(JUDGE_TMPL.format(items="\n\n".join(body)), system=JUDGE_SYSTEM,
                                    temperature=0.0, json_mode=True, max_output_tokens=8000)
            if res.get("error") and ("PerDay" in str(res["error"]) or "per day" in str(res["error"])):
                jl += 1
                continue
            break
        metas.append({**{k: res.get(k) for k in ("tokens_in", "tokens_out", "tokens_thinking", "latency_ms",
                                                    "error", "cached")}, "model": llms[min(jl, len(llms) - 1)].model,
                      "role": "judge", "n": len(part)})
        try:
            for x in json.loads(res["answer"]):
                judged[str(x["qid"])] = x
        except Exception:
            pass
    # ---- tổng hợp
    rows = []
    for q in items:
        o = results[q["id"]]
        j = judged.get(q["id"], {})
        rows.append({"qid": q["id"], "product_id": q["product_id"], "type": q["type"], "origin": q["origin"],
                     "answerable": q["answerable"], "question": q["question"], "gold": q["answer"],
                     "answer": o["answer"], "refused": o["refused"], "refuse_reason": o.get("refuse_reason"),
                     "guard_triggered": o.get("guard_triggered", False),
                     "citations": [c["chunk_id"] for c in o.get("citations", [])],
                     "cited_gold": bool(set(c["chunk_id"] for c in o.get("citations", [])) & gold_ids(q)),
                     "retrieval_score": o.get("retrieval_score"), "model": o.get("model"),
                     "judge": j or None})
    summ = summarize(rows)
    tok_in = sum((m.get("tokens_in") or 0) for m in metas if m.get("role") != "judge")
    tok_out = sum((m.get("tokens_out") or 0) for m in metas if m.get("role") != "judge")
    return {"data_version": DATA_VERSION, "retriever": {"hybrid": "hybrid_rrf(bm25 + multilingual-e5-small)", "bm25": "bm25 (+rewrite)"}.get(retriever_name, retriever_name),
            "tau_r": tau_r, "k": 5, "prompt": "prompts/rag_grounded.md v1.0 (chế độ lô user_batch)",
            "llm_models_used": sorted({m["model"] for m in metas}), "batch_size": batch,
            "real_http_calls": count_real_calls() - c0, "llm_calls_meta": metas,
            "token_answer_tren_moi_cau": {"in": round(tok_in / max(len(ok), 1), 1), "out": round(tok_out / max(len(ok), 1), 1)},
            "summary": summ, "rows": rows,
            "luu_y": ["Giám khảo là LLM cùng họ Gemini – có thiên lệch; cần người kiểm tay ≥ 50 mẫu (Bước 5 sheet Độ đo).",
                      "Sinh theo lô nhiều câu/lời gọi để tiết kiệm quota free tier (20 request/ngày/model); khi phục vụ thật dùng answer() từng câu.",
                      "Câu hỏi + bằng chứng do Gemini sinh, chưa có người duyệt."]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["retrieval", "e2e", "resummarize"])
    ap.add_argument("--dense", nargs="*", default=["intfloat/multilingual-e5-small",
                                                    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"])
    ap.add_argument("--n", type=int, default=52)
    ap.add_argument("--batch", type=int, default=13)
    ap.add_argument("--models", nargs="*", default=["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3-flash-preview"])
    ap.add_argument("--retriever", default="hybrid", help="hybrid | bm25 | <tên model sentence-transformers>")
    ap.add_argument("--tau_r", type=float, default=0.0)
    a = ap.parse_args()
    RES.mkdir(exist_ok=True)
    if a.mode == "retrieval":
        out = run_retrieval(a.dense)
        out["lenh"] = "PYTHONPATH=src python src/scripts/eval_rag.py retrieval"
        (RES / "rag_retrieval_eval.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    elif a.mode == "resummarize":
        # Áp nhãn eval_qa hiện hành (sau khi sửa nhãn) lên kết quả e2e đã chạy – không gọi API
        p = RES / "rag_e2e_eval.json"
        out = json.loads(p.read_text(encoding="utf-8"))
        lab = {r["id"]: r for r in (json.loads(l) for l in EVAL_QA.open(encoding="utf-8"))}
        changed = []
        for r in out["rows"]:
            q = lab[r["qid"]]
            if q["answerable"] != r["answerable"]:
                changed.append(r["qid"])
            r["answerable"], r["gold"] = q["answerable"], q["answer"]
            r["cited_gold"] = bool(set(r["citations"]) & gold_ids(q))
        out.setdefault("summary_truoc_sua_nhan", out["summary"])
        out["summary"] = summarize(out["rows"])
        out["sua_nhan"] = sorted(set(out.get("sua_nhan", []) + changed))
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"sua_nhan": out["sua_nhan"], **out["summary"]}, ensure_ascii=False, indent=1))
    else:
        out = run_e2e(a.n, a.batch, a.models, a.retriever, a.tau_r)
        out["lenh"] = f"MSA_ENV_FILE=<.env> PYTHONPATH=src python src/scripts/eval_rag.py e2e --n {a.n} --batch {a.batch}"
        (RES / "rag_e2e_eval.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(out["summary"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
