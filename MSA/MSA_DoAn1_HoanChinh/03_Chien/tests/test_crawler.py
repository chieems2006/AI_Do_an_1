"""Test crawler: robots.txt giả, parser HTML mẫu, dừng khi bị chặn, dry-run."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("crawl_vn", ROOT / "src" / "scripts" / "02_crawl_vn.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)

ROBOTS = "User-agent: *\nDisallow: /cart\nDisallow: /search\nCrawl-delay: 5\n"
HTML = """<html><head><meta property="og:title" content="Giày thể thao nam X">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Giày thể thao nam X",
"sku":"SKU42","brand":{"@type":"Brand","name":"ABC"},"description":"Đế cao su, vải lưới thoáng khí.",
"image":["https://img/1.jpg"],"offers":{"@type":"Offer","price":"350000","priceCurrency":"VND"},
"aggregateRating":{"ratingValue":"4.6","reviewCount":"12"},
"review":[{"@type":"Review","reviewBody":"Giày êm, đúng size","reviewRating":{"ratingValue":"5"}}]}</script>
</head><body></body></html>"""


def make_fetch(pages, robots_status=200):
    calls = []

    def fetch(url):
        calls.append(url)
        if url.endswith("/robots.txt"):
            return robots_status, ROBOTS if robots_status == 200 else "Forbidden"
        return pages.get(url, (404, ""))
    return fetch, calls


def test_user_agent_has_no_email_and_is_not_browser():
    assert "@" not in cv.USER_AGENT and "Mozilla" not in cv.USER_AGENT


def test_robots_gate_respects_disallow_and_delay():
    fetch, _ = make_fetch({})
    g = cv.RobotsGate(fetch)
    assert g.allowed("https://shop.vn/p/1")
    assert not g.allowed("https://shop.vn/cart/1")
    assert g.crawl_delay("https://shop.vn/p/1") == 5.0


def test_robots_403_means_not_allowed():
    fetch, calls = make_fetch({"https://tiki.vn/p": (200, HTML)}, robots_status=403)
    stats = cv.crawl(["https://tiki.vn/p"], Path("/tmp/_unused.jsonl"), "tiki", dry_run=False, fetch=fetch,
                     sleep=lambda s: None)
    assert stats["disallowed"] == 1 and stats["fetched"] == 0
    assert calls == ["https://tiki.vn/robots.txt"]  # không tải trang SP
    assert stats["robots_evidence"]["https://tiki.vn"]["status"] == 403


def test_parser_extracts_schema_fields():
    rec = cv.parse_product_html(HTML, "https://shop.vn/p/1", "shopvn")
    assert rec["title"] == "Giày thể thao nam X" and rec["price"] == 350000.0 and rec["currency"] == "VND"
    assert rec["brand"] == "ABC" and rec["rating"] == 4.6 and rec["rating_count"] == 12
    assert rec["reviews"][0]["text"] == "Giày êm, đúng size" and rec["product_id"] == "shopvn_SKU42"
    assert cv.parse_product_html("<html></html>", "u", "s") is None


def test_crawl_writes_raw_and_uses_delay(tmp_path):
    fetch, _ = make_fetch({"https://shop.vn/p/1": (200, HTML), "https://shop.vn/cart/2": (200, HTML)})
    waits = []
    out = tmp_path / "raw.jsonl"
    stats = cv.crawl(["https://shop.vn/p/1", "https://shop.vn/cart/2"], out, "shopvn", delay=1.0, fetch=fetch,
                     sleep=waits.append)
    assert stats["parsed"] == 1 and stats["disallowed"] == 1
    assert waits and waits[0] >= 5.0  # tôn trọng Crawl-delay
    assert json.loads(out.read_text(encoding="utf-8").splitlines()[0])["record"]["title"]


def test_crawl_stops_on_429_and_captcha(tmp_path):
    fetch, _ = make_fetch({"https://shop.vn/p/1": (429, ""), "https://shop.vn/p/2": (200, HTML)})
    stats = cv.crawl(["https://shop.vn/p/1", "https://shop.vn/p/2"], tmp_path / "r.jsonl", "s", fetch=fetch,
                     sleep=lambda s: None)
    assert stats["stopped_reason"] == "blocked_status_429" and stats["fetched"] == 1
    fetch2, _ = make_fetch({"https://shop.vn/p/1": (200, "<html>Please solve captcha</html>")})
    assert cv.crawl(["https://shop.vn/p/1"], tmp_path / "r2.jsonl", "s", fetch=fetch2,
                    sleep=lambda s: None)["stopped_reason"].startswith("blocked")


def test_dry_run_and_max_pages(tmp_path):
    fetch, calls = make_fetch({f"https://shop.vn/p/{i}": (200, HTML) for i in range(5)})
    s = cv.crawl([f"https://shop.vn/p/{i}" for i in range(5)], tmp_path / "d.jsonl", "s", dry_run=True, fetch=fetch,
                 sleep=lambda s: None)
    assert s["fetched"] == 0 and s["allowed"] == 5 and calls == ["https://shop.vn/robots.txt"]
    s2 = cv.crawl([f"https://shop.vn/p/{i}" for i in range(5)], tmp_path / "m.jsonl", "s", max_pages=2, fetch=fetch,
                  sleep=lambda s: None)
    assert s2["fetched"] == 2 and s2["stopped_reason"] == "max_pages"
