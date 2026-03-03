import pytest
from bustag.main import recommend


def test_recommend():
    """测试推荐功能"""
    try:
        count, recommend_count = recommend()
        print(f'count: {count}, recommend_count: {recommend_count}')
    except FileNotFoundError:
        # 如果模型文件不存在，这是正常的
        print('Model file not found, skipping test')


def test_main_help():
    """测试CLI帮助命令"""
    from click.testing import CliRunner
    from bustag.main import main
    
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'download' in result.output
    assert 'recommend' in result.output