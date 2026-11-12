"""Fixture cho test tích hợp: dựng toàn bộ hệ thống MSA (API Hoàng + VisualSearcher Khoa + RAG Chiến +
Router/Agent Trung + LLMGateway Hoàng) trên catalog tổng hợp nhỏ, Gemini ở chế độ mock.

Hai kiểu "Gemini giả":
- `LLMGateway(mock=True)`: chế độ mock có sẵn của gateway (không gọi mạng, trả "[MOCK] ...").
- `LLMGateway(transport=httpx.MockTransport)`: đi qua TOÀN BỘ đường gọi REST của gateway (dựng body, đọc
  usageMetadata, cache, retry, fallback) nhưng máy chủ Gemini là hàm giả trong test – không gọi mạng.
"""
from __future__ import annotations

import io
import json
import os
import random
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
import pytest
from PIL import Image, ImageDraw

os.environ.pop("GEMINI_API_KEY", None)  # test không bao giờ gọi Gemini thật

TYPES = {"footwear": ["sneaker", "sandal"], "clothing": ["top", "dress"],
         "headwear": ["cap", "beanie"], "accessory": ["bag", "belt"]}
VI = {"sneaker": "Giày sneaker", "sandal": "Dép sandal", "top": "Áo thun", "dress": "Đầm",
      "cap": "Mũ lưỡi trai", "beanie": "Mũ len", "bag": "Túi xách", "belt": "Thắt lưng"}
COLORS = [("Black", "đen", (15, 15, 15)), ("White", "trắng", (240, 240, 240)),
          ("Red", "đỏ", (200, 20, 30)), ("Navy Blue", "xanh navy", (20, 30, 110))]
SHAPE = {"footwear": "ellipse", "clothing": "rectangle", "headwear": "pieslice", "accessory": "polygon"}
MATERIAL = ["da", "vải", "cotton", "nỉ"]
TEST_KEY = "test-key-khong-phai-key-that"


def make_image(rgb: tuple, ptype: str, seed: int = 0, size=(80, 96)) -> Image.Image:
    rnd = random.Random(seed)
    im = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(im)
    box = (8 + rnd.randint(0, 5), 12 + rnd.randint(0, 5), size[0] - 8, size[1] - 10)
    if SHAPE[ptype] == "polygon":
        d.polygon([(8, 86), (40, 10), (72, 86)], fill=rgb)
    elif SHAPE[ptype] == "pieslice":
        d.pieslice(box, 180, 360, fill=rgb)
    else:
        getattr(d, SHAPE[ptype])(box, fill=rgb)
    return im


def to_jpeg(im: Image.Image) -> bytes:
    b = io.BytesIO()
    im.save(b, format="JPEG", quality=95)
    return b.getvalue()


@pytest.fixture(scope="session")
def catalog(tmp_path_factory) -> dict:
    """16 SP (4 nhóm × 2 lá × 2 màu) theo schema 5.1, có ảnh trên đĩa và review tiếng Việt."""
    root = tmp_path_factory.mktemp("shared")
    rows, i = [], 0
    for pt, subs in TYPES.items():
        for sub in subs:
            for c in range(2):
                en, vi, rgb = COLORS[(i + c) % len(COLORS)]
                pid = f"it_{i:03d}"
                mat = MATERIAL[i % len(MATERIAL)]
                rel = f"images/{pid}.jpg"
                (root / "images").mkdir(exist_ok=True)
                make_image(rgb, pt, seed=i).save(root / rel)
                rows.append(dict(
                    product_id=pid, title=f"{VI[sub]} màu {vi} mẫu {i}", category=f"{pt}/{sub}", brand=f"Brand{i % 3}",
                    price=float(150_000 + 25_000 * i), currency="VND", colors=[en], sizes=["39", "40"] if pt == "footwear" else ["M"],
                    description=f"{VI[sub]} chất liệu {mat}.", specs={"material": mat, "usage": "Casual"},
                    image_paths=[rel], rating=4.5, rating_count=10,
                    reviews=[{"review_id": f"r{i}_0", "rating": 5, "text": f"Chất liệu {mat} mềm, mặc rất thoải mái."},
                             {"review_id": f"r{i}_1", "rating": 4, "text": "Giao hàng nhanh, đóng gói cẩn thận."}],
                    source="synthetic", source_url=None, license="synthetic", product_type=pt, sub_category=sub,
                    gender=["Men", "Women"][i % 2], size_system="EU" if pt == "footwear" else "alpha",
                    view_type="studio", variant_id=None, language="vi"))
                i += 1
    df = pd.DataFrame(rows)
    return {"df": df, "root": root, "by_id": {r["product_id"]: r for r in rows}}


