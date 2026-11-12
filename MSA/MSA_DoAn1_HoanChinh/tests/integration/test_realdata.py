"""Test tích hợp trên dữ liệu THẬT (tự bỏ qua nếu chưa tái tạo): index DINOv2-S của Khoa + shared_data v1
+ kho RAG ViMRHP của Chiến. Gemini vẫn giả (MockTransport) – không tốn quota.

Chuẩn bị: MSA_SHARED_DATA trỏ tới shared_data (00_Chung/prep_shared_data.py) và
04_Khoa/indexes/dinov2_s (cd 04_Khoa && python src/scripts/build_index.py --model dinov2_s --out indexes/dinov2_s --tau-v 0.5923).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import assert_contract, make_gateway

pytestmark = pytest.mark.realdata


def _shared() -> Path | None:
    p = os.environ.get("MSA_SHARED_DATA")
    return Path(p) if p and (Path(p) / "catalog_fpi.parquet").exists() else None


@pytest.fixture(scope="module")
def real_state(tmp_path_factory):
    from msa import paths
    shared = _shared()
    if shared is None:
        pytest.skip("chưa có shared_data (đặt MSA_SHARED_DATA, chạy 00_Chung/prep_shared_data.py)")
    if not (paths.visual_index_dir() / "config.json").exists():
        pytest.skip("chưa build index DINOv2-S (04_Khoa/indexes/dinov2_s)")
    return shared, tmp_path_factory.mktemp("real")


def test_real_visual_search_dinov2(real_state):
    from fastapi.testclient import TestClient
    from msa.api.main import State, create_app
    from msa.data.converters import read_catalog
    shared, tmp = real_state
    cat = read_catalog(shared / "catalog_fpi.parquet")
    st = State(catalog=cat, images_root=str(shared), gateway=make_gateway(tmp, mock=True), log_dir=str(tmp / "logs"),
               qa=object())
    c = TestClient(create_app(st))
    hits = 0
    pids = cat.product_id.iloc[[0, 1000, 2500, 4000]].tolist()
    for pid in pids:
        rel = cat.set_index("product_id").loc[pid].image_paths[0]
        b = c.post("/search/image", files={"file": ("q.jpg", (shared / rel).read_bytes(), "image/jpeg")}).json()
        assert_contract(b)
        assert b["tau_v"] == 0.5923
        hits += b["items"][0]["product_id"] == pid
    assert hits == len(pids)  # ảnh catalog tìm lại đúng chính nó ở top-1
    h = c.get("/health").json()
    assert h["visual"] == {"backend": "VisualSearcher", "tau_v": 0.5923}


def test_real_rag_on_vimrhp_kb(real_state, fake_gemini, monkeypatch):
    """RAG của Chiến trên kho ViMRHP thật (BM25, không tải e5), câu trả lời trích đúng SP được hỏi."""
    from msa.rag.pipeline import build_default_pipeline
    _, tmp = real_state
    gw = make_gateway(tmp, transport=fake_gemini["transport"])
    rag = build_default_pipeline(llm=gw, use_dense=False, tau_r=0.0)
    pid = next(iter(rag.titles))
    out = rag.answer("Chất lượng sản phẩm có tốt không?", pid)
    assert out["refused"] is False and out["citations"]
    assert all(ci["product_id"] == pid for ci in out["citations"])
