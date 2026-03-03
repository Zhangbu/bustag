'''
entry point for command line 
'''

import click
from bustag.model.prepare import prepare_predict_data
from bustag.spider.db import Item, ItemRate, RATE_TYPE
import bustag.model.classifier as clf
from bustag.spider import bus_spider
from bustag.spider.crawler import main as crawler_main, async_download, get_router
from bustag.util import logger, APP_CONFIG
import asyncio


@click.command()
def recommend():
    '''
    根据现有模型预测推荐数据
    '''
    try:
        clf.recommend()
    except FileNotFoundError:
        click.echo('还没有训练好的模型, 无法推荐')


@click.command()
@click.option("--count", help="下载数量", type=int)
def download(count):
    """
    下载更新数据
    """
    print('start download')
    if count is not None:
        APP_CONFIG['download.count'] = count
    
    root_url = APP_CONFIG.get('download.root_path')
    if not root_url:
        logger.error("No root URL configured")
        return
    
    count_val = int(APP_CONFIG.get('download.count', 100))
    
    # Set base URL
    router = get_router()
    router.set_base_url(root_url)
    
    # Run crawler
    asyncio.run(async_download([root_url], count_val))


@click.group()
def main():
    pass


main.add_command(download)
main.add_command(recommend)

if __name__ == "__main__":
    main()