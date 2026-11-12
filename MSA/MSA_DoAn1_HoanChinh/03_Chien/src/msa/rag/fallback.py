# repo: src/msa/rag/fallback.py
"""US_51 – Nhánh Gemini: chitchat / ngoài phạm vi / fallback khi nội bộ không tự tin.

`GeminiFallback.respond(text, route) -> dict` theo định dạng response chung (route, source, answer, …):
- prompt hệ thống + few-shot đọc từ `prompts/gemini_fallback.md` (có version);
- hậu kiểm regex giá/size/tồn kho/chính sách (check_gemini_hallucination) → vi phạm thì thay câu an toàn;
- 429/timeout/lỗi mạng → thông điệp dự phòng (không ném lỗi lên UI);
- `should_fallback(...)`: luật R14 – câu có product_id KHÔNG chuyển Gemini trừ khi retrieval rỗng.
"""
from __future__ import annotations

import importlib.util
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATH = ROOT / "prompts" / "gemini_fallback.md"
GEMINI_ROUTES = {"gemini_chitchat", "gemini_ood"}
LABEL = "Trả lời bởi Gemini – thông tin tham khảo chung"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_gemini_hallucination",
                                                  ROOT / "src" / "scripts" / "check_gemini_hallucination.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.check_text


check_text = _load_checker()


def load_fallback_prompt(path: Path = PROMPT_PATH) -> dict[str, Any]:
    """Đọc system, few-shot, thông điệp dự phòng và version từ file markdown."""
    text = path.read_text(encoding="utf-8")
    blocks = {m.group(1): m.group(2).strip() for m in re.finditer(r"```(\w+)\n(.*?)```", text, re.S)}
    ver = re.search(r"Phiên bản hiện hành:\*\*\s*(v[\d.]+)", text)
    return {"system": blocks["system"], "fewshot": json.loads(blocks["fewshot"]),
            "messages": json.loads(blocks["fallback_messages"]), "version": ver.group(1) if ver else "unknown"}


def should_fallback(route: str, confidence: float, product_id: str | None, retrieval_empty: bool,
                    tau: float = 0.6) -> bool:
    """Quyết định chuyển Gemini: route Gemini; hoặc nội bộ không tự tin (< τ) và KHÔNG có product_id (R14)."""
    if route in GEMINI_ROUTES:
        return True
    if product_id:
        return retrieval_empty
    return confidence < tau


def render_prompt(cfg: dict[str, Any], text: str) -> str:
    """Ghép few-shot dạng hội thoại vào prompt (gateway hiện chỉ nhận 1 chuỗi prompt)."""
    shots = "\n".join(f"Người dùng: {s['user']}\nMia: {s['model']}" for s in cfg["fewshot"])
    return f"Ví dụ cách trả lời:\n{shots}\n\nNgười dùng: {text}\nMia:"


class GeminiFallback:
    """Bọc LLM (LLMGateway/GeminiClient/MockLLM) cho nhánh Gemini."""

    def __init__(self, llm: Any, prompt_path: Path = PROMPT_PATH):
        self.llm = llm
        self.cfg = load_fallback_prompt(prompt_path)

    def respond(self, text: str, route: str = "gemini_chitchat") -> dict[str, Any]:
        t0 = time.perf_counter()
        res = self.llm.generate(render_prompt(self.cfg, text), system=self.cfg["system"], temperature=0.5,
                                max_output_tokens=400)
        out = {"route": route, "confidence": 1.0, "source": "cache" if res.get("cached") else "gemini",
               "label": LABEL, "items": [], "citations": [], "request_id": str(uuid.uuid4()),
               "prompt_version": self.cfg["version"], "error": res.get("error"), "postcheck": None,
               "tokens_in": res.get("tokens_in", 0), "tokens_out": res.get("tokens_out", 0)}
        if res.get("error"):
            out["answer"] = self.cfg["messages"]["llm_error"]
        else:
            chk = check_text(res.get("answer", ""))
            out["postcheck"] = chk
            out["answer"] = self.cfg["messages"]["postcheck_violation"] if chk["violation"] else res["answer"].strip()
            out["raw_answer"] = res.get("answer", "")
        out["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return out
