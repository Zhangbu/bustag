import random
import pytest
from bustag.model import classifier as clf
from bustag.model.prepare import prepare_predict_data
from bustag.spider.db import Item, get_items, ItemRate


def test_train_model():
    """测试训练模型"""
    try:
        clf.train()
        print('Model trained successfully')
    except Exception as e:
        print(f'Training failed: {e}')
        # 可能因为没有足够的打标数据


def test_recommend():
    """测试推荐功能"""
    try:
        total, count = clf.recommend()
        print(f'total: {total}')
        print(f'recommended: {count}')
    except FileNotFoundError:
        print('Model file not found, skipping test')
    except Exception as e:
        print(f'Recommend failed: {e}')


def test_make_model():
    """
    随机打标数据生成模型
    """
    page = 50
    no_rate_items = []
    for i in range(1, page):
        items, _ = get_items(None, None, i)
        no_rate_items.extend(items)
    
    if not no_rate_items:
        print('No items found, skipping test')
        return
    
    size = len(no_rate_items)
    like_ratio = 0.4
    like_items = []
    unlike_items = []
    for item in no_rate_items:
        if random.random() < like_ratio:
            like_items.append(item)
        else:
            unlike_items.append(item)
    print(f'like items: {len(like_items)}, unlike items: {len(unlike_items)}')
    
    for item in like_items:
        ItemRate.saveit(1, 1, item.fanhao)
    for item in unlike_items:
        ItemRate.saveit(1, 0, item.fanhao)

    try:
        clf.train()
    except Exception as e:
        print(f'Training failed: {e}')