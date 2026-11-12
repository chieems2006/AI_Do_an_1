# repo: src/msa/embed/image_embedders.py
"""Registry các bộ trích embedding ảnh (US_19, US_22, US_29) – Owner: Khoa.

- `get_embedder(name)` trả về một `ImageEmbedder` (import lười: chỉ import torch/open_clip/
  transformers/timm khi thật sự cần).
- Mọi model dùng CHUNG một bước tiền xử lý hình học: chuyển RGB -> pad thành hình vuông nền
  trắng -> resize bicubic về độ phân giải đầu vào của model -> chuẩn hoá mean/std của model.
- Đầu ra luôn là `np.ndarray float32 (N, D)` đã L2-normalize.
- `DummyEmbedder` dùng cho test (không cần torch, chạy tức thì, tất định).
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence, Union

import numpy as np
from PIL import Image

ImageLike = Union[str, os.PathLike, Image.Image, bytes]

CLIP_MEAN = (0.48145466, 0.4578275, 0.40821073)
CLIP_STD = (0.26862954, 0.26130258, 0.27577711)
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
HALF = (0.5, 0.5, 0.5)

# name -> cấu hình. backend: open_clip | hf_clip | hf_dinov2 | timm
REGISTRY: dict[str, dict] = {
    "resnet50": dict(backend="timm", model_id="resnet50.tv2_in1k", size=224, mean=IMAGENET_MEAN,
                     std=IMAGENET_STD, text=False, display="ResNet-50 (ImageNet-1K, torchvision V2 weights qua timm)"),
    "clip_b32": dict(backend="open_clip", arch="ViT-B-32-quickgelu", pretrained="openai", size=224, mean=CLIP_MEAN,
                     std=CLIP_STD, text=True, display="CLIP ViT-B/32 (OpenAI)"),
    "clip_b16": dict(backend="open_clip", arch="ViT-B-16-quickgelu", pretrained="openai", size=224, mean=CLIP_MEAN,
                     std=CLIP_STD, text=True, display="CLIP ViT-B/16 (OpenAI)"),
    "openclip_b32_laion2b": dict(backend="open_clip", arch="ViT-B-32", pretrained="laion2b_s34b_b79k", size=224,
                                 mean=CLIP_MEAN, std=CLIP_STD, text=True, display="OpenCLIP ViT-B/32 LAION-2B"),
    "siglip_b16": dict(backend="open_clip", arch="ViT-B-16-SigLIP", pretrained="webli", size=224, mean=HALF,
                       std=HALF, text=True, display="SigLIP ViT-B/16-224 (WebLI)"),
    "fashionclip": dict(backend="hf_clip", model_id="patrickjohncyh/fashion-clip", size=224, mean=CLIP_MEAN,
                        std=CLIP_STD, text=True, display="FashionCLIP (patrickjohncyh/fashion-clip)"),
    "marqo_fashionsiglip": dict(backend="open_clip", arch="hf-hub:Marqo/marqo-fashionSigLIP", pretrained=None,
                                size=224, mean=HALF, std=HALF, text=True, display="Marqo-FashionSigLIP"),
    "dinov2_s": dict(backend="hf_dinov2", model_id="facebook/dinov2-small", size=224, mean=IMAGENET_MEAN,
                     std=IMAGENET_STD, text=False, display="DINOv2 ViT-S/14 (CLS token)"),
}


def set_threads(n: int = 2) -> None:
    """Giới hạn số luồng CPU (máy dùng chung 2 CPU)."""
    os.environ.setdefault("OMP_NUM_THREADS", str(n))
    try:
        import torch

        torch.set_num_threads(n)
    except Exception:  # torch không có -> bỏ qua
        pass


def load_image(img: ImageLike) -> Image.Image:
    """Đọc ảnh từ đường dẫn / bytes / PIL và chuyển RGB."""
    if isinstance(img, Image.Image):
        return img.convert("RGB")
    if isinstance(img, (bytes, bytearray)):
        import io

        return Image.open(io.BytesIO(img)).convert("RGB")
    return Image.open(img).convert("RGB")


def pad_to_square(im: Image.Image, fill=(255, 255, 255)) -> Image.Image:
    """Pad ảnh thành hình vuông bằng nền trắng (giữ nguyên tỉ lệ vật thể)."""
    w, h = im.size
    if w == h:
        return im
    s = max(w, h)
    canvas = Image.new("RGB", (s, s), fill)
    canvas.paste(im, ((s - w) // 2, (s - h) // 2))
    return canvas


def common_preprocess(img: ImageLike, size: int) -> Image.Image:
    """Tiền xử lý hình học DÙNG CHUNG cho mọi model: RGB -> pad vuông nền trắng -> resize bicubic."""
    im = pad_to_square(load_image(img))
    return im.resize((size, size), Image.BICUBIC)


def l2n(x: np.ndarray) -> np.ndarray:
    """L2-normalize theo hàng."""
    x = np.asarray(x, dtype=np.float32)
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.clip(n, 1e-12, None)


class ImageEmbedder:
    """Giao diện chung: `embed(images) -> (N, D)` L2-normalized; `embed_text(texts)` nếu có text tower."""

    name: str = "base"
    dim: int = 0
    has_text: bool = False

    def embed(self, images: Sequence[ImageLike], batch_size: int = 32) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError

    def embed_text(self, texts: Sequence[str]) -> np.ndarray:  # pragma: no cover
        raise NotImplementedError(f"{self.name} không có text tower")

    def info(self) -> dict:
        return {"name": self.name, "dim": self.dim, "has_text": self.has_text}


class DummyEmbedder(ImageEmbedder):
    """Embedder giả, tất định, không cần torch: thumbnail 8x8 màu + phép chiếu ngẫu nhiên cố định.

    Ảnh giống nhau -> vector giống nhau; dùng cho unit test.
    """

    def __init__(self, dim: int = 64, seed: int = 0):
        self.name = "dummy"
        self.dim = dim
        self.has_text = True
        rng = np.random.default_rng(seed)
        self._proj = rng.standard_normal((8 * 8 * 3, dim)).astype(np.float32)

    def embed(self, images: Sequence[ImageLike], batch_size: int = 32) -> np.ndarray:
        feats = []
        for img in images:
            im = common_preprocess(img, 32).resize((8, 8), Image.BILINEAR)
            a = np.asarray(im, dtype=np.float32).reshape(-1) / 255.0
            feats.append(a - a.mean())
        if not feats:
            return np.zeros((0, self.dim), dtype=np.float32)
        return l2n(np.stack(feats) @ self._proj)

    def embed_text(self, texts: Sequence[str]) -> np.ndarray:
        out = []
        for t in texts:
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest()[:8], 16)
            out.append(np.random.default_rng(h).standard_normal(self.dim))
        return l2n(np.stack(out))


class TorchEmbedder(ImageEmbedder):
    """Bọc các backend torch (open_clip / transformers CLIP / DINOv2 / timm)."""

    def __init__(self, name: str, cfg: dict, device: str = "cpu", threads: int = 2, precision: str | None = None):
        set_threads(threads)
        import torch

        # fp32 (mặc định) hoặc bf16 (autocast CPU – nhanh hơn nhiều trên CPU có AMX/AVX512-BF16)
        self.precision = precision or os.environ.get("MSA_PRECISION", "fp32")

        self.torch = torch
        self.name = name
        self.cfg = cfg
        self.device = device
        self.size = cfg["size"]
        self.has_text = bool(cfg.get("text"))
        self._tok = None
        b = cfg["backend"]
        if b == "open_clip":
            import open_clip

            if cfg["arch"].startswith("hf-hub:"):
                model, _, pre = open_clip.create_model_and_transforms(cfg["arch"])
                self._tok = open_clip.get_tokenizer(cfg["arch"])
            else:
                model, _, pre = open_clip.create_model_and_transforms(cfg["arch"], pretrained=cfg["pretrained"])
                self._tok = open_clip.get_tokenizer(cfg["arch"])
            # lấy mean/std/size thật từ cấu hình model nếu có
            pcfg = getattr(model.visual, "preprocess_cfg", None) or {}
            if pcfg.get("mean"):
                self.cfg = {**cfg, "mean": tuple(pcfg["mean"]), "std": tuple(pcfg["std"])}
            isz = pcfg.get("size") or getattr(model.visual, "image_size", None)
            if isz:
                self.size = int(isz[0] if isinstance(isz, (tuple, list)) else isz)
            self._img_fn = lambda x: model.encode_image(x)
            self._txt_fn = lambda t: model.encode_text(t)
        elif b == "hf_clip":
            from transformers import CLIPModel, CLIPTokenizer

            model = CLIPModel.from_pretrained(cfg["model_id"])
            self._tok = CLIPTokenizer.from_pretrained(cfg["model_id"])
            self._img_fn = lambda x: _as_tensor(model.get_image_features(pixel_values=x))
            self._txt_fn = lambda t: _as_tensor(model.get_text_features(**t))
        elif b == "hf_dinov2":
            from transformers import AutoModel

            model = AutoModel.from_pretrained(cfg["model_id"])
            self._img_fn = lambda x: model(pixel_values=x).last_hidden_state[:, 0]
        elif b == "timm":
            import timm

            model = timm.create_model(cfg["model_id"], pretrained=True, num_classes=0)
            self._img_fn = lambda x: model(x)
        else:
            raise ValueError(f"backend lạ: {b}")
        model.eval().to(device)
        self.model = model
        self.n_params = int(sum(p.numel() for p in model.parameters()))
        self.n_params_visual = int(sum(p.numel() for p in self._visual_params()))
        self._mean = torch.tensor(self.cfg["mean"]).view(1, 3, 1, 1)
        self._std = torch.tensor(self.cfg["std"]).view(1, 3, 1, 1)
        with torch.no_grad():
            self.dim = int(self._img_fn(self._to_batch([Image.new("RGB", (8, 8), "white")])).shape[-1])

    def _visual_params(self):
        m = self.model
        for attr in ("visual", "vision_model"):
            if hasattr(m, attr):
                ps = list(getattr(m, attr).parameters())
                if attr == "vision_model" and hasattr(m, "visual_projection"):
                    ps += list(m.visual_projection.parameters())
                return ps
        return list(m.parameters())

    def _to_batch(self, images: Sequence[ImageLike]):
        torch = self.torch
        arr = np.stack([np.asarray(common_preprocess(im, self.size), dtype=np.float32) / 255.0 for im in images])
        x = torch.from_numpy(arr).permute(0, 3, 1, 2)
        return ((x - self._mean) / self._std).to(self.device)

    def embed(self, images: Sequence[ImageLike], batch_size: int = 32) -> np.ndarray:
        torch = self.torch
        out = []
        images = list(images)
        with torch.inference_mode(), torch.autocast("cpu", dtype=torch.bfloat16, enabled=self.precision == "bf16"):
            for i in range(0, len(images), batch_size):
                out.append(self._img_fn(self._to_batch(images[i : i + batch_size])).float().cpu().numpy())
        if not out:
            return np.zeros((0, self.dim), dtype=np.float32)
        return l2n(np.concatenate(out))

    def embed_text(self, texts: Sequence[str]) -> np.ndarray:
        if not self.has_text:
            raise NotImplementedError(f"{self.name} không có text tower")
        torch = self.torch
        with torch.inference_mode(), torch.autocast("cpu", dtype=torch.bfloat16, enabled=self.precision == "bf16"):
            if self.cfg["backend"] == "hf_clip":
                t = self._tok(list(texts), padding=True, return_tensors="pt")
            else:
                t = self._tok(list(texts))
            return l2n(self._txt_fn(t).float().cpu().numpy())

    def info(self) -> dict:
        return {"name": self.name, "dim": self.dim, "has_text": self.has_text, "input_size": self.size,
                "mean": list(self.cfg["mean"]), "std": list(self.cfg["std"]), "n_params_total": self.n_params,
                "n_params_visual": self.n_params_visual, "display": self.cfg.get("display", self.name),
                "precision": self.precision}


def _as_tensor(o):
    """transformers mới có thể trả về ModelOutput thay vì tensor."""
    if hasattr(o, "pooler_output") and o.pooler_output is not None:
        return o.pooler_output
    if hasattr(o, "image_embeds"):
        return o.image_embeds
    if hasattr(o, "text_embeds"):
        return o.text_embeds
    return o


def get_embedder(name: str, **kw) -> ImageEmbedder:
    """Trả về embedder theo tên trong REGISTRY, hoặc 'dummy'."""
    if name == "dummy":
        return DummyEmbedder(**kw)
    if name not in REGISTRY:
        raise KeyError(f"Không có model '{name}'. Có: {['dummy', *REGISTRY]}")
    return TorchEmbedder(name, REGISTRY[name], **kw)


def available_models() -> list[str]:
    return list(REGISTRY)
