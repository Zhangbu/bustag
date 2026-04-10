from bustag.app import schedule


class _DummySource:
    max_page = 30

    def __init__(self):
        self.configured = None

    def configure(self, root_url):
        self.configured = root_url

    def build_page_urls(self, start_page, end_page):
        return [f'https://example.com/page/{page}' for page in range(start_page, end_page + 1)]

    @property
    def router(self):
        class _Router:
            def set_base_url(self, _):
                return None
        return _Router()

    fetch = None

    @staticmethod
    def normalize_url(url):
        return url


def test_fetch_data_submit_task(monkeypatch):
    monkeypatch.setitem(schedule.APP_CONFIG, 'download.root_path', 'https://example.com')
    monkeypatch.setattr(schedule, 'get_source', lambda: _DummySource())

    submitted = {}

    def fake_submit(urls, count, no_parse_links, task_name):
        submitted['urls'] = urls
        submitted['count'] = count
        submitted['no_parse_links'] = no_parse_links
        submitted['task_name'] = task_name
        return 'task-123'

    monkeypatch.setattr(schedule, '_submit_download_task', fake_submit)

    result = schedule.fetch_data(start_page=2, end_page=3, max_count=50)
    assert result['success'] is True
    assert result['task_id'] == 'task-123'
    assert submitted['task_name'] == 'manual_fetch'
    assert submitted['count'] == 50
    assert submitted['urls'] == ['https://example.com/page/2', 'https://example.com/page/3']


def test_download_submit_task(monkeypatch):
    monkeypatch.setitem(schedule.APP_CONFIG, 'download.count', '100')

    submitted = {}

    def fake_submit(urls, count, no_parse_links, task_name):
        submitted['urls'] = urls
        submitted['count'] = count
        submitted['no_parse_links'] = no_parse_links
        submitted['task_name'] = task_name
        return 'task-abc'

    monkeypatch.setattr(schedule, '_submit_download_task', fake_submit)

    task_id = schedule.download(urls=('https://example.com/page/1',), no_parse_links=False)
    assert task_id == 'task-abc'
    assert submitted['task_name'] == 'scheduled_download'
    assert submitted['count'] == 100
    assert submitted['urls'] == ['https://example.com/page/1']


def test_async_download_wrapper_uses_configured_concurrency(monkeypatch):
    monkeypatch.setitem(schedule.APP_CONFIG, 'download.concurrency', '2')
    monkeypatch.setattr(schedule, 'get_source', lambda: _DummySource())

    captured = {}

    async def fake_async_download(urls, count, no_parse_links=False, **kwargs):
        captured['urls'] = urls
        captured['count'] = count
        captured['no_parse_links'] = no_parse_links
        captured['concurrency'] = kwargs.get('concurrency')

    monkeypatch.setattr(schedule, 'async_download', fake_async_download)

    import asyncio
    asyncio.run(schedule.async_download_wrapper(['https://example.com/page/1'], 10, False))

    assert captured['urls'] == ['https://example.com/page/1']
    assert captured['count'] == 10
    assert captured['concurrency'] == 2
