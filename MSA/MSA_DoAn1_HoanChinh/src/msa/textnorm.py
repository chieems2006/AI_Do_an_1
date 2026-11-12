# repo: src/msa/textnorm.py
"""Chuẩn hoá văn bản tiếng Việt dùng chung cho taxonomy và router (bỏ dấu, teencode, viết tắt)."""
from __future__ import annotations

import re
import unicodedata

# Teencode / viết tắt hay gặp khi chat mua sắm (đã chuẩn hoá về dạng KHÔNG dấu).
TEENCODE: dict[str, str] = {
    "ko": "khong", "k": "khong", "kh": "khong", "hok": "khong", "hong": "khong", "khum": "khong", "hem": "khong",
    "dc": "duoc", "đc": "duoc", "dk": "duoc", "duoc": "duoc",
    "j": "gi", "ji": "gi", "z": "vay", "v": "vay", "zay": "vay", "zậy": "vay",
    "sp": "san pham", "sz": "size", "ad": "admin", "shop": "shop", "sh": "shop",
    "bn": "bao nhieu", "bnh": "bao nhieu", "bnhieu": "bao nhieu", "nhiu": "nhieu",
    "mn": "moi nguoi", "ntn": "nhu the nao", "r": "roi", "ok": "ok", "oke": "ok", "okela": "ok",
    # Không map chữ cái đơn a/b/e/m/t/s/l: dễ đụng size (S, M, L) và tên.
    "mik": "minh", "mk": "minh",
    "cx": "cung", "cg": "cung", "vs": "voi", "ns": "noi", "trc": "truoc", "ng": "nguoi",
    "hum": "hom", "nay": "nay", "hnay": "hom nay", "thik": "thich", "iu": "yeu", "bik": "biet", "bit": "biet",
    "tks": "cam on", "thanks": "cam on", "thank": "cam on", "thx": "cam on", "ty": "cam on",
    "hi": "chao", "hello": "chao", "helo": "chao", "alo": "chao",
    "ss": "so sanh", "sosanh": "so sanh", "vd": "vi du", "ib": "nhan tin",
    "tr": "trieu", "cu": "trieu",  # "1 củ" = 1 triệu (lóng)
}

_D_MAP = str.maketrans({"đ": "d", "Đ": "D"})


def strip_accents(s: str) -> str:
    """Bỏ dấu tiếng Việt: 'Giày cao gót' -> 'Giay cao got'."""
    s = s.translate(_D_MAP)
    s = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def normalize(text: str | None, expand_teencode: bool = True) -> str:
    """Chữ thường, bỏ dấu, bỏ ký tự lạ, mở rộng teencode. Trả chuỗi token cách nhau 1 dấu cách."""
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", text)  # gộp ký tự toán học kiểu 𝙇𝑨𝘿 về chữ thường
    s = strip_accents(s.lower())
    s = re.sub(r"\b(\d+)\s*k\b", r"\1 nghin", s)          # 500k -> 500 nghin
    s = re.sub(r"\b(\d+)\s*(tr|trieu)\b", r"\1 trieu", s)
    s = re.sub(r"[^a-z0-9%/.,\s-]", " ", s)
    s = re.sub(r"[.,/-]", " ", s)
    toks = s.split()
    if expand_teencode:
        toks = [TEENCODE.get(t, t) for t in toks]
    return " ".join(" ".join(toks).split())
