# repo: scripts/gen_router_testset_gemini.py
"""Sinh tập test router ĐỘC LẬP bằng Gemini (1 lời gọi) để đo router v1 mà KHÔNG chỉnh luật theo tập này.
Nhãn do Gemini gán theo định nghĩa bên dưới -> origin=llm_gemini, cần 2 người duyệt.

Chạy:  MSA_GEMINI_KEY_FILE=<đường dẫn .env> PYTHONPATH=src python scripts/gen_router_testset_gemini.py --model gemini-3.5-flash-lite
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from msa.agent.gemini_client import GeminiRestClient  # noqa: E402

PROMPT = """Bạn giúp tạo bộ kiểm thử cho bộ định tuyến (router) của chatbot mua sắm thời trang tiếng Việt.
Cửa hàng chỉ bán: giày dép (giày thể thao, giày da, sandal/dép, boot, giày cao gót/búp bê), quần áo (áo, quần/chân váy, váy liền/đầm, áo khoác),
mũ (lưỡi trai, mũ len, bucket, rộng vành), phụ kiện (túi/balo, thắt lưng, kính). KHÔNG bán: đồng hồ, trang sức, tất/vớ, ví, khăn, đồ lót, mỹ phẩm.

Định nghĩa nhãn route:
- visual: người dùng gửi ẢNH (has_image=true), có thể kèm câu ngắn.
- qa: hỏi về MỘT sản phẩm cụ thể đang xem (has_product_context=true) – chất liệu, size, độ bền, đánh giá, giao hàng...
- search: muốn tìm/mua/xem sản phẩm theo mô tả hoặc bộ lọc (loại, màu, giá, size, giới tính).
- compare: so sánh 2-3 sản phẩm cụ thể (nêu tên, hoặc trỏ vào kết quả vừa tìm khi has_last_results=true), cùng một nhóm sản phẩm.
- gemini_chitchat: chào hỏi, cảm ơn, tạm biệt, hỏi về bot, tâm sự, khen chê bot.
- gemini_ood: ngoài phạm vi cửa hàng (thời tiết, học tập, công nghệ, hàng KHÔNG bán như đồng hồ/trang sức) hoặc kiến thức thời trang chung không gắn sản phẩm (cách phối đồ, cách giặt, xu hướng).
- clarify: quá mơ hồ để xử lý (thiếu đối tượng, tham chiếu "cái này/đôi thứ 2" khi không có ngữ cảnh, so sánh 2 nhóm khác nhau như áo với giày).

Hãy viết 49 câu người dùng THỰC TẾ, mỗi nhãn đúng 7 câu, đa dạng: có dấu, không dấu, teencode/viết tắt (ko, k, dc, sz, ss, bn), câu dài/ngắn.
Trả về DUY NHẤT một mảng JSON, mỗi phần tử: {"text": "...", "has_image": bool, "has_product_context": bool, "has_last_results": bool, "route": "..."}"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemini-3.5-flash-lite")
    a = ap.parse_args()
    c = GeminiRestClient(model=a.model, thinking_budget=None, max_output_tokens=6000, temperature=0.9,
                         cache_path=os.path.join(ROOT, "results", "cache", "gemini_cache.sqlite"), prompt_version="router-testgen-v1")
    out = c.generate(PROMPT)
    raw_dir = os.path.join(ROOT, "eval", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    json.dump({k: v for k, v in out.items()}, open(os.path.join(raw_dir, "router_testgen_gemini_raw.json"), "w"), ensure_ascii=False, indent=1)
    if out.get("error"):
        print("Lỗi:", out["error"])
        sys.exit(1)
    m = re.search(r"\[.*\]", out["answer"], re.S)
    items = json.loads(m.group(0))
    with open(os.path.join(ROOT, "eval", "eval_router_gemini_gen.jsonl"), "w", encoding="utf-8") as f:
        for i, it in enumerate(items, 1):
            rec = dict(id=f"trg_{i:03d}", text=it["text"], has_image=bool(it.get("has_image")), route=it["route"],
                       product_id="ctx_product" if it.get("has_product_context") else None,
                       session_last_results=["ctx_1", "ctx_2", "ctx_3"] if it.get("has_last_results") else None,
                       note="sinh bởi Gemini; nhãn chưa người duyệt", origin=f"llm_gemini:{a.model}", annotator_1="", annotator_2="")
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(len(items), "câu;", {k: out[k] for k in ("tokens_in", "tokens_out", "tokens_thinking", "latency_ms", "cached")})


if __name__ == "__main__":
    main()
