# repo: scripts/bench_llm.py
"""US_24 – Benchmark LLM trả lời (RAG trên review) + Gemini vai trò Fallback/Router.

Cùng system prompt, cùng ngữ cảnh, temperature = 0 (greedy với model local) cho mọi model.
Log từng câu trả lời ra JSONL; tổng hợp faithfulness, hallucination rate, refusal, latency, token, chi phí/100 câu.

Chế độ:
  qa      : chạy model trên eval/bench_qa.jsonl            -> results/bench_llm_qa_<tag>.jsonl
  judge   : Gemini chấm tất cả câu trả lời (1 lời gọi/câu)  -> results/bench_llm_judge.jsonl
  router  : Gemini zero-shot route + trả lời chitchat/ood   -> results/bench_llm_router_<tag>.jsonl
  summary : gộp số liệu                                     -> results/bench_llm_summary.json + .md

Ví dụ (key nạp qua MSA_ENV_FILE hoặc GEMINI_API_KEY, KHÔNG in ra):
  python src/scripts/bench_llm.py qa --model gemini --tag gemini35flash_t0 --thinking-budget 0
  python src/scripts/bench_llm.py qa --model hf:Qwen/Qwen2.5-0.5B-Instruct --tag qwen05b
  OPENAI_BASE_URL=http://localhost:11434/v1 python src/scripts/bench_llm.py qa --model openai:qwen2.5:7b-instruct --tag ollama_qwen7b
  python src/scripts/bench_llm.py qa --model gemini:gemini-3.5-flash-lite --tag gemini35flashlite_t0 --thinking-budget 0
  python src/scripts/bench_llm.py qa --model gemini:gemma-4-26b-a4b-it --tag gemma4_26b_api
  python src/scripts/bench_llm.py judge --tags gemini35flashlite_t0,gemma4_26b_api,qwen25_05b --judge-model gemini-2.5-flash
  python src/scripts/bench_llm.py router --tag flashlite_t0 --gemini-model gemini-3.5-flash-lite --thinking-budget 0 --per-route 2
  python src/scripts/bench_llm.py summary
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from make_bench_contexts import context_text  # noqa: E402

RES = ROOT / "results"
EVAL = ROOT / "eval"
CTX_FILE = EVAL / "bench_contexts.jsonl"
QA_FILE = EVAL / "bench_qa.jsonl"
ROUTER_FILE = EVAL / "eval_router_snapshot_from_Chien.jsonl"
BUDGET_FILE = RES / "gemini_budget.json"
CACHE_FILE = RES / "gemini_cache.sqlite"
REFUSAL = "Xin lỗi, hiện chưa có thông tin về điều này trong dữ liệu sản phẩm."

# Đơn giá (USD / 1M token) – [cần xác minh – điền theo bảng giá Google hiện hành]. Để None thì chỉ báo token.
PRICE_PER_1M = {"gemini-3.5-flash": {"input": None, "output": None}}

SYSTEM_QA = (
    "Bạn là trợ lý bán hàng thời trang của một cửa hàng online. Chỉ trả lời dựa trên các đánh giá khách hàng được "
    "cung cấp, ghi nguồn bằng mã [R1], [R2]... Nếu các đánh giá không có thông tin để trả lời, hãy trả lời đúng câu: "
    f"\"{REFUSAL}\" Không tự bịa giá, size, tồn kho hay thông số. Trả lời tiếng Việt, ngắn gọn tối đa 3 câu."
)


def user_prompt(ctx_item: dict, question: str) -> str:
    return f"{context_text(ctx_item)}\n\nCâu hỏi của khách: {question}\nTrả lời:"


# ======================================================================= adapters
class LLM(Protocol):
    name: str

    def generate(self, system: str, prompt: str, max_tokens: int) -> dict: ...


class GeminiLLM:
    """Gemini qua REST (src/msa_td/gemini_client.py), có cache + đếm ngân sách."""

    def __init__(self, thinking_budget: int | None, model: str | None = None, max_calls: int = 250):
        from msa_td.gemini_client import GeminiClient
        self.client = GeminiClient(model=model or os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"),
                                   cache_path=str(CACHE_FILE), budget_file=str(BUDGET_FILE), max_calls=max_calls,
                                   max_retries=1)
        self.thinking_budget = thinking_budget
        self.name = f"{self.client.model}(thinking={'default' if thinking_budget is None else thinking_budget})"

    def generate(self, system: str, prompt: str, max_tokens: int, response_json: bool = False) -> dict:
        # thinking token tính vào maxOutputTokens → cộng thêm room khi để thinking mặc định
        mot = max_tokens if self.thinking_budget == 0 else max_tokens + 4096
        return self.client.generate(prompt, system=system, temperature=0.0, max_output_tokens=mot,
                                    thinking_budget=self.thinking_budget, response_json=response_json)


class HFLocalLLM:
    """Model open-source chạy CPU bằng transformers, greedy decoding (tương đương temperature 0)."""

    def __init__(self, model_id: str, threads: int = 2, dtype: str | None = None):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(threads)
        t0 = time.perf_counter()
        self.tok = AutoTokenizer.from_pretrained(model_id)
        # bf16 để vừa RAM (máy 7 GB dùng chung, fp32 0.5B bị OOM-kill 2 lần); đổi bằng MSA_HF_DTYPE=float32
        dt = getattr(torch, dtype or os.environ.get("MSA_HF_DTYPE", "bfloat16"))
        self.model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dt, low_cpu_mem_usage=True)
        self.model.eval()
        self.load_s = round(time.perf_counter() - t0, 1)
        self.name = model_id
        self.torch = torch

    def generate(self, system: str, prompt: str, max_tokens: int) -> dict:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        ids = self.tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
        if not isinstance(ids, self.torch.Tensor):  # transformers mới trả BatchEncoding
            ids = ids["input_ids"]
        t0 = time.perf_counter()
        with self.torch.no_grad():
            out = self.model.generate(ids, max_new_tokens=max_tokens, do_sample=False,
                                      pad_token_id=self.tok.eos_token_id)
        lat = (time.perf_counter() - t0) * 1000
        new = out[0, ids.shape[1]:]
        return dict(answer=self.tok.decode(new, skip_special_tokens=True).strip(), source="local", cached=False,
                    tokens_in=int(ids.shape[1]), tokens_out=int(new.shape[0]), tokens_thinking=0,
                    latency_ms=round(lat, 1), error=None, model=self.name)


class OpenAICompatLLM:
    """Server tương thích OpenAI (Ollama/vLLM/LM Studio) – để nhóm chạy model 7-8B trên máy có GPU."""

    def __init__(self, base_url: str, model: str):
        import requests
        self.base_url, self.model, self.s = base_url.rstrip("/"), model, requests.Session()
        self.name = f"openai-compat:{model}"

    def generate(self, system: str, prompt: str, max_tokens: int) -> dict:
        t0 = time.perf_counter()
        r = self.s.post(f"{self.base_url}/chat/completions", timeout=300, json={
            "model": self.model, "temperature": 0, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
        lat = (time.perf_counter() - t0) * 1000
        if r.status_code != 200:
            return dict(answer="", source="local", cached=False, tokens_in=0, tokens_out=0, tokens_thinking=0,
                        latency_ms=round(lat, 1), error=f"http_{r.status_code}", model=self.name)
        d = r.json()
        u = d.get("usage", {})
        return dict(answer=d["choices"][0]["message"]["content"].strip(), source="local", cached=False,
                    tokens_in=u.get("prompt_tokens", 0), tokens_out=u.get("completion_tokens", 0), tokens_thinking=0,
                    latency_ms=round(lat, 1), error=None, model=self.name)


class EchoLLM:
    """LLM giả cho test: trả lời bằng câu đầu tiên của review chứa từ khoá câu hỏi, hoặc từ chối."""

    name = "echo-mock"

    def generate(self, system: str, prompt: str, max_tokens: int) -> dict:
        q = prompt.rsplit("Câu hỏi của khách:", 1)[-1].lower()
        for line in prompt.splitlines():
            m = re.match(r"\[(R\d+)\].*?\) (.*)", line)
            if m and any(w in m.group(2).lower() for w in content_tokens(q)):
                return dict(answer=f"{m.group(2)[:120]} [{m.group(1)}]", source="local", cached=False, tokens_in=0,
                            tokens_out=0, tokens_thinking=0, latency_ms=0.0, error=None, model=self.name)
        return dict(answer=REFUSAL, source="local", cached=False, tokens_in=0, tokens_out=0, tokens_thinking=0,
                    latency_ms=0.0, error=None, model=self.name)


def make_llm(spec: str, thinking_budget: int | None) -> LLM:
    if spec == "gemini":
        return GeminiLLM(thinking_budget)
    if spec.startswith("gemini:"):  # gemini:<model id API>, vd gemini:gemini-3.5-flash-lite, gemini:gemma-4-26b-a4b-it
        return GeminiLLM(thinking_budget, model=spec.split(":", 1)[1])
    if spec.startswith("hf:"):
        return HFLocalLLM(spec[3:])
    if spec.startswith("openai:"):  # openai:<tên model>; URL lấy từ OPENAI_BASE_URL (mặc định Ollama)
        return OpenAICompatLLM(os.environ.get("OPENAI_BASE_URL", "http://localhost:11434/v1"), spec.split(":", 1)[1])
    if spec == "echo":
        return EchoLLM()
    raise ValueError(spec)


# ======================================================================= heuristic metrics (không tốn API)
STOP = set("""và là của có không thì mà cho với các những được này đó ạ nha nhé thế nào bao nhiêu gì sao như rất khá
hơi cũng đã sẽ đang một hai bị ở trong trên theo khi nếu vì nên để từ ra vào lên về hay hoặc người khách mình bạn shop
sản phẩm review đánh giá xin lỗi hiện chưa thông tin điều dữ liệu""".split())
REFUSAL_RX = re.compile(r"chưa có thông tin|không có thông tin|không đề cập|không nhắc|không được đề cập|"
                        r"không có dữ liệu|không tìm thấy thông tin|chưa có dữ liệu", re.I)


def content_tokens(s: str) -> list[str]:
    toks = re.findall(r"[0-9a-zà-ỹđ]+", s.lower())
    return [t for t in toks if len(t) >= 2 and t not in STOP]


def heuristic_scores(answer: str, ctx_item: dict) -> dict:
    """refused, cited (có [R#]), invalid_citations, support_overlap = tỉ lệ token nội dung của câu trả lời có trong ngữ cảnh."""
    ctx = " ".join(c["text"] for c in ctx_item["context"]).lower() + " " + ctx_item["title"].lower()
    ctx_toks = set(content_tokens(ctx))
    ans_toks = content_tokens(re.sub(r"\[R\d+\]", " ", answer))
    valid = {c["rid"] for c in ctx_item["context"]}
    cites = re.findall(r"\[?(R\d+)\]?", answer)
    return dict(refused=bool(REFUSAL_RX.search(answer)), cited=bool(cites),
                invalid_citations=sorted({c for c in cites if c not in valid}),
                support_overlap=round(sum(t in ctx_toks for t in ans_toks) / len(ans_toks), 3) if ans_toks else 1.0)


# ======================================================================= modes
def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def run_qa(llm: LLM, tag: str, limit: int | None = None, max_tokens: int = 200, qids: list[str] | None = None) -> Path:
    ctx = {c["product_id"]: c for c in load_jsonl(CTX_FILE)}
    qs = load_jsonl(QA_FILE)
    if qids:
        qs = [q for q in qs if q["qid"] in qids]
    qs = qs[:limit] if limit else qs
    out = RES / f"bench_llm_qa_{tag}.jsonl"
    RES.mkdir(exist_ok=True)
    errs = 0
    with out.open("w", encoding="utf-8") as f:
        for q in qs:
            c = ctx[q["product_id"]]
            r = llm.generate(SYSTEM_QA, user_prompt(c, q["question"]), max_tokens)
            row = dict(qid=q["qid"], tag=tag, model=r.get("model", llm.name), question=q["question"],
                       answerable=q["answerable"], answer=r["answer"], latency_ms=r["latency_ms"],
                       tokens_in=r["tokens_in"], tokens_out=r["tokens_out"], tokens_thinking=r.get("tokens_thinking", 0),
                       cached=r.get("cached", False), error=r.get("error"), temperature=0.0,
                       **heuristic_scores(r["answer"], c))
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(f"{q['qid']} {row['latency_ms']:.0f}ms refused={row['refused']} {row['answer'][:80]!r}", flush=True)
            errs = errs + 1 if row["error"] else 0
            if errs >= 3:  # 3 lỗi liên tiếp (quota/400) → dừng để không đốt ngân sách
                print("DỪNG: 3 lỗi liên tiếp", row["error"], r.get("error_detail"), flush=True)
                break
    return out


JUDGE_SYSTEM = (
    "Bạn là giám khảo nghiêm khắc đánh giá câu trả lời của trợ lý bán hàng. Chỉ dựa vào NGỮ CẢNH (các review) và "
    "ĐÁP ÁN THAM CHIẾU. Trả về JSON đúng schema, không giải thích ngoài JSON."
)


def judge_block(ctx_item: dict, q: dict, answers: list[tuple[str, str]]) -> str:
    lines = [f"### {q['qid']}", f"NGỮ CẢNH:\n{context_text(ctx_item)}", f"CÂU HỎI: {q['question']}",
             f"CÂU HỎI CÓ ĐÁP ÁN TRONG NGỮ CẢNH: {'có' if q['answerable'] else 'KHÔNG – trả lời đúng là từ chối'}",
             f"ĐÁP ÁN THAM CHIẾU: {q['reference_answer']}", "CÁC CÂU TRẢ LỜI CẦN CHẤM:"]
    lines += [f"<{k}>\n{a}\n</{k}>" for k, a in answers]
    return "\n".join(lines)


JUDGE_RUBRIC = (
    "\nVới MỖI câu trả lời của MỖI câu hỏi, chấm:\n"
    "- faithfulness: số thực 0..1 = tỉ lệ ý/khẳng định trong câu trả lời được ngữ cảnh hỗ trợ (câu từ chối thuần → 1.0)\n"
    "- hallucination: true nếu có ít nhất 1 khẳng định KHÔNG có trong ngữ cảnh hoặc mâu thuẫn ngữ cảnh "
    "(kể cả bịa giá/size/tồn kho/thông số)\n"
    "- correctness: 1 nếu đúng ý đáp án tham chiếu (hoặc từ chối đúng khi không có đáp án), 0.5 nếu đúng một phần, "
    "0 nếu sai/từ chối sai/lạc đề/rỗng\n"
    "- refused: true nếu câu trả lời từ chối vì thiếu thông tin\n"
    "- note: ≤ 15 từ tiếng Việt\n"
    'Schema: {"<qid>": {"<nhãn>": {"faithfulness": 0.0, "hallucination": false, "correctness": 0, '
    '"refused": false, "note": ""}}}')


def run_judge(tags: list[str], thinking_budget: int | None = None, model: str | None = None,
              per_call: int = 4, only_qids: list[str] | None = None) -> Path:
    """Chấm bằng LLM-judge; gộp `per_call` câu hỏi/lời gọi để tiết kiệm quota (free tier 20 RPD/model)."""
    ctx = {c["product_id"]: c for c in load_jsonl(CTX_FILE)}
    qs = {q["qid"]: q for q in load_jsonl(QA_FILE)}
    ans: dict[str, dict[str, str]] = {}
    for t in tags:
        for r in load_jsonl(RES / f"bench_llm_qa_{t}.jsonl"):
            ans.setdefault(r["qid"], {})[t] = r["answer"] or "(câu trả lời rỗng)"
    llm = GeminiLLM(thinking_budget, model=model)
    out = RES / "bench_llm_judge.jsonl"
    rng = random.Random(42)
    qids = sorted(ans)
    mode = "w"
    if only_qids:  # chấm bổ sung các câu bị lỗi/thiếu, giữ kết quả cũ của câu khác
        keep = [r for r in load_jsonl(out) if r["qid"] not in only_qids and not r.get("error")] if out.exists() else []
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in keep), encoding="utf-8")
        qids, mode = [q for q in qids if q in only_qids], "a"
    with out.open(mode, encoding="utf-8") as f:
        for i in range(0, len(qids), per_call):
            chunk = qids[i:i + per_call]
            labels_by_q, blocks = {}, []
            for qid in chunk:
                items = list(ans[qid].items())
                rng.shuffle(items)  # ẩn danh + xáo thứ tự để giảm thiên vị vị trí
                labels = {f"A{j + 1}": t for j, (t, _) in enumerate(items)}
                labels_by_q[qid] = labels
                blocks.append(judge_block(ctx[qs[qid]["product_id"]], qs[qid],
                                          [(k, ans[qid][t]) for k, t in labels.items()]))
            r = llm.generate(JUDGE_SYSTEM, "\n\n".join(blocks) + JUDGE_RUBRIC, 600 * len(chunk), response_json=True)
            try:
                raw = json.loads(re.sub(r"^```(json)?|```$", "", r["answer"].strip()))
                err = None
            except (json.JSONDecodeError, AttributeError) as e:
                raw, err = {}, f"parse:{e}"
            for qid in chunk:
                sc = raw.get(qid, {}) if isinstance(raw, dict) else {}
                scores = {labels_by_q[qid][k]: v for k, v in sc.items() if k in labels_by_q[qid]}
                f.write(json.dumps(dict(qid=qid, judge_model=llm.name, labels=labels_by_q[qid], scores=scores,
                                        error=err or r.get("error"), batch_latency_ms=r["latency_ms"],
                                        batch_tokens_in=r["tokens_in"], batch_tokens_out=r["tokens_out"],
                                        batch_tokens_thinking=r.get("tokens_thinking", 0), batch_size=len(chunk)),
                                   ensure_ascii=False) + "\n")
            f.flush()
            print(chunk, "ok" if not (err or r.get("error")) else (err or r.get("error")), flush=True)
    return out


