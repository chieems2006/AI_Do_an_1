import numpy as np
from PIL import Image, ImageDraw

from msa.embed.image_embedders import DummyEmbedder
from msa.search.improvements import LinearAdapter, bbox_crop, embed_tta_hflip


def test_bbox_crop_tightens_white_margin():
    im = Image.new("RGB", (60, 80), "white"); ImageDraw.Draw(im).rectangle([20, 30, 40, 50], fill="black")
    c = bbox_crop(im)
    assert c.size[0] < 60 and c.size[1] < 80


def test_bbox_crop_blank_image_center_crop():
    c = bbox_crop(Image.new("RGB", (60, 80), "white"))
    assert c.size == (51, 68)


def test_tta_shape_and_norm():
    e = DummyEmbedder()
    X = embed_tta_hflip(e, [Image.new("RGB", (60, 80), (i * 40, 0, 0)) for i in range(3)])
    assert X.shape == (3, e.dim) and np.allclose(np.linalg.norm(X, axis=1), 1, atol=1e-5)


def test_linear_adapter_learns_mapping(tmp_path):
    rng = np.random.default_rng(0)
    B = rng.standard_normal((300, 16)); B /= np.linalg.norm(B, axis=1, keepdims=True)
    R = np.linalg.qr(rng.standard_normal((16, 16)))[0]
    A = B @ R.T  # A = B xoay -> adapter cần học R
    ad = LinearAdapter(lam=1e-3).fit(A, B)
    assert np.mean(np.sum(ad.transform(A) * B, axis=1)) > 0.99
    ad.save(tmp_path / "a.npz"); ad2 = LinearAdapter.load(tmp_path / "a.npz")
    assert np.allclose(ad2.W, ad.W)


def test_adapter_large_lambda_is_identity():
    rng = np.random.default_rng(1)
    A = rng.standard_normal((50, 8)); B = rng.standard_normal((50, 8))
    ad = LinearAdapter(lam=1e9).fit(A, B)
    assert np.allclose(ad.W, np.eye(8), atol=1e-4)
