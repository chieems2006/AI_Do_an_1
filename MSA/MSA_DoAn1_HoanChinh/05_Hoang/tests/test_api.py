"""US_30/32/37/38/39 – API qua TestClient trên catalog tổng hợp (DummyVisualSearcher, Gemini mock)."""
import io
import json

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from conftest import make_image, to_bytes
from msa.api.compare import MISSING, compare_products
from msa.api.recommend import check_grounded, recommend
from msa.api.text_search import Filters, color_family, parse_filters_vi

RESP_KEYS = {"route", "confidence", "source", "answer", "items", "citations", "latency_ms", "request_id"}


# ---------------- US_32: 10 tình huống ảnh lỗi ----------------
def _noise(w, h):
    return Image.fromarray(np.random.default_rng(0).integers(0, 255, (h, w, 3), dtype=np.uint8))


def _png_bytes_big():  # > 5 MB: PNG nhiễu không nén được
    return to_bytes(_noise(1400, 1400), "PNG")


ERROR_CASES = [
    ("empty_file", lambda: b"", "a.jpg"),
    ("too_large", _png_bytes_big, "big.png"),
    ("not_an_image", lambda: "đây là văn bản, không phải ảnh".encode(), "note.jpg"),
    ("not_an_image", lambda: b"%PDF-1.4\n%\xe2\xe3\n1 0 obj<<>>endobj", "doc.pdf"),
    ("unsupported_format", lambda: to_bytes(make_image("Red", "footwear"), "GIF"), "a.gif"),
    ("unsupported_format", lambda: to_bytes(make_image("Red", "footwear"), "BMP"), "a.bmp"),
    ("corrupted", lambda: to_bytes(_noise(200, 200), "JPEG")[:1500], "cut.jpg"),
    ("too_small", lambda: to_bytes(_noise(20, 20), "JPEG"), "tiny.jpg"),
    ("bad_aspect", lambda: to_bytes(_noise(900, 40), "PNG"), "strip.png"),
    ("blank_image", lambda: to_bytes(Image.new("RGB", (200, 200), (250, 250, 250)), "JPEG"), "white.jpg"),
]


@pytest.mark.parametrize("code,make,name", ERROR_CASES, ids=[f"{c}_{n}" for c, _, n in ERROR_CASES])
def test_image_errors(client, code, make, name):
    c, _ = client
    r = c.post("/search/image", files={"file": (name, make(), "application/octet-stream")})
    assert r.status_code == 400, r.text
    body = r.json()
    assert body["error"]["code"] == code and body["answer"] and RESP_KEYS <= set(body) and body["items"] == []


