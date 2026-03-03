'''
Modern async crawler using aiohttp (replaces aspider)
'''
import asyncio
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


# Global router instance
_router: Optional[Router] = None


def get_router() -> Router:
    """Get or create global router instance"""
    global _router
    if _router is None:
        _router = Router()
    return _router


class Crawler:
    """Async web crawler using aiohttp"""

    def __init__(self, router: Router, max_count: int = 100, no_parse_links: bool = False):
        self.router = router
        self.max_count = max_count
        self.no_parse_links = no_parse_links
        self.processed_count = 0
        self.seen_urls: set[str] = set()
        self.urls_to_process: list[str] = []

    def _get_full_url(self, path: str) -> str:
        """Convert path to full URL"""
        if path.startswith('http'):
            return path
        return urljoin(self.router.base_url, path)

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract all links from HTML"""
        links = []
        try:
            soup = BeautifulSoup(html, 'lxml')
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(base_url, href)
                # Only keep same-domain links
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    links.append(full_url)
        except Exception as e:
            logger.warning(f"Error extracting links: {e}")
        return links

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch URL content"""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {url}")
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
        return None

    def _match_route(self, path: str) -> tuple[Optional[Route], Optional[dict]]:
        """Find matching route for path"""
        for route in self.routes:
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
        if url in self.seen_urls:
            return
        self.seen_urls.add(url)

        if self.processed_count >= self.max_count:
            return

        path = self.router.get_url_path(url)
        route, params = self._match_route(path)

        if route is None:
            return

        html = await self._fetch(session, url)
        if html is None:
            return

        self.processed_count += 1

        try:
            await route.handler(html, path, **params) if asyncio.iscoroutinefunction(route.handler) else route.handler(html, path, **params)
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")

        # Extract and queue more links if needed
        if not route.no_parse_links and not self.no_parse_links:
            links = self._extract_links(html, url)
            for link in links:
                if link not in self.seen_urls:
                    self.urls_to_process.append(link)

    async def crawl(self, start_urls: list[str]):
        """Start crawling from given URLs"""
        self.urls_to_process = list(start_urls)
        self.seen_urls.clear()
        self.processed_count = 0

        async with aiohttp.ClientSession() as session:
            while self.urls_to_process and self.processed_count < self.max_count:
                url = self.urls_to_process.pop(0)
                await self._process_url(session, url)


async def async_download(start_urls: list[str], max_count: int = 100, no_parse_links: bool = False):
    """Download and process URLs"""
    router = get_router()
    crawler = Crawler(router, max_count=max_count, no_parse_links=no_parse_links)
    await crawler.crawl(start_urls)


def download(loop: asyncio.AbstractEventLoop, options: dict):
    """Synchronous wrapper for download (compatible with old API)"""
    urls = options.get('roots', [])
    count = int(options.get('count', 100))
    no_parse_links = options.get('no_parse_links', False)

    # Set base URL from first URL
    router = get_router()
    if urls:
        router.set_base_url(urls[0])

    # Run async download
    asyncio.run(async_download(urls, count, no_parse_links))


def main():
    """Main entry point for CLI"""
    import sys
    from bustag.util import APP_CONFIG

    # Get root URL from config
    root_url = APP_CONFIG.get('download.root_path')
    if not root_url:
        logger.error("No root URL configured")
        return

    count = int(APP_CONFIG.get('download.count', 100))

    # Set base URL
    router = get_router()
    router.set_base_url(root_url)

    # Run crawler
    asyncio.run(async_download([root_url], count))