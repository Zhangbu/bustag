from datetime import datetime
import configparser
from bustag import util


def test_file_path():
    """测试文件路径获取"""
    file = 'bus.db'
    path = util.get_data_path(file)
    print(f'Data path: {path}')


def test_read_config():
    """测试读取配置"""
    util.load_config()
    print(f'Config: {util.APP_CONFIG}')


def test_to_localtime():
    """测试时间转换"""
    t = datetime.utcnow()
    local = util.to_localtime(t)
    print(f'Local time: {local}')


def test_testing_mode():
    """测试测试模式"""
    import os
    print(f'env TESTING: {os.getenv("TESTING")}')
    # 测试模式下 TESTING 应该为 True
    assert util.TESTING == True


def test_config_defaults():
    """测试配置默认值"""
    config_path = util.get_data_path(util.CONFIG_FILE)
    conf = configparser.ConfigParser()
    defaults = {
        'options': {
            'proxy': 'http://localhost:7890'
        },
        'download': {
            'count': 100,
            'interval': 3600
        }
    }
    conf.read_dict(defaults)
    conf.read(config_path)
    for section in conf:
        print(f'[{section}]')
        for key, value in conf[section].items():
            print(f'{key} = {value}')
        print('')
    print(f'download.count: {conf.get("download", "count")}')
    print(f'download.interval: {conf.get("download", "interval")}')
    print(f'options.proxy: {conf.get("options", "proxy")}')