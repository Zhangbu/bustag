'''
Modern async crawler using aiohttp (replaces aspider)
'''
import asyncio
from collections import deque
import re
from typing import Callable, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from bustag.util import logger


class Route:
    """Route definition for URL matching"""

    def __init__(self, pattern: str, handler: Callable, verify_func: Optional[Callable] = None, no_parse_links: bool = False):
        self.pattern = pattern
        self.handler = handler
        self.verify_func = verify_func
        self.no_parse_links = no_parse_links
        # Convert pattern to regex
        self.regex = self._pattern_to_regex(pattern)

    def _pattern_to_regex(self, pattern: str) -> re.Pattern:
        """Convert route pattern to regex"""
        # Replace <param> with named groups
        regex_pattern = re.sub(r'<(\w+)(?::([^>]+))?>', r'(?P<\1>[^/]+)', pattern)
        regex_pattern = f'^{regex_pattern}$'
        return re.compile(regex_pattern)

    def match(self, path: str) -> Optional[dict]:
        """Check if path matches this route"""
        match = self.regex.match(path)
        if match:
            return match.groupdict()
        return None


class Router:
    """URL router for handling different paths"""

    def __init__(self):
        self.routes: list[Route] = []
        self.base_url: str = ''

    def route(self, pattern: str, verify_func: Optional[Callable] = None, no_parse_links: bool = False):
        """Decorator to register a route handler"""
        def decorator(func: Callable):
            route = Route(pattern, func, verify_func, no_parse_links)
            self.routes.append(route)
            return func
        return decorator

    def get_url_path(self, url: str) -> str:
        """Extract path from URL"""
        parsed = urlparse(url)
        return parsed.path

    def set_base_url(self, url: str):
        """Set base URL for resolving relative URLs"""
        self.base_url = url


_default_router: Optional[Router] = None


def get_router() -> Router:
    """Get or create a default router for backward compatibility."""
    global _default_router
    if _default_router is None:
        _default_router = Router()
    return _default_router