@pytest.fixture(scope="session")
def visual_index(catalog, tmp_path_factory) -> Path:
    """Index ảnh theo đúng định dạng build_index.py của Khoa (config.json, embeddings.npy, meta.parquet).
    config ghi model="dinov2_s" để API lấy τ_v của DINOv2-S từ 04_Khoa/results/tau_v_analysis.json;
    embedder thật được thay bằng DummyEmbedder (tất định, không cần torch) khi nạp."""
    from msa.embed.image_embedders import DummyEmbedder
    from msa.search.visual import build_meta
    d = tmp_path_factory.mktemp("index") / "dinov2_s"
    d.mkdir()
    meta = build_meta(catalog["df"], catalog["root"])
    X = DummyEmbedder().embed(meta.image.tolist())
    np.save(d / "embeddings.npy", X.astype(np.float32))
    meta.to_parquet(d / "meta.parquet", index=False)
    (d / "config.json").write_text(json.dumps({"model": "dinov2_s", "n_items": len(X), "dim": int(X.shape[1]),
                                               "tau_v": 0.25, "gate_tau": 0.0}), encoding="utf-8")
    return d


@pytest.fixture()
def fake_gemini():
    """Máy chủ Gemini giả: ghi lại request, trả lời theo loại prompt; `mode` = ok | 503 | 429day."""
    state = {"mode": "ok", "requests": []}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        state["requests"].append({"url": str(request.url), "body": body, "headers": dict(request.headers)})
        if state["mode"] == "503":
            return httpx.Response(503, json={"error": {"message": "overloaded"}})
        if state["mode"] == "429day":
            return httpx.Response(429, json={"error": {"message": "quota GenerateRequestsPerDayPerProjectPerModel"}})
        prompt = body["contents"][0]["parts"][0]["text"]
        if "[C1]" in prompt:  # prompt RAG của Chiến liệt kê ngữ cảnh [C1]..[Ck]
            text = "Theo đánh giá của khách, chất liệu mềm và mặc thoải mái [C1]."
        else:
            text = "Chào bạn! Mình là trợ lý mua sắm thời trang, bạn cần tìm gì ạ?"
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
                                         "usageMetadata": {"promptTokenCount": 120, "candidatesTokenCount": 18,
                                                           "thoughtsTokenCount": 0}, "modelVersion": "fake"})

    state["transport"] = httpx.MockTransport(handler)
    return state


def make_gateway(tmp_path: Path, transport=None, mock: bool = False):
    from msa.llm_gateway import LLMGateway
    return LLMGateway(model="gemini-test", api_key=None if mock else TEST_KEY, mock=mock, transport=transport, rpm=0,
                      max_retries=1, sleep=lambda s: None, cache_path=str(tmp_path / "llm_cache.sqlite"),
                      log_path=str(tmp_path / "llm_calls.jsonl"))


def make_rag(catalog_df: pd.DataFrame, llm):
    """RAGPipeline của Chiến trên review của catalog test (BM25 – không tải model e5), τ_r = 0 như cấu hình thật."""
    from msa.rag.ingest import build_chunks
    from msa.rag.pipeline import RAGPipeline
    from msa.rag.retriever import BM25Retriever
    prods = catalog_df.to_dict("records")
    return RAGPipeline(BM25Retriever(build_chunks(prods)), llm, tau_r=0.0, k=5,
                       titles={p["product_id"]: p["title"] for p in prods})


@pytest.fixture()
def system(catalog, visual_index, fake_gemini, tmp_path, monkeypatch):
    """Hệ thống ghép đủ 5 module; trả (TestClient, State, fake_gemini)."""
    from fastapi.testclient import TestClient
    from msa.api.main import State, create_app
    from msa.api.searchers import load_visual_index
    from msa.embed.image_embedders import DummyEmbedder
    gw = make_gateway(tmp_path, transport=fake_gemini["transport"])
    st = State(catalog=catalog["df"], images_root=str(catalog["root"]), gateway=gw, log_dir=str(tmp_path / "logs"),
               visual=load_visual_index(visual_index, embedder=DummyEmbedder()), qa=make_rag(catalog["df"], gw))
    return TestClient(create_app(st)), st, fake_gemini


CONTRACT_KEYS = {"route", "confidence", "source", "answer", "items", "citations", "latency_ms", "request_id"}
SOURCES = {"internal", "gemini", "cache", "fallback"}


def assert_contract(body: dict) -> None:
    """Định dạng response chung – 00_THIET_KE_CHUNG.md mục 5.2 (+ source="fallback" theo QUYET_DINH mục D)."""
    assert CONTRACT_KEYS <= set(body), CONTRACT_KEYS - set(body)
    assert body["route"] in {"visual", "qa", "search", "compare", "gemini_chitchat", "gemini_ood", "clarify"}
    assert body["source"] in SOURCES
    assert isinstance(body["items"], list) and isinstance(body["citations"], list)
    for it in body["items"]:
        assert "product_id" in it
