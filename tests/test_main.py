import pytest
from click.testing import CliRunner

pytest.importorskip('sklearn')

from bustag.main import main


def test_recommend_command_runs():
    """测试 recommend CLI 命令可执行"""
    runner = CliRunner()
    result = runner.invoke(main, ['recommend'])
    # 没有模型时允许提示后成功退出；异常退出应被视为失败
    assert result.exit_code == 0


def test_main_help():
    """测试CLI帮助命令"""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'download' in result.output
    assert 'recommend' in result.output
    assert 'migrate' in result.output
    assert 'migrate-status' in result.output
    assert 'serve-api' in result.output
    assert 'serve-web' in result.output


def test_serve_web_bottle(monkeypatch):
    runner = CliRunner()
    called = {}

    from bustag import main as main_module

    def fake_bottle(host, port, start_background_scheduler):
        called['stack'] = 'bottle'
        called['host'] = host
        called['port'] = port
        called['scheduler'] = start_background_scheduler

    monkeypatch.setattr(main_module, '_serve_bottle_web', fake_bottle)

    result = runner.invoke(
        main_module.main,
        ['serve-web', '--stack', 'bottle', '--host', '127.0.0.1', '--port', '9001', '--no-start-background-scheduler'],
    )

    assert result.exit_code == 0
    assert called == {
        'stack': 'bottle',
        'host': '127.0.0.1',
        'port': 9001,
        'scheduler': False,
    }


def test_serve_web_fastapi(monkeypatch):
    runner = CliRunner()
    called = {}

    from bustag import main as main_module

    def fake_fastapi(host, port, reload, start_background_scheduler):
        called['stack'] = 'fastapi'
        called['host'] = host
        called['port'] = port
        called['reload'] = reload
        called['scheduler'] = start_background_scheduler

    monkeypatch.setattr(main_module, '_serve_fastapi_web', fake_fastapi)

    result = runner.invoke(
        main_module.main,
        ['serve-web', '--stack', 'fastapi', '--host', '127.0.0.1', '--port', '9002', '--reload'],
    )

    assert result.exit_code == 0
    assert called == {
        'stack': 'fastapi',
        'host': '127.0.0.1',
        'port': 9002,
        'reload': True,
        'scheduler': False,
    }


def test_download_uses_source_seed_urls(monkeypatch):
    runner = CliRunner()
    called = {}

    from bustag import main as main_module

    class _DummySource:
        def __init__(self):
            self.router = object()
            self.fetch = object()
            self.normalize_url = lambda u: u
            self.configured = None

        def configure(self, root_url):
            self.configured = root_url

        def build_page_urls(self, start_page, end_page):
            assert (start_page, end_page) == (1, 1)
            return ['https://missav.ai/en', 'https://missav.ai/en/new']

    dummy_source = _DummySource()

    monkeypatch.setitem(main_module.APP_CONFIG, 'download.root_path', 'https://missav.ai/')
    monkeypatch.setitem(main_module.APP_CONFIG, 'download.count', '100')
    monkeypatch.setattr(main_module, '_ensure_db_ready', lambda: None)
    monkeypatch.setattr(main_module, 'get_source', lambda: dummy_source)

    async def fake_async_download(start_urls, count, router=None, fetcher=None, url_normalizer=None, concurrency=None):
        called['start_urls'] = start_urls
        called['count'] = count
        called['router'] = router
        called['fetcher'] = fetcher
        called['url_normalizer'] = url_normalizer
        called['concurrency'] = concurrency

    monkeypatch.setattr(main_module, 'async_download', fake_async_download)

    result = runner.invoke(main_module.main, ['download'])
    assert result.exit_code == 0
    assert called['start_urls'] == ['https://missav.ai/en', 'https://missav.ai/en/new']
    assert called['count'] == 100
    assert called['concurrency'] == 3


def test_download_fallback_to_root_when_seed_empty(monkeypatch):
    runner = CliRunner()
    called = {}

    from bustag import main as main_module

    class _DummySource:
        def __init__(self):
            self.router = object()
            self.fetch = object()
            self.normalize_url = lambda u: u
            self.configured = None

        def configure(self, root_url):
            self.configured = root_url

        def build_page_urls(self, start_page, end_page):
            return []

    dummy_source = _DummySource()
    root_url = 'https://example.com/root'

    monkeypatch.setitem(main_module.APP_CONFIG, 'download.root_path', root_url)
    monkeypatch.setitem(main_module.APP_CONFIG, 'download.count', '100')
    monkeypatch.setattr(main_module, '_ensure_db_ready', lambda: None)
    monkeypatch.setattr(main_module, 'get_source', lambda: dummy_source)

    async def fake_async_download(start_urls, count, router=None, fetcher=None, url_normalizer=None, concurrency=None):
        called['start_urls'] = start_urls
        called['count'] = count
        called['concurrency'] = concurrency

    monkeypatch.setattr(main_module, 'async_download', fake_async_download)

    result = runner.invoke(main_module.main, ['download'])
    assert result.exit_code == 0
    assert called['start_urls'] == [root_url]
    assert called['count'] == 100
    assert called['concurrency'] == 3
