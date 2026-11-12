# repo: scripts/baseline_e2e.py
"""US_44 – Đo baseline end-to-end trên 60 kịch bản (≥ 10 chitchat/ngoài phạm vi).

Chế độ agent:
  --agent fake         : agent giả theo luật (CHỈ để kiểm thử khung, số liệu KHÔNG dùng cho báo cáo)
  --agent visual-only  : chạy THẬT VisualSearcher trên index đã build cho các kịch bản visual; các route khác = not_ready
  --agent http --base-url http://localhost:8000 : gọi API của Hoàng khi hệ thống đã ghép (số e2e thật)
      + --resume --max-gemini-calls N --pace-s 15 --llm-log ../runtime/logs/llm_calls.jsonl : chạy nhiều đợt theo
        quota Gemini (ghi từng kịch bản vào results/e2e_http_cases.jsonl; token lấy từ log LLMGateway)
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
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT.parent / "src"))  # + package msa chung

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
    """Gọi API đã ghép (src/msa/api/main.py) đúng hợp đồng mục 5.2: ảnh → POST /search/image (trường `file`);
    text → POST /chat {message, session_id}. Mỗi kịch bản một phiên mới (kịch bản độc lập, không có ngữ cảnh trước)."""

    def __init__(self, base_url: str, timeout: float = 300.0):
        import httpx

        self.c = httpx.Client(base_url=base_url, timeout=timeout)

    def handle(self, text=None, image=None, session=None, case_id: str | None = None) -> dict:
        if image is not None:
            with open(image, "rb") as f:
                return self.c.post("/search/image", files={"file": (Path(image).name, f, "image/jpeg")}).json()
        sid = f"e2e-{case_id or 'x'}-{time.time_ns()}"
        return self.c.post("/chat", json={"message": text, "session_id": sid}).json()


class LlmLogTail:
    """Đọc các dòng MỚI của log LLMGateway (`runtime/logs/llm_calls.jsonl`) sau mỗi kịch bản → token và số lời gọi
    Gemini thật của đúng kịch bản đó (kể cả lời gọi bên trong RAG, vốn không trả token qua /chat). Chạy tuần tự."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.pos = self.path.stat().st_size if self.path.exists() else 0

    def read_new(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, "rb") as f:
            f.seek(self.pos)
            data = f.read()
        self.pos += len(data)
        return [json.loads(l) for l in data.decode("utf-8").splitlines() if l.strip()]


def summarize_llm(events: list[dict]) -> dict:
    """Số lời gọi Gemini thật (kể cả lần thử lại bị lỗi), cache hit, token theo usageMetadata."""
    calls = [e for e in events if e.get("event") == "call"]
    errs = [e for e in events if e.get("event") == "error"]
    return {"gemini_calls": len(calls) + sum((e.get("retries") or 0) + 1 for e in errs if e.get("status")),
            "gemini_retries": sum(e.get("retries") or 0 for e in calls),  # lần thử lại (timeout/503) cũng tốn quota
            "cache_hits": sum(e.get("event") in ("cache_hit", "semantic_hit") for e in events),
            "llm_errors": "; ".join(str(e.get("error"))[:80] for e in errs),
            "tokens_in": sum(e.get("tokens_in") or 0 for e in calls),
            "tokens_out": sum(e.get("tokens_out") or 0 for e in calls),
            "tokens_thinking": sum(e.get("tokens_thinking") or 0 for e in calls),
            "llm_wait_ms": round(sum(e.get("wait_ms") or 0 for e in calls), 1)}


