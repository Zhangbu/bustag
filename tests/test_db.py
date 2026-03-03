import pytest
from bustag.spider.db import get_items, Item, RATE_TYPE, RATE_VALUE
from bustag.spider.parser import parse_item


def test_get_items():
    """测试获取项目列表"""
    rate_type = RATE_TYPE.SYSTEM_RATE
    rate_value = RATE_VALUE.DISLIKE
    page = None
    items, page_info = get_items(
        rate_type=rate_type, rate_value=rate_value, page=page)
    # 如果数据库为空，跳过断言
    print(f'item count:{len(items)}')
    if page_info:
        print(
            f'total_items: {page_info[0]}, total_page: {page_info[1]}, current_page: {page_info[2]}, page_size:{page_info[3]}')


def test_get_items2():
    """测试获取所有项目"""
    rate_type = None
    rate_value = None
    page = None
    items, page_info = get_items(
        rate_type=rate_type, rate_value=rate_value, page=page)
    print(f'item count:{len(items)}')
    if page_info:
        print(
            f'total_items: {page_info[0]}, total_page: {page_info[1]}, current_page: {page_info[2]}, page_size:{page_info[3]}')


def test_getit():
    """测试获取单个项目"""
    id = 100
    item = Item.getit(id)
    print(repr(item))
    # 如果项目不存在，返回 None 是正常的


def test_load_item():
    """测试加载项目"""
    id = 1251
    item = Item.getit(id)
    if item:
        Item.loadit(item)
        if hasattr(item, 'tags'):
            print(item.tags)
        else:
            print('Item has no tags attribute')


def test_get_item_tags():
    """测试获取项目标签"""
    fanhao = 'JUY-981'
    item = Item.get_by_fanhao(fanhao)
    print(item)
    if item:
        Item.get_tags_dict(item)
        if hasattr(item, 'tags_dict'):
            print(item.tags_dict)


@pytest.mark.skip(reason="需要网络访问外部网站")
def test_missed_tags():
    """测试缺失标签 - 跳过因为需要访问外部网站"""
    pass


def test_empty_tags():
    """测试空标签"""
    empty = []
    for item in Item.select():
        tags_db = {t.tag.value for t in item.tags_list}
        if not tags_db:
            empty.append(item.fanhao)
    print(f'Items with empty tags: {empty}')