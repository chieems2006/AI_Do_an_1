# repo: src/msa/llm_gateway.py
"""LLM Gateway dùng chung cho mọi nhánh gọi Gemini (US_50 – Owner: Hoàng, Support: Tuấn Đạt).

- Đọc `GEMINI_API_KEY`, `GEMINI_MODEL` (mặc định `gemini-3.5-flash`) từ biến môi trường – KHÔNG hard-code key.
- Gọi REST `generateContent` qua httpx (header `x-goog-api-key`, key không bao giờ nằm trong URL/log).
- Timeout; retry exponential backoff + jitter cho 429/5xx/timeout (tôn trọng `Retry-After`); rate limiter token-bucket.
- Cache exact-match SQLite (+ hook semantic cache); đếm lời gọi/token/fallback; log JSONL không chứa key/prompt thô.
- Chế độ mock `MSA_LLM_MOCK=1` cho test/demo offline. CHỈ gửi text – từ chối mọi tham số ảnh.
- Tuỳ chọn hạ "thinking": `thinking_budget` (int) hoặc `thinking_level` ("low"/"high"...).

Hợp đồng (mục 5.3): `LLMGateway.generate(prompt, system=None, **kw) -> dict` với các khoá
`answer, source, cached, tokens_in, tokens_out, tokens_thinking, latency_ms, error` (+ `model, origin, mock, retries,
finish_reason, api_latency_ms` = thời gian riêng lời gọi HTTP thành công, `wait_ms` = chờ rate limiter/backoff).
`source` ∈ {"gemini", "cache", "fallback"}: "fallback" = thông điệp dự phòng khi API lỗi (đề xuất bổ sung vào mục 5.2).
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

import httpx

DEFAULT_MODEL = "gemini-3.5-flash"  # [cần xác minh] tên model theo tài liệu Google hiện hành; đã gọi thử thành công 11/2026
API_BASE = "https://generativelanguage.googleapis.com/v1beta"
FALLBACK_VI = ("Xin lỗi, trợ lý trò chuyện đang tạm thời quá tải hoặc mất kết nối. "
               "Bạn vẫn có thể tìm sản phẩm bằng ảnh, tìm theo mô tả hoặc so sánh sản phẩm; vui lòng thử lại sau ít phút.")
RETRY_STATUS = {429, 500, 502, 503, 504}
_IMAGE_KW = {"image", "images", "inline_data", "inlineData", "file_data", "fileData", "image_bytes"}


def load_env_file(path: str | os.PathLike, override: bool = False) -> list[str]:
    """Nạp file dạng KEY=VALUE vào os.environ (không in giá trị). Trả về danh sách tên biến đã nạp."""
    loaded = []
    p = Path(path)
    if not p.exists():
        return loaded
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'")
        if override or k not in os.environ:
            os.environ[k] = v
            loaded.append(k)
    return loaded


class TokenBucket:
    """Rate limiter token-bucket: `rate` token/giây, tối đa `capacity` token. `acquire()` chờ khi hết token."""

    def __init__(self, rate: float, capacity: float, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep):
        self.rate, self.capacity = rate, capacity
        self.tokens = capacity
        self.clock, self.sleep = clock, sleep
        self.t = clock()
        self.lock = threading.Lock()

    def acquire(self) -> float:
        """Lấy 1 token, trả số giây đã phải chờ."""
        waited = 0.0
        with self.lock:
            while True:
                now = self.clock()
                self.tokens = min(self.capacity, self.tokens + (now - self.t) * self.rate)
                self.t = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return waited
                need = (1 - self.tokens) / self.rate
                self.sleep(need)
                waited += need


class SQLiteCache:
    """Cache exact-match: khoá = sha256(model, system, prompt, tham số sinh)."""

    def __init__(self, path: str | os.PathLike):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS llm_cache (key TEXT PRIMARY KEY, model TEXT, value TEXT, "
                          "created_at REAL, hits INTEGER DEFAULT 0)")
        self.conn.commit()
        self.lock = threading.Lock()

    def get(self, key: str) -> dict | None:
        with self.lock:
            row = self.conn.execute("SELECT value FROM llm_cache WHERE key=?", (key,)).fetchone()
            if row:
                self.conn.execute("UPDATE llm_cache SET hits = hits + 1 WHERE key=?", (key,))
                self.conn.commit()
        return json.loads(row[0]) if row else None

    def put(self, key: str, model: str, value: dict) -> None:
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO llm_cache(key, model, value, created_at, hits) VALUES (?,?,?,?,0)",
                              (key, model, json.dumps(value, ensure_ascii=False), time.time()))
            self.conn.commit()

    def size(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM llm_cache").fetchone()[0]


class SemanticCacheProto(Protocol):
    """Hook semantic cache (cho chitchat): get trả dict đã lưu nếu câu đủ gần, put lưu kết quả."""

    def get(self, prompt: str, system: str | None) -> dict | None: ...

    def put(self, prompt: str, system: str | None, value: dict) -> None: ...


class SemanticCache:
    """Semantic cache đơn giản: `embed_fn(list[str]) -> np.ndarray` (L2-normalized), cosine ≥ threshold → hit."""

    def __init__(self, embed_fn: Callable[[list[str]], Any], threshold: float = 0.92, max_items: int = 5000):
        import numpy as np
        self.np = np
        self.embed_fn, self.threshold, self.max_items = embed_fn, threshold, max_items
        self.vecs: list = []
        self.items: list[tuple[str | None, dict]] = []

    def get(self, prompt: str, system: str | None) -> dict | None:
        if not self.vecs:
            return None
        q = self.np.asarray(self.embed_fn([prompt]))[0]
        sims = self.np.stack(self.vecs) @ q
        i = int(sims.argmax())
        if sims[i] >= self.threshold and self.items[i][0] == system:
            return dict(self.items[i][1], semantic_score=float(sims[i]))
        return None

    def put(self, prompt: str, system: str | None, value: dict) -> None:
        if len(self.vecs) >= self.max_items:
            self.vecs.pop(0)
            self.items.pop(0)
        self.vecs.append(self.np.asarray(self.embed_fn([prompt]))[0])
        self.items.append((system, value))


@dataclass
class GatewayStats:
    """Bộ đếm phục vụ bảng 'tỉ lệ chuyển Gemini & chi phí/100 lượt'."""
    requests: int = 0
    api_calls: int = 0
    cache_hits: int = 0
    semantic_hits: int = 0
    errors: int = 0
    fallbacks: int = 0
    retries: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_thinking: int = 0
    latencies_ms: list = field(default_factory=list)

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "latencies_ms"}
        d["cache_hit_rate"] = (self.cache_hits + self.semantic_hits) / self.requests if self.requests else 0.0
        return d


class GeminiAPIError(Exception):
    def __init__(self, status: int | None, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.status, self.retry_after = status, retry_after


class LLMGateway:
    """Cổng gọi Gemini dùng chung. Xem docstring module."""

    def __init__(self, model: str | None = None, api_key: str | None = None, *, timeout: float | None = None,
                 max_retries: int | None = None, backoff_base: float = 1.0, backoff_max: float = 30.0,
                 cache_path: str | None = None, use_cache: bool = True, mock: bool | None = None,
                 rpm: float | None = None, thinking_budget: int | None = None, thinking_level: str | None = None,
                 max_output_tokens: int | None = None, temperature: float | None = None,
                 transport: httpx.BaseTransport | None = None, semantic_cache: SemanticCacheProto | None = None,
                 log_path: str | None = None, sleep: Callable[[float], None] = time.sleep,
                 fallback_message: str = FALLBACK_VI):
        env = os.environ
        self.model = model or env.get("GEMINI_MODEL") or DEFAULT_MODEL
        self._api_key = api_key if api_key is not None else env.get("GEMINI_API_KEY", "")
        self.mock = (env.get("MSA_LLM_MOCK", "0") == "1") if mock is None else mock
        self.timeout = float(timeout if timeout is not None else env.get("GEMINI_TIMEOUT", 30))
        self.max_retries = int(max_retries if max_retries is not None else env.get("GEMINI_MAX_RETRIES", 3))
        self.backoff_base, self.backoff_max = backoff_base, backoff_max
        self.sleep = sleep
        tb = thinking_budget if thinking_budget is not None else env.get("GEMINI_THINKING_BUDGET")
        self.thinking_budget = int(tb) if tb not in (None, "") else None
        self.thinking_level = thinking_level or env.get("GEMINI_THINKING_LEVEL") or None
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.fallback_message = fallback_message
        rpm = float(rpm if rpm is not None else env.get("GEMINI_RPM", 4))  # free tier đo được: 5 RPM/project/model
        self.limiter = TokenBucket(rate=rpm / 60.0, capacity=max(1.0, min(rpm, 5.0)), sleep=sleep) if rpm > 0 else None
        self.use_cache = use_cache and env.get("MSA_LLM_CACHE", "1") != "0"
        cp = cache_path or env.get("MSA_LLM_CACHE_PATH") or "data/cache/llm_cache.sqlite"
        self.cache = SQLiteCache(cp) if self.use_cache else None
        self.semantic_cache = semantic_cache
        lp = log_path if log_path is not None else os.path.join(env.get("MSA_LOG_DIR", "logs"), "llm_calls.jsonl")
        self.log_path = lp or None
        self.client = httpx.Client(timeout=self.timeout, transport=transport)
        self.stats = GatewayStats()

    # ---------------- tiện ích ----------------
    def __repr__(self) -> str:  # không bao giờ lộ key
        return f"LLMGateway(model={self.model!r}, mock={self.mock}, key_set={bool(self._api_key)})"

    def _redact(self, s: str) -> str:
        return s.replace(self._api_key, "***") if self._api_key else s

    def _gen_config(self, kw: dict) -> dict:
        cfg: dict[str, Any] = {}
        t = kw.get("temperature", self.temperature)
        if t is not None:
            cfg["temperature"] = t
        m = kw.get("max_output_tokens", self.max_output_tokens)
        if m is not None:
            cfg["maxOutputTokens"] = int(m)
        tb = kw.get("thinking_budget", self.thinking_budget)
        tl = kw.get("thinking_level", self.thinking_level)
        if tb is not None or tl is not None:
            cfg["thinkingConfig"] = {"thinkingBudget": int(tb)} if tb is not None else {"thinkingLevel": tl}
        return cfg

    def cache_key(self, prompt: str, system: str | None, kw: dict) -> str:
        blob = json.dumps({"m": self.model, "s": system, "p": prompt, "g": self._gen_config(kw)},
                          ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _log(self, rec: dict) -> None:
        if not self.log_path:
            return
        try:
            Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(self._redact(json.dumps(rec, ensure_ascii=False)) + "\n")
        except OSError:
            pass

    def _result(self, **kw) -> dict:
        base = {"answer": "", "source": "gemini", "origin": "gemini", "cached": False, "tokens_in": 0, "tokens_out": 0,
                "tokens_thinking": 0, "latency_ms": 0.0, "error": None, "model": self.model, "mock": self.mock,
                "retries": 0, "finish_reason": None, "model_version": None, "api_latency_ms": None, "wait_ms": 0.0}
        base.update(kw)
        return base

    # ---------------- gọi API ----------------
    def _call_api(self, prompt: str, system: str | None, kw: dict) -> dict:
        body: dict[str, Any] = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        gc = self._gen_config(kw)
        if gc:
            body["generationConfig"] = gc
        url = f"{API_BASE}/models/{self.model}:generateContent"
        try:
            r = self.client.post(url, json=body, headers={"x-goog-api-key": self._api_key,
                                                          "Content-Type": "application/json"})
        except httpx.TimeoutException as e:
            raise GeminiAPIError(None, f"timeout: {type(e).__name__}") from None
        except httpx.TransportError as e:
            raise GeminiAPIError(None, f"transport: {type(e).__name__}") from None
        if r.status_code != 200:
            ra = r.headers.get("retry-after")
            retry_after = float(ra) if ra and ra.replace(".", "", 1).isdigit() else None
            try:
                err = r.json().get("error", {})
                msg = err.get("message", "")[:200]
                for d in err.get("details") or []:  # google.rpc.RetryInfo {"retryDelay": "12s"}
                    if str(d.get("@type", "")).endswith("RetryInfo") and str(d.get("retryDelay", "")).endswith("s"):
                        retry_after = float(d["retryDelay"][:-1])
                    if str(d.get("@type", "")).endswith("QuotaFailure"):
                        v = (d.get("violations") or [{}])[0]
                        msg += f" | quotaId={v.get('quotaId')} quotaValue={v.get('quotaValue')}"
            except Exception:
                msg = r.text[:200]
            raise GeminiAPIError(r.status_code, self._redact(f"HTTP {r.status_code}: {msg}"), retry_after)
        data = r.json()
        um = data.get("usageMetadata", {}) or {}
        cands = data.get("candidates") or []
        text, finish = "", None
        if cands:
            finish = cands[0].get("finishReason")
            parts = (cands[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        return {"answer": text.strip(), "tokens_in": int(um.get("promptTokenCount", 0)),
                "tokens_out": int(um.get("candidatesTokenCount", 0)), "tokens_thinking": int(um.get("thoughtsTokenCount", 0)),
                "finish_reason": finish, "block_reason": (data.get("promptFeedback") or {}).get("blockReason"),
                "model_version": data.get("modelVersion")}

    def _mock(self, prompt: str, system: str | None) -> dict:
        n_in = len(((system or "") + " " + prompt).split())
        ans = f"[MOCK] Trả lời mẫu cho: {prompt[:80]}"
        return {"answer": ans, "tokens_in": n_in, "tokens_out": len(ans.split()), "tokens_thinking": 0,
                "finish_reason": "STOP", "block_reason": None, "model_version": "mock"}

    def _backoff(self, attempt: int, retry_after: float | None) -> float:
        d = min(self.backoff_max, self.backoff_base * (2 ** attempt)) + random.uniform(0, self.backoff_base)
        if retry_after is not None:
            d = max(d, min(retry_after, self.backoff_max))
        return d

    def generate(self, prompt: str, system: str | None = None, **kw) -> dict:
        """Sinh câu trả lời. kw: temperature, max_output_tokens, thinking_budget, thinking_level, use_cache(bool).
        Không bao giờ raise khi API lỗi: trả `source="fallback"`, `answer`=thông điệp dự phòng, `error`=mô tả lỗi."""
        if _IMAGE_KW & set(kw):
            raise ValueError("LLMGateway chỉ gửi text cho Gemini – không gửi ảnh người dùng (quy tắc 5.4).")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt rỗng")
        t0 = time.perf_counter()
        self.stats.requests += 1
        use_cache = kw.pop("use_cache", True) and self.cache is not None
        key = self.cache_key(prompt, system, kw)
        rec = {"ts": time.time(), "model": self.model, "prompt_sha": key[:16], "mock": self.mock}
        if use_cache:
            hit = self.cache.get(key)
            if hit is not None:
                self.stats.cache_hits += 1
                lat = (time.perf_counter() - t0) * 1000
                res = self._result(**{**hit, "source": "cache", "origin": hit.get("origin", "gemini"), "cached": True,
                                      "latency_ms": lat, "retries": 0, "orig_latency_ms": hit.get("latency_ms")})
                self.stats.latencies_ms.append(lat)
                self._log({**rec, "event": "cache_hit", "latency_ms": lat})
                return res
        if self.semantic_cache is not None:
            sh = self.semantic_cache.get(prompt, system)
            if sh is not None:
                self.stats.semantic_hits += 1
                lat = (time.perf_counter() - t0) * 1000
                self._log({**rec, "event": "semantic_hit", "latency_ms": lat})
                return self._result(**{**sh, "source": "cache", "cached": True, "latency_ms": lat})
        if not self.mock and not self._api_key:
            self.stats.errors += 1
            self.stats.fallbacks += 1
            self._log({**rec, "event": "error", "error": "missing_api_key"})
            return self._result(answer=self.fallback_message, source="fallback", origin="fallback",
                                error="missing_api_key: chưa đặt GEMINI_API_KEY",
                                latency_ms=(time.perf_counter() - t0) * 1000)
        attempt, last_err, wait_ms, api_ms = 0, None, 0.0, 0.0
        while True:
            if self.limiter is not None and not self.mock:
                wait_ms += self.limiter.acquire() * 1000
            try:
                if not self.mock:
                    self.stats.api_calls += 1
                ta = time.perf_counter()
                out = self._mock(prompt, system) if self.mock else self._call_api(prompt, system, kw)
                api_ms = (time.perf_counter() - ta) * 1000
                break
            except GeminiAPIError as e:
                last_err = e
                retryable = e.status is None or e.status in RETRY_STATUS
                if e.status == 429 and "PerDay" in str(e):  # hết quota NGÀY → retry vô ích, trả dự phòng ngay
                    retryable = False
                if not retryable or attempt >= self.max_retries:
                    self.stats.errors += 1
                    self.stats.fallbacks += 1
                    lat = (time.perf_counter() - t0) * 1000
                    self._log({**rec, "event": "error", "status": e.status, "error": str(e), "retries": attempt,
                               "latency_ms": lat})
                    return self._result(answer=self.fallback_message, source="fallback", origin="fallback",
                                        error=str(e), latency_ms=lat, retries=attempt)
                self.stats.retries += 1
                b = self._backoff(attempt, e.retry_after)
                wait_ms += b * 1000
                self.sleep(b)
                attempt += 1
        lat = (time.perf_counter() - t0) * 1000
        self.stats.tokens_in += out["tokens_in"]
        self.stats.tokens_out += out["tokens_out"]
        self.stats.tokens_thinking += out["tokens_thinking"]
        self.stats.latencies_ms.append(lat)
        err = None
        if not out["answer"]:
            err = f"empty_answer (finish={out['finish_reason']}, block={out.get('block_reason')})"
            self.stats.errors += 1
        res = self._result(answer=out["answer"] or self.fallback_message, source="gemini" if out["answer"] else "fallback",
                           origin="gemini" if out["answer"] else "fallback", tokens_in=out["tokens_in"],
                           tokens_out=out["tokens_out"], tokens_thinking=out["tokens_thinking"], latency_ms=lat,
                           error=err, retries=attempt, finish_reason=out["finish_reason"],
                           model_version=out.get("model_version"), api_latency_ms=api_ms, wait_ms=wait_ms)
        if err is None:
            if use_cache:
                self.cache.put(key, self.model, {k: res[k] for k in ("answer", "tokens_in", "tokens_out",
                                                                     "tokens_thinking", "latency_ms", "model",
                                                                     "finish_reason", "mock", "origin",
                                                                     "model_version")})
            if self.semantic_cache is not None:
                self.semantic_cache.put(prompt, system, {k: res[k] for k in ("answer", "model", "origin")})
        else:
            self.stats.fallbacks += 1
        self._log({**rec, "event": "call", "latency_ms": lat, "api_latency_ms": api_ms, "wait_ms": wait_ms, "tokens_in": out["tokens_in"], "tokens_out": out["tokens_out"],
                   "tokens_thinking": out["tokens_thinking"], "retries": attempt, "error": err,
                   "finish_reason": out["finish_reason"]})
        return res

    # ---------------- chi phí ----------------
    @staticmethod
    def cost_usd(tokens_in: int, tokens_out: int, tokens_thinking: int = 0,
                 price_in_per_1m: float | None = None, price_out_per_1m: float | None = None) -> float | None:
        """Quy token ra tiền: in·P_in + (out + thinking)·P_out (đơn giá /1M token).
        Đơn giá đọc từ GEMINI_PRICE_IN_PER_1M / GEMINI_PRICE_OUT_PER_1M – [cần xác minh – điền theo bảng giá Google hiện hành]."""
        pi = price_in_per_1m if price_in_per_1m is not None else os.environ.get("GEMINI_PRICE_IN_PER_1M")
        po = price_out_per_1m if price_out_per_1m is not None else os.environ.get("GEMINI_PRICE_OUT_PER_1M")
        if pi in (None, "") or po in (None, ""):
            return None
        return tokens_in / 1e6 * float(pi) + (tokens_out + tokens_thinking) / 1e6 * float(po)

    def close(self) -> None:
        self.client.close()
