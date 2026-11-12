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


def test_http_agent_follows_api_contract(tmp_path):
    """HttpAgent gửi đúng hợp đồng API đã ghép: /chat {message, session_id}, /search/image trường `file`."""
    import httpx

    import baseline_e2e as E

    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(200, json={"route": "search", "source": "internal", "items": []})

    ag = E.HttpAgent("http://api")
    ag.c = httpx.Client(base_url="http://api", transport=httpx.MockTransport(handler))
    ag.handle(text="Tìm giày", case_id="e2e_19")
    body = json.loads(seen[-1].content)
    assert seen[-1].url.path == "/chat" and body["message"] == "Tìm giày" and body["session_id"].startswith("e2e-e2e_19")
    img = tmp_path / "q.jpg"; img.write_bytes(b"\xff\xd8xx")
    ag.handle(text="ảnh", image=str(img))
    assert seen[-1].url.path == "/search/image" and b'name="file"' in seen[-1].content


def test_e2e_resumable_budget_and_429(tmp_path):
    """Chạy nhiều đợt: ghi từng kịch bản, bỏ qua kịch bản đã có, dừng khi đủ ngân sách Gemini; kịch bản dính 429 không ghi."""
    import baseline_e2e as E

    log = tmp_path / "llm.jsonl"; log.write_text("", encoding="utf-8")
    quota = {"left": 1}

    class Ag:
        def handle(self, text=None, image=None, session=None):
            if text.startswith("g"):
                with open(log, "a", encoding="utf-8") as f:
                    if quota["left"] > 0:
                        quota["left"] -= 1
                        f.write(json.dumps({"event": "call", "tokens_in": 10, "tokens_out": 5}) + "\n")
                    else:
                        f.write(json.dumps({"event": "error", "status": 429, "retries": 0, "error": "429 PerDay"}) + "\n")
                        return {"route": "gemini_chitchat", "source": "fallback", "answer": "bận"}
                return {"route": "gemini_chitchat", "source": "gemini", "answer": "chào"}
            return {"route": "clarify", "source": "internal", "answer": "?"}

    sc = [{"id": f"c{i}", "expected_route": r, "text": t, "image": None, "criteria": {"source": "gemini"}}
          for i, (r, t) in enumerate([("clarify", "a"), ("gemini_chitchat", "g1"), ("gemini_chitchat", "g2"), ("clarify", "b")])]
    cases = tmp_path / "cases.jsonl"
    rows, stop = E.run_resumable(Ag(), sc, cases, E.LlmLogTail(str(log)), max_gemini_calls=5, pace_s=0)
    assert [r["id"] for r in rows] == ["c0", "c1"] and "429" in stop  # c2 dính 429 → không ghi, dừng đợt
    assert rows[1]["gemini_calls"] == 1 and rows[1]["tokens_in"] == 10 and rows[1]["success"]
    quota["left"] = 5  # "ngày hôm sau"
    rows, stop = E.run_resumable(Ag(), sc, cases, E.LlmLogTail(str(log)), max_gemini_calls=1, pace_s=0)
    assert [r["id"] for r in rows] == ["c0", "c1", "c2"] and "ngân sách" in stop
    rows, stop = E.run_resumable(Ag(), sc, cases, E.LlmLogTail(str(log)), max_gemini_calls=1, pace_s=0)
    assert [r["id"] for r in rows] == ["c0", "c1", "c2", "c3"] and stop == ""
    assert len(cases.read_text(encoding="utf-8").splitlines()) == 4
