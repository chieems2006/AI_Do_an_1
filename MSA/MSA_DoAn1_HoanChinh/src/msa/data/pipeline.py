# repo: src/msa/data/pipeline.py
"""Logic dùng chung cho scripts/01_download_public.py (US_06) và 01b_download_clothing_hats.py (US_48)."""
from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

import pandas as pd

from . import converters as C

FPI_HF_REPO = "ashraq/fashion-product-images-small"
VIMRHP_HF_REPO = "trucmtnguyen/ViMRHP"


def ensure_raw(raw_dir: Path, download: bool) -> tuple[list[str], list[str]]:
    """Trả (file parquet FPI, file JSON ViMRHP Fashion). Thiếu và --download → tải qua huggingface_hub."""
    fpi = sorted(glob.glob(str(raw_dir / "fpi" / "data" / "*.parquet")))
    vim = sorted(glob.glob(str(raw_dir / "vimrhp" / "Annotation" / "Fashion-*.json")))
    if download and not fpi:
        from huggingface_hub import snapshot_download
        snapshot_download(FPI_HF_REPO, repo_type="dataset", local_dir=str(raw_dir / "fpi"), allow_patterns=["data/*.parquet"])
        fpi = sorted(glob.glob(str(raw_dir / "fpi" / "data" / "*.parquet")))
    if download and not vim:
        from huggingface_hub import snapshot_download
        snapshot_download(VIMRHP_HF_REPO, repo_type="dataset", local_dir=str(raw_dir / "vimrhp"),
                          allow_patterns=["Annotation/Fashion-*.json", "README.md"])
        vim = sorted(glob.glob(str(raw_dir / "vimrhp" / "Annotation" / "Fashion-*.json")))
    if not fpi:
        raise FileNotFoundError(f"Không thấy parquet FPI trong {raw_dir}/fpi/data – chạy với --download")
    return fpi, vim


def _sha_files(paths: list[str]) -> dict:
    out = {}
    for p in paths:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        out[os.path.basename(p)] = h.hexdigest()
    return out


def build(product_types: set[str], raw_dir: Path, out_dir: Path, *, images: bool = True, quota: dict | None = C.FPI_QUOTA,
          seed: int = C.SEED, download: bool = False) -> dict:
    """Chạy converter FPI + ViMRHP cho các product_type; trả {catalog df, image_hashes, info}."""
    fpi_files, vim_files = ensure_raw(raw_dir, download)
    meta = C.read_fpi_metadata(fpi_files)
    avail = C.select_fpi(meta, product_types, quota=None)
    sel = C.select_fpi(meta, product_types, quota=quota, seed=seed)
    fpi_df = pd.DataFrame([C.fpi_row_to_schema(r) for r in sel.itertuples()], columns=C.SCHEMA_FIELDS)
    img_hashes = C.extract_fpi_images(fpi_files, set(sel.id.astype(int)), out_dir / "images") if images else {}
    vim_df = C.convert_vimrhp(vim_files) if vim_files else pd.DataFrame(columns=C.SCHEMA_FIELDS)
    vim_df = vim_df[vim_df.product_type.isin(product_types)]
    cat = pd.concat([fpi_df, vim_df], ignore_index=True).sort_values("product_id").reset_index(drop=True)
    info = {"fpi_rows_total": int(len(meta)), "fpi_available_by_sub": {f"{a}/{b}": int(n) for (a, b), n in
                                                                       avail.groupby(["product_type", "sub_category"]).size().items()},
            "fpi_selected": int(len(fpi_df)), "vimrhp_selected": int(len(vim_df)),
            "vimrhp_reviews": int(vim_df.reviews.map(len).sum()) if len(vim_df) else 0,
            "vimrhp_type_rule": vim_df.specs.map(lambda s: s["type_rule"]).value_counts().to_dict() if len(vim_df) else {},
            "raw_file_sha256": _sha_files(fpi_files + vim_files), "seed": seed, "quota": quota}
    return {"catalog": cat, "image_hashes": img_hashes, "info": info}


def run(name: str, product_types: set[str], args) -> dict:
    """Chạy build, ghi parquet + bảng đếm + sources_log; tuỳ chọn kiểm tái lập (chạy lần 2 vào thư mục tạm)."""
    raw, out = Path(args.raw_dir), Path(args.out_dir)
    t0 = time.time()
    res = build(product_types, raw, out, images=not args.no_images, quota=None if args.full else C.FPI_QUOTA,
                download=args.download)
    cat = res["catalog"]
    errs = C.validate_schema(cat)
    h1 = C.catalog_hash(cat)
    img_h1 = hashlib.sha256(json.dumps(res["image_hashes"], sort_keys=True).encode()).hexdigest()
    path = out / "processed" / f"{name}.parquet"
    C.write_catalog(cat, path)
    report = {"name": name, "product_types": sorted(product_types), "output": str(path.relative_to(out.parent)),
              "counts": C.count_table(cat, product_types), "schema_errors": errs, "catalog_sha256": h1, "images_sha256": img_h1,
              "n_images": len(res["image_hashes"]), "elapsed_s": round(time.time() - t0, 1), **res["info"],
              "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    if args.check_repro:
        with tempfile.TemporaryDirectory() as td:
            r2 = build(product_types, raw, Path(td), images=not args.no_images,
                       quota=None if args.full else C.FPI_QUOTA, download=False)
            h2 = C.catalog_hash(r2["catalog"])
            img_h2 = hashlib.sha256(json.dumps(r2["image_hashes"], sort_keys=True).encode()).hexdigest()
            # đọc lại parquet đã ghi để chắc chắn ghi/đọc không đổi nội dung
            h_disk = C.catalog_hash(C.read_catalog(path)[C.SCHEMA_FIELDS])
        report["repro_check"] = {"run2_catalog_sha256": h2, "run2_images_sha256": img_h2,
                                 "same_catalog": h1 == h2, "same_images": img_h1 == img_h2,
                                 "parquet_roundtrip_same": h_disk == h1}
    C.append_sources_log(out / "sources_log.json", {**C.FPI_SOURCE, "used_for": "catalog + ảnh (visual search)",
                                                    "files_sha256": {k: v for k, v in res["info"]["raw_file_sha256"].items() if k.endswith(".parquet")}})
    C.append_sources_log(out / "sources_log.json", {**C.VIMRHP_SOURCE, "used_for": "review tiếng Việt (RAG/QA), tên SP",
                                                    "files_sha256": {k: v for k, v in res["info"]["raw_file_sha256"].items() if k.endswith(".json")}})
    (out / f"counts_{name}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return report
