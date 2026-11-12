from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from build_eval_visual import TRANSFORMS, apply_transform

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", TRANSFORMS)
def test_transforms_keep_size(name):
    im = Image.new("RGB", (60, 80), "white")
    im.paste(Image.new("RGB", (30, 40), "navy"), (15, 20))
    out, desc = apply_transform(im, name, np.random.default_rng(0))
    assert out.size == (60, 80) and desc.startswith(name)


EVAL = ROOT / "eval" / "eval_visual.csv"


@pytest.mark.skipif(not EVAL.exists(), reason="chưa sinh eval_visual.csv")
def test_eval_visual_meets_acceptance():
    df = pd.read_csv(EVAL, keep_default_na=False)
    need = {"query_id", "query_image", "gt_product_ids", "product_type", "sub_category", "split", "source", "hard_cross_type", "transform"}
    assert need <= set(df.columns)
    assert len(df) >= 200 and df.query_id.is_unique
    assert set(df.split) == {"val", "test"}
    t = df[df.split == "test"].product_type.value_counts()
    assert all(t.get(x, 0) >= 30 for x in ("footwear", "clothing", "headwear", "accessory"))
    assert df.hard_cross_type.astype(str).str.lower().eq("true").sum() >= 20
    # SP của val và test (tầng instance) không trùng nhau
    inst = df[df.tier == "instance"]
    assert not (set(inst[inst.split == "val"].gt_product_ids) & set(inst[inst.split == "test"].gt_product_ids))
    assert all((ROOT / p).exists() for p in df.query_image.head(20))
