import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from bustag.spider import bus_spider
from bustag.spider.crawler import async_download, get_router
from bustag.util import logger, APP_CONFIG

scheduler = None


async def async_download_wrapper(urls: list, count: int, no_parse_links: bool = False):
    """Async wrapper for download"""
    router = get_router()
    if urls:
        router.set_base_url(urls[0])
    await async_download(urls, count, no_parse_links)


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
    scheduler = AsyncIOScheduler()
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