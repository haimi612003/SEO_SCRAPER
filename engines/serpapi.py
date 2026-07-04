"""Google qua SerpAPI — ranking Google chính xác. Cần SERPAPI_KEY trong .env."""
import os

import requests

from .base import BaseEngine, SearchResult

API_URL = "https://serpapi.com/search.json"


class SerpApiEngine(BaseEngine):
    name = "serpapi"

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("Thiếu SERPAPI_KEY trong file .env (đăng ký tại https://serpapi.com)")

    def search(self, keyword: str, top_k: int, country: str = "vn", lang: str = "vi") -> list[SearchResult]:
        results = []
        start = 0
        while len(results) < top_k:
            num = min(top_k - len(results) + 2, 100)
            resp = requests.get(API_URL, params={
                "engine": "google",
                "q": keyword,
                "gl": country,
                "hl": lang,
                "num": num,
                "start": start,
                "api_key": self.api_key,
            }, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            organic = data.get("organic_results", [])
            if not organic:
                break
            for r in organic:
                if len(results) >= top_k:
                    break
                results.append(SearchResult(
                    rank=len(results) + 1,
                    url=r.get("link", ""),
                    title=r.get("title", ""),
                    snippet=r.get("snippet", ""),
                ))
            start += len(organic)
        return results
