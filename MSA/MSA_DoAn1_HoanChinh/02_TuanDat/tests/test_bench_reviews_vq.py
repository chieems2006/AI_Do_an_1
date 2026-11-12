"""US_24 / US_36 / US_11 – benchmark (LLM giả), tóm tắt review, kiểm tập ảnh truy vấn, client Gemini (mock)."""
import json
import os
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


# ---------------- US_24
def test_bench_qa_set_valid():
    import build_bench_qa as B
    rows = B.build()
    assert len(rows) == 36
    un = [r for r in rows if not r["answerable"]]
    assert len(un) == 7 and all(r["reference_answer"] == B.REFUSAL for r in un)
    assert all(r["origin"] == "tac_nhan_AI_viet_tay_tu_review_that" and r["reviewed_by_human"] is False for r in rows)


def test_heuristics_and_echo(tmp_path, monkeypatch):
    import bench_llm as BL
    ctx = {"title": "Dép", "context": [{"rid": "R1", "text": "dép đi êm chân, đế cao 4cm"}]}
    h = BL.heuristic_scores("Dép đi êm chân [R1]", ctx)
    assert h["cited"] and not h["refused"] and h["support_overlap"] == 1.0
    h2 = BL.heuristic_scores(BL.REFUSAL + " [R9]", ctx)
    assert h2["refused"] and h2["invalid_citations"] == ["R9"]
    monkeypatch.setattr(BL, "RES", tmp_path)
    out = BL.run_qa(BL.EchoLLM(), "echo", limit=5)
    rows = [json.loads(l) for l in out.open(encoding="utf-8")]
    assert len(rows) == 5 and all(r["temperature"] == 0.0 for r in rows)
    s = BL.summarize()
    assert s["qa"]["echo"]["n"] == 5


def test_router_stratified_and_cost():
    import bench_llm as BL
    items = BL.load_jsonl(BL.ROUTER_FILE)
    st = BL.stratified(items, 2)
    assert len(st) == 14 and len({i["route"] for i in st}) == 7
    c = BL.cost_per_100(1000, 500, "gemini-3.5-flash")
    assert c["usd_per_100"] is None and c["tokens_in_per_100"] == 1000  # đơn giá chưa xác minh → không quy tiền
    assert BL.pct([1, 2, 3, 4], 0.5) == 2.5


def test_gemini_client_mock_and_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("MSA_LLM_MOCK", "1")
    from msa_td.gemini_client import GeminiClient
    c = GeminiClient(cache_path=str(tmp_path / "c.sqlite"), budget_file=str(tmp_path / "b.json"))
    r = c.generate("xin chào")
    assert r["source"] == "gemini" and r["answer"].startswith("[MOCK]") and r["error"] is None


def test_gemini_client_429_circuit(tmp_path, monkeypatch):
    """Giả lập 429 (quota ngày) → chỉ gọi 1 lần/lượt, ngắt mạch sau 3 lần, không đốt ngân sách."""
    from msa_td import gemini_client as G
    monkeypatch.delenv("MSA_LLM_MOCK", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key-for-test")

    class R:
        status_code = 429
        text = "quota"

        def json(self):
            return {"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota", "details": [
                {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
                 "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier", "quotaValue": "20"}]}]}}

    calls = []
    c = G.GeminiClient(budget_file=str(tmp_path / "b.json"), max_retries=3)
    monkeypatch.setattr(c._session, "post", lambda *a, **k: calls.append(1) or R())
    outs = [c.generate(f"q{i}") for i in range(5)]
    assert [o["error"] for o in outs[:3]] == ["http_429"] * 3
    assert outs[3]["error"] == "circuit_open_429" and len(calls) == 3
    assert c.last_429_info["violations"][0]["quotaValue"] == "20"


