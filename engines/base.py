"""Interface chung cho mọi search engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    rank: int
    url: str
    title: str
    snippet: str = ""


class BaseEngine(ABC):
    """Mọi engine đều implement search() với cùng signature."""

    name = "base"

    @abstractmethod
    def search(self, keyword: str, top_k: int, country: str = "vn", lang: str = "vi") -> list[SearchResult]:
        """Trả về tối đa top_k kết quả cho keyword."""
        raise NotImplementedError
