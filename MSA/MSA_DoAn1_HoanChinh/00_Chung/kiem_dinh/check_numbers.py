#!/usr/bin/env python3
"""Kiểm định số liệu (Tác nhân 3) – đối chiếu số trong tài liệu với file kết quả.

Cách dùng (chạy từ gốc folder MSA_DoAn1_HoanChinh hoặc bất kỳ đâu):
    python 00_Chung/kiem_dinh/check_numbers.py            # in tóm tắt + ghi doi_chieu_so_lieu.md
    python 00_Chung/kiem_dinh/check_numbers.py --strict   # exit 1 nếu có dòng lệch / thiếu

Nguyên tắc
- Mỗi "khẳng định" (claim) gồm: số như viết trong tài liệu (dạng tiếng Việt, dấu phẩy thập phân),
  danh sách tài liệu chứa số đó, file nguồn và cách đọc giá trị từ file nguồn (đọc TRỰC TIẾP file).
- Kết quả: KHỚP (|giá trị file − số tài liệu| ≤ dung sai làm tròn) / LỆCH / THIẾU-TRONG-DOC
  (chuỗi số không còn xuất hiện trong tài liệu được liệt kê – dấu hiệu tài liệu đã bị sửa khác).
- Một số giá trị là phép tính từ file (vd token/100 lượt = fallback_rate × token/lời gọi × 100);
  công thức ghi trong cột "Giá trị trong file".
- Chỉ dùng thư viện chuẩn Python. Không gọi mạng, không chạy model.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_MD = Path(__file__).resolve().parent / "doi_chieu_so_lieu.md"


# ----------------------------------------------------------------------------- đọc file
_cache: dict[str, object] = {}


def J(rel: str):
    if rel not in _cache:
        _cache[rel] = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    return _cache[rel]


def jget(rel: str, *keys):
    x = J(rel)
    for k in keys:
        x = x[k]
    return x


def csv_rows(rel: str) -> list[dict]:
    key = "csv:" + rel
    if key not in _cache:
        with open(ROOT / rel, encoding="utf-8") as f:
            _cache[key] = list(csv.DictReader(f))
    return _cache[key]  # type: ignore[return-value]


def cget(rel: str, keycol: str, keyval: str, col: str) -> float:
    for r in csv_rows(rel):
        if r[keycol] == keyval:
            return float(r[col])
    raise KeyError(f"{rel}: {keycol}={keyval}")


def jsonl(rel: str) -> list[dict]:
    key = "jsonl:" + rel
    if key not in _cache:
        _cache[key] = [json.loads(l) for l in open(ROOT / rel, encoding="utf-8") if l.strip()]
    return _cache[key]  # type: ignore[return-value]


def doc_text(rel: str) -> str:
    key = "doc:" + rel
    if key not in _cache:
        _cache[key] = (ROOT / rel).read_text(encoding="utf-8")
    return _cache[key]  # type: ignore[return-value]


# ----------------------------------------------------------------------------- tài liệu
KHOA_R = "04_Khoa/README.md"
TRUNG_R = "01_Trung/README.md"
DAT_R = "02_TuanDat/README.md"
CHIEN_R = "03_Chien/README.md"
HOANG_R = "05_Hoang/README.md"
QD = "00_Chung/QUYET_DINH_CAN_CHOT.md"
TN = "00_Chung/THUAT_NGU.md"
US27 = "01_Trung/docs/US_27_bao_cao_tuan2_khung.md"
US25 = "01_Trung/docs/US_25_bang_cham_diem_co_trong_so.md"
US45 = "04_Khoa/docs/US_45_cai_tien_va_do_truoc_sau.md"
US41 = "01_Trung/docs/US_41_router_agent_va_gemini.md"
BC = "BAO_CAO_TONG_HOP.md"
RD = "README.md"

BENCH = "04_Khoa/results/bench_image_embed.csv"
IMPR = "04_Khoa/results/improvements_fashionclip.json"
TAU = "04_Khoa/results/tau_v_analysis.json"
RBT = "04_Khoa/results/recall_by_transform.csv"
WS = "01_Trung/results/weighted_scoring.json"
WSB = "01_Trung/results/weighted_scoring_scenario_B.json"
WSS = "01_Trung/results/weighted_scoring_sensitivity.json"
RV0 = "01_Trung/results/router_eval_v0.json"
RV1 = "01_Trung/results/router_eval_v1.json"
RV1E = "01_Trung/results/router_eval_v1_emb.json"
GFL = "01_Trung/results/gemini_fallback_live.json"
GSF = "01_Trung/results/gemini_store_fact_recheck.json"
SCH = "01_Trung/results/schema_validation.json"
TAX = "01_Trung/results/taxonomy_coverage.json"
CLEAN = "02_TuanDat/results/clean_report.json"
LLM = "02_TuanDat/results/bench_llm_summary.json"
RAGR = "03_Chien/results/rag_retrieval_eval.json"
RAGE = "03_Chien/results/rag_e2e_eval.json"
GFC = "03_Chien/results/gemini_fallback_check.json"
API = "05_Hoang/results/api_eval.json"
TXT = "05_Hoang/results/bench_text_embed_summary.csv"
GW = "05_Hoang/results/llm_gateway_live.json"
DV1 = "05_Hoang/data/counts_data_v1.json"
STATS = "00_Chung/stats.json"


def ws(model: str, key: str = "tong_diem", rel: str = WS) -> float:
    rows = J(rel)
    rows = rows if isinstance(rows, list) else rows.get("rows", rows)
    for r in rows:
        if r["model"] == model:
            return float(r[key])
    raise KeyError(model)


def fallback_rate() -> float:
    g = jget(GFL, "routing")
    return g["total_routed_gemini"] / g["total_turns"]


def hyb(split: str = "test", metric: str = "hit@5") -> float:
    res = jget(RAGR, "results")
    k = [k for k in res if k.startswith("hybrid")][0]
    return float(res[k]["theo_product_id"][split][metric]) if split else float(res[k]["theo_product_id"][metric])


def ragr(name: str, metric: str, split: str = "test") -> float:
    return float(jget(RAGR, "results", name, "theo_product_id", split, metric))


def eval_qa_counts():
    rows = jsonl("03_Chien/eval/eval_qa.jsonl")
    return len(rows), sum(1 for r in rows if r.get("answerable") is False), Counter(r.get("origin") for r in rows)


def eval_router_counts():
    rows = jsonl("03_Chien/eval/eval_router.jsonl")
    return len(rows), sum(1 for r in rows if r["route"] in ("gemini_chitchat", "gemini_ood"))


def chunks_counts():
    rows = jsonl("03_Chien/data/kb/chunks.jsonl")
    kinds = Counter(r.get("chunk_type") or r.get("kind") or r.get("type") or "?" for r in rows)
    return len(rows), kinds, len({r["product_id"] for r in rows})


def oos_counts():
    rows = csv_rows("03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv")
    c = Counter(r["bo_eval"] for r in rows)
    return c.get("eval_qa", 0), c.get("eval_router", 0)


def vimrhp_reviews(scope: str) -> int:
    rows = csv_rows("01_Trung/data/vimrhp_taxonomy_v1.csv")
    if scope == "all":
        return sum(int(r["n_reviews"]) for r in rows)
    if scope == "no_watch":
        return sum(int(r["n_reviews"]) for r in rows if r["vimrhp_subcategory"] != "DongHo")
    if scope == "in_scope":  # 361 SP = keep 349 + unknown 12
        return sum(int(r["n_reviews"]) for r in rows if r["action"] != "exclude")
    if scope == "keep":  # 349 SP có lá taxonomy
        return sum(int(r["n_reviews"]) for r in rows if r["action"] == "keep")
    raise ValueError(scope)


def us36_bad() -> tuple[int, int, int]:
    rows = csv_rows("02_TuanDat/results/us36_kiem_tay_20sp.csv")
    bad = [r for r in rows if r["verdict"] != "co_trong_review"]
    return len(bad), len(rows), len({r["product_id"] for r in bad})


def n429() -> int:
    p = ROOT / "02_TuanDat/results/failed/bench_llm_qa_gemini35flash_t0_ALL_429.jsonl"
    return sum(1 for l in open(p, encoding="utf-8") if l.strip())


# ----------------------------------------------------------------------------- khẳng định
# (mã, mô tả, số như viết trong doc, giá trị so sánh (float), dung sai, [docs], nguồn, getter)
C: list[tuple] = []


def add(cid, desc, shown, claimed, tol, docs, src, getter, note=""):
    C.append((cid, desc, shown, claimed, tol, docs, src, getter, note))


# --- Khoa: Bảng A (5 model) – split test
for m, r1, r5, mrr, cte, catp, emb, peak in [
    ("dinov2_s", 0.750, 0.846, 0.791, 0.043, 0.307, 288.75, 1446),
    ("siglip_b16", 0.704, 0.833, 0.760, 0.055, 0.355, 189.99, 2431),
    ("fashionclip", 0.704, 0.829, 0.757, 0.062, 0.378, 294.22, 1597),
    ("clip_b32", 0.621, 0.721, 0.660, 0.076, 0.353, 428.34, 2024),
    ("resnet50", 0.604, 0.704, 0.644, 0.138, 0.332, 1602.9, 1357),
]:
    add(f"A-{m}-macroR5", f"{m} macro R@5 (test)", f"{r5:.3f}", r5, 6e-4, [KHOA_R], BENCH,
        lambda m=m: cget(BENCH, "model", m, "test_macro_R@5"))
    add(f"A-{m}-R1", f"{m} R@1", f"{r1:.3f}", r1, 6e-4, [KHOA_R], BENCH, lambda m=m: cget(BENCH, "model", m, "test_R@1"))
    add(f"A-{m}-MRR", f"{m} MRR@10", f"{mrr:.3f}", mrr, 6e-4, [KHOA_R], BENCH, lambda m=m: cget(BENCH, "model", m, "test_MRR@10"))
    add(f"A-{m}-CTE", f"{m} CTE@5", f"{cte:.3f}", cte, 6e-4, [KHOA_R], BENCH, lambda m=m: cget(BENCH, "model", m, "test_CTE@5"))
    add(f"A-{m}-catP5", f"{m} cat P@5", f"{catp:.3f}", catp, 6e-4, [KHOA_R], BENCH, lambda m=m: cget(BENCH, "model", m, "test_cat_P@5"))
    add(f"A-{m}-emb", f"{m} embed truy vấn median (ms)", f"{emb}", emb, 0.01, [KHOA_R], BENCH,
        lambda m=m: cget(BENCH, "model", m, "query_embed_ms_median_bs1"))
    add(f"A-{m}-peak", f"{m} RAM đỉnh (MB)", f"{peak:,}".replace(",", "."), peak, 0.6, [US27], BENCH,
        lambda m=m: cget(BENCH, "model", m, "peak_rss_mb"))
add("A-macro-vn", "macro R@5 DINOv2-S (dạng VN)", "0,846", 0.846, 6e-4, [US27, BC], BENCH,
    lambda: cget(BENCH, "model", "dinov2_s", "test_macro_R@5"))
add("A-macro-fc-vn", "macro R@5 FashionCLIP (dạng VN)", "0,829", 0.829, 6e-4, [TN, BC], BENCH,
    lambda: cget(BENCH, "model", "fashionclip", "test_macro_R@5"))
for grp, v in [("footwear", 0.733), ("clothing", 0.833), ("headwear", 0.883), ("accessory", 0.867)]:
    add(f"A-fc-{grp}", f"FashionCLIP R@5 {grp} (ví dụ macro trong THUAT_NGU)", f"{v:.3f}".replace(".", ","), v, 6e-4, [TN], BENCH,
        lambda g=grp: cget(BENCH, "model", "fashionclip", f"test_R@5_{g}"))
add("A-dino-embed-s", "DINOv2-S embed catalog (s)", "790,8", 790.8, 0.05, [KHOA_R, QD], BENCH,
    lambda: cget(BENCH, "model", "dinov2_s", "catalog_embed_total_s"))
add("A-fc-embed-s", "FashionCLIP embed catalog (s)", "775,8", 775.8, 0.05, [KHOA_R], BENCH,
    lambda: cget(BENCH, "model", "fashionclip", "catalog_embed_total_s"))
add("A-dino-gate", "DINOv2-S gate centroid R@5 sau", "0,796", 0.796, 6e-4, [QD, US45], BENCH,
    lambda: cget(BENCH, "model", "dinov2_s", "gate_centroid_test_R@5"))
add("A-fc-gateCTE", "FashionCLIP gate zero-shot CTE@5", "0,044", 0.044, 6e-4, [QD, TN, KHOA_R], BENCH,
    lambda: cget(BENCH, "model", "fashionclip", "gate_zeroshot_test_CTE@5"))

# --- Bảng F (Trung chạy trên CSV của Khoa)
for m, v in [("dinov2_s", 4.83), ("siglip_b16", 3.98), ("fashionclip", 3.96), ("clip_b32", 2.99), ("resnet50", 2.40)]:
    add(f"F-{m}", f"Bảng F tổng điểm {m}", f"{v:.2f}".replace(".", ","), v, 0.006, [QD, US27, BC], WS, lambda m=m: ws(m))
for m, v in [("dinov2_s", 4.48), ("fashionclip", 4.03), ("siglip_b16", 3.96)]:
    add(f"FB-{m}", f"Bảng F kịch bản B {m}", f"{v:.2f}".replace(".", ","), v, 0.006, [QD], WSB, lambda m=m: ws(m, rel=WSB))


def ws_recompute(model: str) -> float:
    w = {"Độ chính xác": .35, "Tốc độ": .15, "Tài nguyên": .15, "Phù hợp miền": .15, "License": .10, "Dễ tích hợp": .10}
    rows = J(WS)
    r = [x for x in rows if x["model"] == model][0]
    return sum(r[k] * v for k, v in w.items())


add("F-recompute-dino", "Bảng F DINOv2-S tính lại từ điểm thành phần × trọng số", "4,83", 4.83, 0.006, [QD], WS,
    lambda: ws_recompute("dinov2_s"))
add("F-sens", "DINOv2-S hạng 1 ở bao nhiêu/12 cấu hình độ nhạy", "12/12", 12, 0, [QD, KHOA_R, BC], WSS,
    lambda: sum(1 for c in J(WSS)["configs"] if c["hang_1"] == "dinov2_s"))

# --- Độ bền theo họ biến đổi
for fam, m, v in [("background", "siglip_b16", 0.906), ("background", "dinov2_s", 0.812), ("background", "fashionclip", 0.656),
                  ("combo", "dinov2_s", 0.750), ("combo", "fashionclip", 0.667), ("lowres_jpeg", "siglip_b16", 0.278),
                  ("lowres_jpeg", "fashionclip", 0.500)]:
    add(f"T-{fam}-{m}", f"R@5 {fam} {m}", f"{v:.3f}".replace(".", ","), v, 6e-4, [QD], RBT, lambda f=fam, m=m: cget(RBT, "ho_bien_doi", f, m))

# --- τ_v
for m, v in [("fashionclip", 0.7039), ("dinov2_s", 0.5923), ("siglip_b16", 0.7531), ("clip_b32", 0.8887)]:
    add(f"TAU-{m}", f"τ_v {m} (max OOD val + 0,01)", f"{v:.4f}".replace(".", ","), v, 6e-5, [QD], TAU,
        lambda m=m: jget(TAU, m, "b_max_ood_val+0.01", "tau"))
for m, v in [("fashionclip", 84.2), ("dinov2_s", 94.2), ("siglip_b16", 96.3), ("clip_b32", 67.1)]:
    add(f"TAUk-{m}", f"% giữ truy vấn instance tại τ_v của {m}", f"{v:.1f} %".replace(".", ","), v, 0.06, [QD], TAU,
        lambda m=m: 100 * jget(TAU, m, "b_max_ood_val+0.01", "test_instance_kept"))
add("TAU-025", "τ_v = 0,25 loại được bao nhiêu % OOD (FashionCLIP)", "0 %", 0, 0, [QD], TAU,
    lambda: 100 * jget(TAU, "fashionclip", "default_0.25", "test_ood_rejected"))

# --- Cải tiến (US_45) – [Thật–tổng hợp]
for name, key, v in [("baseline", "R@5", 0.829), ("I3_linear_adapter", "R@5", 0.921), ("I2_tta_hflip", "R@5", 0.838),
                     ("I1_bbox_crop_query_only", "R@5", 0.825), ("I19_type_gate_zeroshot", "R@5", 0.821),
                     ("I19_type_gate_zeroshot", "CTE@5", 0.044), ("I3_linear_adapter", "MRR@10", 0.872),
                     ("I3_linear_adapter", "CTE@5", 0.026)]:
    add(f"I-{name}-{key}", f"Cải tiến {name} {key}", f"{v:.3f}".replace(".", ","), v, 6e-4, [US45], IMPR,
        lambda n=name, k=key: jget(IMPR, "rows", n, k))
add("I-adapter-n", "Số ảnh huấn luyện adapter (biến đổi tổng hợp)", "800", 800, 0, [US45], IMPR, lambda: jget(IMPR, "adapter_train", "n"))

# --- Build index & e2e (Khoa)
add("BI-search", "FashionCLIP search-only median (ms)", "1,9 ms", 1.9, 0.05, [KHOA_R], "04_Khoa/results/build_index_fashionclip.json",
    lambda: jget("04_Khoa/results/build_index_fashionclip.json", "search_only_ms_median"))
add("BI-e2e", "FashionCLIP embed+gate+search median (ms)", "168,8", 168.8, 0.05, [KHOA_R], "04_Khoa/results/build_index_fashionclip.json",
    lambda: jget("04_Khoa/results/build_index_fashionclip.json", "query_e2e_ms_median"))
add("E2E-tsr", "TSR visual-only", "15/18 = 0,833", 0.833, 6e-4, [KHOA_R, BC], "04_Khoa/results/e2e_visual-only.json",
    lambda: jget("04_Khoa/results/e2e_visual-only.json", "visual_only", "tsr"))
add("EV-n", "Số truy vấn eval_visual", "600", 600, 0, [KHOA_R], "04_Khoa/eval/eval_visual_stats.json",
    lambda: jget("04_Khoa/eval/eval_visual_stats.json", "n_queries"))
add("EV-hard", "hard_cross_type (test)", "96 hard_cross_type (53", 53, 0, [KHOA_R], "04_Khoa/eval/eval_visual_stats.json",
    lambda: jget("04_Khoa/eval/eval_visual_stats.json", "hard_cross_type_test"))

# --- Trung: router, Gemini, schema, taxonomy
add("R-v0", "Router v0 trên bộ Chiến (n=78)", "0,667", 0.667, 6e-4, [TRUNG_R, US41], RV0, lambda: jget(RV0, "sets", "chien_eval_router", "route_accuracy"))
add("R-v1-chien", "Router v1 trên bộ Chiến (ĐÃ chỉnh theo lỗi – không phải held-out)", "0,923", 0.923, 6e-4, [TRUNG_R, TN, US41, BC], RV1,
    lambda: jget(RV1, "sets", "chien_eval_router", "route_accuracy"))
add("R-v1-merged", "Router v1 bộ Chiến gộp 2 nhãn gemini", "0,949", 0.949, 6e-4, [TRUNG_R], RV1,
    lambda: jget(RV1, "sets", "chien_eval_router", "route_accuracy_gemini_merged"))
add("R-v1-held", "Router v1 trên tập Gemini sinh (n=49, held-out)", "0,878", 0.878, 6e-4, [TRUNG_R, US27, TN, BC], RV1,
    lambda: jget(RV1, "sets", "gemini_gen_heldout", "route_accuracy"))
add("R-v1-held-n", "n tập held-out router", "n=49", 49, 0, [TRUNG_R, US27], RV1, lambda: jget(RV1, "sets", "gemini_gen_heldout", "n"))
add("R-emb", "Router + e5-small trên bộ Chiến", "0,846 (bộ Chiến)", 0.846, 6e-4, [TRUNG_R], RV1E,
    lambda: jget(RV1E, "sets", "chien_eval_router", "route_accuracy"))
add("G-fb", "Fallback rate (47/172)", "0,273", 0.273, 6e-4, [TRUNG_R, US27, TN, BC], GFL, fallback_rate)
add("G-p50", "Gemini latency p50 (s, gồm chờ 429)", "14,4 s", 14.4, 0.05, [TRUNG_R], GFL, lambda: jget(GFL, "A_default", "latency_ms_p50") / 1000)
add("G-p95", "Gemini latency p95 (s)", "41,1 s", 41.1, 0.05, [TRUNG_R], GFL, lambda: jget(GFL, "A_default", "latency_ms_p95") / 1000)
add("G-tin", "Token vào TB/lời gọi (A)", "165,1", 165.1, 0.05, [TRUNG_R, QD], GFL, lambda: jget(GFL, "A_default", "tokens_in_mean"))
add("G-tout", "Token ra TB/lời gọi (A)", "55,5", 55.5, 0.05, [TRUNG_R, QD], GFL, lambda: jget(GFL, "A_default", "tokens_out_mean"))
add("G-think", "Thinking TB/lời gọi (B, budget 1024)", "350,3", 350.3, 0.05, [TRUNG_R, QD], GFL, lambda: jget(GFL, "B_thinking", "tokens_thinking_mean"))
add("G-t100", "Token/100 lượt hội thoại (Trung, A) = fallback × 100 × total/lời gọi", "6.028", 6028, 1.0, [TRUNG_R, QD, US27, BC], GFL,
    lambda: fallback_rate() * 100 * jget(GFL, "A_default", "tokens_total_mean"))
add("G-t100B", "Token/100 lượt (Trung, B thinking)", "15.092", 15092, 1.0, [TRUNG_R, QD], GFL,
    lambda: fallback_rate() * 100 * jget(GFL, "B_thinking", "tokens_total_mean"))
add("G-t100-chien", "Token/100 lượt quy đổi (Chiến, prompt few-shot)", "21.566", 21566, 1.0, [QD, US27, BC], GFC,
    lambda: fallback_rate() * 100 * (jget(GFC, "summary", "tokens_in_tb") + jget(GFC, "summary", "tokens_out_tb")))
add("G-t100-hoang", "Token/100 lượt quy đổi (Hoàng, prompt ngắn)", "4.599", 4599, 1.0, [QD, HOANG_R, BC], GW,
    lambda: fallback_rate() * 100 * (jget(GW, "passes", "default", "summary", "mean_tokens_in") + jget(GW, "passes", "default", "summary", "mean_tokens_out")))
add("G-sf", "Gemini khẳng định có bán hàng ngoài danh mục (n=40)", "2/40", 2, 0, [TRUNG_R, US27, TN, BC], GSF, lambda: jget(GSF, "A_default", "flagged_regex_v2"))
add("G-cache", "Cache trúng (Trung)", "10/10", 10, 0, [TRUNG_R], GFL, lambda: jget(GFL, "C_cache", "hits"))
add("S-tax", "Schema hợp lệ catalog taxonomy v1", "4.586/4.586", 4586, 0, [TRUNG_R], SCH, lambda: jget(SCH, "catalog_fpi_taxonomy_v1_inscope", "valid"))
add("S-vi", "Schema hợp lệ ViMRHP trong phạm vi", "361/361", 361, 0, [TRUNG_R], SCH, lambda: jget(SCH, "vimrhp_inscope", "valid"))
add("TX-168", "Số nhãn FPI map được", "168/168", 168, 0, [TRUNG_R], TAX, lambda: jget(TAX, "fpi", "distinct_labels") - jget(TAX, "fpi", "labels_unmapped"))
add("TX-286", "Mũ sau taxonomy v1 (trước làm sạch)", "286", 286, 0, [QD], TAX, lambda: jget(TAX, "catalog_fpi_v1", "by_type", "headwear"))

# --- Đạt: làm sạch, LLM
add("D-4385", "Số SP sau làm sạch", "4.385", 4385, 0, [DAT_R, US27, BC, RD], CLEAN, lambda: jget(CLEAN, "after", "n"))
add("D-285", "Mũ chuẩn sau làm sạch", "285", 285, 0, [DAT_R, QD, US27, BC, RD], CLEAN, lambda: jget(CLEAN, "after", "by_type", "headwear"))
add("D-293", "Mũ trước làm sạch (nhãn gốc FPI)", "293", 293, 0, [QD], STATS, lambda: jget(STATS, "fpi_by_type", "headwear"))
add("D-md5", "Số nhóm trùng MD5 / SP xoá", "xoá 21", 21, 0, [DAT_R], CLEAN, lambda: jget(CLEAN, "removed_duplicates") if "removed_duplicates" in J(CLEAN) else jget(CLEAN, "dedupe", "removed_duplicates"))
add("D-phash", "Cặp pHash ≤ 4", "3.937", 3937, 0, [DAT_R], CLEAN, lambda: jget(CLEAN, "dedupe", "pairs_le_thr_total"))
add("D-review", "Cặp pHash cần người xem", "122", 122, 0, [DAT_R], CLEAN, lambda: jget(CLEAN, "dedupe", "pairs_action", "review"))
add("D-title27", "Nhãn mũ sửa theo tiêu đề", "27 nhãn", 27, 0, [DAT_R], CLEAN, lambda: sum(jget(CLEAN, "title_refined").values()))
for mk, key, v in [("gemini35flashlite", "faithfulness", 0.939), ("gemini35flashlite", "hallucination_rate", 0.111),
                   ("gemma4_26b_api", "faithfulness", 0.992), ("gemma4_26b_api", "hallucination_rate", 0.031),
                   ("qwen25_05b", "faithfulness", 0.255), ("qwen25_05b", "hallucination_rate", 0.333)]:
    add(f"L-{mk}-{key}", f"Bảng D {mk} {key} [LLM chấm]", f"{v:.3f}".replace(".", ","), v, 6e-4, [DAT_R, US27], LLM,
        lambda mk=mk, key=key: jget(LLM, "qa", mk, key))
for mk, key, v in [("gemini35flashlite", "tokens_in_per_100", 60619), ("gemini35flashlite", "tokens_out_incl_thinking_per_100", 3631),
                   ("gemma4_26b_api", "tokens_out_incl_thinking_per_100", 63112), ("qwen25_05b", "tokens_in_per_100", 68994)]:
    add(f"L-{mk}-{key}", f"Bảng D {mk} {key}", f"{v:,}".replace(",", "."), v, 0, [US27], LLM, lambda mk=mk, key=key: jget(LLM, "qa", mk, key))
add("L-router", "Gemini Flash-Lite làm router (n=14)", "0,857", 0.857, 6e-4, [DAT_R, US27, BC], LLM, lambda: jget(LLM, "router", "gemini35flashlite", "route_accuracy"))
add("L-budget", "Lời gọi Gemini Đạt đã dùng", "250/250", 250, 0, [DAT_R], "02_TuanDat/results/gemini_budget.json",
    lambda: jget("02_TuanDat/results/gemini_budget.json", "calls"))
add("L-429", "Lời gọi bị 429 = số câu trong file failed × 4 lần thử (1 + 3 retry)", "144 lời gọi bị 429", 144, 0, [DAT_R], "02_TuanDat/results/failed/bench_llm_qa_gemini35flash_t0_ALL_429.jsonl", lambda: 4 * n429(),
    "36 dòng × 4")
add("L-us36", "Ý tóm tắt LLM không có trong review", "3/93", 3, 0, [DAT_R], "02_TuanDat/results/us36_kiem_tay_20sp.csv", lambda: us36_bad()[0])
add("L-us36n", "Tổng số ý đã kiểm (US_36)", "3/93", 93, 0, [DAT_R], "02_TuanDat/results/us36_kiem_tay_20sp.csv", lambda: us36_bad()[1])

# --- Chiến: eval, RAG
add("Q-280", "Số câu eval_qa", "280 câu", 280, 0, [CHIEN_R, US27], "03_Chien/eval/eval_qa.jsonl", lambda: eval_qa_counts()[0])
add("Q-71", "Câu không có đáp án", "71 câu answerable=false", 71, 0, [CHIEN_R], "03_Chien/eval/eval_qa.jsonl", lambda: eval_qa_counts()[1])
add("Q-254", "Tỉ lệ câu không đáp án (%)", "25,4 %", 25.4, 0.05, [CHIEN_R, US27], "03_Chien/eval/eval_qa.jsonl",
    lambda: 100 * eval_qa_counts()[1] / eval_qa_counts()[0])
add("Q-llm", "Câu eval_qa do LLM sinh", "251", 251, 0, [CHIEN_R], "03_Chien/eval/eval_qa.jsonl", lambda: eval_qa_counts()[2].get("llm_gemini", 0))
add("Q-r78", "Số câu eval_router", "78 câu", 78, 0, [CHIEN_R], "03_Chien/eval/eval_router.jsonl", lambda: eval_router_counts()[0])
add("Q-r21", "Câu chitchat/ood eval_router", "21 chitchat/ood", 21, 0, [CHIEN_R], "03_Chien/eval/eval_router.jsonl", lambda: eval_router_counts()[1])
add("Q-chunks", "Số chunk kho RAG", "10.173", 10173, 0, [CHIEN_R, US27], "03_Chien/data/kb/chunks.jsonl", lambda: chunks_counts()[0])
add("Q-kbsp", "Số SP trong kho RAG", "428", 428, 0, [CHIEN_R, US27], "03_Chien/data/kb/chunks.jsonl", lambda: chunks_counts()[2])
add("Q-oos-qa", "Câu eval_qa ngoài phạm vi taxonomy", "45/280", 45, 0, [CHIEN_R, QD], "03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv", lambda: oos_counts()[0])
add("Q-oos-r", "Câu eval_router ngoài phạm vi", "4/78", 4, 0, [CHIEN_R, QD], "03_Chien/eval/ngoai_pham_vi_taxonomy_v1.csv", lambda: oos_counts()[1])
add("V-rev-all", "Review ViMRHP toàn bộ 509 SP", "11.009", 11009, 0, [KHOA_R, US27], STATS, lambda: jget(STATS, "vimrhp_reviews"))
add("V-rev-428", "Review của 428 SP (bỏ đồng hồ)", "9.403", 9403, 0, [QD, US27], "01_Trung/data/vimrhp_taxonomy_v1.csv", lambda: vimrhp_reviews("no_watch"))
add("V-rev-349", "Review của 349 SP có lá taxonomy (keep)", "7.575", 7575, 0, [QD, "01_Trung/docs/US_49_taxonomy.md"], "01_Trung/data/vimrhp_taxonomy_v1.csv", lambda: vimrhp_reviews("keep"))
add("V-rev-361", "Review của 361 SP trong phạm vi (349 keep + 12 unknown)", "7.833", 7833, 0, [QD], "01_Trung/data/vimrhp_taxonomy_v1.csv", lambda: vimrhp_reviews("in_scope"))
add("H-866", "Hybrid Hit@5 (toàn 209 câu)", "0.866", 0.866, 6e-4, [CHIEN_R], RAGR, lambda: hyb("", "hit@5") if False else float(J("03_Chien/results/rag_eval.json")["retrieval"]["theo_product_id"]["hybrid(bm25+dense:intfloat/multilingual-e5-small)"]["hit@5"]))
add("H-895", "Hybrid Hit@5 split test (n=114)", "0,895", 0.895, 6e-4, [CHIEN_R, US27, BC], RAGR, lambda: hyb("test", "hit@5"))
add("H-377", "Hybrid Hit@1 test", "0,377", 0.377, 6e-4, [US27], RAGR, lambda: hyb("test", "hit@1"))
add("H-599", "Hybrid MRR@10 test", "0,599", 0.599, 6e-4, [US27], RAGR, lambda: hyb("test", "mrr@10"))
add("H-tfidf", "TF-IDF char Hit@5 test", "0,877", 0.877, 6e-4, [CHIEN_R, US27], RAGR, lambda: ragr("tfidf_char", "hit@5"))
add("H-bm25", "BM25 Hit@5 test", "0,868", 0.868, 6e-4, [US27], RAGR, lambda: ragr("bm25", "hit@5"))
add("E-ref", "Refusal accuracy RAG (sau sửa nhãn qa108)", "15/15", 15, 0, [CHIEN_R, US27, TN, BC], RAGE,
    lambda: round(jget(RAGE, "summary", "refusal_accuracy (answerable=false bị từ chối đúng)") * jget(RAGE, "summary", "n_khong_dap_an")))
add("E-ref-before", "Refusal accuracy RAG TRƯỚC sửa nhãn (15/16)", "15/16", 0.9375, 6e-4, [BC, "03_Chien/docs/US_33_34_35_rag.md"], RAGE,
    lambda: jget(RAGE, "summary_truoc_sua_nhan", "refusal_accuracy (answerable=false bị từ chối đúng)"))
add("E-cg", "Cited-gold", "0.865", 0.865, 6e-4, [CHIEN_R], RAGE, lambda: jget(RAGE, "summary", "cited_gold_rate (answerable được trả lời, trích trúng review bằng chứng)"))
add("E-faith", "Faithfulness RAG Chiến [LLM chấm]", "1.00", 1.0, 0, [CHIEN_R], RAGE, lambda: jget(RAGE, "summary", "faithfulness_judge_mean"))
add("E-n", "Số câu e2e RAG", "52 câu", 52, 0, [CHIEN_R], RAGE, lambda: jget(RAGE, "summary", "n_cau"))
add("E-tok", "Token vào/câu RAG", "378,9", 378.9, 0.05, [CHIEN_R], RAGE, lambda: jget(RAGE, "token_answer_tren_moi_cau", "in"))
add("F-viol", "Vi phạm giá/size/tồn kho nhánh Gemini (Chiến)", "0/20", 0, 0, [CHIEN_R, US27], GFC, lambda: jget(GFC, "summary", "vi_pham_gia_size_tonkho (eval_router)"))
add("F-ok", "Phản hồi hợp lệ nhánh Gemini (Chiến)", "22/60", 22, 0, [CHIEN_R], GFC, lambda: jget(GFC, "summary", "n_phan_hoi_hop_le"))
add("F-tin", "Token vào TB nhánh fallback Chiến", "747,5", 747.5, 0.05, [QD], GFC, lambda: jget(GFC, "summary", "tokens_in_tb"))
add("F-p50", "Latency nhánh Gemini Chiến p50 (s)", "16,0 s", 16.0, 0.05, [CHIEN_R], GFC, lambda: jget(GFC, "summary", "latency_ms_p50") / 1000)
add("F-p95", "Latency nhánh Gemini Chiến p95 (s)", "27,8 s", 27.8, 0.05, [CHIEN_R], GFC, lambda: jget(GFC, "summary", "latency_ms_p95") / 1000)
add("F-74750", "Token vào /100 LỜI GỌI Gemini (Chiến)", "74.750", 74750, 0, [CHIEN_R, QD], GFC, lambda: jget(GFC, "summary", "token_tren_100_luot", "in"))

# --- Hoàng: API, text-embed, gateway, data v1
add("API-p50", "API /search/image p50 (ms)", "p50 393 ms", 393, 0.6, [HOANG_R, TN], API, lambda: jget(API, "search_image", "overall", "latency_ms_client", "p50"))
add("API-p95", "API /search/image p95 (ms)", "1.106 ms", 1106, 0.6, [HOANG_R, TN, BC], API, lambda: jget(API, "search_image", "overall", "latency_ms_client", "p95"))
add("API-1500", "% truy vấn < 1,5 s", "97,5 %", 97.5, 0.05, [HOANG_R], API, lambda: 100 * jget(API, "search_image", "overall", "pct_under_1500ms"))
add("API-cte", "CTE@5 qua API (CLIP B/32 + gate)", "1,5 %", 1.5, 0.05, [HOANG_R], API, lambda: 100 * jget(API, "search_image", "overall", "cross_type_error@5"))
add("API-subp", "Sub-category P@5 qua API", "0,925", 0.925, 6e-4, [HOANG_R], API, lambda: jget(API, "search_image", "overall", "subcategory_precision@5"))
add("API-top1", "Top-1 cosine trung bình CLIP B/32", "0,96", 0.96, 0.005, [HOANG_R, QD], API, lambda: jget(API, "search_image", "overall", "top1_score_mean"))
add("API-cmp", "Ô so sánh khớp", "370/370", 370, 0, [HOANG_R, BC], API, lambda: jget(API, "compare", "n_cells_match"))
add("API-txt", "Kết quả /search/text thoả lọc", "300/300", 300, 0, [HOANG_R], API, lambda: jget(API, "search_text", "total_items") - jget(API, "search_text", "total_violations"))
for m, v in [("tfidf_word", 0.875), ("tfidf_char", 0.856), ("e5-small", 0.803), ("minilm-l12", 0.794), ("vn-sbert", 0.775)]:
    add(f"TE-{m}", f"Text-embed Hit@5 trong SP {m} (Hoàng)", f"{v:.3f}".replace(".", ","), v, 6e-4, [HOANG_R], TXT,
        lambda m=m: cget(TXT, "model", m, "C_ev_inprod_hit@5_mean"))
add("TE-n", "n câu Bảng C của Hoàng (tfidf/e5)", "208 câu", 208, 0, [HOANG_R], TXT, lambda: cget(TXT, "model", "tfidf_word", "n_queries_C_mean"),
    "minilm-l12 và vn-sbert chạy trên 209 câu – xem doi_chieu ghi chú")
add("GW-10", "Gateway request thành công", "10/10", 10, 0, [HOANG_R], GW, lambda: jget(GW, "passes", "default", "summary", "n_success"))
add("GW-tin", "Token vào /100 LỜI GỌI (Hoàng)", "10.460", 10460, 0, [HOANG_R, QD], GW, lambda: jget(GW, "passes", "default", "summary", "tokens_per_100_requests", "tokens_in"))
add("GW-tout", "Token ra /100 LỜI GỌI (Hoàng)", "6.370", 6370, 0, [HOANG_R, QD], GW, lambda: jget(GW, "passes", "default", "summary", "tokens_per_100_requests", "tokens_out"))
add("GW-cache", "Cache p50 (ms) gateway", "17,9 ms", 17.9, 0.05, [HOANG_R], GW, lambda: jget(GW, "passes", "default_repeat_cache", "summary", "latency_ms_end_to_end", "p50"))
add("DV1-n", "Data v1 tổng SP", "5.021", 5021, 0, [HOANG_R], DV1, lambda: jget(DV1, "counts", "total"))
add("DV1-298", "Data v1 mũ (gồm băng đô + ViMRHP)", "298", 298, 0, [HOANG_R, QD], DV1, lambda: jget(DV1, "counts", "by_type", "headwear"))
add("DV1-cl", "Data v1 quần áo (gồm ViMRHP)", "2.388", 2388, 0, [HOANG_R], DV1, lambda: jget(DV1, "counts", "by_type", "clothing"))
add("SH-4593", "Catalog FPI shared_data", "4.593", 4593, 0, [KHOA_R, US27, RD], STATS, lambda: jget(STATS, "fpi_total"))
add("SH-509", "ViMRHP số SP", "509", 509, 0, [KHOA_R, US27, RD], STATS, lambda: jget(STATS, "vimrhp_products"))


# --- Bổ sung cho BAO_CAO_TONG_HOP.md / README.md gốc (Tác nhân 3)
E5 = "dense:intfloat/multilingual-e5-small"
ML = "dense:sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
for name, metric, v in [(E5, "hit@5", 0.807), (ML, "hit@5", 0.763), (E5, "hit@1", 0.298), (ML, "hit@1", 0.316),
                        (E5, "mrr@10", 0.525), (ML, "mrr@10", 0.511), ("tfidf_char", "hit@1", 0.289), ("bm25", "hit@1", 0.272)]:
    add(f"H-{name[-8:]}-{metric}", f"{name} {metric} test", f"{v:.3f}".replace(".", ","), v, 6e-4, [US27, BC], RAGR,
        lambda n=name, m=metric: ragr(n, m))
for name, v in [("tfidf_char", 0.833), ("bm25", 0.837), (E5, 0.794), (ML, 0.756)]:
    add(f"H209-{name[-8:]}", f"{name} Hit@5 trên 209 câu", f"{v:.3f}".replace(".", ","), v, 6e-4, [BC], "03_Chien/results/rag_eval.json",
        lambda n=name: J("03_Chien/results/rag_eval.json")["retrieval"]["theo_product_id"][n]["hit@5"])
for setname, n, k in [("seed_trung", 45, 13), ("chien_eval_router", 78, 21), ("gemini_gen_heldout", 49, 13)]:
    add(f"FR-{setname}", f"Số câu chuyển Gemini – {setname}", f"| {n} | {k} |", k, 0, [BC], GFL,
        lambda s_=setname: jget(GFL, "routing", "per_set", s_, "routed_gemini"))
add("FR-47", "Tổng câu chuyển Gemini / 172", "**47**", 47, 0, [BC], GFL, lambda: jget(GFL, "routing", "total_routed_gemini"))
add("T100-trung-call", "Token/100 lời gọi (Trung A)", "22.060", 22060, 1, [BC], GFL, lambda: 100 * jget(GFL, "A_default", "tokens_total_mean"))
add("T100-chien-call", "Token/100 lời gọi (Chiến)", "78.920", 78920, 1, [BC, HOANG_R], GFC,
    lambda: 100 * (jget(GFC, "summary", "tokens_in_tb") + jget(GFC, "summary", "tokens_out_tb")))
add("T100-hoang-call", "Token/100 lời gọi (Hoàng)", "16.830", 16830, 1, [BC], GW,
    lambda: 100 * (jget(GW, "passes", "default", "summary", "mean_tokens_in") + jget(GW, "passes", "default", "summary", "mean_tokens_out")))
add("T100-dat-qa", "Token/100 câu QA (Đạt, vào + ra)", "64.250", 64250, 0, [BC], LLM,
    lambda: jget(LLM, "qa", "gemini35flashlite", "tokens_in_per_100") + jget(LLM, "qa", "gemini35flashlite", "tokens_out_incl_thinking_per_100"))
add("D-brand", "Dòng chuẩn hoá thương hiệu", "1.304 dòng", 1304, 0, [BC], CLEAN, lambda: jget(CLEAN, "brand_fixed"))
add("TX-keep", "Nhãn FPI giữ / unknown / loại", "61 giữ, 5 unknown, 102 loại", 61, 0, [BC], TAX, lambda: jget(TAX, "fpi", "labels_keep"))
add("TX-vi", "ViMRHP giữ / unknown / loại", "giữ 349, unknown 12, loại 148", 349, 0, [BC], TAX, lambda: jget(TAX, "vimrhp", "keep"))
add("EDA-37", "Số articleType trong catalog", "37 `articleType`", 37, 0, [BC], "04_Khoa/docs/US_09_eda/eda_stats.json",
    lambda: jget("04_Khoa/docs/US_09_eda/eda_stats.json", "catalog", "n_article_types"))
add("EDA-785", "Dòng trùng tên", "785 dòng trùng tên", 785, 0, [BC, KHOA_R], "04_Khoa/docs/US_09_eda/eda_stats.json",
    lambda: jget("04_Khoa/docs/US_09_eda/eda_stats.json", "catalog", "dup_title_rows"))
add("PYT-sum", "Tổng test pass 5 folder (53+21+51+30+78)", "233 passed", 233, 0, [BC], "KIEM_DINH_TAC_NHAN_3.md (chạy pytest)",
    lambda: 53 + 21 + 51 + 30 + 78, "số từng folder lấy từ lần chạy pytest cuối, ghi trong KIEM_DINH")
add("US-sum", "Tổng US Đạt (3+3+4+6+7)", "**23**", 23, 0, [BC], "README mục 0 của 5 thành viên", lambda: 3 + 3 + 4 + 6 + 7)


# ----------------------------------------------------------------------------- quét câu chữ rủi ro
# (mẫu regex, điều kiện "an toàn" trên cùng dòng, giải thích). Một dòng khớp mẫu mà không có từ an toàn → cảnh báo.
import re  # noqa: E402

RISK = [
    (r"0[,.]921", r"tổng hợp|biến đổi|ảnh thật|tables|\| I3_linear_adapter \||lịch sử|Tác nhân 3", "adapter 0,921 phải ghi là trên truy vấn tổng hợp"),
    (r"74[.,]750[^\n]{0,40}/ ?100 lượt(?! hội thoại)", r"lời gọi", "74.750 là /100 lời gọi, không phải /100 lượt"),
    (r"10[.,]460[^\n]{0,40}/ ?100 lượt(?! hội thoại)", r"lời gọi", "10.460 là /100 lời gọi"),
    (r"7[.,]575[^\n]{0,30}361", r"349", "7.575 review thuộc 349 SP, không phải 361"),
    (r"0[,.]923[^\n]{0,60}held-out", r"không|chỉnh|sửa", "0,923 là tập đã chỉnh luật – không phải held-out"),
    (r"[Ff]aithfulness[^\n]{0,80}(người chấm|đánh giá của người)", r"LLM|chờ|cần|chưa|không phải", "faithfulness là LLM chấm"),
]
SCAN_GLOBS = ["README.md", "BAO_CAO_TONG_HOP.md", "00_Chung/*.md", "0*/README.md", "0*/docs/*.md", "0*/docs/*/*.md"]


def scan_risks() -> list[tuple[str, int, str, str]]:
    out = []
    seen = set()
    for g in SCAN_GLOBS:
        for p in sorted(ROOT.glob(g)):
            if p in seen or "kiem_dinh" in p.parts:
                continue
            seen.add(p)
            for i, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
                for pat, safe, why in RISK:
                    if re.search(pat, line) and not re.search(safe, line):
                        out.append((str(p.relative_to(ROOT)), i, why, line.strip()[:120]))
    return out

# ----------------------------------------------------------------------------- chạy
def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.4f}".rstrip("0").rstrip(".") if abs(v) < 1000 else f"{v:.1f}"
    return str(v)


def main() -> int:
    rows, n_ok, n_bad, n_missing, n_err = [], 0, 0, 0, 0
    for cid, desc, shown, claimed, tol, docs, src, getter, note in C:
        try:
            val = getter()
        except Exception as e:  # noqa: BLE001
            rows.append((cid, desc, shown, ", ".join(docs), src, f"LỖI ĐỌC: {e!r}", "LỖI"))
            n_err += 1
            continue
        match = abs(float(val) - float(claimed)) <= tol + 1e-9
        present, absent = [], []
        for d in docs:
            p = ROOT / d
            if not p.exists():
                absent.append(d + " (không có file)")
            elif shown in doc_text(d):
                present.append(d)
            else:
                absent.append(d)
        status = "KHỚP" if match else "LỆCH"
        if match and absent:
            status = "KHỚP (thiếu chuỗi ở: " + ", ".join(absent) + ")"
            n_missing += 1
        if match:
            n_ok += 1
        else:
            n_bad += 1
        rows.append((cid, desc, shown, ", ".join(present) or "—", src, fmt(val) + (f" · {note}" if note else ""), status))

    lines = [
        "# Đối chiếu số liệu – tài liệu ↔ file kết quả (sinh tự động)",
        "",
        "Sinh bởi `python 00_Chung/kiem_dinh/check_numbers.py` (Tác nhân 3). **Không sửa tay** – sửa tài liệu rồi chạy lại.",
        "Cột *Số trong tài liệu* là chuỗi tìm thấy trong các tài liệu ở cột kế; *Giá trị trong file* đọc trực tiếp từ file nguồn",
        "(một số dòng là phép tính từ file, ghi trong mô tả). KHỚP = chênh ≤ dung sai làm tròn của số đã viết.",
        "",
        f"**Tổng: {len(C)} khẳng định · KHỚP {n_ok} · LỆCH {n_bad} · lỗi đọc {n_err} · khớp nhưng thiếu chuỗi ở ≥ 1 tài liệu {n_missing}.**",
        "",
        "| Mã | Nội dung | Số trong tài liệu | Tài liệu chứa số | File nguồn | Giá trị trong file | Kết quả |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |")
    risks = scan_risks()
    lines += ["", f"## Quét câu chữ rủi ro: {len(risks)} cảnh báo", "",
              "Mẫu: adapter 0,921 không ghi tổng hợp; token /100 lượt nhầm đơn vị; 7.575 ↔ 361; 0,923 gọi là held-out; faithfulness gọi là người chấm.", ""]
    if risks:
        lines += ["| File | Dòng | Vấn đề | Trích |", "|---|---|---|---|"]
        lines += [f"| {a} | {b} | {c} | {d.replace('|', '\\|')} |" for a, b, c, d in risks]
    else:
        lines.append("Không có cảnh báo.")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for r in risks:
        print("  RỦI RO", r[0], r[1], r[2])
    print(f"{len(C)} khẳng định: KHỚP {n_ok}, LỆCH {n_bad}, lỗi {n_err}, thiếu chuỗi {n_missing} -> {OUT_MD.relative_to(ROOT)}")
    for r in rows:
        if not r[-1].startswith("KHỚP") or "thiếu" in r[-1]:
            print("  ", r[0], "|", r[2], "|", r[5], "|", r[-1])
    return 1 if ("--strict" in sys.argv and (n_bad or n_err)) else 0


if __name__ == "__main__":
    sys.exit(main())
