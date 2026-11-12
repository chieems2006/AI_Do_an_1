# Client Gemini cũ của Chiến – CHỈ dùng cho các script đo đã sinh số liệu trong báo cáo
# (build_eval_qa.py, eval_rag.py, run_gemini_fallback_check.py). Hệ thống chạy dùng msa.llm_gateway.LLMGateway.
# Tách từ src/msa/rag/llm.py khi hợp nhất package (12/11/2026); nội dung không đổi.
"""Client REST Gemini tối thiểu của Chiến (US_33/US_51): cache SQLite, retry 429/5xx, log lời gọi thật."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]  # 03_Chien (log/cache giữ đúng chỗ cũ)
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
FALLBACK_MSG = "Xin lỗi, trợ lý đang bận hoặc mất kết nối. Bạn thử lại sau ít phút nhé."


def _load_key() -> str | None:
    """Lấy key từ env hoặc file .env (đường dẫn qua MSA_ENV_FILE). Không bao giờ log key."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    p = os.environ.get("MSA_ENV_FILE")
    if p and Path(p).exists():
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


class GeminiClient:
    """Client REST Gemini tối thiểu: timeout, retry/backoff 429/5xx, cache SQLite exact-match."""

    def __init__(self, model: str = DEFAULT_MODEL, cache_path: Path | None = None, timeout: float = 60.0,
                 max_retries: int = 3, thinking_budget: int | None = 0, log_path: Path | None = None,
                 tag: str = ""):
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.thinking_budget = thinking_budget
        self.tag = tag
        self.cache_path = cache_path or ROOT / "logs" / "gemini_cache.sqlite"
        self.log_path = log_path or ROOT / "logs" / "gemini_calls.jsonl"
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache_path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT)")

    def _key(self, payload: dict) -> str:
        return hashlib.sha256(json.dumps([self.model, payload], ensure_ascii=False, sort_keys=True)
                              .encode()).hexdigest()

    def generate(self, prompt: str, system: str | None = None, temperature: float = 0.2,
                 json_mode: bool = False, max_output_tokens: int = 2048, use_cache: bool = True,
                 **kw: Any) -> dict:
        """Gọi Gemini; trả dict{answer, source, cached, tokens_in, tokens_out, tokens_thinking, latency_ms, error}."""
        gen_cfg: dict[str, Any] = {"temperature": temperature, "maxOutputTokens": max_output_tokens}
        if self.thinking_budget is not None:
            gen_cfg["thinkingConfig"] = {"thinkingBudget": self.thinking_budget}
        if json_mode:
            gen_cfg["responseMimeType"] = "application/json"
        payload: dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                                   "generationConfig": gen_cfg}
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        k = self._key(payload)
        if use_cache:
            with sqlite3.connect(self.cache_path) as c:
                row = c.execute("SELECT v FROM cache WHERE k=?", (k,)).fetchone()
            if row:
                out = json.loads(row[0])
                out.update(cached=True, source="cache", latency_ms=0)
                return out
        key = _load_key()
        if not key:
            return {"answer": FALLBACK_MSG, "source": "gemini", "cached": False, "tokens_in": 0,
                    "tokens_out": 0, "tokens_thinking": 0, "latency_ms": 0, "error": "no_api_key"}
        import httpx

        err = None
        t0 = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            try:
                r = httpx.post(API_URL.format(model=self.model), json=payload, timeout=self.timeout,
                               headers={"x-goog-api-key": key, "Content-Type": "application/json"})
                self._log_call(r.status_code, attempt)
                if r.status_code == 200:
                    data = r.json()
                    um = data.get("usageMetadata", {})
                    cands = data.get("candidates") or [{}]
                    parts = cands[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
                    out = {"answer": text, "source": "gemini", "cached": False,
                           "tokens_in": um.get("promptTokenCount", 0),
                           "tokens_out": um.get("candidatesTokenCount", 0),
                           "tokens_thinking": um.get("thoughtsTokenCount", 0),
                           "finish_reason": cands[0].get("finishReason"),
                           "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "error": None}
                    if use_cache and text:
                        with sqlite3.connect(self.cache_path) as c:
                            c.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (k, json.dumps(out, ensure_ascii=False)))
                    return out
                err = f"http_{r.status_code}"
                if r.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(self._retry_delay(r.text, attempt))
                    continue
                # lỗi khác (vd. 400 do tham số): trả nội dung lỗi rút gọn (không chứa key)
                err += ":" + r.text[:1500].replace(key, "***")
                break
            except httpx.TimeoutException:
                err = "timeout"
                self._log_call("timeout", attempt)
                if attempt < self.max_retries:
                    continue
            except httpx.HTTPError as e:
                err = f"http_error:{type(e).__name__}"
                break
        return {"answer": FALLBACK_MSG, "source": "gemini", "cached": False, "tokens_in": 0, "tokens_out": 0,
                "tokens_thinking": 0, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "error": err}

    @staticmethod
    def _retry_delay(body: str, attempt: int) -> float:
        """Thời gian chờ: dùng `retryDelay` server gợi ý (429) nếu có, ngược lại backoff mũ."""
        import re as _re
        m = _re.search(r'"retryDelay":\s*"(\d+(?:\.\d+)?)s"', body or "")
        if m:
            return min(float(m.group(1)) + 1.0, 65.0)
        return min(2 ** attempt * 3, 30)

    def _log_call(self, status: Any, attempt: int) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": self.model, "tag": self.tag,
                                "status": status, "attempt": attempt,
                                "thinking_budget": self.thinking_budget}) + "\n")


def count_real_calls(log_path: Path | None = None) -> int:
    """Đếm số lời gọi HTTP thật đã thực hiện (để giữ ngân sách ≤ 250)."""
    p = log_path or ROOT / "logs" / "gemini_calls.jsonl"
    return sum(1 for _ in p.open(encoding="utf-8")) if p.exists() else 0

