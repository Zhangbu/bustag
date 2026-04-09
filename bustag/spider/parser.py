"""
HTML parser helpers for bustag.
"""
import re
from collections import namedtuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

Tag = namedtuple('Tag', ['type', 'value', 'link'])


def parse_item(text):
    """
    Parse item metadata and tags from a detail page.

    Supports both the current busjav-style layout and a simplified fallback
    structure used by tests.
    """
    soup = BeautifulSoup(text, 'lxml')
    meta, tags = _parse_busjav_layout(soup)
    if meta is None:
        meta, tags = _parse_fallback_layout(soup)
    if meta is None:
        raise ValueError('Unable to parse item page')
    return meta, tags


def _parse_busjav_layout(soup):
    title_node = soup.select_one('body > div.container > h3')
    cover_link = soup.select_one('body > div.container > div.row.movie > div.col-md-9.screencap > a')
    info_node = soup.select_one('body > div.container > div.row.movie > div.col-md-3.info')
    if not (title_node and cover_link and info_node):
        return None, None

    title_text = title_node.get_text(' ', strip=True)
    title_parts = title_text.split(maxsplit=1)
    if len(title_parts) != 2:
        return None, None

    tags = info_node.find_all('p')
    if len(tags) < 3:
        return None, None

    release_match = re.search(r'(\d{4}-\d{2}-\d{2})', tags[1].get_text(' ', strip=True))
    length_match = re.search(r'(\d+)', tags[2].get_text(' ', strip=True))
    if not (release_match and length_match):
        return None, None

    meta = {
        'fanhao': title_parts[0],
        'title': title_parts[1],
        'cover_img_url': cover_link.get('href', ''),
        'release_date': release_match.group(1),
        'length': length_match.group(1),
    }
    return meta, _extract_tag_list(tags[3:])


def _parse_fallback_layout(soup):
    text = soup.get_text('\n', strip=True)
    fanhao_match = re.search(r'番号[:：]\s*([A-Z]+-?\d+)', text, re.IGNORECASE)
    title_match = re.search(r'标题[:：]\s*(.+)', text)
    release_match = re.search(r'发行日期[:：]\s*(\d{4}-\d{2}-\d{2})', text)
    length_match = re.search(r'时长[:：]\s*(\d+)', text)
    if not (fanhao_match and title_match and release_match and length_match):
        return None, None

    meta = {
        'fanhao': _normalize_fanhao(fanhao_match.group(1)),
        'title': title_match.group(1).strip(),
        'cover_img_url': '',
        'release_date': release_match.group(1),
        'length': length_match.group(1),
    }

    tag_list = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        value = link.get_text(strip=True)
        if '/star/' in href:
            tag_list.append(create_tag('star', value, href))
        elif '/tag/' in href or '/genre/' in href:
            tag_list.append(create_tag('genre', value, href))
    return meta, tag_list


def _extract_tag_list(tag_nodes):
    tag_list = []
    for tag in tag_nodes:
        links = tag.find_all('a')
        spans = tag.find_all('span', class_='header')
        if spans and len(links) == 1:
            tag_type = spans[0].get_text(strip=True)
            tag_value = links[0].get_text(strip=True)
            tag_link = links[0].get('href', '')
            if tag_type and tag_value:
                tag_list.append(create_tag(tag_type, tag_value, tag_link))
            continue

        for link in links:
            tag_link = link.get('href', '')
            tag_value = link.get_text(strip=True)
            tag_type = ''
            if 'genre' in tag_link or '/tag/' in tag_link:
                tag_type = 'genre'
            if 'star' in tag_link:
                tag_type = 'star'
            if tag_type and tag_value:
                tag_list.append(create_tag(tag_type, tag_value, tag_link))
    return tag_list


def _normalize_fanhao(fanhao):
    match = re.search(r'([A-Z]+)-?(\d+)', fanhao.upper())
    if not match:
        return fanhao.upper()
    return f'{match.group(1)}-{match.group(2)}'


def create_tag(tag_type, tag_value, tag_link):
    tag_link = urlparse(tag_link).path
    return Tag(tag_type, tag_value, tag_link)
