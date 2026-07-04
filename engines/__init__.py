"""Registry các search engine."""
from .base import BaseEngine, SearchResult

ENGINES = {
    "serpapi": ("engines.serpapi", "SerpApiEngine"),
    "duckduckgo": ("engines.duckduckgo", "DuckDuckGoEngine"),
    "google": ("engines.google_scrape", "GoogleScrapeEngine"),
    "bing": ("engines.bing", "BingEngine"),
}


def get_engine(name: str) -> BaseEngine:
    name = name.lower().strip()
    if name not in ENGINES:
        raise ValueError(f"Engine không hợp lệ: '{name}'. Chọn một trong: {', '.join(ENGINES)}")
    module_name, class_name = ENGINES[name]
    import importlib
    module = importlib.import_module(module_name)
    return getattr(module, class_name)()
