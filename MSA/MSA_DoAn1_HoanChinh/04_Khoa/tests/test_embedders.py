import numpy as np
import pytest
from PIL import Image

from msa.embed.image_embedders import (REGISTRY, DummyEmbedder, common_preprocess, get_embedder, l2n, pad_to_square)


def test_registry_has_at_least_6_models():
    assert len(REGISTRY) >= 6
    for k in ("resnet50", "clip_b32", "clip_b16", "siglip_b16", "fashionclip", "dinov2_s"):
        assert k in REGISTRY


def test_pad_and_preprocess():
    im = Image.new("RGB", (60, 80), "red")
    sq = pad_to_square(im)
    assert sq.size == (80, 80)
    assert sq.getpixel((0, 0)) == (255, 255, 255)
    assert common_preprocess(im, 224).size == (224, 224)


def test_dummy_embedder_normalized_and_deterministic():
    e = get_embedder("dummy")
    a = Image.new("RGB", (60, 80), (200, 10, 10)); b = Image.new("RGB", (60, 80), (10, 10, 200))
    X = e.embed([a, b, a])
    assert X.shape == (3, e.dim)
    assert np.allclose(np.linalg.norm(X, axis=1), 1, atol=1e-5)
    assert np.allclose(X[0], X[2])
    T = e.embed_text(["a photo of shoes", "a photo of shoes"])
    assert np.allclose(T[0], T[1])


def test_unknown_model_raises():
    with pytest.raises(KeyError):
        get_embedder("khong_co")


def test_l2n_zero_safe():
    assert np.all(np.isfinite(l2n(np.zeros((2, 3)))))
