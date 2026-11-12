"""Test ingest, retriever, pipeline (trích nguồn + từ chối) trên dữ liệu giả lập."""
import os
import json

import pytest

from msa.rag.ingest import build_chunks, chunk_product, split_sentences
from msa.rag.llm import MockLLM
from msa.rag.pipeline import REFUSAL_PREFIX, RAGPipeline, load_prompt_blocks, postprocess, refusal_message
from msa.rag.retriever import (BM25Retriever, DenseRetriever, DummyEmbedder, HybridRetriever, TfidfRetriever,
                               normalize_query, strip_accents)

PRODUCTS = [
    {"product_id": "shopee_1", "title": "Dép bánh mì quai ngang", "source_url": "https://x/1",
     "reviews": [
         {"comment_id": 11, "rating": 5, "text": "Dép đi rất êm, đế cao su không trơn.", "detail_rating": "product_quality: 5\nseller_service: 4\ndelivery_service: 5"},
         {"comment_id": 12, "rating": 4, "text": "Chân 40 mình lấy size 41 vừa, form hơi nhỏ.", "detail_rating": "product_quality: 4\nseller_service: 4\ndelivery_service: 3"},
         {"comment_id": 12, "rating": 4, "text": "trùng lặp", "detail_rating": ""},
     ]},
    {"product_id": "fpi_2", "title": "Áo hoodie nỉ", "description": "Áo nỉ bông dày. Mặc mùa đông rất ấm. Có mũ 2 lớp.",
     "specs": {"chất liệu": "nỉ bông", "màu": "xám"}, "source": "fpi",
     "reviews": [{"review_id": "a", "text": "Vải dày, giặt không xù lông", "rating": 5}]},
]


def test_chunk_traceable_and_unique():
    chunks = build_chunks(PRODUCTS)
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))
    for c in chunks:
        assert c["chunk_id"].startswith(c["product_id"] + "::" + c["field"])
        assert c["source"] and c["product_id"]
    fields = {c["field"] for c in chunks if c["product_id"] == "fpi_2"}
    assert {"title", "description", "specs", "review"} <= fields
    rv = [c for c in chunks if c["field"] == "review" and c["product_id"] == "shopee_1"]
    assert [c["review_id"] for c in rv] == ["11", "12"]  # bản trùng bị bỏ
    det = [c for c in chunks if c["field"] == "detail_rating"]
    assert det and "giao hàng 4.0/5" in det[0]["text"]


def test_split_sentences_limit():
    parts = split_sentences("Câu một. " * 200, max_chars=100)
    assert all(len(p) <= 200 for p in parts) and len(parts) > 5


def test_text_normalisation():
    assert strip_accents("Đôi giày ĐẸP") == "doi giay dep"
    assert "không" in normalize_query("dep co tron ko")
    assert "size" in normalize_query("sz 40")


@pytest.mark.parametrize("cls", [TfidfRetriever, BM25Retriever])
def test_lexical_retrievers_find_evidence(cls):
    r = cls(build_chunks(PRODUCTS))
    hits = r.search("dep di co em ko", k=3, product_id="shopee_1")  # không dấu
    assert hits[0]["chunk_id"] == "shopee_1::review::11"
    assert all(h["product_id"] == "shopee_1" for h in hits)
    assert r.search("abc", product_id="khong_ton_tai") == []


def test_dense_and_hybrid_with_dummy_embedder():
    chunks = build_chunks(PRODUCTS)
    d = DenseRetriever(chunks, DummyEmbedder())
    top = d.search("size 41 form nhỏ", k=2, product_id="shopee_1")
    assert top[0]["chunk_id"] == "shopee_1::review::12"
    h = HybridRetriever([BM25Retriever(chunks), d])
    assert h.search("size 41 form nhỏ", k=1, product_id="shopee_1")[0]["chunk_id"] == "shopee_1::review::12"


def test_prompt_file_has_blocks():
    b = load_prompt_blocks()
    assert {"system", "user", "user_batch"} <= set(b)
    assert "{contexts}" in b["user"] and "{question}" in b["user"]


def _pipe(responder, tau_r=0.0):
    return RAGPipeline(BM25Retriever(build_chunks(PRODUCTS)), MockLLM(responder), tau_r=tau_r, k=3)


def test_answer_with_citation():
    res = _pipe(lambda p, s: "Theo đánh giá của khách, dép đi rất êm [C1].").answer("dép có êm không", "shopee_1")
    assert not res["refused"]
    assert res["citations"][0]["product_id"] == "shopee_1"
    assert res["citations"][0]["chunk_id"].startswith("shopee_1::")


def test_refuse_when_llm_says_no_info():
    res = _pipe(lambda p, s: "Hiện cửa hàng chưa có thông tin về giá bán.").answer("giá bao nhiêu", "shopee_1")
    assert res["refused"] and res["citations"] == []


def test_guard_refuses_uncited_answer():
    res = _pipe(lambda p, s: "Giá 250k và còn size 42.").answer("giá bao nhiêu", "shopee_1")
    assert res["refused"] and res["answer"].startswith(REFUSAL_PREFIX)
    assert "250k" not in res["answer"]


def test_refuse_below_tau_r_without_calling_llm():
    llm = MockLLM()
    pipe = RAGPipeline(BM25Retriever(build_chunks(PRODUCTS)), llm, tau_r=1e9)
    res = pipe.answer("dép có êm không", "shopee_1")
    assert res["refused"] and res["refuse_reason"] == "below_tau_r" and llm.calls == []


def test_llm_error_gives_fallback_not_fabrication():
    class ErrLLM:
        def generate(self, *a, **k):
            return {"answer": "Xin lỗi, trợ lý đang bận", "error": "http_429", "source": "gemini"}
    res = RAGPipeline(BM25Retriever(build_chunks(PRODUCTS)), ErrLLM(), tau_r=0.0).answer("dép có êm không", "shopee_1")
    assert res["refused"] and res["llm_error"] == "http_429"


def test_invalid_citation_index_ignored():
    out = postprocess("Êm lắm [C9]", [{"product_id": "p", "field": "review", "chunk_id": "p::review::1"}], "êm không")
    assert out["refused"] and out["guard_triggered"]


def test_refusal_message_topic():
    assert "giá" in refusal_message("đôi này giá bao nhiêu")
    assert "còn hàng" in refusal_message("còn size 40 không")


def test_answer_batch_mock():
    def resp(p, s):
        return json.dumps([{"qid": "q1", "answer": "Êm [C1]"}, {"qid": "q2", "answer": "Hiện cửa hàng chưa có thông tin về giá."}])
    outs, meta = _pipe(resp).answer_batch([{"qid": "q1", "question": "dép êm không", "product_id": "shopee_1"},
                                           {"qid": "q2", "question": "giá bao nhiêu", "product_id": "shopee_1"}])
    assert not outs[0]["refused"] and outs[1]["refused"]


@pytest.mark.skipif(not __import__("pathlib").Path((os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/vimrhp_fashion_products.jsonl")).exists(),
                    reason="thiếu shared_data")
def test_default_pipeline_on_real_kb_lexical():
    from msa.rag.pipeline import build_default_pipeline

    pipe = build_default_pipeline(llm=MockLLM(lambda p, s: "Theo đánh giá của khách, giao hàng nhanh [C1]."), use_dense=False)
    res = pipe.answer("shop giao hàng có nhanh không", "shopee_1050114357")
    assert res["citations"] and all(c["product_id"] == "shopee_1050114357" for c in res["citations"])
