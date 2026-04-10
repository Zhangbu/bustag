import asyncio
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from bustag.app.tasks import task_queue
from bustag.spider.crawler import async_download
from bustag.spider.sources import get_source
from bustag.util import APP_CONFIG, logger

scheduler = None


async def async_download_wrapper(urls: list, count: int, no_parse_links: bool = False):
    """Async wrapper for download"""
    source = get_source()
    router = source.router
    try:
        concurrency = max(1, int(APP_CONFIG.get('download.concurrency', 3)))
    except (TypeError, ValueError):
        concurrency = 3
    if urls:
        router.set_base_url(urls[0])
    await async_download(
        urls,
        count,
        no_parse_links,
        router=router,
        fetcher=source.fetch,
        url_normalizer=source.normalize_url,
        concurrency=concurrency,
    )


def _download_and_recommend(urls: list[str], count: int, no_parse_links: bool = False):
    """Worker task: crawl urls then run recommendation."""
    asyncio.run(async_download_wrapper(urls, count, no_parse_links))

    import bustag.model.classifier as clf

    try:
        recommend_result = clf.recommend()
    except FileNotFoundError:
        logger.warning('Model not ready; skip recommend after download')
        recommend_result = None

    return {
        'downloaded_urls': len(urls),
        'count': count,
        'no_parse_links': no_parse_links,
        'recommend_result': recommend_result,
    }


def _submit_download_task(urls: list[str], count: int, no_parse_links: bool, task_name: str) -> str:
    task_id = task_queue.submit(task_name, _download_and_recommend, urls, count, no_parse_links)
    logger.info('Submitted task %s: %s, urls=%s, count=%s', task_id, task_name, len(urls), count)
    return task_id


def download(loop=None, no_parse_links=False, urls=None):
    """
    下载更新数据（通过后台任务执行）

    Args:
        urls: tuple of urls
    """
    if not urls:
        logger.warning('no links to download')
        return None

    count = int(APP_CONFIG.get('download.count', 100))
    if no_parse_links:
        count = len(urls)

    try:
        return _submit_download_task(list(urls), count, no_parse_links, task_name='scheduled_download')
    except Exception as exc:
        logger.error('Download task submit error: %s', exc)
        return None


def start_scheduler():
    global scheduler

    if scheduler is not None:
        return

    interval = int(APP_CONFIG.get('download.interval', 1800))
    scheduler = BackgroundScheduler()
    t1 = datetime.now() + timedelta(seconds=1)
    int_trigger = IntervalTrigger(seconds=interval)
    date_trigger = DateTrigger(run_date=t1)
    urls = (APP_CONFIG['download.root_path'],)
    scheduler.add_job(download, trigger=date_trigger, args=(None, False, urls))
    scheduler.add_job(download, trigger=int_trigger, args=(None, False, urls))
    scheduler.start()


def add_download_job(urls):
    add_job(download, (urls,))


def add_job(job_func, args):
    """add a one-shot job to scheduler"""
    global scheduler
    if scheduler is None:
        start_scheduler()
    default_args = (None, True)
    default_args = default_args + args
    logger.debug(default_args)
    t1 = datetime.now() + timedelta(seconds=10)
    date_trigger = DateTrigger(run_date=t1)
    scheduler.add_job(job_func, trigger=date_trigger, args=default_args)


def fetch_data(start_page=1, end_page=1, max_count=100):
    """
    手动拉取数据（提交后台任务）

    Returns:
        dict: 包含提交结果与任务ID
    """
    root_url = APP_CONFIG.get('download.root_path')
    if not root_url:
        logger.error('No root URL configured')
        return {'success': False, 'message': '未配置根URL'}

    start_page = max(1, start_page)
    source = get_source()
    end_page = min(source.max_page, end_page)
    if start_page > end_page:
        start_page, end_page = end_page, start_page

    max_count = max(1, min(1000, max_count))

    source.configure(root_url)
    urls = source.build_page_urls(start_page, end_page)

    logger.info('开始手动拉取数据: 页数 %s-%s, 最大条数 %s', start_page, end_page, max_count)

    try:
        task_id = _submit_download_task(urls, max_count, False, task_name='manual_fetch')
        message = f'已提交后台拉取任务: 页数 {start_page}-{end_page}, 最大条数 {max_count}, 任务ID: {task_id}'
        return {'success': True, 'message': message, 'task_id': task_id}
    except Exception as exc:
        error_msg = f'拉取数据失败: {str(exc)}'
        logger.error(error_msg)
        return {'success': False, 'message': error_msg}


def get_task_info(task_id: str):
    """Get task status for UI/API polling."""
    return task_queue.get(task_id)
