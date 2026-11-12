"""Kiểm eval_router.jsonl và eval_qa.jsonl hợp lệ theo tiêu chí US_16."""
import os
import collections
import json
from pathlib import Path

import pytest

import build_eval_qa
import build_eval_router

ROOT = Path(__file__).resolve().parents[1]
VIMRHP = Path((os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/vimrhp_fashion_products.jsonl"))


def load(name):
    return [json.loads(l) for l in (ROOT / "eval" / name).open(encoding="utf-8")]


def test_eval_router_valid():
    rows = load("eval_router.jsonl")
    assert build_eval_router.check(rows, build_eval_router.load_vimrhp_ids()) == []
    c = collections.Counter(r["route"] for r in rows)
    assert len(rows) >= 60 and c["gemini_chitchat"] + c["gemini_ood"] >= 15
    assert all(r["origin"] == "viet_tay_tac_nhan" and r["annotator_1"] == "" for r in rows)  # chưa người duyệt
    assert max(c.values()) / min(c.values()) <= 2.0  # phân bố tương đối cân đối


def test_eval_router_file_matches_builder():
    assert load("eval_router.jsonl") == build_eval_router.build()


@pytest.mark.skipif(not VIMRHP.exists(), reason="thiếu shared_data")
def test_eval_qa_valid_on_real_data():
    from msa.rag.data import load_vimrhp

    rows = load("eval_qa.jsonl")
    assert build_eval_qa.check(rows, load_vimrhp()) == []
    assert len(rows) >= 150
    assert sum(not r["answerable"] for r in rows) / len(rows) > 0.15
    types = {r["type"] for r in rows}
    assert {"size_giay", "size_ao_quan", "chat_lieu", "form"} <= types
    assert all(r["reviewed_by"] == [] for r in rows)  # chưa có người thật duyệt – không ghi giả


def test_eval_qa_split_by_product():
    rows = load("eval_qa.jsonl")
    sp = collections.defaultdict(set)
    for r in rows:
        sp[r["product_id"]].add(r["split"])
    assert all(len(v) == 1 for v in sp.values())  # không lẫn SP giữa val/test


def test_check_detects_errors():
    bad = [{"id": "x", "product_id": "p", "question": "q", "answer": "a", "answerable": True, "evidence_review_ids": [],
            "type": "lạ", "origin": "llm_gemini", "reviewed_by": [], "split": "val"}]
    errs = build_eval_qa.check(bad)
    assert any("150" in e for e in errs) and any("type" in e for e in errs) and any("evidence" in e for e in errs)
