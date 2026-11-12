"""Test tích hợp 5 luồng của MSA qua API (Gemini ở chế độ mock, không gọi mạng).

Luồng: (1) tìm bằng ảnh, (2) hỏi đáp, (3) tìm bằng văn bản, (4) so sánh, (5) chitchat/ngoài phạm vi → Gemini.
Mỗi luồng được gọi cả qua endpoint riêng lẫn qua /chat (Router + Agent của Trung) khi áp dụng được.
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image

from conftest import TEST_KEY, assert_contract, make_gateway, make_rag, to_jpeg

DINOV2_TAU_V = 0.5923  # 04_Khoa/results/tau_v_analysis.json → dinov2_s["b_max_ood_val+0.01"]["tau"]


def _ood_image() -> bytes:
    """Ảnh gradient – không giống SP nào (cosine top-1 với DummyEmbedder ≈ 0,22 < τ_v)."""
    a = np.tile(np.linspace(0, 255, 80, dtype=np.uint8)[None, :, None], (96, 1, 3))
    return to_jpeg(Image.fromarray(a))


# ============================================================== (1) tìm bằng ảnh
def test_visual_uses_khoa_searcher_and_tau_v_from_analysis(system, catalog):
    c, st, _ = system
    from msa.search.visual import VisualSearcher
    assert isinstance(st.visual, VisualSearcher)
    assert st.visual_tau_v == DINOV2_TAU_V  # không còn τ_v = 0,25 cố định
    pid = "it_005"
    img = (catalog["root"] / catalog["by_id"][pid]["image_paths"][0]).read_bytes()
    r = c.post("/search/image", files={"file": ("q.jpg", img, "image/jpeg")}, data={"k": "5"})
    b = r.json()
    assert r.status_code == 200, b
    assert_contract(b)
    assert b["route"] == "visual" and b["source"] == "internal" and b["tau_v"] == DINOV2_TAU_V
    assert b["items"][0]["product_id"] == pid and b["items"][0]["score"] >= DINOV2_TAU_V
    assert b["items"][0]["title"] == catalog["by_id"][pid]["title"]  # thông tin SP lấy từ catalog
    assert len(b["items"]) == 5


def test_visual_rejects_below_tau_v(system):
    c, _, _ = system
    r = c.post("/search/image", files={"file": ("x.jpg", _ood_image(), "image/jpeg")})
    b = r.json()
    assert r.status_code == 200 and b["error"]["code"] == "not_product" and b["items"] == []
    assert b["confidence"] < DINOV2_TAU_V
    assert_contract(b)


def test_visual_product_type_filter(system, catalog):
    c, _, _ = system
    img = (catalog["root"] / catalog["by_id"]["it_000"]["image_paths"][0]).read_bytes()
    b = c.post("/search/image", files={"file": ("q.jpg", img, "image/jpeg")},
               data={"product_type": "footwear", "k": "10"}).json()
    assert b["items"] and {i["product_type"] for i in b["items"]} == {"footwear"}


def test_visual_via_agent_tool(system, catalog):
    """Agent của Trung: có ảnh → route visual → công cụ VisualSearcher (áp τ_v của searcher)."""
    _, st, _ = system
    img = (catalog["root"] / catalog["by_id"]["it_002"]["image_paths"][0]).read_bytes()
    session: dict = {}
    r = st.agent.handle(text="tìm mẫu giống ảnh này", image=img, session=session)
    assert r["route"] == "visual" and r["items"][0]["product_id"] == "it_002"
    assert session["last_results"][0] == "it_002"  # nhớ kết quả cho câu sau ("so sánh 2 đôi đầu")
    r2 = st.agent.handle(text=None, image=_ood_image(), session={})
    assert r2["route"] == "visual" and r2["items"] == [] and "chưa thấy" in r2["answer"]


def test_visual_unavailable_without_index(catalog, tmp_path, monkeypatch):
    """Chưa build index → 503 rõ ràng (không lặng lẽ quay về CLIP B/32 + τ_v 0,25)."""
    from fastapi.testclient import TestClient
    from msa.api.main import State, create_app
    monkeypatch.setenv("MSA_VISUAL_INDEX", str(tmp_path / "khong_co_index"))
    monkeypatch.delenv("MSA_VISUAL_BACKEND", raising=False)
    c = TestClient(create_app(State(catalog=catalog["df"], log_dir=str(tmp_path / "logs"))))
    img = (catalog["root"] / catalog["by_id"]["it_000"]["image_paths"][0]).read_bytes()
    r = c.post("/search/image", files={"file": ("q.jpg", img, "image/jpeg")})
    assert r.status_code == 503 and r.json()["error"]["code"] == "visual_unavailable"
    assert "build_index.py" in c.get("/health").json()["visual_error"]


# ============================================================== (2) hỏi đáp
def test_qa_rag_answer_with_citation(system):
    c, _, gem = system
    b = c.post("/qa", json={"question": "Chất liệu sản phẩm này thế nào?", "product_id": "it_001"}).json()
    assert_contract(b)
    assert b["route"] == "qa" and b["refused"] is False and b["source"] == "internal"
    assert b["citations"] and all(ci["product_id"] == "it_001" for ci in b["citations"])
    assert "[C1]" in b["answer"]
    # prompt RAG của Chiến đi qua LLMGateway: có system prompt, ngữ cảnh, KHÔNG có ảnh
    req = gem["requests"][-1]["body"]
    assert "systemInstruction" in req and "[C1]" in req["contents"][0]["parts"][0]["text"]
    assert all(set(p) == {"text"} for p in req["contents"][0]["parts"])


def test_qa_guard_refuses_uncited_mock_answer(catalog, tmp_path):
    """LLMGateway mock trả "[MOCK] ..." không trích nguồn → guard của Chiến từ chối (không bịa)."""
    gw = make_gateway(tmp_path, mock=True)
    out = make_rag(catalog["df"], gw).answer("Chất liệu thế nào?", "it_001")
    assert out["refused"] is True and out["guard_triggered"] is True
    assert out["answer"].startswith("Hiện cửa hàng chưa có thông tin")


def test_qa_llm_error_gives_fallback_not_fabrication(system):
    c, _, gem = system
    gem["mode"] = "503"
    b = c.post("/qa", json={"question": "Đi có êm chân không?", "product_id": "it_000"}).json()
    assert b["refused"] is True and b["source"] == "fallback" and b["citations"] == []
    assert "503" in b["llm_error"]


def test_qa_via_chat_uses_current_product(system):
    c, _, _ = system
    b = c.post("/chat", json={"message": "giày này chất liệu gì vậy", "session_id": "s-qa", "product_id": "it_001"}).json()
    assert_contract(b)
    assert b["route"] == "qa" and b["citations"] and b["citations"][0]["product_id"] == "it_001"


# ============================================================== (3) tìm bằng văn bản
def test_text_search_with_vietnamese_filters(system):
    c, _, _ = system
    b = c.post("/search/text", json={"query": "giày sneaker màu đen", "auto_filters": True}).json()
    assert_contract(b)
    assert b["route"] == "search" and b["items"]
    top = b["items"][0]
    assert top["product_type"] == "footwear" and top["sub_category"] == "sneaker" and "Black" in top["colors"]


def test_text_search_via_chat_remembers_results(system):
    c, st, _ = system
    b = c.post("/chat", json={"message": "tìm giày sneaker màu đen", "session_id": "s-search"}).json()
    assert_contract(b)
    assert b["route"] == "search" and b["source"] == "internal" and b["items"]
    assert st.sessions["s-search"]["last_results"] == [i["product_id"] for i in b["items"]]


# ============================================================== (4) so sánh
def test_compare_endpoint(system):
    c, _, _ = system
    b = c.post("/compare", json={"product_ids": ["it_000", "it_002"]}).json()
    assert_contract(b)
    assert b["route"] == "compare" and b["table"]["product_type"] == "footwear"
    assert [i["product_id"] for i in b["items"]] == ["it_000", "it_002"]


def test_compare_rejects_cross_type(system):
    c, _, _ = system
    r = c.post("/compare", json={"product_ids": ["it_000", "it_004"]})  # giày vs áo (R19)
    assert r.status_code == 400 and r.json()["route"] == "compare"


def test_search_then_compare_in_one_chat_session(system):
    """Luồng hội thoại: tìm → 'so sánh 2 đôi đầu' dùng last_results của phiên (session memory của Trung)."""
    c, _, _ = system
    found = c.post("/chat", json={"message": "tìm giày sneaker", "session_id": "s-cmp"}).json()
    ids = [i["product_id"] for i in found["items"]]
    b = c.post("/chat", json={"message": "so sánh 2 đôi đầu", "session_id": "s-cmp"}).json()
    assert_contract(b)
    assert b["route"] == "compare" and [i["product_id"] for i in b["items"]] == ids[:2]
    assert b["answer"].startswith("Bảng so sánh 2 sản phẩm")


# ============================================================== (5) chitchat / ngoài phạm vi → Gemini
def test_chitchat_goes_through_gateway_then_cache(system):
    c, _, gem = system
    b1 = c.post("/chat", json={"message": "Chào shop"}).json()
    assert_contract(b1)
    assert b1["route"] == "gemini_chitchat" and b1["source"] == "gemini" and b1["answer"].startswith("Chào bạn")
    assert b1["tokens_in"] == 120  # usageMetadata đọc qua LLMGateway
    n = len(gem["requests"])
    b2 = c.post("/chat", json={"message": "Chào shop"}).json()
    assert b2["source"] == "cache" and len(gem["requests"]) == n  # lần 2 không gọi Gemini


def test_out_of_scope_routes_to_gemini_ood(system):
    c, _, gem = system
    b = c.post("/chat", json={"message": "thời tiết Hà Nội hôm nay thế nào"}).json()
    assert b["route"] == "gemini_ood" and b["source"] == "gemini"
    assert gem["requests"][-1]["headers"]["x-goog-api-key"] == TEST_KEY  # key chỉ nằm ở header


def test_gemini_error_labelled_fallback(system):
    c, _, gem = system
    gem["mode"] = "429day"
    b = c.post("/chat", json={"message": "Chào shop"}).json()
    assert_contract(b)
    assert b["source"] == "fallback" and "429" in b["llm_error"]
    assert len(gem["requests"]) == 1  # hết quota NGÀY → không retry vô ích


def test_gateway_mock_mode_end_to_end(catalog, tmp_path, monkeypatch):
    """MSA_LLM_MOCK=1: hệ thống dựng gateway mặc định ở chế độ mock (không cần key, không gọi mạng)."""
    from fastapi.testclient import TestClient
    from msa.api.main import State, create_app
    monkeypatch.setenv("MSA_LLM_MOCK", "1")
    monkeypatch.setenv("MSA_RUNTIME_DIR", str(tmp_path / "runtime"))
    st = State(catalog=catalog["df"], log_dir=str(tmp_path / "logs"), qa=object())
    c = TestClient(create_app(st))
    b = c.post("/chat", json={"message": "Chào shop"}).json()
    assert b["source"] == "gemini" and b["answer"].startswith("[MOCK]")
    h = c.get("/health").json()
    assert h["llm"]["mock"] is True and h["agent_loaded"] is True


def test_store_facts_from_gemini_are_replaced(system):
    """Hậu kiểm của Trung: Gemini nêu giá/tồn kho → thay bằng câu an toàn (quy tắc 5.4)."""
    _, st, _ = system
    from msa.agent.router import SAFE_REPLACEMENT

    class PriceyLLM:
        def generate(self, prompt, system=None, **kw):
            return {"answer": "Mẫu này giá chỉ 199k, còn hàng nhé!", "source": "gemini", "cached": False, "error": None}

    st.agent.llm = PriceyLLM()
    r = st.agent.handle(text="Chào shop", session={})
    assert r["answer"] == SAFE_REPLACEMENT and set(r["store_fact_flags"]) >= {"gia", "ton_kho"}


# ============================================================== hợp đồng chung
def test_every_request_logged_with_contract_fields(system, tmp_path):
    c, st, _ = system
    c.post("/chat", json={"message": "Chào shop"})
    c.post("/search/text", json={"query": "túi xách"})
    recs = [json.loads(l) for l in (st.log_dir / "requests.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["endpoint"] for r in recs[-2:]] == ["/chat", "/search/text"]
    assert all({"request_id", "route", "source", "latency_ms"} <= set(r) for r in recs)
    log = (tmp_path / "llm_calls.jsonl").read_text(encoding="utf-8")
    assert TEST_KEY not in log  # gateway không ghi key vào log
