"""
MissAV source adapter prototype.
"""
from __future__ import annotations

from urllib.parse import urlencode, urljoin, urlparse, urlunparse

from curl_cffi import requests as curl_requests

from bustag.spider.db import Item, save
from bustag.spider.parser_missav import extract_fanhao_from_slug, parse_item
from bustag.spider.sources.base import SourceAdapter
from bustag.util import APP_CONFIG, logger


class MissAVSourceAdapter(SourceAdapter):
    def __init__(self):
        super().__init__(name='missav', max_page=1000)
        self._register_routes()

    def get_item_url(self, fanhao: str) -> str:
        slug = fanhao.strip().lower()
        return urljoin(self._base_url(), f'{self.language}/{slug}')

    def build_page_urls(self, start_page: int, end_page: int) -> list[str]:
        urls = []
        for page in range(start_page, end_page + 1):
            urls.extend(self._page_seed_urls(page))
        deduped = []
        seen = set()
        for url in urls:
            normalized = self.normalize_url(url)
            if normalized not in seen:
                seen.add(normalized)
                deduped.append(normalized)
        return deduped

    def fetch(self, url: str) -> str | None:
        options = {
            'timeout': 30,
            'impersonate': APP_CONFIG.get('missav.browser', 'chrome124'),
            'headers': {
                'User-Agent': APP_CONFIG.get('missav.user_agent', 'Mozilla/5.0'),
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': self._base_url(),
            },
        }
        proxy = APP_CONFIG.get('missav.proxy')
        if proxy:
            options['proxies'] = {'https': proxy, 'http': proxy}
        cookie = APP_CONFIG.get('missav.cookie')
        if cookie:
            options['headers']['Cookie'] = cookie

        response = curl_requests.get(url, **options)
        if response.status_code != 200:
            raise RuntimeError(
                f'MissAV HTTP {response.status_code} for {url}. '
                '站点可能触发了 Cloudflare，必要时请在 [missav] 里配置 proxy/cookie。'
            )
        if 'Just a moment...' in response.text or 'Enable JavaScript and cookies to continue' in response.text:
            raise RuntimeError(
                f'MissAV Cloudflare challenge for {url}. '
                '请尝试在 [missav] 配置浏览器拿到的 cf_clearance cookie。'
            )
        return response.text

    def _register_routes(self):
        @self.router.route('/<lang>', self.verify_home_path)
        def process_home(text, path, lang):
            logger.debug(f'missav home {path} has length {len(text)}')

        @self.router.route('/<lang>/<section>', self.verify_simple_listing_path)
        def process_simple_listing(text, path, lang, section):
            logger.debug(f'missav simple listing {path} has length {len(text)}')

        @self.router.route('/<catalog>/<lang>/<section>', self.verify_catalog_listing_path)
        def process_catalog_listing(text, path, catalog, lang, section):
            logger.debug(f'missav catalog listing {path} has length {len(text)}')

        @self.router.route('/sitemap.xml')
        def process_sitemap_index(text, path):
            logger.debug(f'missav sitemap index {path} has length {len(text)}')

        @self.router.route('/sitemap_<name>.xml')
        def process_sitemap_file(text, path, name):
            logger.debug(f'missav sitemap file {path} has length {len(text)}')

        @self.router.route('/<lang>/<slug>', self.verify_item_path, no_parse_links=True)
        def process_item(text, path, lang, slug):
            logger.debug(f'missav process item {slug}')
            meta, tags = parse_item(text)
            meta.update(url=path)
            save(meta, tags)

        self.process_page = process_simple_listing
        self.process_item = process_item
        self.process_home = process_home

    def verify_home_path(self, path, lang):
        return lang == self.language

    def verify_simple_listing_path(self, path, lang, section):
        valid_sections = {'new', 'release', 'popular'}
        return lang == self.language and section in valid_sections

    def verify_catalog_listing_path(self, path, catalog, lang, section):
        valid_sections = {
            'new',
            'release',
            'popular',
            'weekly-hot',
            'monthly-hot',
            'today-hot',
            'english-subtitle',
            'uncensored-leak',
        }
        return catalog.startswith('dm') and lang == self.language and section in valid_sections

    def verify_item_path(self, path, lang, slug):
        if lang != self.language:
            return False
        fanhao = extract_fanhao_from_slug(slug)
        if fanhao is None:
            return False
        exists = Item.get_by_fanhao(fanhao)
        logger.debug(f'verify missav {fanhao}: exists={exists is not None}, skip {path}')
        return exists is None

    @property
    def language(self) -> str:
        return APP_CONFIG.get('missav.language', 'en')

    def _base_url(self) -> str:
        return self.router.base_url or APP_CONFIG.get('download.root_path', '')

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        if not parsed.netloc:
            return url
        normalized = parsed._replace(netloc='missav.ai' if parsed.netloc == 'missav.ws' else parsed.netloc)
        return urlunparse(normalized)

    def _page_seed_urls(self, page: int) -> list[str]:
        base_url = self._base_url()
        lang = self.language
        if page == 1:
            return [
                urljoin(base_url, f'{lang}'),
                urljoin(base_url, f'{lang}/new'),
                urljoin(base_url, f'{lang}/release?page=2'),
                urljoin(base_url, 'sitemap.xml'),
                urljoin(base_url, 'sitemap_pages.xml'),
            ]
        return [
            urljoin(base_url, f'{lang}?{urlencode({"page": page})}'),
            urljoin(base_url, f'{lang}/new?{urlencode({"page": page})}'),
            urljoin(base_url, f'{lang}/release?{urlencode({"page": page + 1})}'),
        ]
