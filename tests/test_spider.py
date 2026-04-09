import pytest
from bustag.spider.bus_spider import process_item, router
from bustag.spider.sources import get_source, list_sources


@pytest.mark.skip(reason="需要网络访问外部网站")
def test_process_item():
    """测试处理项目 - 跳过因为需要访问外部网站"""
    pass


def test_router_exists():
    """测试路由器是否存在"""
    source = get_source('bus')
    assert source.router is not None
    print('Router created successfully')


def test_router_routes():
    """测试路由配置"""
    source = get_source('bus')
    router = source.router
    print(f'Number of routes: {len(router.routes)}')
    # 验证路由已注册
    assert len(router.routes) > 0


def test_source_registry():
    assert 'bus' in list_sources()


def test_source_build_urls():
    source = get_source('bus')
    source.configure('https://example.com/')
    urls = source.build_page_urls(1, 2)
    assert urls == ['https://example.com/page/1', 'https://example.com/page/2']
    assert source.get_item_url('ABC-123') == 'https://example.com/ABC-123'
