import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from bustag.spider.crawler import async_download
from bustag.spider.sources import get_source
from bustag.util import logger, APP_CONFIG

scheduler = None


async def async_download_wrapper(urls: list, count: int, no_parse_links: bool = False):
    """Async wrapper for download"""
    source = get_source()
    router = source.router
    if urls:
        router.set_base_url(urls[0])
    await async_download(
        urls,
        count,
        no_parse_links,
        router=router,
        fetcher=source.fetch,
        url_normalizer=source.normalize_url,
    )


def download(loop=None, no_parse_links=False, urls=None):
    """
    下载更新数据

    Args:
        urls:tuple - tuple of urls
    """
    print('start download')
    if not urls:
        logger.warning('no links to download')
        return
    
    count = int(APP_CONFIG.get('download.count', 100))
    if no_parse_links:
        count = len(urls)

    try:
        # Run async download
        asyncio.run(async_download_wrapper(list(urls), count, no_parse_links))
        
        import bustag.model.classifier as clf
        clf.recommend()
    except FileNotFoundError:
        print('还没有训练好的模型, 无法推荐')
    except Exception as e:
        logger.error(f"Download error: {e}")


def start_scheduler():
    global scheduler

    interval = int(APP_CONFIG.get('download.interval', 1800))
    source = get_source()
    scheduler = BackgroundScheduler()
    t1 = datetime.now() + timedelta(seconds=1)
    int_trigger = IntervalTrigger(seconds=interval)
    date_trigger = DateTrigger(run_date=t1)
    urls = (APP_CONFIG['download.root_path'],)
    # add for down at server start
    scheduler.add_job(download, trigger=date_trigger, args=(None, False, urls))
    scheduler.add_job(download, trigger=int_trigger, args=(None, False, urls))
    scheduler.start()


def add_download_job(urls):
    add_job(download, (urls,))


def add_job(job_func, args):
    '''
    add a job to scheduler
    '''
    default_args = (None, True)
    default_args = default_args + args
    logger.debug(default_args)
    t1 = datetime.now() + timedelta(seconds=10)
    date_trigger = DateTrigger(run_date=t1)
    scheduler.add_job(job_func, trigger=date_trigger, args=default_args)


def fetch_data(start_page=1, end_page=1, max_count=100):
    '''
    手动拉取数据

    Args:
        start_page: 起始页码
        end_page: 结束页码
        max_count: 最大爬取条数

    Returns:
        dict: 包含爬取结果信息
    '''
    root_url = APP_CONFIG.get('download.root_path')
    if not root_url:
        logger.error("No root URL configured")
        return {'success': False, 'message': '未配置根URL'}

    # 限制页数范围
    start_page = max(1, start_page)
    source = get_source()
    end_page = min(source.max_page, end_page)
    if start_page > end_page:
        start_page, end_page = end_page, start_page

    # 限制最大条数
    max_count = max(1, min(1000, max_count))

    # 生成要爬取的页面URL列表
    source.configure(root_url)
    urls = source.build_page_urls(start_page, end_page)
    
    logger.info(f"开始手动拉取数据: 页数 {start_page}-{end_page}, 最大条数 {max_count}")

    try:
        # 运行爬虫
        asyncio.run(async_download_wrapper(urls, max_count))
        
        # 执行推荐
        import bustag.model.classifier as clf
        clf.recommend()
        
        message = f'成功拉取数据: 页数 {start_page}-{end_page}, 最大条数 {max_count}'
        logger.info(message)
        return {'success': True, 'message': message}
    except FileNotFoundError:
        msg = '还没有训练好的模型, 无法推荐'
        logger.warning(msg)
        return {'success': False, 'message': msg}
    except Exception as e:
        error_msg = f'拉取数据失败: {str(e)}'
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}
