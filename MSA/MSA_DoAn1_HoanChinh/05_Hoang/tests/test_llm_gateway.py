"""US_50 – LLM Gateway: 10 request mock, giả lập 429/timeout/5xx, cache hit, key không bị log, đổi model bằng env."""
import json
import os

import httpx
import pytest
from msa.llm_gateway import FALLBACK_VI, LLMGateway, SemanticCache, TokenBucket, load_env_file

FAKE_KEY = "FAKEKEY-test-1234567890"


def ok_json(text="Xin chào!", thinking=7):
    return {"candidates": [{"content": {"parts": [{"text": "suy nghĩ...", "thought": True}, {"text": text}]},
                            "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 5, "thoughtsTokenCount": thinking},
            "modelVersion": "test-model"}


def gw_with(handler, tmp_path, **kw):
    kw.setdefault("rpm", 0)
    return LLMGateway(model="gemini-test", api_key=FAKE_KEY, mock=False, transport=httpx.MockTransport(handler),
                      cache_path=str(tmp_path / "cache.sqlite"), log_path=str(tmp_path / "llm.jsonl"),
                      sleep=lambda s: None, **kw)


def test_ten_mock_requests(tmp_path):
    g = LLMGateway(mock=True, cache_path=str(tmp_path / "c.sqlite"), log_path=str(tmp_path / "l.jsonl"))
    outs = [g.generate(f"Câu hỏi số {i}", system="persona") for i in range(10)]
    assert all(o["source"] == "gemini" and o["answer"] and o["error"] is None for o in outs)
    assert set(outs[0]) >= {"answer", "source", "cached", "tokens_in", "tokens_out", "tokens_thinking", "latency_ms", "error"}
    assert g.stats.requests == 10 and g.stats.api_calls == 0


def test_success_parses_tokens_and_skips_thought(tmp_path):
    seen = {}

    def h(req):
        seen["url"], seen["body"], seen["hdr"] = str(req.url), json.loads(req.content), req.headers
        return httpx.Response(200, json=ok_json())
    g = gw_with(h, tmp_path)
    r = g.generate("Chào", system="sys", thinking_budget=0, temperature=0.2)
    assert r["answer"] == "Xin chào!" and r["tokens_in"] == 11 and r["tokens_out"] == 5 and r["tokens_thinking"] == 7
    assert r["model_version"] == "test-model" and r["api_latency_ms"] is not None
    assert seen["body"]["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}
    assert seen["body"]["systemInstruction"]["parts"][0]["text"] == "sys"
    assert FAKE_KEY not in seen["url"] and seen["hdr"]["x-goog-api-key"] == FAKE_KEY  # key chỉ ở header


def test_retry_429_then_success(tmp_path):
    calls = {"n": 0}

    def h(req):
        calls["n"] += 1
        if calls["n"] <= 2:
            return httpx.Response(429, json={"error": {"message": "quota", "details": [
                {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "3s"}]}})
        return httpx.Response(200, json=ok_json("Được rồi"))
    g = gw_with(h, tmp_path)
    r = g.generate("Hi")
    assert r["answer"] == "Được rồi" and r["retries"] == 2 and calls["n"] == 3 and g.stats.retries == 2
    assert r["wait_ms"] >= 6000  # tôn trọng retryDelay=3s × 2 lần


def test_429_exhausted_returns_fallback_not_crash(tmp_path):
    g = gw_with(lambda req: httpx.Response(429, json={"error": {"message": "quota"}}), tmp_path, max_retries=2)
    r = g.generate("Hi")
    assert r["source"] == "fallback" and r["answer"] == FALLBACK_VI and "429" in r["error"] and r["retries"] == 2
    assert g.stats.fallbacks == 1


def test_daily_quota_not_retried(tmp_path):
    calls = {"n": 0}

    def h(req):
        calls["n"] += 1
        return httpx.Response(429, json={"error": {"message": "quota", "details": [
            {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
             "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier", "quotaValue": "20"}]}]}})
    r = gw_with(h, tmp_path).generate("Hi")
    assert r["source"] == "fallback" and calls["n"] == 1 and "PerDay" in r["error"]


def test_timeout_and_5xx(tmp_path):
    def to(req):
        raise httpx.ReadTimeout("timed out", request=req)
    r = gw_with(to, tmp_path, max_retries=1).generate("Hi")
    assert r["source"] == "fallback" and r["error"].startswith("timeout")
    seq = iter([503, 200])
    r = gw_with(lambda req: httpx.Response(next(seq), json=ok_json() if True else None), tmp_path).generate("Hi2")
    assert r["source"] == "gemini" and r["retries"] == 1


def test_400_not_retried(tmp_path):
    calls = {"n": 0}

    def h(req):
        calls["n"] += 1
        return httpx.Response(400, json={"error": {"message": "bad"}})
    r = gw_with(h, tmp_path).generate("Hi")
    assert r["source"] == "fallback" and calls["n"] == 1


def test_cache_hit(tmp_path):
    calls = {"n": 0}

    def h(req):
        calls["n"] += 1
        return httpx.Response(200, json=ok_json())
    g = gw_with(h, tmp_path)
    a, b = g.generate("Q", system="S"), g.generate("Q", system="S")
    c = g.generate("Q", system="S", thinking_budget=0)  # tham số sinh khác → khoá cache khác
    assert calls["n"] == 2 and not a["cached"] and b["cached"] and b["source"] == "cache" and b["origin"] == "gemini"
    assert b["answer"] == a["answer"] and not c["cached"] and g.stats.cache_hits == 1
    g.generate("Q", system="S", use_cache=False)
    assert calls["n"] == 3


def test_key_never_logged(tmp_path):
    def h(req):
        return httpx.Response(500, json={"error": {"message": f"echo {FAKE_KEY}"}})
    g = gw_with(h, tmp_path, max_retries=1)
    r = g.generate("Hi")
    blob = json.dumps(r) + (tmp_path / "llm.jsonl").read_text() + repr(g)
    assert FAKE_KEY not in blob and "***" in r["error"]


def test_model_from_env_and_missing_key(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-other")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    g = LLMGateway(mock=False, cache_path=str(tmp_path / "c.sqlite"), log_path="")
    assert g.model == "gemini-other"
    r = g.generate("Hi")
    assert r["source"] == "fallback" and r["error"].startswith("missing_api_key")


def test_no_images_and_empty_prompt(tmp_path):
    g = LLMGateway(mock=True, cache_path=":memory:", log_path="")
    with pytest.raises(ValueError):
        g.generate("mô tả ảnh", image=b"\xff\xd8")
    with pytest.raises(ValueError):
        g.generate("   ")


def test_empty_answer_is_fallback(tmp_path):
    r = gw_with(lambda req: httpx.Response(200, json={"candidates": [{"finishReason": "SAFETY"}]}), tmp_path).generate("Hi")
    assert r["source"] == "fallback" and "SAFETY" in r["error"]


def test_token_bucket():
    t = {"now": 0.0}
    slept = []

    def sleep(s):
        slept.append(s)
        t["now"] += s
    b = TokenBucket(rate=1.0, capacity=2, clock=lambda: t["now"], sleep=sleep)
    assert b.acquire() == 0 and b.acquire() == 0
    assert b.acquire() == pytest.approx(1.0) and slept


def test_semantic_cache_hook(tmp_path):
    import numpy as np
    emb = lambda xs: np.array([[1.0, 0.0] if "chào" in x.lower() else [0.0, 1.0] for x in xs])
    g = LLMGateway(mock=True, cache_path=":memory:", log_path="", semantic_cache=SemanticCache(emb, 0.9))
    g.generate("Chào bạn")
    r = g.generate("chào shop nhé")
    assert r["cached"] and g.stats.semantic_hits == 1


def test_cost_formula():
    assert LLMGateway.cost_usd(1_000_000, 500_000, 500_000, 0.1, 0.4) == pytest.approx(0.1 + 0.4)
    assert LLMGateway.cost_usd(10, 10) is None or isinstance(LLMGateway.cost_usd(10, 10), float)


def test_load_env_file(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text("# c\nexport MSA_X_TEST='abc'\nGEMINI_MODEL=m1\n")
    monkeypatch.delenv("MSA_X_TEST", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "keep")
    assert "MSA_X_TEST" in load_env_file(p) and os.environ["MSA_X_TEST"] == "abc" and os.environ["GEMINI_MODEL"] == "keep"


@pytest.mark.live
def test_live_gemini_one_call(tmp_path):
    """Chạy: MSA_ENV_FILE=<file .env có GEMINI_API_KEY> python -m pytest -m live (tốn 1 lời gọi)."""
    if os.environ.get("MSA_ENV_FILE"):
        load_env_file(os.environ["MSA_ENV_FILE"], override=True)
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("không có GEMINI_API_KEY")
    g = LLMGateway(mock=False, cache_path=str(tmp_path / "c.sqlite"), log_path="")
    r = g.generate("Chào bạn", thinking_budget=0)
    assert r["source"] in ("gemini", "fallback")
