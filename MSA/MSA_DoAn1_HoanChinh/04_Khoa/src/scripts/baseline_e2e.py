# repo: scripts/baseline_e2e.py
"""US_44 – Đo baseline end-to-end trên 60 kịch bản (≥ 10 chitchat/ngoài phạm vi).

Chế độ agent:
  --agent fake         : agent giả theo luật (CHỈ để kiểm thử khung, số liệu KHÔNG dùng cho báo cáo)
  --agent visual-only  : chạy THẬT VisualSearcher trên index đã build cho các kịch bản visual; các route khác = not_ready
  --agent http --base-url http://localhost:8000 : gọi API của Hoàng khi hệ thống đã ghép (số e2e thật)
  --agent python --agent-cls msa.agent.router:Agent : gọi trực tiếp Agent của Trung

Kết quả: results/e2e_<agent>.json + results/e2e_<agent>_per_case.csv
Chi phí/100 lượt = (tokens_in·giá_in + tokens_out·giá_out)/1e6 · 100/n — đơn giá đọc từ biến môi trường
GEMINI_PRICE_IN_PER_M, GEMINI_PRICE_OUT_PER_M  [cần xác minh – điền theo bảng giá Google hiện hành].
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

# --------------------------------------------------------------------------- kịch bản
TEXT_SCENARIOS = [
    # (route mong đợi, câu, tiêu chí)
    ("search", "Tìm giày thể thao nam màu đen", {"product_type": "footwear"}),
    ("search", "Có túi xách nữ màu đỏ không?", {"product_type": "accessory"}),
    ("search", "Gợi ý áo thun nam màu trắng", {"product_type": "clothing"}),
    ("search", "Mũ lưỡi trai màu xanh navy", {"product_type": "headwear"}),
    ("search", "Kính râm nữ", {"product_type": "accessory"}),
    ("search", "Dép xỏ ngón nam", {"product_type": "footwear"}),
    ("search", "Váy đầm nữ đi tiệc", {"product_type": "clothing"}),
    ("search", "Thắt lưng da nam màu nâu", {"product_type": "accessory"}),
    ("search", "Quần jean nữ", {"product_type": "clothing"}),
    ("search", "Balo đi học", {"product_type": "accessory"}),
    ("qa", "Đôi giày này có bị đau chân không?", {"needs_product": True}),
    ("qa", "Chất vải áo này có nóng không?", {"needs_product": True}),
    ("qa", "Người mua đánh giá giao hàng thế nào?", {"needs_product": True}),
    ("qa", "Sản phẩm này có giống mô tả không?", {"needs_product": True}),
    ("qa", "Size giày này có chuẩn không?", {"needs_product": True}),
    ("qa", "Màu ngoài thực tế có đúng như ảnh không?", {"needs_product": True}),
    ("qa", "Túi này đựng vừa laptop không?", {"needs_product": True}),
    ("qa", "Áo này giặt có bị phai màu không?", {"needs_product": True}),
    ("qa", "Có ai phàn nàn về chất lượng không?", {"needs_product": True}),
    ("qa", "Giày này có chống nước không?", {"needs_product": True}),
    ("compare", "So sánh 2 đôi giày thể thao này giúp mình", {"n_items": 2}),
    ("compare", "Nên chọn túi nào trong 3 cái này?", {"n_items": 3}),
    ("compare", "Hai áo này khác nhau ở điểm nào?", {"n_items": 2}),
    ("compare", "So sánh mũ A và mũ B", {"n_items": 2}),
    ("compare", "Kính nào hợp mặt tròn hơn trong 2 cái này?", {"n_items": 2}),
    ("compare", "So sánh 3 đôi sandal này về độ bền", {"n_items": 3}),
    ("gemini_chitchat", "Chào bạn, hôm nay thế nào?", {"source": "gemini"}),
    ("gemini_chitchat", "Cảm ơn nhé!", {"source": "gemini"}),
    ("gemini_chitchat", "Bạn là ai vậy?", {"source": "gemini"}),
    ("gemini_chitchat", "Đi đám cưới nên mặc gì cho lịch sự?", {"source": "gemini"}),
    ("gemini_chitchat", "Phối áo sơ mi trắng với quần gì đẹp?", {"source": "gemini"}),
    ("gemini_chitchat", "Xu hướng thời trang mùa đông năm nay?", {"source": "gemini"}),
    ("gemini_ood", "Thời tiết Hà Nội mai thế nào?", {"source": "gemini", "no_store_facts": True}),
    ("gemini_ood", "Giải giúp mình phương trình bậc hai", {"source": "gemini", "no_store_facts": True}),
    ("gemini_ood", "Shop có bán điện thoại không?", {"source": "gemini", "no_store_facts": True}),
    ("gemini_ood", "Đồng hồ nam loại nào tốt?", {"source": "gemini", "no_store_facts": True}),
    ("gemini_ood", "Viết giúp mình bài thơ về mùa thu", {"source": "gemini", "no_store_facts": True}),
    ("gemini_ood", "Tỉ giá đô la hôm nay?", {"source": "gemini", "no_store_facts": True}),
    ("clarify", "Cái kia", {"needs_clarification": True}),
    ("clarify", "Còn không?", {"needs_clarification": True}),
    ("clarify", "Rẻ hơn", {"needs_clarification": True}),
    ("clarify", "Size nào?", {"needs_clarification": True}),
]
N_VISUAL = 18


def build_scenarios(n_visual: int = N_VISUAL, seed: int = 42) -> list[dict]:
    """60 kịch bản: 18 visual (ảnh test của eval_visual) + 42 text (≥ 12 chitchat/ood)."""
    ev = pd.read_csv(ROOT / "eval" / "eval_visual.csv", keep_default_na=False)
    test = ev[ev.split == "test"]
    vis = pd.concat([test[test.tier == "instance"].groupby("product_type").sample(3, random_state=seed),
                     test[test.tier == "category"].groupby("product_type").sample(1, random_state=seed)])
    vis = vis.head(n_visual) if len(vis) >= n_visual else pd.concat([vis, test.sample(n_visual - len(vis), random_state=seed)])
    out = []
    for i, r in enumerate(vis.itertuples()):
        out.append({"id": f"e2e_{i + 1:02d}", "expected_route": "visual", "text": "Tìm sản phẩm giống ảnh này",
                    "image": r.query_image, "criteria": {"tier": r.tier, "gt": r.gt_product_ids.split("|"),
                                                       "product_type": r.product_type, "exclude": r.exclude_ids}})
    for j, (route, text, crit) in enumerate(TEXT_SCENARIOS):
        out.append({"id": f"e2e_{len(out) + 1:02d}", "expected_route": route, "text": text, "image": None, "criteria": crit})
    return out


# --------------------------------------------------------------------------- chấm
STORE_FACT_WORDS = ("giá", "đ ", "vnđ", "còn hàng", "tồn kho", "size ")


def judge(sc: dict, resp: dict) -> tuple[bool, str]:
    """Trả về (thành công?, mã lỗi). Tiêu chí tự động – cần người chấm lại các ca qa/compare/chitchat."""
    exp = sc["expected_route"]; c = sc["criteria"]; route = resp.get("route")
    if resp.get("error"):
        return False, f"error:{str(resp['error'])[:40]}"
    if exp == "visual":
        if route != "visual":
            return False, f"route_sai:{route}"
        items = [it for it in resp.get("items", []) if it["product_id"] not in set(str(c.get("exclude", "")).split("|"))]
        if not items:
            return False, "visual_no_match"
        if c["tier"] == "instance":
            return (any(it["product_id"] in c["gt"] for it in items[:5]), "visual_gt_ngoai_top5")
        return (items[0].get("product_type") == c["product_type"], "visual_top1_sai_nhom")
    if exp in ("gemini_chitchat", "gemini_ood"):
        if resp.get("source") not in ("gemini", "cache"):
            return False, f"khong_chuyen_gemini:{route}"
        if c.get("no_store_facts") and any(w in str(resp.get("answer", "")).lower() for w in STORE_FACT_WORDS):
            return False, "gemini_neu_du_kien_cua_hang"
        return True, ""
    if route != exp:
        return False, f"route_sai:{exp}->{route}"
    if exp == "clarify":
        return True, ""
    if exp == "search":
        items = resp.get("items", [])
        return (bool(items) and items[0].get("product_type") == c["product_type"], "search_top1_sai_nhom")
    if exp == "compare":
        return (len(resp.get("items", [])) >= c["n_items"], "compare_thieu_sp")
    if exp == "qa":
        return (bool(resp.get("citations")) or "chưa có thông tin" in str(resp.get("answer", "")).lower(), "qa_khong_trich_dan")
    return False, "khong_ro"


# --------------------------------------------------------------------------- agent
class FakeAgent:
    """Agent giả theo luật – chỉ để kiểm thử khung đo (KHÔNG phải số liệu thật)."""

    def handle(self, text: str | None = None, image: Any = None, session: dict | None = None) -> dict:
        t = (text or "").lower()
        if image is not None:
            return {"route": "visual", "source": "internal", "items": [], "answer": "", "confidence": 0.0}
        if any(w in t for w in ("chào", "cảm ơn", "bạn là ai")):
            return {"route": "gemini_chitchat", "source": "gemini", "answer": "Xin chào!", "tokens_in": 50, "tokens_out": 20}
        if "so sánh" in t:
            return {"route": "compare", "source": "internal", "items": [{"product_id": "x"}, {"product_id": "y"}]}
        return {"route": "search", "source": "internal", "items": [{"product_id": "x", "product_type": "footwear"}]}


class VisualOnlyAgent:
    """Chạy THẬT phần visual bằng VisualSearcher; route khác trả `not_ready` (chưa ghép hệ thống)."""

    def __init__(self, index_dir: str):
        from msa.search.visual import VisualSearcher

        self.vs = VisualSearcher.load(index_dir)

    def handle(self, text: str | None = None, image: Any = None, session: dict | None = None) -> dict:
        if image is None:
            return {"route": "not_ready", "source": "internal", "error": "module_chua_ghep"}
        return self.vs.query(image, k=10)


class HttpAgent:
    def __init__(self, base_url: str):
        import httpx

        self.c = httpx.Client(base_url=base_url, timeout=30)

    def handle(self, text=None, image=None, session=None) -> dict:
        if image is not None:
            with open(image, "rb") as f:
                return self.c.post("/search/image", files={"file": f}).json()
        return self.c.post("/chat", json={"text": text, "session": session or {}}).json()


def run(agent, scenarios: list[dict], price_in: float | None, price_out: float | None) -> tuple[dict, pd.DataFrame]:
    rows = []
    for sc in scenarios:
        img = str(ROOT / sc["image"]) if sc.get("image") else None
        t = time.perf_counter()
        try:
            resp = agent.handle(text=sc["text"], image=img, session={})
        except Exception as ex:  # ghi lỗi thật
            resp = {"route": "exception", "error": f"{type(ex).__name__}: {ex}"}
        lat = (time.perf_counter() - t) * 1000
        ok, err = judge(sc, resp)
        rows.append({"id": sc["id"], "expected_route": sc["expected_route"], "route": resp.get("route"), "source": resp.get("source"),
                     "success": ok, "error_code": "" if ok else err, "latency_ms": round(lat, 2),
                     "tokens_in": resp.get("tokens_in", 0) or 0, "tokens_out": resp.get("tokens_out", 0) or 0})
    df = pd.DataFrame(rows)
    n = len(df)
    lat = df.latency_ms.tolist()
    summ = {"n": n, "task_success_rate": round(df.success.mean(), 4),
            "tsr_by_route": df.groupby("expected_route").success.mean().round(4).to_dict(),
            "n_by_route": df.expected_route.value_counts().to_dict(),
            "route_accuracy": round(float((df.route == df.expected_route).mean()), 4),
            "latency_ms_p50": round(statistics.median(lat), 2), "latency_ms_p95": round(float(np.percentile(lat, 95)), 2),
            "gemini_rate": round(float(df.source.isin(["gemini", "cache"]).mean()), 4),
            "tokens_per_100_turns": {"in": round(df.tokens_in.sum() * 100 / n, 1), "out": round(df.tokens_out.sum() * 100 / n, 1)},
            "top10_errors": Counter(df[~df.success].error_code.str.split(":").str[0]).most_common(10)}
    if price_in is not None and price_out is not None:
        summ["cost_per_100_turns_usd"] = round((df.tokens_in.sum() * price_in + df.tokens_out.sum() * price_out) / 1e6 * 100 / n, 6)
    else:
        summ["cost_per_100_turns_usd"] = "CHƯA TÍNH – thiếu đơn giá [cần xác minh]"
    return summ, df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="fake", choices=["fake", "visual-only", "http", "python"])
    ap.add_argument("--index-dir", default=str(ROOT / "indexes" / "best"))
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--agent-cls", default="msa.agent.router:Agent")
    a = ap.parse_args()
    sc = build_scenarios()
    (ROOT / "eval").mkdir(exist_ok=True)
    with open(ROOT / "eval" / "e2e_scenarios.jsonl", "w", encoding="utf-8") as f:
        for s in sc:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    if a.agent == "fake":
        agent = FakeAgent()
    elif a.agent == "visual-only":
        agent = VisualOnlyAgent(a.index_dir)
    elif a.agent == "http":
        agent = HttpAgent(a.base_url)
    else:
        mod, cls = a.agent_cls.split(":"); agent = getattr(importlib.import_module(mod), cls)()
    pi = os.environ.get("GEMINI_PRICE_IN_PER_M"); po = os.environ.get("GEMINI_PRICE_OUT_PER_M")
    summ, df = run(agent, sc, float(pi) if pi else None, float(po) if po else None)
    summ["agent"] = a.agent
    summ["note"] = "fake = chỉ kiểm thử khung, KHÔNG phải số liệu" if a.agent == "fake" else ""
    if a.agent == "visual-only":
        v = df[df.expected_route == "visual"]
        summ["visual_only"] = {"n": len(v), "tsr": round(v.success.mean(), 4), "latency_ms_p50": round(v.latency_ms.median(), 2),
                               "latency_ms_p95": round(float(np.percentile(v.latency_ms, 95)), 2),
                               "errors": v[~v.success].error_code.value_counts().to_dict()}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / f"e2e_{a.agent}.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    df.to_csv(ROOT / "results" / f"e2e_{a.agent}_per_case.csv", index=False)
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
