"""Google scraping trực tiếp — miễn phí nhưng có thể bị chặn/CAPTCHA.

Chỉ lấy rank + url từ Google (ranking chính xác). title/snippet lấy qua
DuckDuckGo bằng cách khớp url, vì HTML Google trả về thường không đủ tin cậy
để trích snippet (hay bị đổi layout / chặn một phần).

Chỉ nên dùng cho số lượng keyword nhỏ. Với công việc thường xuyên hãy dùng serpapi.
"""
import random
import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from .base import BaseEngine, SearchResult
from .duckduckgo import DuckDuckGoEngine

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def _normalize_url(url: str) -> str:
    """Chuẩn hoá url để so khớp giữa Google và DuckDuckGo (bỏ scheme, www, query, trailing slash)."""
    url = url.split("#")[0].split("?")[0]
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url.rstrip("/").lower()


class GoogleScrapeEngine(BaseEngine):
    name = "google"

    def search(self, keyword: str, top_k: int, country: str = "vn", lang: str = "vi") -> list[SearchResult]:
        ranked = self._search_rank_url(keyword, top_k, country, lang)
        if not ranked:
            return []

        # lấy title/snippet theo url từ DuckDuckGo
        try:
            ddg_results = DuckDuckGoEngine().search(keyword, max(top_k * 2, 20), country, lang)
        except Exception:
            ddg_results = []
        ddg_by_url = {_normalize_url(r.url): r for r in ddg_results}

        results = []
        for rank, href, google_title in ranked:
            match = ddg_by_url.get(_normalize_url(href))
            results.append(SearchResult(
                rank=rank,
                url=href,
                title=match.title if match else google_title,
                snippet=match.snippet if match else "",
            ))
        return results

    def _search_rank_url(self, keyword: str, top_k: int, country: str, lang: str) -> list[tuple[int, str, str]]:
        """Lấy danh sách (rank, url, title) theo đúng thứ tự ranking trên Google."""
        ranked: list[tuple[int, str, str]] = []
        seen_urls: set[str] = set()
        start = 0
        session = requests.Session()
        while len(ranked) < top_k and start < top_k + 20:
            params = {
                "q": keyword,
                "gl": country,
                "hl": lang,
                "num": min(top_k - len(ranked) + 5, 20),
                "start": start,
            }
            url = "https://www.google.com/search?" + urllib.parse.urlencode(params)
            resp = session.get(url, headers={
                "User-Agent": random.choice(USER_AGENTS),
                "Accept-Language": f"{lang},{lang}-{country.upper()};q=0.9,en;q=0.5",
            }, timeout=20)
            if resp.status_code == 429 or "captcha" in resp.text.lower()[:5000]:
                raise RuntimeError(
                    "Google đã chặn request (CAPTCHA/429). Hãy thử lại sau, hoặc dùng --engine serpapi/duckduckgo."
                )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            found_this_page = 0
            for block in soup.select("div.g, div[data-sokoban-container]"):
                a = block.find("a", href=True)
                h3 = block.find("h3")
                if not a or not h3:
                    continue
                href = a["href"]
                if not href.startswith("http") or "google.com" in href.split("/")[2]:
                    continue
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                ranked.append((len(ranked) + 1, href, h3.get_text(strip=True)))
                found_this_page += 1
                if len(ranked) >= top_k:
                    break

            if found_this_page == 0:
                break  # hết kết quả hoặc Google đổi layout
            start += 10
            time.sleep(random.uniform(2, 5))  # tránh bị chặn
        return ranked
