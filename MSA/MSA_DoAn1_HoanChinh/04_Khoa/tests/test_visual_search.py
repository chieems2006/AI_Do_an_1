import numpy as np

from _synth import make_catalog
from msa.embed.image_embedders import DummyEmbedder
from msa.search.visual import NO_MATCH_MSG, VisualSearcher, build_meta


def _vs(tmp_path, **kw):
    cat = make_catalog(tmp_path)
    meta = build_meta(cat, tmp_path)
    e = DummyEmbedder()
    return VisualSearcher(e, e.embed(meta.image.tolist()), meta, **kw), meta


def test_self_retrieval_top1(tmp_path):
    vs, meta = _vs(tmp_path)
    hits = sum(vs.search(p, k=1)[0]["product_id"] == pid for p, pid in zip(meta.image, meta.product_id))
    assert hits == len(meta)


def test_filter_by_type(tmp_path):
    vs, meta = _vs(tmp_path)
    res = vs.search(meta.image[0], k=5, product_type="headwear")
    assert res and all(r["product_type"] == "headwear" for r in res)


def test_type_gate_and_query_contract(tmp_path):
    vs, meta = _vs(tmp_path, gate_mode="centroid")
    t, conf = vs.type_gate(meta.image[0])
    assert t in ("footwear", "clothing", "headwear", "accessory") and 0 <= conf <= 1
    r = vs.query(meta.image[0], k=3)
    for key in ("route", "confidence", "source", "answer", "items", "latency_ms"):
        assert key in r
    assert r["route"] == "visual" and r["source"] == "internal"


def test_no_match_below_tau(tmp_path):
    vs, meta = _vs(tmp_path, tau_v=1.01)
    r = vs.query(meta.image[0], k=3)
    assert r["no_match"] and r["items"] == [] and r["answer"] == NO_MATCH_MSG


def test_zeroshot_gate_runs_with_text_tower(tmp_path):
    vs, meta = _vs(tmp_path, gate_mode="zeroshot")
    p = vs.type_probs(vs.embed_query(meta.image[0]))
    assert abs(p.sum() - 1) < 1e-6