def test_gemini_client_timeout(tmp_path, monkeypatch):
    import requests
    from msa_td import gemini_client as G
    monkeypatch.delenv("MSA_LLM_MOCK", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key-for-test")
    monkeypatch.setattr(G.time, "sleep", lambda s: None)
    c = G.GeminiClient(budget_file=str(tmp_path / "b.json"), max_retries=1)

    def boom(*a, **k):
        raise requests.Timeout()
    monkeypatch.setattr(c._session, "post", boom)
    assert c.generate("x")["error"] == "network:Timeout"


@pytest.mark.live
def test_gemini_live_one_call():
    from msa_td.gemini_client import GeminiClient
    c = GeminiClient(model=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                     budget_file=str(ROOT / "results" / "gemini_budget.json"))
    r = c.generate("Trả lời đúng 1 từ: xin chào")
    assert r["error"] is None and r["answer"]


# ---------------- US_36
def test_review_aspects():
    import summarize_reviews as S
    assert S.aspect_hits("Dép đi êm chân, giao hàng nhanh")["comfort"] == "pos"
    assert S.aspect_hits("áo bị rách phần nách")["durability"] == "neg"
    assert S.aspect_hits("không có chỉ thừa, đường may đẹp")["stitching"] == "pos"
    assert S.aspect_hits("nhiều chỉ thừa")["stitching"] == "neg"
    assert "fit" not in S.aspect_hits("mặc size M rộng rãi thoải mái")
    assert "durability" not in S.aspect_hits("không biết có bền không")
    assert S.is_spam("[QC] Mừng sinh nhật, nhận voucher") and not S.is_spam("áo đẹp")


def test_summarize_product_grounded():
    import summarize_reviews as S
    p = {"product_id": "p", "title": "Áo", "vimrhp_subcategory": "ThoiTrangNu", "reviews": [
        {"comment_id": 1, "rating": 5, "text": "vải mát, giao hàng nhanh"},
        {"comment_id": 2, "rating": 4, "text": "vải mát lắm, giao nhanh"},
        {"comment_id": 3, "rating": 2, "text": "áo bị rách"},
        {"comment_id": 4, "rating": 5, "text": "[QC] voucher giảm giá"}]}
    s = S.summarize_product(p)
    assert s["n_spam_filtered"] == 1 and s["avg_rating"] == 4.0
    ids = {e["comment_id"] for x in s["pros"] + s["cons"] for e in x["evidence"]}
    assert ids <= {1, 2, 3}                                       # mọi minh chứng là review thật
    assert {x["aspect"] for x in s["cons"]} == {"durability"}


@pytest.mark.skipif(not (ROOT / "results" / "product_review_summary.json").exists(), reason="chưa chạy baseline")
def test_summary_file_real():
    d = json.loads((ROOT / "results" / "product_review_summary.json").read_text(encoding="utf-8"))
    assert d["_meta"]["n_products"] == 428 and "DongHo" in d["_meta"]["excluded_subcategories"]


# ---------------- US_11
def _vq_df(n_per):
    rows = []
    i = 0
    for t, n in n_per.items():
        for _ in range(n):
            i += 1
            rows.append(dict(query_id=f"VQ{i:03d}", file=f"x/{i}.jpg", product_type=t,
                             scenario="nguoi_mac_nhieu_mon" if i == 1 else "tu_chup", gt_product_ids="fpi_1|fpi_2",
                             annotator_1="Đạt", annotator_2="Chiến", agreed="yes", note=""))
    return pd.DataFrame(rows)


def test_visual_queries_pass_and_fail():
    from check_visual_queries import check
    ok = check(_vq_df({"footwear": 25, "clothing": 25, "headwear": 15, "accessory": 15}), catalog_ids={"fpi_1", "fpi_2"})
    assert ok["ok"], ok["errors"]
    bad_df = _vq_df({"footwear": 25, "clothing": 20, "headwear": 15, "accessory": 15})
    bad_df.loc[0, "annotator_2"] = ""
    bad = check(bad_df, catalog_ids={"fpi_1"})
    msgs = " ".join(bad["errors"])
    assert not bad["ok"] and "clothing" in msgs and "2 người" in msgs and "không có trong catalog" in msgs


def test_visual_template_parses():
    from check_visual_queries import check
    df = pd.read_csv(ROOT / "eval" / "visual_queries_ground_truth_template.csv", dtype=str)
    res = check(df)
    assert not res["ok"] and res["stats"]["n"] == 0                # dòng ví dụ bị bỏ, chưa có ảnh thật → CHƯA ĐẠT