ROUTER_SYSTEM = (
    "Bạn là bộ định tuyến của trợ lý mua sắm thời trang (giày dép, quần áo, mũ, phụ kiện: túi, thắt lưng, kính). "
    "Phân loại tin nhắn vào ĐÚNG 1 route:\n"
    "- visual: người dùng gửi ảnh và muốn tìm sản phẩm giống ảnh\n"
    "- qa: hỏi về thuộc tính/đánh giá của 1 sản phẩm cụ thể (chất liệu, size, độ bền...)\n"
    "- search: tìm sản phẩm bằng mô tả chữ, có thể kèm bộ lọc giá/màu/size\n"
    "- compare: so sánh 2-3 sản phẩm\n"
    "- gemini_chitchat: chào hỏi, cảm ơn, nói chuyện phiếm, hỏi trợ lý là ai\n"
    "- gemini_ood: ngoài phạm vi cửa hàng (thời tiết, nấu ăn, code, sản phẩm không phải thời trang...) hoặc kiến thức chung\n"
    "- clarify: câu quá mơ hồ, thiếu thông tin để làm gì\n"
    "Nếu route là gemini_chitchat hoặc gemini_ood thì viết thêm câu trả lời ngắn (≤ 2 câu) tiếng Việt, thân thiện, "
    "KHÔNG nêu giá, size, tồn kho, khuyến mãi hay tên sản phẩm cụ thể của cửa hàng; với ood thì lịch sự kéo về mua sắm. "
    'Trả về JSON: {"route": "...", "confidence": 0.0, "reply": "..."} (reply rỗng với route khác).'
)
ROUTES = ["visual", "qa", "search", "compare", "gemini_chitchat", "gemini_ood", "clarify"]
STORE_FACT_RX = re.compile(r"\d+\s*(k|nghìn|ngàn|đ|vnđ|vnd|triệu)\b|\b(giá|size|còn hàng|hết hàng|tồn kho|"
                           r"khuyến mãi|giảm giá|freeship)\b", re.I)


