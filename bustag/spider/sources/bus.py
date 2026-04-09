"""
Default source adapter for bus-style sites.
"""
from __future__ import annotations

from urllib.parse import urljoin

from bustag.spider.db import Item, save
from bustag.spider.parser import parse_item
from bustag.spider.sources.base import SourceAdapter
from bustag.util import APP_CONFIG, logger


class BusSourceAdapter(SourceAdapter):
    def __init__(self):
        super().__init__(name='bus', max_page=30)
        self._register_routes()

    def get_item_url(self, fanhao: str) -> str:
        return urljoin(self._base_url(), fanhao)

    def build_page_urls(self, start_page: int, end_page: int) -> list[str]:
        base_url = self._base_url()
        return [urljoin(base_url, f'page/{page}') for page in range(start_page, end_page + 1)]

    def _register_routes(self):
        @self.router.route('/page/<no>', self.verify_page_path)
        def process_page(text, path, no):
            logger.debug(f'page {no} has length {len(text)}')
            print(f'process page {no}')

        @self.router.route(r'/<fanhao:[\w]+-[\d]+>', self.verify_fanhao, no_parse_links=True)
        def process_item(text, path, fanhao):
            logger.debug(f'process item {fanhao}')
            meta, tags = parse_item(text)
            meta.update(url=path)
            save(meta, tags)
            print(f'item {fanhao} is processed')

        self.process_page = process_page
        self.process_item = process_item

    def verify_page_path(self, path, no):
        logger.debug(f'verify page {path} , args {no}')
        return int(no) <= self.max_page

    def verify_fanhao(self, path, fanhao):
        exists = Item.get_by_fanhao(fanhao)
        logger.debug(f'verify {fanhao}: , exists:{exists is not None}, skip {path}')
        return exists is None

    def _base_url(self) -> str:
        return self.router.base_url or APP_CONFIG.get('download.root_path', '')
