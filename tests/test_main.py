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
