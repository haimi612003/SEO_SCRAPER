"""Crawl URL và trích nội dung chính của bài viết.

Dùng trafilatura (chuyên trích nội dung chính, loại menu/quảng cáo/footer),
fallback sang BeautifulSoup nếu trafilatura thất bại.
"""
import random
import time

import requests

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

TIMEOUT = 15
MAX_RETRIES = 2


def _fetch(url: str) -> str:
    """Tải HTML, retry khi lỗi mạng."""
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                "Accept-Language": "vi,en;q=0.8",
            }, timeout=TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "xml" not in ctype and ctype:
                raise ValueError(f"Không phải trang HTML (Content-Type: {ctype})")
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding
            return resp.text
        except Exception as e:
            last_err = e
            if attempt < MAX_RETRIES:
                time.sleep(1 + attempt)
    raise last_err


def _extract_with_bs4(html: str) -> tuple[str, str]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]):
        tag.decompose()
    main = soup.find("article") or soup.find("main") or soup.body or soup
    text = main.get_text("\n", strip=True)
    lines = [ln for ln in text.splitlines() if len(ln.strip()) > 30]  # bỏ dòng vụn (menu, nút bấm)
    return title, "\n".join(lines)


def extract_article(url: str) -> tuple[str, str]:
    """Trả về (title, content). Ném exception nếu không tải được trang."""
    html = _fetch(url)

    title, content = "", ""
    try:
        import trafilatura
        content = trafilatura.extract(
            html, url=url,
            include_comments=False, include_tables=True,
            favor_recall=True,
        ) or ""
        meta = trafilatura.extract_metadata(html)
        if meta and meta.title:
            title = meta.title
    except Exception:
        pass

    if not content or len(content) < 100:
        bs_title, bs_content = _extract_with_bs4(html)
        title = title or bs_title
        if len(bs_content) > len(content):
            content = bs_content

    return title.strip(), content.strip()
