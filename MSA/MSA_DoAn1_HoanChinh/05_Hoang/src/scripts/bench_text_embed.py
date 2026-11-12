# repo: scripts/bench_text_embed.py
"""US_23 – Benchmark text-embedding cho khâu retrieval của RAG (Owner: Hoàng, Support: Chiến).

Chạy THẬT trên review tiếng Việt thật (ViMRHP, shared_data v1). Ngoài bộ eval_qa của Chiến (C), script dùng
thêm 2 bộ PROXY (ghi rõ bản chất trong báo cáo):
  A. review→product: mỗi sản phẩm giữ lại 1 review (≥ 8 từ, chọn theo seed) làm truy vấn; corpus =
     mọi review còn lại của tất cả sản phẩm; đúng nếu sản phẩm của chunk khớp product_id của truy vấn.
  B. title→product: truy vấn = tên sản phẩm; corpus = toàn bộ review (không chứa tên SP).
  C. (tuỳ chọn) --eval-qa <jsonl> của Chiến: {question, product_id | evidence_review_ids}.
Cùng chunking (1 review = 1 chunk, cắt 100 từ đầu) và cùng top-K (50 chunk → gộp theo sản phẩm bằng max)
cho MỌI model. Mỗi seed đổi review được giữ lại (bộ A) → báo mean ± std qua các seed.

Lệnh tái lập:
  for m in tfidf_word tfidf_char e5-small minilm-l12 vn-sbert; do
      python src/scripts/bench_text_embed.py --models $m --seeds 42,43,44; done   # mỗi model 1 tiến trình (RAM)
  python src/scripts/bench_text_embed.py --summarize-only
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from msa.eval.metrics import hit_at_k, latency_summary, mrr, ndcg_at_k  # noqa: E402

SHARED = Path(os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data"))
CACHE = ROOT / "results" / "cache"
MAX_WORDS = 100
TOPK_CHUNKS = 50
MIN_QUERY_WORDS = 8

MODELS = {
    "tfidf_word": {"kind": "tfidf", "analyzer": "word", "ngram": (1, 2)},
    "tfidf_char": {"kind": "tfidf", "analyzer": "char_wb", "ngram": (2, 4)},
    "e5-small": {"kind": "st", "name": "intfloat/multilingual-e5-small", "qp": "query: ", "pp": "passage: "},
    "minilm-l12": {"kind": "st", "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "qp": "", "pp": ""},
    "vn-sbert": {"kind": "st", "name": "keepitreal/vietnamese-sbert", "qp": "", "pp": ""},
    "e5-base": {"kind": "st", "name": "intfloat/multilingual-e5-base", "qp": "query: ", "pp": "passage: "},
    "bge-m3": {"kind": "st", "name": "BAAI/bge-m3", "qp": "", "pp": ""},
}


def clean(t: str) -> str:
    """Gộp khoảng trắng, cắt MAX_WORDS từ đầu (chunking chung cho mọi model)."""
    return " ".join((t or "").split()[:MAX_WORDS])


def load_data() -> tuple[list[dict], list[dict]]:
    """Trả (products, chunks). Loại nhóm DongHo (ngoài phạm vi)."""
    prods, chunks = [], []
    with open(SHARED / "vimrhp_fashion_products.jsonl", encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            if p["vimrhp_subcategory"] == "DongHo":
                continue
            prods.append(p)
            for r in p["reviews"]:
                txt = clean(r["text"])
                if txt:
                    chunks.append({"chunk_id": f"rv_{r['comment_id']}", "product_id": p["product_id"], "text": txt,
                                   "n_words": len(txt.split())})
    return prods, chunks


class Encoder:
    """Bọc TF-IDF hoặc sentence-transformers dưới cùng một giao diện encode → vector L2-normalized."""

    def __init__(self, key: str):
        self.key, self.cfg = key, MODELS[key]
        self.model = None
        self.vec = None

    def fit_corpus(self, texts: list[str]) -> np.ndarray:
        cfg = self.cfg
        if cfg["kind"] == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vec = TfidfVectorizer(analyzer=cfg["analyzer"], ngram_range=cfg["ngram"], sublinear_tf=True,
                                       min_df=1, lowercase=True)
            return self.vec.fit_transform(texts)  # sparse, đã L2-normalize mặc định
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(2)
        self.model = SentenceTransformer(cfg["name"], device="cpu")
        self.model.max_seq_length = 256
        CACHE.mkdir(parents=True, exist_ok=True)
        cp = CACHE / f"corpus_{self.key}_{len(texts)}.npy"
        if cp.exists():
            return np.load(cp)
        emb = self.model.encode([cfg["pp"] + t for t in texts], batch_size=32, normalize_embeddings=True,
                                show_progress_bar=False, convert_to_numpy=True).astype("float32")
        np.save(cp, emb)
        return emb

    def encode_queries(self, texts: list[str]):
        if self.cfg["kind"] == "tfidf":
            return self.vec.transform(texts)
        return self.model.encode([self.cfg["qp"] + t for t in texts], batch_size=32, normalize_embeddings=True,
                                 show_progress_bar=False, convert_to_numpy=True).astype("float32")


def sims(q, C) -> np.ndarray:
    """Cosine (vector đã chuẩn hoá) – tương đương FAISS IndexFlatIP."""
    s = q @ C.T
    return s.toarray() if hasattr(s, "toarray") else np.asarray(s)


def rank_products(sim_row: np.ndarray, chunk_pid: np.ndarray, mask: np.ndarray | None) -> list[str]:
    """Top-K chunk → gộp theo product_id bằng max điểm, giữ thứ tự."""
    s = sim_row.copy()
    if mask is not None:
        s[~mask] = -np.inf
    top = np.argpartition(-s, TOPK_CHUNKS)[:TOPK_CHUNKS]
    top = top[np.argsort(-s[top])]
    seen, out = set(), []
    for i in top:
        pid = chunk_pid[i]
        if pid not in seen and np.isfinite(s[i]):
            seen.add(pid)
            out.append(pid)
    return out


def score(runs: list[list[str]], gold: list[str]) -> dict:
    return {"hit@1": float(np.mean([hit_at_k(r, {g}, 1) for r, g in zip(runs, gold)])),
            "hit@5": float(np.mean([hit_at_k(r, {g}, 5) for r, g in zip(runs, gold)])),
            "hit@10": float(np.mean([hit_at_k(r, {g}, 10) for r, g in zip(runs, gold)])),
            "mrr@10": float(np.mean([mrr(r, {g}, k=10) for r, g in zip(runs, gold)])),
            "ndcg@10": float(np.mean([ndcg_at_k(r, {g}, 10) for r, g in zip(runs, gold)]))}


def build_task_a(prods, chunks, seed):
    rng = random.Random(seed)
    by_pid: dict[str, list[int]] = {}
    for i, c in enumerate(chunks):
        if c["n_words"] >= MIN_QUERY_WORDS:
            by_pid.setdefault(c["product_id"], []).append(i)
    q_idx = [rng.choice(by_pid[p["product_id"]]) for p in prods if len(by_pid.get(p["product_id"], [])) >= 2]
    return q_idx


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="tfidf_word,tfidf_char,e5-small,minilm-l12,vn-sbert")
    ap.add_argument("--seeds", default="42,43,44")
    ap.add_argument("--latency-queries", type=int, default=100, help="số truy vấn đo latency đơn lẻ mỗi seed")
    ap.add_argument("--eval-qa", default=None, help="jsonl của Chiến (tuỳ chọn)")
    ap.add_argument("--out", default=str(ROOT / "results" / "bench_text_embed"))
    ap.add_argument("--summarize-only", action="store_true")
    a = ap.parse_args()
    if a.summarize_only:
        summarize(Path(a.out))
        return
    seeds = [int(s) for s in a.seeds.split(",")]
    prods, chunks = load_data()
    texts = [c["text"] for c in chunks]
    chunk_pid = np.array([c["product_id"] for c in chunks])
    titles = [clean(p["title"]) for p in prods]
    title_gold = [p["product_id"] for p in prods]
    qa = []  # (question, product_id, set(evidence chunk_id))
    if a.eval_qa and Path(a.eval_qa).exists():
        cid2pid = {c["chunk_id"]: c["product_id"] for c in chunks}
        for line in open(a.eval_qa, encoding="utf-8"):
            r = json.loads(line)
            ev = {f"rv_{e}" for e in r.get("evidence_review_ids") or []} & set(cid2pid)
            pid = r.get("product_id") or next((cid2pid[e] for e in ev), None)
            if r.get("question") and pid and r.get("answerable", True) and ev:
                qa.append((r["question"], pid, ev))
    rows, per_query = [], []
    meta = {"data_version": "shared_data v1 (prep_shared_data.py seed 42)", "n_products": len(prods),
            "n_chunks": len(chunks), "chunking": f"1 review = 1 chunk, cắt {MAX_WORDS} từ đầu",
            "top_k_chunks": TOPK_CHUNKS, "aggregation": "max theo product_id", "seeds": seeds,
            "min_query_words": MIN_QUERY_WORDS, "cpu": os.cpu_count(), "python": platform.python_version(),
            "torch_threads": 2, "eval_qa_file": a.eval_qa if qa else None, "n_eval_qa": len(qa)}
    for key in a.models.split(","):
        print(f"[{time.strftime('%H:%M:%S')}] model {key}", flush=True)
        enc = Encoder(key)
        t0 = time.perf_counter()
        C = enc.fit_corpus(texts)
        t_corpus = time.perf_counter() - t0
        # B: title→product (không phụ thuộc seed về chất lượng)
        Qb = enc.encode_queries(titles)
        Sb = sims(Qb, C)
        runs_b = [rank_products(Sb[i], chunk_pid, None) for i in range(len(titles))]
        res_b = score(runs_b, title_gold)
        res_c = None
        if qa:
            Sc = sims(enc.encode_queries([q for q, _, _ in qa]), C)
            res_c = score([rank_products(Sc[i], chunk_pid, None) for i in range(len(qa))], [p for _, p, _ in qa])
            chunk_ids = np.array([c["chunk_id"] for c in chunks])
            # C_ev_*: chunk bằng chứng (evidence_review_ids) có nằm trong top-K chunk không
            #   global = tìm trên toàn corpus; inprod = chỉ trong review của SP đang hỏi (bối cảnh RAG khi đã biết product_id)
            for tag, restrict in (("ev_global", False), ("ev_inprod", True)):
                runs, golds = [], []
                for i, (_, pid, ev) in enumerate(qa):
                    srow = Sc[i].copy()
                    if restrict:
                        srow[chunk_pid != pid] = -np.inf
                    order = np.argsort(-srow)[:10]
                    runs.append([chunk_ids[j] for j in order if np.isfinite(srow[j])])
                    golds.append(ev)
                res_c.update({f"{tag}_hit@1": float(np.mean([hit_at_k(r, g, 1) for r, g in zip(runs, golds)])),
                              f"{tag}_hit@5": float(np.mean([hit_at_k(r, g, 5) for r, g in zip(runs, golds)])),
                              f"{tag}_mrr@10": float(np.mean([mrr(r, g, k=10) for r, g in zip(runs, golds)]))})
        for seed in seeds:
            q_idx = build_task_a(prods, chunks, seed)
            Qa = enc.encode_queries([texts[i] for i in q_idx])
            Sa = sims(Qa, C)
            runs_a = []
            for j, qi in enumerate(q_idx):
                mask = np.ones(len(chunks), bool)
                mask[qi] = False  # loại chính review truy vấn khỏi corpus
                runs_a.append(rank_products(Sa[j], chunk_pid, mask))
            res_a = score(runs_a, [chunks[i]["product_id"] for i in q_idx])
            # latency 1 truy vấn (encode + tìm + gộp), thứ tự xáo theo seed
            lat = []
            rng = random.Random(seed)
            sample = rng.sample(q_idx, min(a.latency_queries, len(q_idx)))
            for qi in sample:
                t = time.perf_counter()
                q = enc.encode_queries([texts[qi]])
                rank_products(sims(q, C)[0], chunk_pid, None)
                lat.append((time.perf_counter() - t) * 1000)
            ls = latency_summary(lat)
            row = {"model": key, "model_name": MODELS[key].get("name", f"TF-IDF {MODELS[key].get('analyzer')}"),
                   "seed": seed, "n_queries_A": len(q_idx), **{f"A_{k}": v for k, v in res_a.items()},
                   "n_queries_B": len(titles), **{f"B_{k}": v for k, v in res_b.items()},
                   "latency_p50_ms": ls["p50"], "latency_p95_ms": ls["p95"], "corpus_encode_s": t_corpus,
                   "dim": int(C.shape[1])}
            if res_c:
                row.update({"n_queries_C": len(qa), **{f"C_{k}": v for k, v in res_c.items()}})
            rows.append(row)
            per_query += [{"model": key, "seed": seed, "query_chunk": chunks[qi]["chunk_id"],
                           "gold": chunks[qi]["product_id"], "top5": r[:5]} for qi, r in zip(q_idx, runs_a)]
            print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}, ensure_ascii=False), flush=True)
        del enc
    out = Path(a.out)
    runs_dir = out.parent / "bench_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    for key in a.models.split(","):  # mỗi model 1 file → chạy từng model ở tiến trình riêng (RAM 7 GB dùng chung)
        json.dump({"meta": meta, "runs": [r for r in rows if r["model"] == key]},
                  open(runs_dir / f"{key}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(runs_dir / f"per_query_{'_'.join(a.models.split(','))}.jsonl", "w", encoding="utf-8") as f:
        for r in per_query:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summarize(out)


def summarize(out: Path) -> None:
    """Gộp mọi file results/bench_runs/<model>.json → <out>.csv (từng lần chạy), <out>_summary.csv (mean ± std), <out>.json."""
    import pandas as pd
    runs_dir = out.parent / "bench_runs"
    rows, meta = [], None
    for fp in sorted(runs_dir.glob("*.json")):
        d = json.load(open(fp, encoding="utf-8"))
        rows += d["runs"]
        meta = meta or d["meta"]
    df = pd.DataFrame(rows)
    df.to_csv(f"{out}.csv", index=False)
    num = [c for c in df.columns if c not in ("model", "model_name", "seed") and df[c].dtype != object]
    agg = df.groupby(["model", "model_name"])[num].agg(["mean", "std"])
    agg.columns = [f"{a_}_{b}" for a_, b in agg.columns]
    agg.reset_index().to_csv(f"{out}_summary.csv", index=False)
    json.dump({"meta": meta, "runs": rows, "summary": agg.reset_index().to_dict(orient="records")},
              open(f"{out}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(agg.reset_index().to_string())


if __name__ == "__main__":
    main()