class Crawler:
    """Async web crawler using aiohttp"""

    def __init__(
        self,
        router: Router,
        max_count: int = 100,
        no_parse_links: bool = False,
        concurrency: int = 5,
        fetcher: Optional[Callable] = None,
        url_normalizer: Optional[Callable[[str], str]] = None,
    ):
        self.router = router
        self.max_count = max_count
        self.no_parse_links = no_parse_links
        self.concurrency = max(1, concurrency)
        self.fetcher = fetcher
        self.url_normalizer = url_normalizer
        self.processed_count = 0
        self.seen_urls: set[str] = set()
        self.urls_to_process: deque[str] = deque()
        self._lock = asyncio.Lock()

    def _get_full_url(self, path: str) -> str:
        """Convert path to full URL"""
        if path.startswith('http'):
            return path
        return urljoin(self.router.base_url, path)

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract all links from HTML"""
        links = []
        try:
            parser = 'xml' if '<loc>' in html or html.lstrip().startswith('<?xml') else 'lxml'
            soup = BeautifulSoup(html, parser)
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = self._normalize_url(urljoin(base_url, href))
                if self._is_same_domain(full_url, base_url):
                    links.append(full_url)
            for loc_tag in soup.find_all('loc'):
                loc = loc_tag.get_text(strip=True)
                if not loc:
                    continue
                full_url = self._normalize_url(loc)
                if self._is_same_domain(full_url, base_url):
                    links.append(full_url)
        except Exception as e:
            logger.warning(f"Error extracting links: {e}")
        return links

    def _normalize_url(self, url: str) -> str:
        if self.url_normalizer is None:
            return url
        return self.url_normalizer(url)

    def _is_same_domain(self, url: str, base_url: str) -> bool:
        return urlparse(url).netloc == urlparse(self._normalize_url(base_url)).netloc

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch URL content"""
        if self.fetcher is not None:
            try:
                if asyncio.iscoroutinefunction(self.fetcher):
                    return await self.fetcher(url)
                return await asyncio.to_thread(self.fetcher, url)
            except RuntimeError as e:
                logger.warning(str(e))
                return None
            except Exception as e:
                logger.warning(f"Custom fetcher error for {url}: {e}")
                return None
        headers = {'User-Agent': 'bustag/0.3 (+https://github.com/gxtrobot/bustag)'}
        for attempt in range(1, 4):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30), headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    logger.warning(f"HTTP {response.status} for {url}")
                    if response.status in {403, 404}:
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}, attempt {attempt}")
            except Exception as e:
                logger.warning(f"Error fetching {url}, attempt {attempt}: {e}")
            await asyncio.sleep(min(attempt, 3))
        return None

    def _match_route(self, path: str) -> tuple[Optional[Route], Optional[dict]]:
        """Find matching route for path"""
        for route in self.router.routes:
            params = route.match(path)
            if params is not None:
                if route.verify_func is not None:
                    try:
                        if not route.verify_func(path, **params):
                            continue
                    except Exception as e:
                        logger.debug(f"Verify function error: {e}")
                        continue
                return route, params
        return None, None

    async def _process_url(self, session: aiohttp.ClientSession, url: str):
        """Process a single URL"""
        url = self._normalize_url(url)
        async with self._lock:
            if url in self.seen_urls or self.processed_count >= self.max_count:
                return
            self.seen_urls.add(url)

        path = self.router.get_url_path(url)
        route, params = self._match_route(path)

        if route is None:
            return

        html = await self._fetch(session, url)
        if html is None:
            return

        async with self._lock:
            self.processed_count += 1

        try:
            await route.handler(html, path, **params) if asyncio.iscoroutinefunction(route.handler) else route.handler(html, path, **params)
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

        # Extract and queue more links if needed
        if not route.no_parse_links and not self.no_parse_links:
            links = self._extract_links(html, url)
            async with self._lock:
                for link in links:
                    if link not in self.seen_urls:
                        self.urls_to_process.append(link)

    async def _worker(self, session: aiohttp.ClientSession):
        while True:
            async with self._lock:
                if not self.urls_to_process or self.processed_count >= self.max_count:
                    return
                url = self.urls_to_process.popleft()
            await self._process_url(session, url)

    async def crawl(self, start_urls: list[str]):
        """Start crawling from given URLs"""
        self.urls_to_process = deque(self._normalize_url(url) for url in start_urls)
        self.seen_urls.clear()
        self.processed_count = 0

        async with aiohttp.ClientSession() as session:
            workers = [asyncio.create_task(self._worker(session)) for _ in range(self.concurrency)]
            await asyncio.gather(*workers)


async def async_download(
    start_urls: list[str],
    max_count: int = 100,
    no_parse_links: bool = False,
    router: Optional[Router] = None,
    fetcher: Optional[Callable] = None,
    url_normalizer: Optional[Callable[[str], str]] = None,
):
    """Download and process URLs"""
    router = router or get_router()
    crawler = Crawler(
        router,
        max_count=max_count,
        no_parse_links=no_parse_links,
        fetcher=fetcher,
        url_normalizer=url_normalizer,
    )
    await crawler.crawl(start_urls)


def download(loop: asyncio.AbstractEventLoop, options: dict):
    """Synchronous wrapper for download (compatible with old API)"""
    urls = options.get('roots', [])
    count = int(options.get('count', 100))
    no_parse_links = options.get('no_parse_links', False)

    # Set base URL from first URL
    router = options.get('router') or get_router()
    if urls:
        router.set_base_url(urls[0])

    # Run async download
    asyncio.run(
        async_download(
            urls,
            count,
            no_parse_links,
            router=router,
            fetcher=options.get('fetcher'),
            url_normalizer=options.get('url_normalizer'),
        )
    )


def main():
    """Main entry point for CLI"""
    import sys
    from bustag.util import APP_CONFIG
    from bustag.spider.sources import get_source

    # Get root URL from config
    root_url = APP_CONFIG.get('download.root_path')
    if not root_url:
        logger.error("No root URL configured")
        return

    count = int(APP_CONFIG.get('download.count', 100))

    # Set base URL
    source = get_source()
    router = source.router
    router.set_base_url(root_url)

    # Run crawler
    asyncio.run(
        async_download(
            [root_url],
            count,
            router=router,
            fetcher=source.fetch,
            url_normalizer=source.normalize_url,
        )
    )
