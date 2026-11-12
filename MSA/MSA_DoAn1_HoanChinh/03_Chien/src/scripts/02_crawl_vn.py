# repo: scripts/02_crawl_vn.py
"""US_07 – Crawler LỊCH SỰ, quy mô nhỏ cho trang sản phẩm sàn TMĐT Việt Nam.

Nguyên tắc (không thương lượng):
- Đọc robots.txt (urllib.robotparser) và kiểm `can_fetch` TRƯỚC MỖI URL; robots.txt không tải được (403/lỗi) ⇒ DỪNG
  (không coi là "được phép").
- Delay ≥ crawl-delay của robots (mặc định 3 s) + jitter ngẫu nhiên; giới hạn số trang (`--max-pages`).
- User-Agent nhận diện dự án học thuật, KHÔNG giả trình duyệt, KHÔNG xoay IP/proxy, KHÔNG vượt captcha/đăng nhập.
- Gặp 403/429/captcha ⇒ dừng hẳn (không retry né chặn).
- Lưu raw HTML-trích (JSONL) + log; parser tách riêng: HTML → dict theo schema 5.1 (dùng JSON-LD schema.org/Product
  và thẻ Open Graph – không phụ thuộc cấu trúc riêng của một sàn).
- Người chạy PHẢI tự đọc ToS của sàn và ghi vào docs/US_07_kiem_tra_robots_tos.md trước khi chạy thật.

Dùng:
    python src/scripts/02_crawl_vn.py --urls urls.txt --out data/raw/crawl_vn.jsonl --dry-run
    python src/scripts/02_crawl_vn.py --urls urls.txt --out data/raw/crawl_vn.jsonl --max-pages 50 --delay 5
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import re
import sys
import time
import urllib.robotparser
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

USER_AGENT = "MSA-DoAn1-StudentBot/0.1 (academic project; small-scale; respects robots.txt)"
DEFAULT_DELAY = 3.0
STOP_STATUSES = {401, 403, 429, 503}
CAPTCHA_RE = re.compile(r"captcha|verify you are human|xác minh bạn không phải", re.I)

log = logging.getLogger("crawl_vn")

# ------------------------------------------------------------------ robots

Fetcher = Callable[[str], tuple[int, str]]


def default_fetch(url: str, timeout: float = 20.0) -> tuple[int, str]:
    """GET đơn giản với UA dự án; trả (status, text)."""
    import httpx

    r = httpx.get(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "vi"}, timeout=timeout,
                  follow_redirects=True)
    return r.status_code, r.text


class RobotsGate:
    """Bộ nhớ robots.txt theo host. Không tải được robots ⇒ không cho phép."""

    def __init__(self, fetch: Fetcher = default_fetch, user_agent: str = USER_AGENT):
        self.fetch, self.ua = fetch, user_agent
        self.cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.evidence: dict[str, dict[str, Any]] = {}

    def _parser(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        u = urlparse(url)
        host = f"{u.scheme}://{u.netloc}"
        if host not in self.cache:
            robots_url = host + "/robots.txt"
            try:
                status, text = self.fetch(robots_url)
            except Exception as e:  # mạng lỗi
                status, text = -1, str(e)
            self.evidence[host] = {"robots_url": robots_url, "status": status, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                   "excerpt": text[:500] if status == 200 else ""}
            if status != 200:
                log.warning("robots.txt %s trả %s ⇒ KHÔNG crawl host này", robots_url, status)
                self.cache[host] = None
            else:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(text.splitlines())
                self.cache[host] = rp
        return self.cache[host]

    def allowed(self, url: str) -> bool:
        rp = self._parser(url)
        return bool(rp and rp.can_fetch(self.ua, url))

    def crawl_delay(self, url: str) -> float | None:
        rp = self._parser(url)
        if not rp:
            return None
        d = rp.crawl_delay(self.ua)
        return float(d) if d else None


# ------------------------------------------------------------------ parser (tách biệt)

def _jsonld_blocks(html: str) -> list[Any]:
    out = []
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            out.append(json.loads(m.group(1).strip()))
        except Exception:
            continue
    return out


def _find_product(obj: Any) -> dict | None:
    if isinstance(obj, dict):
        t = obj.get("@type")
        if t == "Product" or (isinstance(t, list) and "Product" in t):
            return obj
        for v in obj.values():
            p = _find_product(v)
            if p:
                return p
    elif isinstance(obj, list):
        for v in obj:
            p = _find_product(v)
            if p:
                return p
    return None


def _meta(html: str, prop: str) -> str | None:
    m = re.search(rf'<meta[^>]+(?:property|name)=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']*)["\']', html, re.I)
    return m.group(1) if m else None


def parse_product_html(html: str, url: str, source: str) -> dict | None:
    """HTML trang sản phẩm → dict theo schema 5.1 (các trường không có để None/[]). None nếu không nhận ra SP."""
    prod = None
    for blk in _jsonld_blocks(html):
        prod = _find_product(blk)
        if prod:
            break
    title = (prod or {}).get("name") or _meta(html, "og:title")
    if not title:
        return None
    offers = (prod or {}).get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price") or offers.get("lowPrice") or _meta(html, "product:price:amount")
    try:
        price = float(str(price).replace(",", "")) if price not in (None, "") else None
    except ValueError:
        price = None
    images = (prod or {}).get("image") or _meta(html, "og:image") or []
    if isinstance(images, str):
        images = [images]
    reviews = []
    for i, rv in enumerate((prod or {}).get("review") or []):
        if not isinstance(rv, dict):
            continue
        rating = (rv.get("reviewRating") or {}).get("ratingValue")
        reviews.append({"review_id": str(rv.get("@id") or i), "text": rv.get("reviewBody") or rv.get("description") or "",
                        "rating": float(rating) if rating not in (None, "") else None,
                        "date": rv.get("datePublished")})
    agg = (prod or {}).get("aggregateRating") or {}
    sku = (prod or {}).get("sku") or (prod or {}).get("productID") or re.sub(r"\W+", "_", urlparse(url).path)[-40:]
    return {
        "product_id": f"{source}_{sku}", "title": title.strip(), "category": (prod or {}).get("category"),
        "brand": ((prod or {}).get("brand") or {}).get("name") if isinstance((prod or {}).get("brand"), dict)
        else (prod or {}).get("brand"),
        "price": price, "currency": offers.get("priceCurrency") or ("VND" if price else None),
        "colors": [], "sizes": [], "description": (prod or {}).get("description") or _meta(html, "og:description"),
        "specs": {}, "image_paths": [], "image_urls": images, "rating": float(agg["ratingValue"]) if agg.get("ratingValue") else None,
        "rating_count": int(agg["reviewCount"]) if agg.get("reviewCount") else None, "reviews": reviews,
        "source": source, "source_url": url, "license": "chỉ dùng nội bộ học thuật – xem ToS nguồn",
        "product_type": "unknown", "sub_category": "unknown", "gender": None, "size_system": "none",
        "view_type": None, "variant_id": None, "language": "vi",
    }


# ------------------------------------------------------------------ crawl loop

def crawl(urls: list[str], out: Path, source: str, max_pages: int = 50, delay: float = DEFAULT_DELAY,
          dry_run: bool = False, fetch: Fetcher = default_fetch, sleep: Callable[[float], None] = time.sleep,
          gate: RobotsGate | None = None) -> dict[str, Any]:
    """Crawl tuần tự; trả thống kê. Dừng hẳn khi gặp 403/429/captcha."""
    gate = gate or RobotsGate(fetch)
    stats = {"checked": 0, "allowed": 0, "disallowed": 0, "fetched": 0, "parsed": 0, "stopped_reason": None,
             "dry_run": dry_run}
    out.parent.mkdir(parents=True, exist_ok=True)
    fout = None if dry_run else out.open("a", encoding="utf-8")
    try:
        for url in urls:
            if stats["fetched"] >= max_pages:
                stats["stopped_reason"] = "max_pages"
                break
            stats["checked"] += 1
            if not gate.allowed(url):
                stats["disallowed"] += 1
                log.info("robots KHÔNG cho phép / không đọc được: %s", url)
                continue
            stats["allowed"] += 1
            if dry_run:
                log.info("[dry-run] sẽ tải %s", url)
                continue
            wait = max(delay, gate.crawl_delay(url) or 0) + random.uniform(0, delay * 0.5)
            sleep(wait)
            status, html = fetch(url)
            stats["fetched"] += 1
            if status in STOP_STATUSES or CAPTCHA_RE.search(html or ""):
                stats["stopped_reason"] = f"blocked_status_{status}"
                log.error("Gặp %s tại %s ⇒ DỪNG (không né chặn)", status, url)
                break
            rec = parse_product_html(html, url, source) if status == 200 else None
            if rec:
                stats["parsed"] += 1
                fout.write(json.dumps({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": status,
                                       "record": rec}, ensure_ascii=False) + "\n")
    finally:
        if fout:
            fout.close()
    stats["robots_evidence"] = gate.evidence
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--urls", required=True, help="file text, mỗi dòng 1 URL trang sản phẩm")
    ap.add_argument("--out", default="data/raw/crawl_vn.jsonl")
    ap.add_argument("--source", default="vn_ecom")
    ap.add_argument("--max-pages", type=int, default=50)
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    ap.add_argument("--dry-run", action="store_true", help="chỉ kiểm robots, không tải trang")
    ap.add_argument("--log", default="logs/crawl_vn.log")
    a = ap.parse_args()
    Path(a.log).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(a.log, encoding="utf-8"), logging.StreamHandler()])
    urls = [u.strip() for u in Path(a.urls).read_text(encoding="utf-8").splitlines() if u.strip() and not u.startswith("#")]
    stats = crawl(urls, Path(a.out), a.source, a.max_pages, max(a.delay, 1.0), a.dry_run)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
