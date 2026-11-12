# repo: src/msa/agent/gemini_client.py
"""Client Gemini REST tối giản (của Trung, để đo nhánh fallback) – tương thích giao diện LLMGateway (mục 5.3).

- Key đọc từ biến môi trường GEMINI_API_KEY, hoặc từ file chỉ định bởi MSA_GEMINI_KEY_FILE (dòng GEMINI_API_KEY=...).
  Key gửi qua header x-goog-api-key (không nằm trong URL) và KHÔNG bao giờ được in/ghi log.
- Cache exact-match SQLite: khoá = sha256(model | prompt_version | thinking_budget | system | câu đã chuẩn hoá).
- Retry/backoff khi 429/5xx; timeout; chế độ MSA_LLM_MOCK=1 trả câu giả lập (không gọi mạng).
- Trả dict{answer, source, cached, tokens_in, tokens_out, tokens_thinking, latency_ms, error, finish_reason}.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from typing import Any

from msa.textnorm import normalize

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")  # [cần xác minh định kỳ – R11]


def _read_key() -> str | None:
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k.strip()
    path = os.environ.get("MSA_GEMINI_KEY_FILE")
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _scrub(msg: str, key: str | None) -> str:
    """Xoá key khỏi thông điệp lỗi (phòng hờ)."""
    return msg.replace(key, "***") if key else msg


class GeminiRestClient:
    def __init__(self, model: str | None = None, thinking_budget: int | None = 0, cache_path: str | None = None,
                 timeout_s: float = 30.0, max_retries: int = 3, prompt_version: str = "trung-v1",
                 max_output_tokens: int = 512, temperature: float = 0.4):
        self.model = model or DEFAULT_MODEL
        self.thinking_budget = thinking_budget
        self.timeout_s, self.max_retries = timeout_s, max_retries
        self.prompt_version = prompt_version
        self.max_output_tokens, self.temperature = max_output_tokens, temperature
        self.mock = os.environ.get("MSA_LLM_MOCK") == "1"
        self.cache_path = cache_path
        self.calls_api = 0
        if cache_path:
            os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
            with sqlite3.connect(cache_path) as c:
                c.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT, ts REAL)")

    # ------------------------------------------------------------------ cache
    def cache_key(self, prompt: str, system: str | None) -> str:
        raw = "|".join([self.model, self.prompt_version, str(self.thinking_budget), system or "", normalize(prompt, expand_teencode=False)])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_get(self, k: str) -> dict | None:
        if not self.cache_path:
            return None
        with sqlite3.connect(self.cache_path) as c:
            row = c.execute("SELECT v FROM cache WHERE k=?", (k,)).fetchone()
        return json.loads(row[0]) if row else None

    def _cache_put(self, k: str, v: dict) -> None:
        if self.cache_path:
            with sqlite3.connect(self.cache_path) as c:
                c.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (k, json.dumps(v, ensure_ascii=False), time.time()))

    # ------------------------------------------------------------------ gọi
    def build_body(self, prompt: str, system: str | None) -> dict:
        gc: dict[str, Any] = {"maxOutputTokens": self.max_output_tokens, "temperature": self.temperature}
        if self.thinking_budget is not None:
            gc["thinkingConfig"] = {"thinkingBudget": self.thinking_budget}
        body: dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": gc}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        return body

    def generate(self, prompt: str, system: str | None = None, use_cache: bool = True, **kw: Any) -> dict:
        k = self.cache_key(prompt, system)
        if use_cache:
            hit = self._cache_get(k)
            if hit is not None:
                return dict(hit, cached=True, source="cache", latency_ms=0.0)
        if self.mock:
            out = dict(answer=f"[mock] Mình là trợ lý thời trang, bạn cần tìm gì ạ? ({prompt[:30]})", source="gemini", cached=False,
                       tokens_in=len(prompt.split()), tokens_out=12, tokens_thinking=0, latency_ms=1.0, error=None, finish_reason="MOCK")
            self._cache_put(k, out)
            return out
        key = _read_key()
        if not key:
            return dict(answer="", source="gemini", cached=False, tokens_in=0, tokens_out=0, tokens_thinking=0,
                        latency_ms=0.0, error="missing_api_key", finish_reason=None)
        import httpx

        url = API_URL.format(model=self.model)
        body = self.build_body(prompt, system)
        err = None
        t0 = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            try:
                self.calls_api += 1
                t_att = time.perf_counter()
                r = httpx.post(url, json=body, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, timeout=self.timeout_s)
                if r.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                    time.sleep(min(2 ** attempt * 2, 20))
                    err = f"http_{r.status_code}"
                    continue
                if r.status_code != 200:
                    err = _scrub(f"http_{r.status_code}: {r.text[:200]}", key)
                    break
                data = r.json()
                lat = (time.perf_counter() - t0) * 1000
                cand = (data.get("candidates") or [{}])[0]
                parts = (cand.get("content") or {}).get("parts") or []
                ans = "".join(p.get("text", "") for p in parts if not p.get("thought"))
                um = data.get("usageMetadata") or {}
                out = dict(answer=ans.strip(), source="gemini", cached=False, tokens_in=um.get("promptTokenCount", 0),
                           tokens_out=um.get("candidatesTokenCount", 0), tokens_thinking=um.get("thoughtsTokenCount", 0),
                           latency_ms=round(lat, 1), latency_ms_last_attempt=round((time.perf_counter() - t_att) * 1000, 1),
                           attempts=attempt + 1, error=None, finish_reason=cand.get("finishReason"),
                           model_version=data.get("modelVersion"))
                if out["answer"]:
                    self._cache_put(k, out)
                return out
            except Exception as e:  # timeout, mạng
                err = _scrub(f"{type(e).__name__}: {str(e)[:150]}", key)
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt * 2, 20))
                    continue
        return dict(answer="", source="gemini", cached=False, tokens_in=0, tokens_out=0, tokens_thinking=0,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 1), error=err, finish_reason=None)
