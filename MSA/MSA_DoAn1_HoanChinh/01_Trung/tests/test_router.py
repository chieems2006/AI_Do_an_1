"""Kiểm US_41: router 7 route, hỏi lại tối đa 1 lần rồi chuyển Gemini, Agent gọi nội bộ trước, hậu kiểm Gemini."""
import json
import os

from msa.agent.router import ROUTES, Agent, Router, Tools, find_store_facts
from msa.textnorm import normalize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeLLM:
    def __init__(self, answer="Chào bạn! Mình giúp gì được ạ?", error=None):
        self.answer, self.error, self.calls = answer, error, 0

    def generate(self, prompt, system=None, **kw):
        self.calls += 1
        return dict(answer=self.answer, source="gemini", cached=False, tokens_in=10, tokens_out=5, latency_ms=1, error=self.error)


def test_normalize_teencode_and_accents():
    assert normalize("Shop ơi, giày này có ĐC ko?") == "shop oi giay nay co duoc khong"
    assert normalize("dưới 500k") == "duoi 500 nghin"
    assert normalize("Áo Y2K") == "ao y2k"


def test_seed_set_accuracy_at_least_90pct():
    data = [json.loads(line) for line in open(os.path.join(ROOT, "eval", "eval_router_seed.jsonl"), encoding="utf-8")]
    assert len(data) >= 30
    assert sum(d["route"] in ("gemini_chitchat", "gemini_ood") for d in data) >= 10
    r = Router()
    ok = 0
    for d in data:
        s = {}
        if d.get("product_id"):
            s["current_product_id"] = d["product_id"]
        if d.get("session_last_results"):
            s["last_results"] = d["session_last_results"]
        ok += r.route(d["text"], b"x" if d["has_image"] else None, s)["route"] == d["route"]
    assert ok / len(data) >= 0.9


def test_output_contract():
    out = Router().route("tìm giày thể thao nam màu trắng dưới 1 triệu")
    assert set(out) >= {"route", "confidence", "needs_clarification"}
    assert out["route"] in ROUTES and 0 <= out["confidence"] <= 1


def test_image_always_visual():
    assert Router().route("chào shop", b"\x89PNG")["route"] == "visual"


def test_clarify_once_then_gemini():
    r = Router()
    assert r.route("đôi thứ 2", None, {})["route"] == "clarify"
    assert r.route("đôi thứ 2", None, {"clarify_count": 1})["route"].startswith("gemini_")


def test_cross_type_compare_needs_clarification():
    assert Router().route("so sánh cái áo này với đôi giày kia")["route"] == "clarify"


def test_qa_needs_product_context():
    assert Router().route("có bền không?", None, {})["route"] == "clarify"
    assert Router().route("có bền không?", None, {"current_product_id": "shopee_1"})["route"] == "qa"
    assert Router().route("đôi thứ 2 có bền không", None, {"last_results": ["a", "b", "c"]})["route"] == "qa"


def test_unaccented_and_teencode():
    assert Router().route("co dep quai ngang nu ko shop")["route"] == "search"
    assert Router().route("dep nay di mua mua co tron khong", None, {"current_product_id": "x"})["route"] == "qa"
    assert Router().route("tìm cái giống vậy")["route"] != "search"  # 'vậy' không phải 'váy'


def test_agent_internal_first_and_gemini_label():
    llm = FakeLLM()
    called = {}
    tools = Tools(search=lambda q: called.setdefault("search", [{"product_id": "fpi_1", "title": "x", "price": None, "score": 1.0}]))
    ag = Agent(tools=tools, llm=llm)
    s = {}
    r1 = ag.handle("tìm giày thể thao nam màu trắng", None, s)
    assert r1["route"] == "search" and r1["source"] == "internal" and llm.calls == 0
    assert s["last_results"] == ["fpi_1"]
    r2 = ag.handle("chào shop", None, s)
    assert r2["route"] == "gemini_chitchat" and r2["source"] == "gemini" and llm.calls == 1
    assert set(r2) >= {"route", "confidence", "source", "answer", "items", "citations", "latency_ms", "request_id"}


def test_agent_qa_refused_does_not_call_gemini():
    llm = FakeLLM()
    ag = Agent(tools=Tools(qa=lambda q, pid: {"answer": "", "citations": [], "retrieval_score": 0.1, "refused": True}), llm=llm)
    r = ag.handle("đôi này giá bao nhiêu", None, {"current_product_id": "shopee_1"})
    assert r["route"] == "qa" and "chưa có thông tin" in r["answer"] and llm.calls == 0


def test_postcheck_blocks_invented_store_facts():
    assert set(find_store_facts("Giá chỉ 299.000đ, còn hàng size 39, freeship")) >= {"gia", "ton_kho", "size", "khuyen_mai"}
    assert find_store_facts("Bạn có thể phối áo trắng với quần jean xanh.") == []
    ag = Agent(llm=FakeLLM(answer="Đôi này giá 500k, còn hàng nhé"))
    r = ag.handle("chào shop")
    assert r["store_fact_flags"] and "chưa có thông tin" in r["answer"]


def test_gemini_error_gives_fallback_message():
    ag = Agent(llm=FakeLLM(answer="", error="http_429"))
    r = ag.handle("kể chuyện cười đi bạn")
    assert r["source"] == "fallback" and r["answer"] and r["error"] == "http_429"  # QUYET_DINH mục D


def test_postcheck_v2_real_cases():
    # 2 câu trả lời THẬT của Gemini (results/gemini_fallback_live.json) mà regex v1 bỏ sót
    assert "danh_muc" in find_store_facts("Cửa hàng mình hiện có nhiều mẫu đồng hồ Casio phong cách từ trẻ trung đến lịch lãm")
    # regex v1 bắt nhầm ký hiệu $ trong công thức toán (r064)
    assert find_store_facts("Phương trình $x^2 - 5x + 6 = 0$ có hai nghiệm là $x = 2$ và $x = 3$ bạn nhé!") == []
    assert "gia" in find_store_facts("chỉ $25 thôi")
