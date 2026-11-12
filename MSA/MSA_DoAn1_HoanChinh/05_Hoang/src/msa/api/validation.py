# repo: src/msa/api/validation.py
"""Kiểm tra ảnh tải lên (US_32 – Owner: Hoàng, Support: Tuấn Đạt).

Trả `ImageCheck(ok, code, message, image, ...)` – KHÔNG bao giờ raise với dữ liệu người dùng.
Mỗi lỗi có mã ổn định (để UI/test dựa vào) và thông điệp tiếng Việt rõ ràng.
"""
from __future__ import annotations

import io
import warnings
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageFile, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024
MIN_SIDE = 32           # ảnh catalog FPI là 60×80 nên ngưỡng tối thiểu phải ≤ 60
MAX_PIXELS = 40_000_000  # chống "decompression bomb"
MAX_ASPECT = 8.0
BLANK_STD = 4.0          # độ lệch chuẩn mức xám < ngưỡng → ảnh gần như một màu
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

MESSAGES = {
    "missing_file": "Bạn chưa gửi ảnh. Hãy chọn một ảnh JPG, PNG hoặc WEBP.",
    "empty_file": "Tệp ảnh rỗng (0 byte). Hãy chọn lại ảnh khác.",
    "too_large": "Ảnh vượt quá 5 MB. Hãy giảm kích thước hoặc chụp lại với độ phân giải thấp hơn.",
    "not_an_image": "Tệp tải lên không phải là ảnh. Hãy chọn tệp JPG, PNG hoặc WEBP.",
    "unsupported_format": "Định dạng ảnh {fmt} chưa được hỗ trợ. Hãy dùng JPG, PNG hoặc WEBP.",
    "corrupted": "Ảnh bị hỏng hoặc tải lên chưa trọn vẹn nên không đọc được. Hãy thử lại với ảnh khác.",
    "too_small": "Ảnh quá nhỏ ({w}×{h} px). Cần tối thiểu {m}×{m} px để nhận diện sản phẩm.",
    "too_many_pixels": "Ảnh có độ phân giải quá lớn ({w}×{h} px). Hãy thu nhỏ ảnh trước khi tải lên.",
    "bad_aspect": "Tỉ lệ khung hình ảnh bất thường ({w}×{h} px). Hãy chụp/cắt ảnh sao cho sản phẩm nằm gọn trong khung.",
    "blank_image": "Ảnh gần như chỉ có một màu, không thấy sản phẩm. Hãy chụp rõ món đồ bạn muốn tìm.",
    "not_product": "Chưa thấy sản phẩm giống trong cửa hàng (độ tương đồng thấp). Bạn có thể mô tả món đồ bằng chữ để tìm.",
}


@dataclass
class ImageCheck:
    ok: bool
    code: str = "ok"
    message: str = ""
    image: Image.Image | None = field(default=None, repr=False)
    width: int = 0
    height: int = 0
    format: str | None = None
    n_bytes: int = 0

    def as_error(self) -> dict:
        return {"code": self.code, "message": self.message}


def _fail(code: str, n: int = 0, **fmt) -> ImageCheck:
    return ImageCheck(ok=False, code=code, message=MESSAGES[code].format(**fmt), n_bytes=n)


def validate_image(data: bytes | None, filename: str | None = None, content_type: str | None = None) -> ImageCheck:
    """Kiểm tra theo thứ tự: tồn tại → rỗng → dung lượng → nhận dạng định dạng (theo nội dung, không tin đuôi file)
    → kích thước pixel → giải mã đầy đủ → tỉ lệ khung → ảnh trống."""
    if data is None:
        return _fail("missing_file")
    n = len(data)
    if n == 0:
        return _fail("empty_file")
    if n > MAX_BYTES:
        return _fail("too_large", n)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            probe = Image.open(io.BytesIO(data))
            fmt = probe.format
            w, h = probe.size
    except Image.DecompressionBombWarning:
        return _fail("too_many_pixels", n, w="?", h="?")
    except Image.DecompressionBombError:
        return _fail("too_many_pixels", n, w="?", h="?")
    except UnidentifiedImageError:
        return _fail("not_an_image", n)
    except Exception:
        return _fail("corrupted", n)
    if fmt not in ALLOWED_FORMATS:
        return _fail("unsupported_format", n, fmt=fmt or "không rõ")
    if w * h > MAX_PIXELS:
        return _fail("too_many_pixels", n, w=w, h=h)
    if min(w, h) < MIN_SIDE:
        return _fail("too_small", n, w=w, h=h, m=MIN_SIDE)
    if max(w, h) / min(w, h) > MAX_ASPECT:
        return _fail("bad_aspect", n, w=w, h=h)
    try:
        ImageFile.LOAD_TRUNCATED_IMAGES = False
        img = Image.open(io.BytesIO(data))
        img.load()  # giải mã toàn bộ – phát hiện ảnh bị cắt cụt
        img = img.convert("RGB")
    except Exception:
        return _fail("corrupted", n)
    gray = np.asarray(img.convert("L").resize((64, 64)), dtype=np.float32)
    if gray.std() < BLANK_STD:
        return _fail("blank_image", n)
    return ImageCheck(ok=True, code="ok", message="", image=img, width=w, height=h, format=fmt, n_bytes=n)