def stratified(items: list[dict], per_route: int, seed: int = 42) -> list[dict]:
    """Lấy `per_route` câu mỗi route (seed cố định) – dùng khi quota Gemini hạn chế."""
    rng = random.Random(seed)
    out = []
    for rt in ROUTES:
        g = [it for it in items if it["route"] == rt]
        out += rng.sample(g, min(per_route, len(g)))
    return out


def run_router(tag: str, thinking_budget: int | None, limit: int | None = None, model: str | None = None,
               per_route: int | None = None) -> Path:
    items = load_jsonl(ROUTER_FILE)
    items = stratified(items, per_route) if per_route else items
    items = items[:limit] if limit else items
    llm = GeminiLLM(thinking_budget, model=model)
    out = RES / f"bench_llm_router_{tag}.jsonl"
    errs = 0
    with out.open("w", encoding="utf-8") as f:
        for it in items:
            msg = ("[Người dùng có gửi kèm 1 ảnh]\n" if it.get("has_image") else "") + f"Tin nhắn: {it['text']}"
            r = llm.generate(ROUTER_SYSTEM, msg, 300, response_json=True)
            try:
                d = json.loads(r["answer"])
                pred, conf, reply = d.get("route"), d.get("confidence"), d.get("reply", "") or ""
            except (json.JSONDecodeError, AttributeError):
                pred, conf, reply = None, None, ""
            row = dict(id=it["id"], text=it["text"], has_image=it.get("has_image"), gold=it["route"], pred=pred,
                       correct=pred == it["route"], confidence=conf, reply=reply,
                       store_fact_flag=bool(STORE_FACT_RX.search(reply)), latency_ms=r["latency_ms"],
                       tokens_in=r["tokens_in"], tokens_out=r["tokens_out"],
                       tokens_thinking=r.get("tokens_thinking", 0), cached=r.get("cached"), error=r.get("error"),
                       model=r.get("model"))
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            print(it["id"], it["route"], "->", pred, f"{r['latency_ms']:.0f}ms", flush=True)
            errs = errs + 1 if row["error"] else 0
            if errs >= 3:
                print("DỪNG: 3 lỗi liên tiếp", row["error"], r.get("error_detail"), flush=True)
                break
    return out


