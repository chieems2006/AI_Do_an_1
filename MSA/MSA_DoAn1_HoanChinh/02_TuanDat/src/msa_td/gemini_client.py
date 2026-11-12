# repo: src/msa/llm/gemini_rest.py  (bản rút gọn để Hoàng tái dùng trong LLMGateway – US_24/US_50)
"""Client REST tối giản cho Gemini: cache SQLite exact-match, đếm lời gọi (ngân sách), retry 429/5xx,
đo latency và token thật từ `usageMetadata`. KHÔNG bao giờ in/ghi API key.

Nạp key: biến môi trường GEMINI_API_KEY, hoặc đường dẫn file `KEY=VALUE` trong MSA_ENV_FILE.
Chế độ giả lập: MSA_LLM_MOCK=1 (không gọi mạng).
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import requests

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")


def load_api_key() -> str | None:
    """Đọc key từ env hoặc file MSA_ENV_FILE; trả None nếu không có. Không log key."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    env_file = os.environ.get("MSA_ENV_FILE")
    if env_file and Path(env_file).exists():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


class BudgetExceeded(RuntimeError):
    """Vượt ngân sách số lời gọi Gemini."""


@dataclass
class GeminiClient:
    """Gọi Gemini generateContent qua REST.

    budget_file: file JSON đếm số lời gọi THẬT (không tính cache) – dùng chung giữa các script.
    """

    model: str = DEFAULT_MODEL
    cache_path: str | None = None
    budget_file: str | None = None
    max_calls: int = 250
    timeout_s: float = 60.0
    max_retries: int = 3
    mock: bool = field(default_factory=lambda: os.environ.get("MSA_LLM_MOCK") == "1")
    _session: Any = None
    mock_fn: Callable[[str, str | None], str] | None = None
    circuit_429: int = 3
    _consecutive_429: int = 0
    last_429_info: dict | None = None
    last_error_detail: str | None = None

    @staticmethod
    def retry_delay_s(resp: Any) -> float | None:
        """Đọc RetryInfo.retryDelay ('12s') trong body lỗi 429 của Google API."""
        try:
            for d in resp.json().get("error", {}).get("details", []):
                if d.get("@type", "").endswith("RetryInfo"):
                    return float(str(d.get("retryDelay", "")).rstrip("s"))
        except (ValueError, AttributeError):
            pass
        return None

    @staticmethod
    def quota_info(resp: Any) -> dict:
        """Tóm tắt QuotaFailure (quotaId/metric) để ghi log – không chứa key."""
        info: dict[str, Any] = {}
        try:
            err = resp.json().get("error", {})
            info["status"] = err.get("status")
            for d in err.get("details", []):
                if d.get("@type", "").endswith("QuotaFailure"):
                    info["violations"] = [{k: v.get(k) for k in ("quotaMetric", "quotaId", "quotaValue")}
                                          for v in d.get("violations", [])]
        except (ValueError, AttributeError):
            pass
        return info

    def __post_init__(self) -> None:
        self._key = None if self.mock else load_api_key()
        if not self.mock and not self._key:
            raise RuntimeError("Không có GEMINI_API_KEY (đặt env hoặc MSA_ENV_FILE) – hoặc bật MSA_LLM_MOCK=1")
        self._session = requests.Session()
        self._db = None
        if self.cache_path:
            Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(self.cache_path)
            self._db.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT)")

    # ---------- ngân sách ----------
    def _calls_used(self) -> int:
        if not self.budget_file or not Path(self.budget_file).exists():
            return 0
        return int(json.loads(Path(self.budget_file).read_text()).get("calls", 0))

    def _inc_calls(self) -> None:
        if not self.budget_file:
            return
        Path(self.budget_file).parent.mkdir(parents=True, exist_ok=True)
        n = self._calls_used() + 1
        Path(self.budget_file).write_text(json.dumps({"calls": n, "max_calls": self.max_calls}))

    # ---------- cache ----------
    @staticmethod
    def cache_key(model: str, prompt: str, system: str | None, cfg: dict) -> str:
        raw = json.dumps([model, prompt, system, cfg], ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def generate(self, prompt: str, system: str | None = None, temperature: float = 0.0,
                 max_output_tokens: int = 1024, thinking_budget: int | None = None,
                 response_json: bool = False) -> dict:
        """Trả dict{answer, source, cached, tokens_in, tokens_out, tokens_thinking, latency_ms, error, model}."""
        cfg: dict[str, Any] = {"temperature": temperature, "maxOutputTokens": max_output_tokens}
        is_gemma = self.model.startswith("gemma")
        if thinking_budget is not None and not is_gemma:
            cfg["thinkingConfig"] = {"thinkingBudget": thinking_budget}
        if response_json and not is_gemma:
            cfg["responseMimeType"] = "application/json"
        if is_gemma and system:  # Gemma qua API không nhận systemInstruction → ghép vào đầu prompt
            prompt, system = f"{system}\n\n{prompt}", None
        k = self.cache_key(self.model, prompt, system, cfg)
        if self._db is not None:
            row = self._db.execute("SELECT v FROM cache WHERE k=?", (k,)).fetchone()
            if row:
                out = json.loads(row[0])
                out.update(cached=True, source="cache", latency_ms_cached_original=out.get("latency_ms"))
                return out
        if self.mock:
            text = self.mock_fn(prompt, system) if self.mock_fn else "[MOCK] Xin chào, mình là trợ lý mua sắm."
            return dict(answer=text, source="gemini", cached=False, tokens_in=0, tokens_out=0,
                        tokens_thinking=0, latency_ms=0.0, error=None, model=f"mock:{self.model}")
        if self._calls_used() >= self.max_calls:
            raise BudgetExceeded(f"Đã dùng {self._calls_used()}/{self.max_calls} lời gọi Gemini")
        body: dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": cfg}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        url = f"{API_BASE}/{self.model}:generateContent"
        err = None
        data: dict = {}
        t0 = time.perf_counter()
        for attempt in range(self.max_retries + 1):
            if self._consecutive_429 >= self.circuit_429:
                err = "circuit_open_429"  # ngắt mạch: không gọi thêm khi quota đang cạn
                break
            self._inc_calls()
            try:
                r = self._session.post(url, json=body, timeout=self.timeout_s,
                                       headers={"x-goog-api-key": self._key or ""})
            except requests.RequestException as e:  # timeout / mạng
                err = f"network:{type(e).__name__}"
                time.sleep(2 ** attempt)
                continue
            if r.status_code == 200:
                data, err = r.json(), None
                self._consecutive_429 = 0
                break
            err = f"http_{r.status_code}"
            try:
                self.last_error_detail = str(r.json().get("error", {}).get("message", ""))[:300]
            except ValueError:
                self.last_error_detail = r.text[:300]
            if r.status_code == 429:
                self._consecutive_429 += 1
                delay = self.retry_delay_s(r)
                self.last_429_info = self.quota_info(r)
                # chỉ thử lại 1 lần với 429, và chỉ khi server bảo chờ ≤ 60 s
                if attempt == 0 and delay is not None and delay <= 60:
                    time.sleep(delay + 1)
                    continue
                break
            if r.status_code in (500, 502, 503, 504) and attempt < self.max_retries:
                time.sleep(min(30, 2 ** (attempt + 1)))
                continue
            break
        latency = (time.perf_counter() - t0) * 1000
        text = ""
        try:
            parts = data["candidates"][0]["content"].get("parts", [])
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        except (KeyError, IndexError, TypeError):
            if err is None:
                err = "empty_response"
        um = data.get("usageMetadata", {}) if data else {}
        out = dict(answer=text.strip(), source="gemini", cached=False,
                   tokens_in=um.get("promptTokenCount", 0), tokens_out=um.get("candidatesTokenCount", 0),
                   tokens_thinking=um.get("thoughtsTokenCount", 0), latency_ms=round(latency, 1),
                   error=err, model=data.get("modelVersion", self.model) if data else self.model,
                   finish_reason=(data.get("candidates") or [{}])[0].get("finishReason") if data else None,
                   error_detail=self.last_error_detail if err else None)
        if self._db is not None and err is None:
            self._db.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (k, json.dumps(out, ensure_ascii=False)))
            self._db.commit()
        return out
