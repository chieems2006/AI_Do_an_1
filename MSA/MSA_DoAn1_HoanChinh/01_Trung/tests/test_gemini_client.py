"""Kiểm client Gemini: mock, cache, thiếu key, không lộ key, cấu hình thinking. Test gọi thật đánh dấu live."""
import os

import pytest

from msa_trung.gemini_client import GeminiRestClient, _scrub


def test_mock_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("MSA_LLM_MOCK", "1")
    c = GeminiRestClient(cache_path=str(tmp_path / "c.sqlite"))
    a = c.generate("chào shop", system="sys")
    b = c.generate("Chào   SHOP", system="sys")  # chuẩn hoá -> trúng cache
    assert a["source"] == "gemini" and not a["cached"]
    assert b["cached"] and b["source"] == "cache" and b["answer"] == a["answer"]
    c2 = GeminiRestClient(cache_path=str(tmp_path / "c.sqlite"), prompt_version="khac")
    assert c2.cache_key("chào shop", "sys") != c.cache_key("chào shop", "sys")


def test_missing_key(monkeypatch):
    monkeypatch.delenv("MSA_LLM_MOCK", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MSA_GEMINI_KEY_FILE", raising=False)
    out = GeminiRestClient().generate("hi")
    assert out["error"] == "missing_api_key" and out["answer"] == ""


def test_scrub_and_body():
    assert "SECRET123" not in _scrub("lỗi với key SECRET123", "SECRET123")
    b = GeminiRestClient(thinking_budget=0).build_body("hi", "sys")
    assert b["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0} and b["systemInstruction"]["parts"][0]["text"] == "sys"
    assert "thinkingConfig" not in GeminiRestClient(thinking_budget=None).build_body("hi", None)["generationConfig"]


@pytest.mark.live
def test_live_call_once():
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("MSA_GEMINI_KEY_FILE")):
        pytest.skip("không có key")
    out = GeminiRestClient(model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"), thinking_budget=None).generate("chào shop", use_cache=False)
    assert out["error"] is None and out["answer"]
