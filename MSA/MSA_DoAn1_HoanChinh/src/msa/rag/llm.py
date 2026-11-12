# repo: src/msa/rag/llm.py
"""Lớp LLM tối thiểu cho RAG + Gemini fallback (Chiến).

- Giao diện theo hợp đồng `LLMGateway.generate(...) -> dict` của Hoàng (mục 5.3).
- `get_llm()` trả `MockLLM` khi `MSA_LLM_MOCK=1`, ngược lại `msa.llm_gateway.LLMGateway` – client Gemini DUY NHẤT
  của hệ thống (cache, retry, nhãn source="gemini"|"cache"|"fallback").
- Client REST cũ của Chiến (dùng cho các script đo đã báo cáo) nằm ở `03_Chien/src/msa_chien/gemini_client.py`.
"""
from __future__ import annotations

import os
from typing import Any, Callable

FALLBACK_MSG = "Xin lỗi, trợ lý đang bận hoặc mất kết nối. Bạn thử lại sau ít phút nhé."


class MockLLM:
    """LLM giả cho test: trả lời theo hàm `responder(prompt, system)` hoặc chuỗi cố định."""

    def __init__(self, responder: Callable[[str, str | None], str] | None = None):
        self.responder = responder or (lambda p, s: "Đây là câu trả lời giả lập.")
        self.calls: list[dict] = []

    def generate(self, prompt: str, system: str | None = None, **kw: Any) -> dict:
        self.calls.append({"prompt": prompt, "system": system, **kw})
        ans = self.responder(prompt, system)
        return {"answer": ans, "source": "gemini", "cached": False, "tokens_in": 0, "tokens_out": 0,
                "tokens_thinking": 0, "latency_ms": 0, "error": None}


def get_llm(**kw: Any):
    """Trả về LLM: `MockLLM` nếu MSA_LLM_MOCK=1, ngược lại `LLMGateway` (kw chuyển thẳng cho LLMGateway)."""
    if os.environ.get("MSA_LLM_MOCK") == "1":
        return MockLLM()
    from msa.llm_gateway import LLMGateway

    return LLMGateway(**kw)
