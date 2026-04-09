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
