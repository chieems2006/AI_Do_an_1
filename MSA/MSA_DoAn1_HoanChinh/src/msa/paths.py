# repo: src/msa/paths.py
"""Đường dẫn dùng chung cho package `msa` – nơi DUY NHẤT gắn code với bố cục thư mục đồ án.

Code chạy hệ thống nằm ở `src/msa/`; tài nguyên vẫn thuộc folder của thành viên phụ trách
(prompt của Chiến, schema/eval của Trung, index của Khoa, dữ liệu của Hoàng). Mọi đường dẫn
đều đổi được bằng biến môi trường (xem README §2).
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRUNG = PROJECT_ROOT / "01_Trung"
TUANDAT = PROJECT_ROOT / "02_TuanDat"
CHIEN = PROJECT_ROOT / "03_Chien"
KHOA = PROJECT_ROOT / "04_Khoa"
HOANG = PROJECT_ROOT / "05_Hoang"


def env_path(var: str, default: str | os.PathLike) -> Path:
    """Đường dẫn từ biến môi trường `var`, nếu không đặt thì dùng `default`."""
    v = os.environ.get(var)
    return Path(v) if v else Path(default)


def shared_data() -> Path:
    """Thư mục dữ liệu dùng chung (catalog_fpi.parquet, fpi_images/, vimrhp_fashion_products.jsonl)."""
    return env_path("MSA_SHARED_DATA", "/home/claude/work/shared_data")


# ---- tài nguyên theo thành viên phụ trách
SCHEMA_PATH = TRUNG / "src" / "schema" / "product.schema.json"          # US_05 – Trung
ROUTER_PROTOS = TRUNG / "eval" / "eval_router_seed.jsonl"               # prototype intent – Trung
RAG_PROMPT = CHIEN / "prompts" / "rag_grounded.md"                      # US_34 – Chiến
FALLBACK_PROMPT = CHIEN / "prompts" / "gemini_fallback.md"              # US_51 – Chiến
HALLUCINATION_CHECKER = CHIEN / "src" / "scripts" / "check_gemini_hallucination.py"
TAU_V_ANALYSIS = KHOA / "results" / "tau_v_analysis.json"               # US_29 – Khoa
TAU_V_RULE = "b_max_ood_val+0.01"                                       # QUYET_DINH_CAN_CHOT mục C


def rag_kb() -> Path:
    """Kho tri thức RAG (chunks.jsonl) – mặc định của Chiến."""
    return env_path("MSA_KB_PATH", CHIEN / "data" / "kb" / "chunks.jsonl")


def rag_cache_dir() -> Path:
    """Cache embedding e5 cho dense retriever."""
    return env_path("MSA_RAG_CACHE_DIR", CHIEN / "results" / "cache")


def visual_index_dir() -> Path:
    """Index FAISS cho /search/image – mặc định DINOv2-S (Bảng F hạng 1, QUYET_DINH mục E)."""
    return env_path("MSA_VISUAL_INDEX", KHOA / "indexes" / "dinov2_s")


def runtime_dir() -> Path:
    """Thư mục ghi log/cache khi chạy hệ thống (không commit)."""
    return env_path("MSA_RUNTIME_DIR", PROJECT_ROOT / "runtime")
