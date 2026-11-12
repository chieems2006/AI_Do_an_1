# repo: scripts/build_visual_index.py (bản tạm phía API – bản chính thức do Khoa sở hữu)
"""Trích embedding CLIP ViT-B/32 cho toàn bộ ảnh catalog Data v1 và lưu cache cho ClipFaissSearcher.
Lệnh: python src/scripts/build_visual_index.py   (≈ vài phút trên 2 CPU)"""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from msa.data.converters import read_catalog  # noqa: E402
from msa.api.searchers import ClipFaissSearcher  # noqa: E402

if __name__ == "__main__":
    t = time.time()
    cat = read_catalog(ROOT / "data" / "processed" / "catalog_v1.parquet")
    s = ClipFaissSearcher(cat, ROOT / "data", ROOT / "results" / "cache")
    print(f"index: {len(s.index.ids)} ảnh, {time.time() - t:.1f}s")
