"""
Parser helpers for MissAV detail pages.
"""
from __future__ import annotations

import math
import re
from collections import namedtuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

Tag = namedtuple('Tag', ['type', 'value', 'link'])

RESERVED_SLUGS = {
    'actresses',
    'actors',
    'genres',
    'makers',
    'directors',
    'series',
    'search',
    'popular',
    'new',
    'release',
    'vip',
    'saved',
    'playlists',
    'history',
    'klive',
    'clive',
}

SECTION_TYPE_MAP = {
    'genre': 'genre',
    'actress': 'star',
    'actor': 'star',
    'series': 'series',
    'maker': 'maker',
    'label': 'label',
}


def parse_item(text: str):
    soup = BeautifulSoup(text, 'lxml')
    meta = _parse_meta(soup)
    tags = _parse_tags(soup)
    if meta is None:
        raise ValueError('Unable to parse MissAV item page')
    return meta, tags


def extract_fanhao_from_slug(slug: str) -> str | None:
    slug = slug.strip('/').split('/')[-1]
    if slug.lower() in RESERVED_SLUGS:
        return None
    match = re.search(r'([a-z]{2,10})-0*([0-9]{2,6}[a-z]?)', slug, re.IGNORECASE)
    if not match:
        return None
    prefix, number = match.groups()
    return f'{prefix.upper()}-{number.upper()}'


def _parse_meta(soup: BeautifulSoup) -> dict | None:
    title = _meta_content(soup, 'og:title') or _first_heading_text(soup) or ''
    page_text = soup.get_text('\n', strip=True)

    fanhao = _extract_fanhao_from_text(title) or _extract_fanhao_from_text(page_text)
    if fanhao is None:
        return None

    cleaned_title = _clean_title(title, fanhao)
    release_date = _extract_date(page_text)
    length = _extract_length(soup, page_text)
    cover_img_url = _meta_content(soup, 'og:image') or ''

    return {
        'fanhao': fanhao,
        'title': cleaned_title or fanhao,
        'cover_img_url': cover_img_url,
        'release_date': release_date or '1970-01-01',
        'length': length or '0',
    }


def _parse_tags(soup: BeautifulSoup) -> list[Tag]:
    tags: list[Tag] = []
    seen: set[tuple[str, str]] = set()

    for block in soup.select('div.text-secondary'):
        label_node = block.find('span')
        if label_node is None:
            continue
        label = label_node.get_text(' ', strip=True).rstrip(':').lower()
        tag_type = SECTION_TYPE_MAP.get(label)
        if tag_type is None:
            continue

        for link in block.find_all('a', href=True):
            value = link.get_text(' ', strip=True)
            href_path = urlparse(link['href']).path
            if not value or not href_path:
                continue
            key = (tag_type, value)
            if key in seen:
                continue
            seen.add(key)
            tags.append(Tag(tag_type, value, href_path))
    return tags


def _meta_content(soup: BeautifulSoup, property_name: str) -> str:
    node = soup.find('meta', attrs={'property': property_name})
    if node and node.get('content'):
        return node['content'].strip()
    return ''


def _first_heading_text(soup: BeautifulSoup) -> str:
    for selector in ('h1', 'h2', 'title'):
        node = soup.select_one(selector)
        if node:
            return node.get_text(' ', strip=True)
    return ''


def _extract_fanhao_from_text(text: str) -> str | None:
    match = re.search(r'([A-Z]{2,10})-0*([0-9]{2,6}[A-Z]?)', text, re.IGNORECASE)
    if not match:
        return None
    prefix, number = match.groups()
    return f'{prefix.upper()}-{number.upper()}'


def _clean_title(title: str, fanhao: str) -> str:
    title = re.sub(r'\s+', ' ', title).strip()
    if not title:
        return ''
    pattern = re.compile(rf'^\s*{re.escape(fanhao)}\s*', re.IGNORECASE)
    return pattern.sub('', title).strip(' -|')


def _extract_date(text: str) -> str:
    match = re.search(r'Release date\s*:?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return ''


def _extract_length(soup: BeautifulSoup, text: str) -> str:
    match = re.search(r'Length\s*:?\s*(\d+)', text, re.IGNORECASE)
    if match:
        return match.group(1)

    duration = _meta_content(soup, 'og:video:duration')
    if duration.isdigit():
        minutes = max(1, math.ceil(int(duration) / 60))
        return str(minutes)

    match = re.search(r'(\d+)\s*(?:min|minute|minutes)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    return ''