# ======================================================================= summary
def pct(xs: list[float], p: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    lo, hi = math.floor(k), math.ceil(k)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (k - lo), 1)


def cost_per_100(tin: float, tout: float, model: str) -> dict:
    """Token/100 câu (đo thật) + công thức quy tiền với đơn giá cấu hình (chưa xác minh)."""
    pr = PRICE_PER_1M.get(model, {})
    usd = None
    if pr.get("input") is not None and pr.get("output") is not None:
        usd = round((tin * pr["input"] + tout * pr["output"]) / 1e6, 4)
    return {"tokens_in_per_100": round(tin), "tokens_out_incl_thinking_per_100": round(tout), "usd_per_100": usd,
            "formula": "USD/100 = (tokens_in × giá_in + (tokens_out + tokens_thinking) × giá_out) / 1e6"}


def summarize() -> dict:
    judge = {r["qid"]: r for r in load_jsonl(RES / "bench_llm_judge.jsonl")} if (RES / "bench_llm_judge.jsonl").exists() else {}
    out: dict[str, Any] = {"qa": {}, "router": {}}
    for p in sorted(RES.glob("bench_llm_qa_*.jsonl")):
        tag = p.stem.replace("bench_llm_qa_", "")
        rows = load_jsonl(p)
        live = [r for r in rows if not r.get("cached")]
        lat = [r["latency_ms"] / 1000 for r in live if not r.get("error")]
        js = [judge[r["qid"]]["scores"].get(tag) for r in rows if r["qid"] in judge]
        js = [j for j in js if j]
        ans_rows = [r for r in rows if r["answerable"]]
        una_rows = [r for r in rows if not r["answerable"]]
        tin = statistics.mean([r["tokens_in"] for r in rows]) * 100 if rows else 0
        tout = statistics.mean([r["tokens_out"] + r.get("tokens_thinking", 0) for r in rows]) * 100 if rows else 0
        m: dict[str, Any] = dict(
            model=rows[0]["model"] if rows else None, n=len(rows), errors=sum(bool(r.get("error")) for r in rows),
            latency_s_p50=pct(lat, 0.5), latency_s_p95=pct(lat, 0.95), latency_s_mean=round(statistics.mean(lat), 2) if lat else None,
            n_latency_measured=len(lat),
            heur_support_overlap=round(statistics.mean(r["support_overlap"] for r in rows), 3) if rows else None,
            heur_citation_rate=round(sum(r["cited"] for r in rows) / len(rows), 3) if rows else None,
            heur_invalid_citation_answers=sum(bool(r["invalid_citations"]) for r in rows),
            heur_refusal_on_unanswerable=round(sum(r["refused"] for r in una_rows) / len(una_rows), 3) if una_rows else None,
            heur_false_refusal_on_answerable=round(sum(r["refused"] for r in ans_rows) / len(ans_rows), 3) if ans_rows else None,
            mean_tokens_thinking=round(statistics.mean(r.get("tokens_thinking", 0) for r in rows), 1) if rows else None,
            **cost_per_100(tin, tout, "gemini-3.5-flash" if "gemini" in tag else "local"))
        if js:
            m.update(judge_n=len(js),
                     faithfulness=round(statistics.mean(float(j.get("faithfulness", 0)) for j in js), 3),
                     hallucination_rate=round(sum(bool(j.get("hallucination")) for j in js) / len(js), 3),
                     correctness=round(statistics.mean(float(j.get("correctness", 0)) for j in js), 3))
            ja = [judge[r["qid"]]["scores"].get(tag) for r in ans_rows if r["qid"] in judge]
            ju = [judge[r["qid"]]["scores"].get(tag) for r in una_rows if r["qid"] in judge]
            ja, ju = [j for j in ja if j], [j for j in ju if j]
            if ja:
                m["correctness_answerable"] = round(statistics.mean(float(j.get("correctness", 0)) for j in ja), 3)
            if ju:
                m["correct_refusal_unanswerable"] = round(sum(bool(j.get("refused")) for j in ju) / len(ju), 3)
        out["qa"][tag] = m
    for p in sorted(RES.glob("bench_llm_router_*.jsonl")):
        tag = p.stem.replace("bench_llm_router_", "")
        rows = load_jsonl(p)
        lat = [r["latency_ms"] / 1000 for r in rows if not r.get("cached") and not r.get("error")]
        per = {}
        for rt in ROUTES:
            g = [r for r in rows if r["gold"] == rt]
            if g:
                per[rt] = {"n": len(g), "acc": round(sum(r["correct"] for r in g) / len(g), 3)}
        gem = [r for r in rows if r["pred"] in ("gemini_chitchat", "gemini_ood")]
        tin = statistics.mean([r["tokens_in"] for r in rows]) * 100
        tout = statistics.mean([r["tokens_out"] + r.get("tokens_thinking", 0) for r in rows]) * 100
        out["router"][tag] = dict(
            n=len(rows), errors=sum(bool(r.get("error")) for r in rows),
            route_accuracy=round(sum(r["correct"] for r in rows) / len(rows), 3), per_route=per,
            latency_s_p50=pct(lat, 0.5), latency_s_p95=pct(lat, 0.95), n_latency_measured=len(lat),
            n_replies=len(gem), store_fact_flagged=sum(r["store_fact_flag"] for r in gem),
            predicted_gemini_share=round(len(gem) / len(rows), 3),
            confusion=_confusion(rows), **cost_per_100(tin, tout, "gemini-3.5-flash"))
    if BUDGET_FILE.exists():
        out["gemini_calls_used_total"] = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))["calls"]
    (RES / "bench_llm_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (RES / "bench_llm_summary.md").write_text(render_summary_md(out), encoding="utf-8")
    return out


def _confusion(rows: list[dict]) -> dict:
    c: dict[str, dict[str, int]] = {}
    for r in rows:
        c.setdefault(r["gold"], {}).setdefault(str(r["pred"]), 0)
        c[r["gold"]][str(r["pred"])] += 1
    return c


def render_summary_md(s: dict) -> str:
    L = ["# Tổng hợp benchmark LLM (sinh tự động – results/bench_llm_summary.json)", "",
         "## Bảng D – LLM trả lời trên 36 câu hỏi từ review ViMRHP", "",
         "| Tag | Model | n | Faithfulness | Hallucination | Correctness | Từ chối đúng (7 câu không đáp án) | "
         "Latency p50/p95 (s) | Token in/100 | Token out+thinking/100 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for t, m in s["qa"].items():
        L.append(f"| {t} | {m['model']} | {m['n']} | {m.get('faithfulness', 'CHƯA ĐO')} | "
                 f"{m.get('hallucination_rate', 'CHƯA ĐO')} | {m.get('correctness', 'CHƯA ĐO')} | "
                 f"{m.get('correct_refusal_unanswerable', 'CHƯA ĐO')} | {m['latency_s_p50']}/{m['latency_s_p95']} | "
                 f"{m['tokens_in_per_100']} | {m['tokens_out_incl_thinking_per_100']} |")
    L += ["", "## Bảng D2 – Gemini vai trò Router/Fallback (eval_router)", "",
          "| Tag | n | Route accuracy | Latency p50/p95 (s) | Số reply chitchat/ood | Reply bị cờ dữ kiện cửa hàng | Token in/100 | Token out+thinking/100 |",
          "|---|---|---|---|---|---|---|---|"]
    for t, m in s["router"].items():
        L.append(f"| {t} | {m['n']} | {m['route_accuracy']} | {m['latency_s_p50']}/{m['latency_s_p95']} | "
                 f"{m['n_replies']} | {m['store_fact_flagged']} | {m['tokens_in_per_100']} | {m['tokens_out_incl_thinking_per_100']} |")
    L.append(f"\nTổng lời gọi Gemini đã dùng (kể cả retry): {s.get('gemini_calls_used_total')}")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["qa", "judge", "router", "summary"])
    ap.add_argument("--model", default="gemini")
    ap.add_argument("--tag")
    ap.add_argument("--tags")
    ap.add_argument("--thinking-budget", type=int, default=None)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--qids")
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--judge-model", default=None, help="model API làm giám khảo (mặc định GEMINI_MODEL)")
    ap.add_argument("--gemini-model", default=None, help="model API cho chế độ router")
    ap.add_argument("--per-route", type=int, default=None)
    ap.add_argument("--per-call", type=int, default=4)
    a = ap.parse_args()
    if a.mode == "qa":
        run_qa(make_llm(a.model, a.thinking_budget), a.tag, a.limit, a.max_tokens,
               a.qids.split(",") if a.qids else None)
    elif a.mode == "judge":
        run_judge(a.tags.split(","), a.thinking_budget, a.judge_model, a.per_call,
                  a.qids.split(",") if a.qids else None)
    elif a.mode == "router":
        run_router(a.tag, a.thinking_budget, a.limit, a.gemini_model, a.per_route)
    print(json.dumps(summarize(), ensure_ascii=False, indent=1)[:3000])


if __name__ == "__main__":
    main()
