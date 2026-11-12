# repo: scripts/check_env.py
"""US_02 – Kiểm tra môi trường cho người mới clone repo (mục tiêu: < 10 phút từ clone đến chạy được).
Lệnh: python scripts/check_env.py [--json out.json]
Kiểm: phiên bản Python, thư viện + phiên bản (so với requirements.txt), CPU/RAM/đĩa, cấu trúc thư mục,
biến môi trường Gemini (chỉ báo CÓ/KHÔNG, không in giá trị), FAISS/torch chạy được phép tính nhỏ.
"""
from __future__ import annotations

import importlib
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKGS = {"numpy": "numpy", "pandas": "pandas", "pyarrow": "pyarrow", "PIL": "pillow", "imagehash": "ImageHash",
        "sklearn": "scikit-learn", "faiss": "faiss-cpu", "torch": "torch", "transformers": "transformers",
        "sentence_transformers": "sentence-transformers", "open_clip": "open_clip_torch", "fastapi": "fastapi",
        "uvicorn": "uvicorn", "httpx": "httpx", "pydantic": "pydantic", "multipart": "python-multipart", "pytest": "pytest"}
OPTIONAL = {"gradio": "gradio", "matplotlib": "matplotlib", "huggingface_hub": "huggingface_hub"}
DIRS = ["data", "src", "eval", "app", "notebooks", "prompts", "logs", "scripts", "tests"]


def pinned() -> dict:
    req = ROOT / "requirements.txt"
    out = {}
    if req.exists():
        for line in req.read_text().splitlines():
            if "==" in line and not line.startswith("#"):
                k, v = line.strip().split("==")
                out[k.lower()] = v
    return out


def main() -> int:
    t0 = time.time()
    pins = pinned()
    rep = {"python": platform.python_version(), "platform": platform.platform(), "cpu": os.cpu_count(), "checks": []}

    def add(name, ok, detail="", required=True):
        rep["checks"].append({"name": name, "ok": bool(ok), "required": required, "detail": detail})

    add("python>=3.10", sys.version_info >= (3, 10), rep["python"])
    from importlib.metadata import PackageNotFoundError, version
    for mod, dist in {**PKGS, **OPTIONAL}.items():
        req = mod in PKGS
        try:
            importlib.import_module(mod)
            v = version(dist)
            want = pins.get(dist.lower())
            add(f"import {mod}", True, f"{v}" + (f" (ghim {want}{'' if want == v else ' – KHÁC'})" if want else ""), req)
        except (ImportError, PackageNotFoundError) as e:
            add(f"import {mod}", False, f"thiếu: pip install {dist} ({type(e).__name__})", req)
    try:
        import psutil  # type: ignore
        ram = psutil.virtual_memory().total / 2**30
    except ImportError:
        ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30 if hasattr(os, "sysconf") else float("nan")
    add("RAM >= 6 GB", ram >= 6, f"{ram:.1f} GB", required=False)
    free = shutil.disk_usage(ROOT).free / 2**30
    add("đĩa trống >= 5 GB", free >= 5, f"{free:.1f} GB", required=False)
    missing = [d for d in DIRS if not (ROOT / d).exists()]
    add("cấu trúc thư mục", not missing, "đủ" if not missing else f"thiếu {missing} (tạo bằng mkdir)", required=False)
    add("GEMINI_API_KEY đã đặt", bool(os.environ.get("GEMINI_API_KEY")) or os.environ.get("MSA_LLM_MOCK") == "1",
        "có" if os.environ.get("GEMINI_API_KEY") else ("không – đang MSA_LLM_MOCK=1" if os.environ.get("MSA_LLM_MOCK") == "1"
                                                         else "không – đặt trong .env hoặc MSA_LLM_MOCK=1"), required=False)
    add("GEMINI_MODEL", True, os.environ.get("GEMINI_MODEL", "gemini-3.5-flash (mặc định)"), required=False)
    try:
        import faiss
        import numpy as np
        x = np.random.default_rng(0).random((100, 16), dtype=np.float32)
        idx = faiss.IndexFlatIP(16)
        idx.add(x)
        add("faiss search", idx.search(x[:1], 1)[1][0][0] == 0, "IndexFlatIP OK")
    except Exception as e:  # noqa: BLE001
        add("faiss search", False, repr(e)[:120])
    try:
        import torch
        torch.set_num_threads(2)
        add("torch CPU matmul", float((torch.ones(2, 2) @ torch.ones(2, 2)).sum()) == 8.0, f"threads={torch.get_num_threads()}")
    except Exception as e:  # noqa: BLE001
        add("torch CPU matmul", False, repr(e)[:120])
    rep["elapsed_s"] = round(time.time() - t0, 2)
    rep["ok"] = all(c["ok"] for c in rep["checks"] if c["required"])
    for c in rep["checks"]:
        flag = "OK  " if c["ok"] else ("LỖI" if c["required"] else "CẢNH BÁO")
        print(f"[{flag}] {c['name']}: {c['detail']}")
    print(f"=> {'MÔI TRƯỜNG SẴN SÀNG' if rep['ok'] else 'CẦN SỬA CÁC MỤC LỖI'} ({rep['elapsed_s']} s)")
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
