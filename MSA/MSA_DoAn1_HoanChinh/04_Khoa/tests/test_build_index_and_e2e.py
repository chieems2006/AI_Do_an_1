import json

import pandas as pd

from _synth import make_catalog


def test_build_index_dummy(tmp_path):
    import build_index as BI
    from msa.search.visual import VisualSearcher

    cat = make_catalog(tmp_path)
    cp = tmp_path / "cat.parquet"; cat.to_parquet(cp)
    res = BI.build("dummy", cp, tmp_path, tmp_path / "idx", tau_v=0.25, gate_tau=0.0, reuse_cache=False, n_lat=5, rep=3, query_csv=None)
    assert res["n_items"] == len(cat) and res["n_latency_measurements"] == 15
    vs = VisualSearcher.load(tmp_path / "idx", embedder=__import__("msa.embed.image_embedders", fromlist=["x"]).DummyEmbedder())
    assert vs.search(str(tmp_path / cat.image_paths[0][0]), k=1)[0]["product_id"] == cat.product_id[0]


def test_e2e_judge_and_fake_run():
    import baseline_e2e as E

    sc = [{"id": "1", "expected_route": "gemini_ood", "text": "x", "image": None, "criteria": {"source": "gemini", "no_store_facts": True}},
          {"id": "2", "expected_route": "search", "text": "Tìm giày", "image": None, "criteria": {"product_type": "footwear"}},
          {"id": "3", "expected_route": "compare", "text": "So sánh 2 áo", "image": None, "criteria": {"n_items": 2}}]
    summ, df = E.run(E.FakeAgent(), sc, 0.1, 0.4)
    assert summ["n"] == 3 and 0 <= summ["task_success_rate"] <= 1
    assert df.loc[0, "error_code"].startswith("khong_chuyen_gemini")
    ok, _ = E.judge(sc[0], {"route": "gemini_ood", "source": "gemini", "answer": "Giá áo là 200k"})
    assert not ok


def test_e2e_has_60_scenarios_with_10_chitchat_ood():
    import baseline_e2e as E

    if not (E.ROOT / "eval" / "eval_visual.csv").exists():
        return
    sc = E.build_scenarios()
    assert len(sc) == 60
    assert sum(s["expected_route"] in ("gemini_chitchat", "gemini_ood") for s in sc) >= 10
