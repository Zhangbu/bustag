import importlib.util

from bustag.spider.parser_missav import extract_fanhao_from_slug, parse_item
from bustag.spider.sources import get_source, list_sources


SAMPLE_MISSAV_HTML = """
<html>
  <head>
    <title>ABP-1234 Sample Title - MissAV</title>
    <meta property="og:title" content="ABP-1234 Sample Title" />
    <meta property="og:image" content="https://static.example/abp-1234.jpg" />
    <meta property="og:video:duration" content="6000" />
  </head>
  <body>
    <h1>ABP-1234 Sample Title</h1>
    <div class="text-secondary">
      <span>Release date:</span>
      <time datetime="2025-01-31T10:00:00+08:00" class="font-medium">2025-01-31</time>
    </div>
    <div class="text-secondary">
      <span>Genre:</span>
      <a href="/en/genres/drama">Drama</a>
      <a href="/en/genres/featured">Featured</a>
    </div>
    <div class="text-secondary">
      <span>Actress:</span>
      <a href="/en/actresses/sample-actress">Sample Actress</a>
    </div>
    <div class="text-secondary">
      <span>Maker:</span>
      <a href="/en/makers/sample-maker">Sample Maker</a>
    </div>
  </body>
</html>
"""


def test_missav_source_registered():
    has_curl_cffi = importlib.util.find_spec('curl_cffi') is not None
    if has_curl_cffi:
        assert 'missav' in list_sources()
    else:
        assert 'missav' not in list_sources()


def test_missav_build_urls():
    source = get_source('missav')
    source.configure('https://missav.ai/')
    urls = source.build_page_urls(1, 3)
    assert urls[:5] == [
        'https://missav.ai/en',
        'https://missav.ai/en/new',
        'https://missav.ai/en/release?page=2',
        'https://missav.ai/sitemap.xml',
        'https://missav.ai/sitemap_pages.xml',
    ]
    assert 'https://missav.ai/en?page=2' in urls
    assert 'https://missav.ai/en/new?page=2' in urls
    assert source.get_item_url('ABP-1234') == 'https://missav.ai/en/abp-1234'


def test_normalize_missav_url():
    source = get_source('missav')
    assert source.normalize_url('https://missav.ws/sitemap_pages.xml') == 'https://missav.ai/sitemap_pages.xml'


def test_extract_fanhao_from_slug():
    assert extract_fanhao_from_slug('abp-1234') == 'ABP-1234'
    assert extract_fanhao_from_slug('genres') is None


def test_parse_missav_item():
    meta, tags = parse_item(SAMPLE_MISSAV_HTML)
    assert meta['fanhao'] == 'ABP-1234'
    assert meta['title'] == 'Sample Title'
    assert meta['release_date'] == '2025-01-31'
    assert meta['length'] == '100'
    assert meta['cover_img_url'] == 'https://static.example/abp-1234.jpg'
    assert {tag.type for tag in tags} == {'genre', 'star', 'maker'}
