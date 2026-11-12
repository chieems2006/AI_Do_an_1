"""Kiểm US_42 (stretch): hiểu 'đôi thứ 2', 'cái vừa tìm', '2 đôi đầu', 'cái cuối'."""
from msa.agent.session_memory import SessionMemory, resolve_compare_refs, resolve_product_ref

S = {"last_results": ["a", "b", "c"]}


def test_product_ref():
    assert resolve_product_ref("đôi thứ 2 có bền không", S) == "b"
    assert resolve_product_ref("cái cuối giá bao nhiêu", S) == "c"
    assert resolve_product_ref("cái vừa tìm chất liệu gì", S) == "a"
    assert resolve_product_ref("đôi thứ 2", {}) is None
    assert resolve_product_ref("đôi thứ 9", S) is None


def test_compare_refs():
    assert resolve_compare_refs("so sánh đôi vừa tìm với đôi thứ 2", S) == ["a", "b"]
    assert resolve_compare_refs("so sanh 2 doi dau", S) == ["a", "b"]
    assert resolve_compare_refs("so sanh 3 cai mu vua tim", S) == ["a", "b", "c"]
    assert resolve_compare_refs("đôi đầu tiên với đôi cuối", S) == ["a", "c"]


def test_session_store_records_results():
    m = SessionMemory()
    m.record("u1", "tìm dép", {"route": "search", "items": [{"product_id": "x"}, {"product_id": "y"}]})
    assert m.get("u1")["last_results"] == ["x", "y"]
    m.record("u1", "chào", {"route": "gemini_chitchat"})
    assert m.get("u1")["last_results"] == ["x", "y"] and len(m.get("u1")["history"]) == 2