def run_case(agent, sc: dict, llm_tail: "LlmLogTail | None" = None) -> dict:
    img = str(ROOT / sc["image"]) if sc.get("image") else None
    if llm_tail is not None:
        llm_tail.read_new()  # bỏ dòng log không thuộc kịch bản này
    t = time.perf_counter()
    try:
        kw = {"case_id": sc["id"]} if isinstance(agent, HttpAgent) else {}
        resp = agent.handle(text=sc["text"], image=img, session={}, **kw)
    except Exception as ex:  # ghi lỗi thật
        resp = {"route": "exception", "error": f"{type(ex).__name__}: {ex}"}
    lat = (time.perf_counter() - t) * 1000
    ok, err = judge(sc, resp)
    row = {"id": sc["id"], "expected_route": sc["expected_route"], "route": resp.get("route"), "source": resp.get("source"),
           "success": ok, "error_code": "" if ok else err, "latency_ms": round(lat, 2),
           "tokens_in": resp.get("tokens_in", 0) or 0, "tokens_out": resp.get("tokens_out", 0) or 0}
    if llm_tail is not None:  # token lấy từ log gateway (đủ cả lời gọi trong RAG), thay cho số /chat trả về
        row.update(summarize_llm(llm_tail.read_new()))
    row["answer"] = str(resp.get("answer", ""))[:200].replace("\n", " ")
    row["top_items"] = "|".join(str(it.get("product_id")) for it in (resp.get("items") or [])[:5])
    row["n_citations"] = len(resp.get("citations") or [])
    row["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return row


def summarize(df: pd.DataFrame, price_in: float | None, price_out: float | None) -> dict:
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
    return summ


def run(agent, scenarios: list[dict], price_in: float | None, price_out: float | None) -> tuple[dict, pd.DataFrame]:
    df = pd.DataFrame([run_case(agent, sc) for sc in scenarios])
    return summarize(df, price_in, price_out), df


def run_resumable(agent, scenarios: list[dict], cases_path: Path, llm_tail: "LlmLogTail | None",
                  max_gemini_calls: int | None, pace_s: float) -> tuple[list[dict], str]:
    """Chạy được qua nhiều đợt (quota Gemini free tier ~20 request/ngày/model): kịch bản nào xong thì ghi ngay một dòng
    vào `cases_path`, kịch bản đã có thì bỏ qua. Đợt dừng khi đã dùng đủ `max_gemini_calls` lời gọi thật hoặc khi gateway
    báo 429; kịch bản dính 429 KHÔNG được ghi (câu dự phòng do hết quota không phải kết quả của hệ thống) để chạy lại đợt sau."""
    done = {}
    if cases_path.exists():
        for l in cases_path.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l); done[r["id"]] = r
    used, stop = 0, ""
    for sc in scenarios:
        if sc["id"] in done:
            continue
        if max_gemini_calls is not None and used >= max_gemini_calls:
            stop = f"đủ ngân sách đợt này ({used} lời gọi Gemini thật)"; break
        row = run_case(agent, sc, llm_tail)
        used += row.get("gemini_calls", 0)
        if "429" in row.get("llm_errors", ""):
            stop = f"Gemini 429 ở {sc['id']}: {row['llm_errors'][:160]}"; break
        done[sc["id"]] = row
        with open(cases_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"{row['id']} {row['expected_route']:>15} -> {str(row['route']):>15} {str(row['source']):>8} "
              f"ok={row['success']} {row['latency_ms']:.0f} ms gemini={row.get('gemini_calls', 0)} "
              f"cache={row.get('cache_hits', 0)} {row['error_code']}", flush=True)
        if row.get("gemini_calls", 0) and pace_s > 0:
            time.sleep(pace_s)  # giữ dưới 5 RPM để limiter của gateway không phải chờ (không lẫn thời gian chờ vào latency)
    order = {sc["id"]: i for i, sc in enumerate(scenarios)}
    return sorted(done.values(), key=lambda r: order.get(r["id"], 1e9)), stop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="fake", choices=["fake", "visual-only", "http", "python"])
    ap.add_argument("--index-dir", default=str(ROOT / "indexes" / "best"))
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--agent-cls", default="msa.agent.router:Agent")
    ap.add_argument("--resume", action="store_true",
                    help="chạy nhiều đợt: ghi từng kịch bản vào results/e2e_<agent>_cases.jsonl, bỏ qua kịch bản đã chạy")
    ap.add_argument("--max-gemini-calls", type=int, default=None, help="dừng đợt khi đã dùng chừng này lời gọi Gemini thật")
    ap.add_argument("--pace-s", type=float, default=0.0, help="nghỉ sau mỗi kịch bản có gọi Gemini thật (giữ dưới RPM)")
    ap.add_argument("--llm-log", default=None, help="log LLMGateway của API (runtime/logs/llm_calls.jsonl) để đếm token/lời gọi")
    ap.add_argument("--config-note", default="", help="mô tả cấu hình hệ thống được đo (ghi vào file kết quả)")
    a = ap.parse_args()
    sc = build_scenarios()
    (ROOT / "eval").mkdir(exist_ok=True)
    with open(ROOT / "eval" / "e2e_scenarios.jsonl", "w", encoding="utf-8", newline="\n") as f:  # LF: giữ nguyên file trên Windows
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
    pi, po = (float(pi) if pi else None), (float(po) if po else None)
    if a.resume:
        (ROOT / "results").mkdir(exist_ok=True)
        tail = LlmLogTail(a.llm_log) if a.llm_log else None
        rows, stop = run_resumable(agent, sc, ROOT / "results" / f"e2e_{a.agent}_cases.jsonl", tail,
                                   a.max_gemini_calls, a.pace_s)
        if len(rows) < len(sc):
            print(f"ĐỢT DỪNG: {stop or 'chưa xong'} – đã có {len(rows)}/{len(sc)} kịch bản; chạy lại cùng lệnh để tiếp.")
            return
        df = pd.DataFrame(rows)
        summ = summarize(df, pi, po)
        col = lambda c: df[c] if c in df else pd.Series([0] * len(df))  # noqa: E731
        summ["gemini_api_calls_total"] = int(col("gemini_calls").sum())
        summ["cache_hits_total"] = int(col("cache_hits").sum())
        summ["gemini_retries_total"] = int(col("gemini_retries").fillna(0).sum())  # thử lại sau timeout/503 – cũng là request tới Gemini
        summ["tokens_thinking_per_100_turns"] = round(float(col("tokens_thinking").sum()) * 100 / len(df), 1)
        summ["run_dates"] = sorted({r["ts"][:10] for r in rows})
        summ["config"] = a.config_note
        lv, lt = df[df.expected_route == "visual"].latency_ms, df[df.expected_route != "visual"].latency_ms
        summ["latency_ms_by_kind"] = {k: {"p50": round(float(v.median()), 2), "p95": round(float(np.percentile(v, 95)), 2)}
                                      for k, v in (("visual", lv), ("text", lt)) if len(v)}
        summ["by_route"] = {r: {"n": int(len(g)), "tsr": round(float(g.success.mean()), 4),
                                "route_accuracy": round(float((g.route == r).mean()), 4),
                                "latency_ms_p50": round(float(g.latency_ms.median()), 2),
                                "latency_ms_p95": round(float(np.percentile(g.latency_ms, 95)), 2),
                                "gemini_rate": round(float(g.source.isin(["gemini", "cache"]).mean()), 4),
                                "gemini_calls": int(col("gemini_calls")[g.index].sum()),
                                "tokens_in": int(g.tokens_in.sum()), "tokens_out": int(g.tokens_out.sum())}
                            for r, g in df.groupby("expected_route")}
    else:
        summ, df = run(agent, sc, pi, po)
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
