import pytest
from bustag.spider.parser import parse_item


# Sample HTML for testing (避免网络依赖)
SAMPLE_HTML = '''
<html>
<head><title>DVAJ-419</title></head>
<body>
<div class="container">
    <h3>基本信息</h3>
    <span>番号: DVAJ-419</span>
    <span>标题: 测试标题</span>
    <span>发行日期: 2024-01-01</span>
    <span>时长: 120分钟</span>
    <h3>演员</h3>
    <a href="/star/1">演员A</a>
    <a href="/star/2">演员B</a>
    <h3>标签</h3>
    <a href="/tag/1">标签1</a>
    <a href="/tag/2">标签2</a>
</div>
</body>
</html>
'''


@pytest.fixture
def html():
    """返回测试HTML，避免网络依赖"""
    return SAMPLE_HTML


def test_process_item(html):
    """测试解析HTML页面"""
    print('')
    meta, tags = parse_item(html)
    print(f'meta: {meta}')
    print(f'tags: {tags}')
    assert meta is not None
    assert tags is not None
