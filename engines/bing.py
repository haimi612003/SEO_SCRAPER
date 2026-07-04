"""Bing Web Search API — cần BING_API_KEY trong .env."""
import os

import requests

from .base import BaseEngine, SearchResult

API_URL = "https://api.bing.microsoft.com/v7.0/search"


class BingEngine(BaseEngine):
    name = "bing"

    def __init__(self):
        self.api_key = os.getenv("BING_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("Thiếu BING_API_KEY trong file .env (đăng ký tại Azure Portal)")

    def search(self, keyword: str, top_k: int, country: str = "vn", lang: str = "vi") -> list[SearchResult]:
        results = []
        offset = 0
        mkt = f"{lang.lower()}-{country.upper()}"  # ví dụ vi-VN, en-US
        while len(results) < top_k:
            count = min(top_k - len(results), 50)
            resp = requests.get(API_URL, params={
                "q": keyword,
                "mkt": mkt,
                "count": count,
                "offset": offset,
            }, headers={"Ocp-Apim-Subscription-Key": self.api_key}, timeout=30)
            resp.raise_for_status()
            pages = resp.json().get("webPages", {}).get("value", [])
            if not pages:
                break
            for r in pages:
                if len(results) >= top_k:
                    break
                results.append(SearchResult(
                    rank=len(results) + 1,
                    url=r.get("url", ""),
                    title=r.get("name", ""),
                    snippet=r.get("snippet", ""),
                ))
            offset += len(pages)
        return results
