"""Test hậu kiểm Gemini, nhánh fallback (mock), client LLM (cache/429 giả), và test live (bỏ qua mặc định)."""
import os
from pathlib import Path

import pytest

from check_gemini_hallucination import check_text
from msa.rag.fallback import LABEL, GeminiFallback, load_fallback_prompt, should_fallback
from msa.rag.llm import GeminiClient, MockLLM

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("text,kind", [
    ("Đôi này giá 350k bạn nhé", "gia"),
    ("Chỉ 1.200.000đ thôi", "gia"),
    ("Đang giảm 30% nha", "gia"),
    ("Bạn mang size 42 là vừa", "size"),
    ("Áo size M rộng vừa", "size"),
    ("Mẫu này còn hàng đó bạn", "ton_kho"),
    ("Shop freeship toàn quốc", "chinh_sach"),
    ("Đổi trả trong 7 ngày", "chinh_sach"),
])
def test_checker_flags(text, kind):
    r = check_text(text)
    assert r["violation"] and kind in {h["loai"] for h in r["hits"]}


@pytest.mark.parametrize("text", [
    "Chào bạn! Mình là Mia, bạn cần tìm giày hay áo?",
    "Mình chưa có thông tin về giá, bạn gửi tên sản phẩm để mình kiểm tra nhé.",
    "Mình không biết còn hàng không, bạn gửi ảnh để mình tra giúp nhé.",
    "Thủ đô của Úc là Canberra.",
    "1 + 1 bằng 2 bạn nhé, không khó đâu!",
    "Trời mưa bạn nên chọn áo khoác chống nước và giày đế cao su.",
])
def test_checker_no_false_positive(text):
    assert not check_text(text)["violation"]


def test_checker_allows_values_from_context():
    assert not check_text("Theo dữ liệu, giá 350k", context="giá 350k")["violation"]


def test_fallback_prompt_versioned():
    cfg = load_fallback_prompt()
    assert cfg["version"].startswith("v") and len(cfg["fewshot"]) >= 3
    assert "KHÔNG nêu giá" in cfg["system"] and {"llm_error", "postcheck_violation"} <= set(cfg["messages"])


def test_fallback_normal_and_label():
    out = GeminiFallback(MockLLM(lambda p, s: "Chào bạn! Mình giúp gì được?")).respond("chào shop")
    assert out["source"] == "gemini" and out["label"] == LABEL and not out["postcheck"]["violation"]


def test_fallback_postcheck_replaces_fabrication():
    fb = GeminiFallback(MockLLM(lambda p, s: "Giày này giá 500k, còn size 42 nha"))
    out = fb.respond("giày giá bao nhiêu", "gemini_ood")
    assert out["postcheck"]["violation"] and "500k" not in out["answer"]
    assert out["answer"] == fb.cfg["messages"]["postcheck_violation"]


def test_fallback_429_message():
    class Err:
        def generate(self, *a, **k):
            return {"answer": "", "error": "http_429", "source": "gemini"}
    fb = GeminiFallback(Err())
    out = fb.respond("chào")
    assert out["answer"] == fb.cfg["messages"]["llm_error"] and out["error"] == "http_429"


def test_should_fallback_rule_r14():
    assert should_fallback("gemini_chitchat", 0.9, None, False)
    assert not should_fallback("qa", 0.1, "shopee_1", retrieval_empty=False)  # có product_id → giữ nội bộ
    assert should_fallback("qa", 0.1, "shopee_1", retrieval_empty=True)
    assert should_fallback("search", 0.3, None, False) and not should_fallback("search", 0.9, None, False)


def test_gemini_client_no_key_and_cache(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MSA_ENV_FILE", raising=False)
    c = GeminiClient(cache_path=tmp_path / "c.sqlite", log_path=tmp_path / "l.jsonl")
    r = c.generate("xin chào")
    assert r["error"] == "no_api_key" and r["answer"]  # thông điệp dự phòng, không ném lỗi


def test_gemini_client_retry_on_429(tmp_path, monkeypatch):
    import httpx

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")
    seq = [httpx.Response(429, text='{"error":{"details":[{"retryDelay":"0s"}]}}'),
           httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
                                     "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 1}})]
    monkeypatch.setattr(httpx, "post", lambda *a, **k: seq.pop(0))
    monkeypatch.setattr("time.sleep", lambda s: None)
    c = GeminiClient(cache_path=tmp_path / "c.sqlite", log_path=tmp_path / "l.jsonl", max_retries=2)
    r = c.generate("hi")
    assert r["answer"] == "ok" and r["tokens_in"] == 3
    r2 = c.generate("hi")
    assert r2["cached"] and r2["source"] == "cache"
    assert "fake-key" not in (tmp_path / "l.jsonl").read_text(encoding="utf-8")


def test_gemini_client_timeout_returns_fallback(tmp_path, monkeypatch):
    import httpx

    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")

    def boom(*a, **k):
        raise httpx.ReadTimeout("t")
    monkeypatch.setattr(httpx, "post", boom)
    c = GeminiClient(cache_path=tmp_path / "c.sqlite", log_path=tmp_path / "l.jsonl", max_retries=1)
    r = c.generate("hi")
    assert r["error"] == "timeout" and r["answer"]


@pytest.mark.live
def test_live_gemini_fallback_no_fabrication():
    """Gọi Gemini thật (cần GEMINI_API_KEY hoặc MSA_ENV_FILE). Chạy: pytest -m live"""
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("MSA_ENV_FILE")):
        pytest.skip("không có key")
    out = GeminiFallback(GeminiClient(model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                                      thinking_budget=None)).respond("chào shop, giày bên bạn giá bao nhiêu?")
    assert out["answer"] and not (out["postcheck"] or {}).get("violation", False)