def test_missing_file_and_pixel_bomb(client, monkeypatch):
    c, _ = client
    r = c.post("/search/image", data={"k": "5"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "missing_file"
    import msa.api.validation as V
    monkeypatch.setattr(V, "MAX_PIXELS", 5000)
    r = c.post("/search/image", files={"file": ("a.jpg", to_bytes(make_image("Red", "footwear", size=(100, 100))))})
    assert r.json()["error"]["code"] == "too_many_pixels"


# ---------------- US_30: tìm bằng ảnh ----------------
def test_search_image_same_type(client, synth):
    c, tmp = client
    pid = "syn_005"
    r = c.post("/search/image", files={"file": ("q.jpg", to_bytes(synth["images"][pid]), "image/jpeg")}, data={"k": "5"})
    b = r.json()
    assert r.status_code == 200 and b["route"] == "visual" and len(b["items"]) == 5
    # histogram màu không phân biệt được các SP cùng màu+hình → chỉ yêu cầu SP gốc nằm trong top-5, top-1 cùng nhóm
    assert pid in [i["product_id"] for i in b["items"]] and b["confidence"] > 0.9
    assert b["items"][0]["product_type"] == synth["types"][pid]
    r = c.post("/search/image", files={"file": ("q.jpg", to_bytes(synth["images"][pid]))},
               data={"k": "5", "product_type": "accessory"})
    assert all(i["product_type"] == "accessory" for i in r.json()["items"])
    log = (tmp / "logs" / "requests.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(log[-1])["endpoint"] == "/search/image"


def test_search_image_low_confidence(client, monkeypatch):
    import msa.api.main as main
    monkeypatch.setattr(main, "TAU_V", 1.01)
    c, _ = client
    r = c.post("/search/image", files={"file": ("q.jpg", to_bytes(make_image("Green", "headwear")))})
    assert r.status_code == 200 and r.json()["error"]["code"] == "not_product" and r.json()["items"] == []


# ---------------- US_37: 15 truy vấn lọc ----------------
QUERIES = [
    ("giày", {"product_type": "footwear"}),
    ("sneaker", {"sub_category": "sneaker"}),
    ("", {"colors": ["đen"]}),
    ("áo", {"product_type": "clothing", "colors": ["Red"]}),
    ("", {"gender": "Women"}),
    ("", {"gender": "Men", "include_unisex": False}),
    ("", {"price_max": 300000}),
    ("", {"price_min": 500000, "price_max": 700000}),
    ("giày", {"size": "41"}),
    ("", {"product_type": "clothing", "size": "XL"}),
    ("mũ", {"product_type": "headwear", "colors": ["xanh dương"]}),
    ("túi", {"sub_category": "bag", "price_max": 600000}),
    ("", {"product_type": "accessory", "gender": "Unisex"}),
    ("dép", {"sub_category": "sandal", "colors": ["hồng", "nâu"]}),
    ("", {"product_type": "footwear", "gender": "Women", "price_min": 200000}),
]


def satisfies(item: dict, f: dict, cat) -> bool:
    row = cat.set_index("product_id").loc[item["product_id"]]
    if f.get("product_type") and row.product_type != f["product_type"]:
        return False
    if f.get("sub_category") and row.sub_category != f["sub_category"]:
        return False
    if f.get("colors"):
        want = {color_family(x) for x in f["colors"]}
        if not ({color_family(x) for x in row.colors} & want):
            return False
    if f.get("gender"):
        ok = {f["gender"]} | ({"Unisex"} if f.get("include_unisex", True) else set())
        if row.gender not in ok:
            return False
    if "price_min" in f or "price_max" in f:
        if row.price is None or row.price != row.price:
            return False
        if row.price < f.get("price_min", -1) or row.price > f.get("price_max", 1e18):
            return False
    if f.get("size") and f["size"] not in row.sizes:
        return False
    return True


@pytest.mark.parametrize("q,f", QUERIES)
def test_text_filters(client, synth, q, f):
    c, _ = client
    r = c.post("/search/text", json={"query": q, "k": 50, "filters": f})
    b = r.json()
    assert r.status_code == 200 and RESP_KEYS <= set(b) and b["route"] == "search"
    assert b["items"], f"không có kết quả cho {f}"
    assert all(satisfies(i, f, synth["df"]) for i in b["items"])
    # đủ: mọi SP thoả bộ lọc đều được trả (k=50 ≥ số SP)
    n_true = sum(satisfies({"product_id": p}, f, synth["df"]) for p in synth["df"].product_id)
    assert len(b["items"]) == n_true


def test_parse_filters_vi():
    f = parse_filters_vi("Tìm giày thể thao nữ màu trắng dưới 500k")
    assert f.product_type == "footwear" and f.colors == ["white"] and f.gender == "Women" and f.price_max == 500_000
    f = parse_filters_vi("áo khoác có mũ nam xanh navy từ 1,5tr")
    assert f.product_type == "clothing" and f.colors == ["blue"] and f.gender == "Men" and f.price_min == 1_500_000


def test_text_ranking_vietnamese(client):
    c, _ = client
    b = c.post("/search/text", json={"query": "giày sneaker màu đen", "k": 3}).json()
    assert b["items"][0]["sub_category"] == "sneaker"
    b = c.post("/search/text", json={"query": "mũ đen", "k": 3, "auto_filters": True}).json()
    assert b["applied_filters"]["product_type"] == "headwear" and all(i["product_type"] == "headwear" for i in b["items"])


# ---------------- US_38: 20 cặp so sánh khớp 100% dữ liệu gốc ----------------
def _pairs(df, n=20):
    rng = np.random.default_rng(42)
    out = []
    for pt, g in df.groupby("product_type"):
        ids = g.product_id.tolist()
        for _ in range(n // 4):
            k = 2 if len(out) % 2 == 0 else 3
            out.append(list(rng.choice(ids, size=k, replace=False)))
    return out


def test_compare_20_pairs_exact(client, synth):
    c, _ = client
    df = synth["df"].set_index("product_id")
    pairs = _pairs(synth["df"])
    assert len(pairs) == 20
    for ids in pairs:
        b = c.post("/compare", json={"product_ids": ids}).json()
        t = b["table"]
        rows = {r["key"]: r["values"] for r in t["rows"]}
        for p in ids:
            src = df.loc[p]
            exp = {"title": src.title, "price": src.price, "colors": ", ".join(src.colors) if src.colors else MISSING,
                   "sizes": ", ".join(src.sizes) if src.sizes else MISSING, "gender": src.gender,
                   "material": src.specs["material"] or MISSING, "usage": src.specs["usage"],
                   "rating": src.rating if src.rating is not None and src.rating == src.rating else MISSING,
                   "description": MISSING if pd.isna(src.description) else src.description}
            if exp["price"] is None or exp["price"] != exp["price"]:
                exp["price"] = MISSING
            for k_, v in exp.items():
                assert rows[k_][p] == v, (p, k_, rows[k_][p], v)


def test_compare_errors(client):
    c, _ = client
    assert c.post("/compare", json={"product_ids": ["syn_000"]}).json()["error"]["code"] == "bad_count"
    assert c.post("/compare", json={"product_ids": ["syn_000", "nope"]}).json()["error"]["code"] == "not_found"
    r = c.post("/compare", json={"product_ids": ["syn_000", "syn_020"]})  # footwear vs clothing
    assert r.status_code == 400 and r.json()["error"]["code"] == "mixed_types"


# ---------------- US_39: gợi ý không bịa ----------------
def test_recommend_uses_only_table(synth):
    t = compare_products(synth["df"], ["syn_000", "syn_001", "syn_002"])
    r = recommend(t, "đi bộ nhiều, ngân sách dưới 200k, màu đen")
    assert r["pick"] in t["columns"] and r["grounded"]
    ok, bad = check_grounded(r["answer"], t, "dưới 200k")
    assert ok, bad
    ok, bad = check_grounded("Nên chọn syn_999 vì giá 999999 và chất liệu lụa", t)
    assert not ok and any("999" in b for b in bad)


class FakeLLM:
    def __init__(self, text):
        self.text = text

    def generate(self, prompt, system=None, **kw):
        assert "BẢNG" in prompt
        return {"answer": self.text, "source": "gemini"}


def test_recommend_rejects_hallucinated_llm(synth):
    t = compare_products(synth["df"], ["syn_000", "syn_001"])
    r = recommend(t, "đi làm", gateway=FakeLLM("Chọn syn_000 vì đế cao 5cm, giá 123456."))
    assert r["source"] == "internal" and not r["grounded"] and r["violations"]
    good = f"Chọn syn_000 vì có màu {t['rows'][5]['values']['syn_000']}."
    r = recommend(t, "đi làm", gateway=FakeLLM(good))
    assert r["source"] == "gemini" and r["grounded"]


def test_compare_with_needs_endpoint(client):
    c, _ = client
    b = c.post("/compare", json={"product_ids": ["syn_001", "syn_002"], "needs": "dưới 300k"}).json()
    assert b["recommendation"]["pick"] in ("syn_001", "syn_002") and b["source"] == "internal"


# ---------------- /qa, /chat, /health ----------------
def test_qa_stub_and_refusal(client):
    c, _ = client
    b = c.post("/qa", json={"question": "Chất liệu có mềm không?", "product_id": "syn_001"}).json()
    assert b["route"] == "qa" and not b["refused"] and b["citations"][0]["field"] == "review"
    b = c.post("/qa", json={"question": "Bảo hành bao lâu?", "product_id": "syn_001"}).json()
    assert b["refused"] and "Chưa có thông tin" in b["answer"] and b["source"] == "internal"


def test_chat_mock_gemini_label(client):
    c, _ = client
    b = c.post("/chat", json={"message": "Chào shop"}).json()
    assert b["source"] == "gemini" and b["route"] == "gemini_chitchat"
    b2 = c.post("/chat", json={"message": "Chào shop"}).json()
    assert b2["source"] == "cache"
    assert c.get("/health").json()["status"] == "ok"
