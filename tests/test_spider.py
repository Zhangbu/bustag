import pytest
from bustag.spider.bus_spider import process_item, router


@pytest.mark.skip(reason="需要网络访问外部网站")
def test_process_item():
    """测试处理项目 - 跳过因为需要访问外部网站"""
    pass


def test_router_exists():
    """测试路由器是否存在"""
    from bustag.spider.crawler import get_router
    router = get_router()
    assert router is not None
    print('Router created successfully')


def test_router_routes():
    """测试路由配置"""
    from bustag.spider.crawler import get_router
    from bustag.spider import bus_spider
    
    router = get_router()
    print(f'Number of routes: {len(router.routes)}')
    # 验证路由已注册
    assert len(router.routes) > 0