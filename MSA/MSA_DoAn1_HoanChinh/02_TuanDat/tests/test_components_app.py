"""US_31/US_43 – card, nhãn nguồn, bảng so sánh, 4 luồng UI qua backend mock (dữ liệu thật đã làm sạch)."""
import os
from pathlib import Path

import pandas as pd
import pytest

import components as C

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "results" / "catalog_clean.parquet"
IMG_ROOT = os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data")


def test_labels():
    assert C.source_label({"source": "gemini"}) == C.LABEL_GEMINI
    assert C.source_label({"source": "internal"}) == C.LABEL_STORE
    assert C.source_label({"source": "cache", "route": "gemini_ood"}).startswith(C.LABEL_GEMINI)
    assert C.source_label({"source": "cache", "route": "qa"}) == C.LABEL_STORE
    # Tác nhân 2: thông điệp dự phòng của LLMGateway (Hoàng) không được hiện là "Từ dữ liệu cửa hàng"
    assert C.source_label({"source": "fallback", "route": "gemini_chitchat"}) == C.LABEL_SYSTEM


def test_formatters():
    assert C.format_price(1250000) == "1.250.000 ₫"
    assert C.format_price(None) == "Chưa có giá" and C.format_price(float("nan")) == "Chưa có giá"
    assert C.format_score(0.873) == "Tương đồng 87%" and C.format_score(None) == "Chưa có điểm"


def test_card_escapes_html():
    h = C.render_card_html({"title": "<script>x</script>", "price": 1, "score": 0.5})
    assert "<script>" not in h and "Không có ảnh" in h and "Không có link" in h


@pytest.mark.skipif(not CATALOG.exists(), reason="chưa chạy 03_clean.py")
def test_20_real_products_all_fields():
    """Tiêu chí US_31: hiển thị đúng 100% trường trên 20 SP thử (catalog thật, ảnh thật)."""
    df = pd.read_parquet(CATALOG).sample(20, random_state=42)
    ok = 0
    for i, r in enumerate(df.itertuples()):
        item = {"product_id": r.product_id, "title": r.title, "price": 199000 * (i % 2) or None,
                "score": 0.5 + i / 50, "image": list(r.image_paths)[0], "source_url": r.source_url}
        f = C.card_fields(item, IMG_ROOT)
        html = C.render_card_html(item, IMG_ROOT)
        assert f["image"].startswith("data:image/jpeg;base64,")
        assert f["title"] == r.title
        assert f["price"] == ("199.000 ₫" if i % 2 else "Chưa có giá")
        assert f["score"] == f"Tương đồng {(0.5 + i / 50) * 100:.0f}%"
        assert f["link"] == r.source_url
        assert all(x in html for x in ["msa-img", "msa-price", "msa-score", "Xem nguồn"])
        ok += 1
    assert ok == 20


def test_compare_table():
    md = C.render_compare_table([{"title": "A", "price": 100000, "colors": ["Black"]}, {"title": "B"}])
    assert "| Tên | A | B |" in md and "100.000 ₫" in md and "Chưa có thông tin" in md
    assert "Cần ít nhất 2" in C.render_compare_table([{"title": "A"}])


def test_validate_response():
    good = {"route": "qa", "confidence": 0.5, "source": "internal", "answer": "x", "items": [], "citations": [],
            "latency_ms": 1, "request_id": "r"}
    assert C.validate_response(good) == []
    assert C.validate_response({"route": "bad"})


@pytest.mark.skipif(not CATALOG.exists(), reason="chưa chạy 03_clean.py")
def test_four_flows_mock_backend():
    """US_43: đủ 4 luồng ảnh / hỏi đáp / tìm / so sánh (+ chat) qua Backend ở chế độ mock."""
    from app import Backend
    b = Backend(force_mock=True)
    df = pd.read_parquet(CATALOG)
    img = Path(IMG_ROOT, list(df.image_paths.iloc[0])[0]).read_bytes()
    r_img = b.handle("", img)
    r_search = b.handle("tìm giày đen nam", None)
    r_cmp = b.handle(f"so sánh {df.product_id.iloc[0]} {df.product_id.iloc[1]}", None)
    r_qa = b.handle("shopee_25814055660 quần có co giãn không?", None)
    r_chat = b.handle("chào shop", None)
    assert r_img["route"] == "visual" and r_img["items"]
    assert r_search["route"] == "search" and r_search["items"]
    assert r_cmp["route"] == "compare" and len(r_cmp["items"]) == 2
    assert r_qa["route"] == "qa" and r_qa["answer"]
    assert r_chat["source"] == "gemini" and C.source_label(r_chat) == C.LABEL_GEMINI
    for r in (r_img, r_search, r_cmp, r_qa, r_chat):
        assert C.validate_response(r) == []
        chat_md, cards, cmp_md = C.render_response(r, IMG_ROOT)
        assert ("Từ dữ liệu cửa hàng" in chat_md) or ("Trả lời bởi Gemini" in chat_md)
    assert "| Thuộc tính |" in C.render_response(r_cmp)[2]


def test_backend_falls_back_when_api_down():
    from app import Backend
    b = Backend(url="http://127.0.0.1:9", force_mock=False, timeout=0.5)
    r = b.handle("chào shop", None)
    assert r.get("mock") is True
