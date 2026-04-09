"""
Base classes for pluggable crawl sources.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from bustag.spider.crawler import Router


@dataclass
class SourceAdapter:
    name: str
    router: Router = field(default_factory=Router)
    max_page: int = 30

    def configure(self, base_url: str):
        self.router.set_base_url(base_url)

    def get_item_url(self, fanhao: str) -> str:
        raise NotImplementedError

    def build_page_urls(self, start_page: int, end_page: int) -> list[str]:
        raise NotImplementedError

    def normalize_urls(self, urls: Iterable[str]) -> list[str]:
        return list(urls)

    def normalize_url(self, url: str) -> str:
        return url

    def fetch(self, url: str) -> str | None:
        return None
