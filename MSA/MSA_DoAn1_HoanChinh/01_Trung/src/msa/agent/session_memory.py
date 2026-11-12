# repo: src/msa/agent/session_memory.py
"""US_42 (stretch) – Bộ nhớ hội thoại đơn giản: nhớ SP đang xem + kết quả gần nhất; hiểu 'đôi thứ 2', 'cái vừa tìm',
'2 đôi đầu', 'cái cuối'. Không dùng LLM; mỗi phiên là 1 dict (lưu trong RAM của API/UI)."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from msa.textnorm import normalize

_ORD_WORDS = {"nhat": 1, "dau": 1, "hai": 2, "ba": 3, "cuoi": -1}


def _ordinals(norm: str) -> list[int]:
    """Trích chỉ số thứ tự (1-based; -1 = cuối) từ câu đã chuẩn hoá."""
    out: list[int] = []
    for m in re.finditer(r"thu\s*(\d|nhat|hai|ba)|\b(\d)\s*(?:doi|cai|chiec|mau)?\s*dau(?: tien)?|\b(cuoi)\b|(?:doi|cai|chiec|mau) (dau) tien", norm):
        if m.group(2):  # "2 đôi đầu" -> 1..n
            out.extend(range(1, int(m.group(2)) + 1))
            continue
        g = m.group(1) or m.group(3) or m.group(4)
        if g:
            out.append(int(g) if g.isdigit() else _ORD_WORDS[g])
    return out


def resolve_product_ref(text: str, session: dict) -> str | None:
    """'đôi thứ 2' -> product_id thứ 2 trong last_results; 'cái vừa tìm' -> phần tử đầu; không có -> None."""
    last = list(session.get("last_results") or [])
    if not last:
        return None
    norm = normalize(text)
    o = _ordinals(norm)
    if o:
        i = o[0]
        if i == -1:
            return last[-1]
        return last[i - 1] if 0 < i <= len(last) else None
    if re.search(r"vua (tim|xem)", norm):
        return last[0]
    return None


def resolve_compare_refs(text: str, session: dict) -> list[str]:
    """'so sánh đôi vừa tìm với đôi thứ 2' -> [last[0], last[1]]; '3 cái vừa tìm' -> 3 phần tử đầu (tối đa 3)."""
    last = list(session.get("last_results") or [])
    if not last:
        return []
    norm = normalize(text)
    idx = _ordinals(norm)
    m = re.search(r"\b(\d)\s*(?:doi|cai|chiec|mau)(?:\s+[a-z]+)?\s+(?:vua|dau|tren)", norm)
    if m and not idx:
        idx = list(range(1, int(m.group(1)) + 1))
    if re.search(r"(doi|cai|chiec|mau) vua (tim|xem)", norm) and 1 not in idx:
        idx = [1] + idx
    ids = []
    for i in idx:
        if i == -1:
            ids.append(last[-1])
        elif 0 < i <= len(last):
            ids.append(last[i - 1])
    return list(dict.fromkeys(ids))[:3]


@dataclass
class SessionMemory:
    """Kho phiên trong RAM: session_id -> dict(current_product_id, last_results, clarify_count, history)."""
    ttl_s: int = 3600
    max_history: int = 10
    _store: dict[str, dict] = field(default_factory=dict)

    def get(self, session_id: str) -> dict:
        s = self._store.get(session_id)
        if s is None or time.time() - s.get("_ts", 0) > self.ttl_s:
            s = {"current_product_id": None, "last_results": [], "clarify_count": 0, "history": []}
            self._store[session_id] = s
        s["_ts"] = time.time()
        return s

    def record(self, session_id: str, user_text: str | None, resp: dict) -> None:
        """Cập nhật sau mỗi lượt: kết quả mới thay kết quả cũ; QA về SP nào thì SP đó thành 'đang xem'."""
        s = self.get(session_id)
        items = resp.get("items") or []
        if resp.get("route") in ("visual", "search") and items:
            s["last_results"] = [i["product_id"] for i in items]
        if resp.get("route") == "qa" and resp.get("product_id"):
            s["current_product_id"] = resp["product_id"]
        s["history"] = (s["history"] + [{"user": user_text, "route": resp.get("route")}])[-self.max_history:]
