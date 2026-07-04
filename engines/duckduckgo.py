"""DuckDuckGo — miễn phí, không cần API key. Dùng thư viện ddgs."""
from .base import BaseEngine, SearchResult

# Map country/lang -> region code của DuckDuckGo
REGION_MAP = {
    ("vn", "vi"): "vn-vi",
    ("us", "en"): "us-en",
    ("gb", "en"): "uk-en",
    ("jp", "ja"): "jp-jp",
    ("kr", "ko"): "kr-kr",
    ("cn", "zh"): "cn-zh",
    ("fr", "fr"): "fr-fr",
    ("de", "de"): "de-de",
}


class DuckDuckGoEngine(BaseEngine):
    name = "duckduckgo"

    def search(self, keyword: str, top_k: int, country: str = "vn", lang: str = "vi") -> list[SearchResult]:
        region = REGION_MAP.get((country.lower(), lang.lower()), f"{country.lower()}-{lang.lower()}")
        try:
            return self._search_ddgs(keyword, top_k, region)
        except ImportError:
            # thư viện ddgs chưa cài -> fallback endpoint HTML (chỉ cần requests + bs4)
            return self._search_html(keyword, top_k, region)

    def _search_ddgs(self, keyword: str, top_k: int, region: str) -> list[SearchResult]:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # tên cũ của thư viện

        results = []
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.text(keyword, region=region, max_results=top_k), start=1):
                results.append(SearchResult(
                    rank=i,
                    url=r.get("href") or r.get("link", ""),
                    title=r.get("title", ""),
                    snippet=r.get("body", ""),
                ))
                if len(results) >= top_k:
                    break
        return results

    def _search_html(self, keyword: str, top_k: int, region: str) -> list[SearchResult]:
        import urllib.parse

        import requests
        from bs4 import BeautifulSoup

        results = []
        params = {"q": keyword, "kl": region}
        offset = 0
        while len(results) < top_k:
            if offset:
                params["s"] = offset
            resp = requests.post("https://html.duckduckgo.com/html/", data=params, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            }, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("div.result")
            if not items:
                break
            for item in items:
                if len(results) >= top_k:
                    break
                a = item.select_one("a.result__a")
                if not a or not a.get("href"):
                    continue
                href = a["href"]
                # DDG bọc link dạng //duckduckgo.com/l/?uddg=<url-encoded>
                if "uddg=" in href:
                    href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                if not href.startswith("http"):
                    continue
                snippet_el = item.select_one("a.result__snippet, div.result__snippet")
                results.append(SearchResult(
                    rank=len(results) + 1,
                    url=href,
                    title=a.get_text(strip=True),
                    snippet=snippet_el.get_text(" ", strip=True) if snippet_el else "",
                ))
            offset += 30
        return results
