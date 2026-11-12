# repo: src/msa/rag/pipeline.py
"""US_34/US_35 – RAGPipeline: retrieve → (cổng τ_r) → LLM có grounding → trích nguồn / từ chối.

Hợp đồng (mục 5.3): `RAGPipeline.answer(question, product_id=None) -> dict{answer, citations, retrieval_score, refused}`
(+ trường phụ: contexts, source, llm_error, latency_ms).
- Từ chối "Hiện cửa hàng chưa có thông tin về …" khi: không có chunk, điểm retrieval < τ_r, LLM tự từ chối,
  hoặc LLM trả lời mà không trích được nguồn hợp lệ nào (guard chống bịa).
- QA thiếu dữ kiện không được nhờ Gemini "bù" bằng kiến thức chung (quy tắc 5.4).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from msa.paths import CHIEN as ROOT, RAG_PROMPT, rag_cache_dir, rag_kb

PROMPT_PATH = RAG_PROMPT  # 03_Chien/prompts/rag_grounded.md
REFUSAL_PREFIX = "Hiện cửa hàng chưa có thông tin về"
REFUSAL_RE = re.compile(r"chưa có thông tin|không có thông tin|chưa có dữ liệu|không đủ thông tin", re.I)
CITE_RE = re.compile(r"\[C(\d+)\]")
# Chủ đề mà dữ liệu cửa hàng hiện KHÔNG có trường cấu trúc (ViMRHP) – dùng để đặt tên chủ đề khi từ chối
TOPIC_PATTERNS = [
    (r"giá|bao nhiêu tiền|bn tiền|nhiêu tiền", "giá bán hiện tại"),
    (r"còn hàng|còn size|còn sz|còn màu|hết hàng|tồn kho|có size|có sz", "tình trạng còn hàng"),
    (r"đổi trả|bảo hành|hoàn tiền", "chính sách đổi trả/bảo hành"),
    (r"xuất xứ|sản xuất ở|nhà máy|made in", "xuất xứ"),
]


def load_prompt_blocks(path: Path = PROMPT_PATH) -> dict[str, str]:
    """Đọc các khối ```system```, ```user```, ```user_batch``` trong file prompt markdown."""
    text = path.read_text(encoding="utf-8")
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"```(\w+)\n(.*?)```", text, re.S)}


def refusal_message(question: str) -> str:
    """Câu từ chối có nêu chủ đề nếu nhận ra (giá, tồn kho, …)."""
    q = question.lower()
    for pat, topic in TOPIC_PATTERNS:
        if re.search(pat, q):
            return f"{REFUSAL_PREFIX} {topic} của sản phẩm này."
    return f"{REFUSAL_PREFIX} nội dung bạn hỏi cho sản phẩm này."


def format_contexts(chunks: list[dict], max_chars: int = 350) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        tag = {"review": f"review {c.get('rating') or ''}★".strip(), "title": "tên sản phẩm",
               "detail_rating": "điểm đánh giá", "description": "mô tả", "specs": "thông số"}.get(c["field"], c["field"])
        lines.append(f"[C{i}] ({tag}) {c['text'][:max_chars]}")
    return "\n".join(lines)


def postprocess(raw_answer: str, chunks: list[dict], question: str) -> dict[str, Any]:
    """Tách trích dẫn [Cx] → citations; quyết định refused; guard: trả lời không có nguồn ⇒ từ chối."""
    ans = (raw_answer or "").strip()
    idx = sorted({int(n) for n in CITE_RE.findall(ans) if 1 <= int(n) <= len(chunks)})
    citations = [{"product_id": chunks[i - 1]["product_id"], "field": chunks[i - 1]["field"],
                  "chunk_id": chunks[i - 1]["chunk_id"]} for i in idx]
    refused = bool(REFUSAL_RE.search(ans)) and not citations
    guard = False
    if not refused and not citations:
        refused, guard = True, True
        ans = refusal_message(question)
    if refused and not ans:
        ans = refusal_message(question)
    return {"answer": ans, "citations": citations, "refused": refused, "guard_triggered": guard}


class RAGPipeline:
    """Pipeline hỏi đáp sản phẩm có trích nguồn."""

    def __init__(self, retriever: Any, llm: Any, tau_r: float = 0.35, k: int = 5,
                 titles: dict[str, str] | None = None, prompt_path: Path = PROMPT_PATH):
        self.retriever, self.llm, self.tau_r, self.k = retriever, llm, tau_r, k
        self.blocks = load_prompt_blocks(prompt_path)
        self.titles = titles or {}

    def retrieve(self, question: str, product_id: str | None) -> list[dict]:
        return self.retriever.search(question, k=self.k, product_id=product_id)

    def build_prompt(self, question: str, product_id: str | None, chunks: list[dict]) -> str:
        title = self.titles.get(product_id or "", "") or (chunks[0].get("title", "") if chunks else "")
        return self.blocks["user"].format(title=title, contexts=format_contexts(chunks), question=question)

    def answer(self, question: str, product_id: str | None = None) -> dict[str, Any]:
        t0 = time.perf_counter()
        chunks = self.retrieve(question, product_id)
        score = float(chunks[0]["score"]) if chunks else 0.0
        base = {"retrieval_score": score, "contexts": [c["chunk_id"] for c in chunks]}
        if not chunks or score < self.tau_r:
            return {**base, "answer": refusal_message(question), "citations": [], "refused": True,
                    "refuse_reason": "no_chunk" if not chunks else "below_tau_r", "source": "internal",
                    "llm_error": None, "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}
        res = self.llm.generate(self.build_prompt(question, product_id, chunks), system=self.blocks["system"],
                                temperature=0.1)
        if res.get("error"):
            # Lỗi LLM (429/timeout): không bịa – trả thông điệp dự phòng, đánh dấu từ chối
            return {**base, "answer": res["answer"], "citations": [], "refused": True, "refuse_reason": "llm_error",
                    "source": res.get("source", "gemini"), "llm_error": res["error"],
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}
        out = postprocess(res["answer"], chunks, question)
        return {**base, **out, "refuse_reason": "llm" if out["refused"] else None,
                "source": "internal", "llm_error": None,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}

    # ---- chế độ lô: chỉ dùng cho đánh giá (tiết kiệm quota) ----
    def answer_batch(self, items: list[dict]) -> tuple[list[dict], dict]:
        """items: [{qid, question, product_id}] → (kết quả như answer(), meta LLM); 1 lời gọi LLM cho cả lô."""
        prepared, outs = [], {}
        for it in items:
            chunks = self.retrieve(it["question"], it.get("product_id"))
            score = float(chunks[0]["score"]) if chunks else 0.0
            if not chunks or score < self.tau_r:
                outs[it["qid"]] = {"answer": refusal_message(it["question"]), "citations": [], "refused": True,
                                   "refuse_reason": "below_tau_r", "retrieval_score": score,
                                   "contexts": [c["chunk_id"] for c in chunks]}
            else:
                prepared.append((it, chunks, score))
        if prepared:
            body = []
            for it, chunks, _ in prepared:
                title = self.titles.get(it.get("product_id") or "", "") or chunks[0].get("title", "")
                body.append(f"### qid: {it['qid']}\nSẢN PHẨM: {title}\nNGỮ CẢNH:\n{format_contexts(chunks)}\n"
                            f"CÂU HỎI: {it['question']}")
            prompt = self.blocks["user_batch"].format(n=len(prepared), items="\n\n".join(body))
            res = self.llm.generate(prompt, system=self.blocks["system"], temperature=0.1, json_mode=True,
                                    max_output_tokens=8000)
            try:
                got = {str(x["qid"]): x.get("answer", "") for x in json.loads(res["answer"])}
            except Exception:
                got = {}
            for it, chunks, score in prepared:
                if it["qid"] not in got:
                    outs[it["qid"]] = {"answer": res.get("answer", ""), "citations": [], "refused": True,
                                       "refuse_reason": "llm_error", "llm_error": res.get("error") or "parse",
                                       "retrieval_score": score, "contexts": [c["chunk_id"] for c in chunks]}
                    continue
                o = postprocess(got[it["qid"]], chunks, it["question"])
                outs[it["qid"]] = {**o, "refuse_reason": "llm" if o["refused"] else None, "retrieval_score": score,
                                   "contexts": [c["chunk_id"] for c in chunks], "raw_answer": got[it["qid"]],
                                   "context_texts": [c["text"][:350] for c in chunks]}
            meta = {k: res.get(k) for k in ("tokens_in", "tokens_out", "tokens_thinking", "latency_ms", "error", "cached")}
        else:
            meta = {}
        return [outs[it["qid"]] for it in items], meta


def build_default_pipeline(llm: Any = None, use_dense: bool = True, tau_r: float = 0.0,
                           kb_path: Path | None = None) -> RAGPipeline:
    """Dựng pipeline mặc định cho API /qa (Hoàng gọi): kho tri thức ViMRHP + Hybrid RRF(BM25 + e5-small).

    - `kb_path`: chunks.jsonl (mặc định data/kb/chunks.jsonl; nếu chưa có thì chunk lại từ shared_data).
    - Vector store: embedding e5-small cache .npy ở results/cache (mã hoá 1 lần).
    - τ_r mặc định 0.0: đo thật cho thấy điểm top-1 tách câu có/không đáp án kém (AUC 0.72–0.76),
      nên từ chối dựa vào LLM + guard trích dẫn (xem docs/US_33_34_35_rag.md).
    """
    from msa.rag.data import load_vimrhp
    from msa.rag.ingest import build_chunks, load_chunks
    from msa.rag.llm import get_llm
    from msa.rag.retriever import BM25Retriever, DenseRetriever, HybridRetriever, STEmbedder

    kb = kb_path or rag_kb()
    products = load_vimrhp()
    chunks = load_chunks(kb) if kb.exists() else build_chunks(products)
    retr: Any = BM25Retriever(chunks)
    if use_dense:
        retr = HybridRetriever([retr, DenseRetriever(chunks, STEmbedder(cache_dir=rag_cache_dir()))])
    return RAGPipeline(retr, llm or get_llm(), tau_r=tau_r, k=5, titles={p["product_id"]: p["title"] for p in products})
