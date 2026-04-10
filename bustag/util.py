import logging
import os
import sys
import configparser
import pytz
import datetime
from urllib.parse import urljoin

logger = logging.getLogger('bustag')
TESTING = False
DATA_PATH = 'data/'
CONFIG_FILE = 'config.ini'
MODEL_PATH = 'model/'
APP_CONFIG = {}
DEFAULT_CONFIG = {
    'download': {
        'source': 'missav',
        'count': 100,
        'interval': 3600
    },
    'missav': {
        'language': 'en',
        'list_path': '/en',
        'proxy': '',
        'browser': 'chrome136',
        'user_agent': 'Mozilla/5.0',
        'cookie': '',
        'probe_url': '',
    },
    'auth': {
        'secret_key': '',
        'admin_username': 'admin',
        'admin_password': ''
    }
}
_initialized = False


def get_cwd():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.getcwd()


def check_testing():
    global TESTING
    if os.environ.get('TESTING'):
        TESTING = True
        print('*** in test mode ***')


def setup_logging():
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s \n %(message)s '
    formatter = logging.Formatter(fmt)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    logger.setLevel(logging.WARNING)
    if TESTING:
        logger.setLevel(logging.DEBUG)
        pw_logger = logging.getLogger('peewee')
        if not pw_logger.handlers:
            pw_logger.addHandler(logging.StreamHandler())
        pw_logger.setLevel(logging.DEBUG)


def get_data_path(file):
    cwd = get_cwd()
    file_path = os.path.join(cwd, DATA_PATH, file)
    return file_path


def get_now_time():
    return datetime.datetime.now()


def get_full_url(path):
    root_path = APP_CONFIG['download.root_path']
    full_url = urljoin(root_path, path)
    return full_url


def check_config():
    config_path = get_data_path(CONFIG_FILE)
    abs_path = os.path.abspath(config_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(
            f'配置文件不存在: {abs_path}. 请先创建 data/config.ini'
        )


def load_config():
    check_config()
    config_path = get_data_path(CONFIG_FILE)
    conf = configparser.ConfigParser()
    conf.read_dict(DEFAULT_CONFIG)
    conf.read(config_path)
    APP_CONFIG.clear()
    for section in conf.sections():
        APP_CONFIG[section.lower()] = dict(conf[section])
        for key in conf.options(section):
            value = conf.get(section, key)
            key = section + '.' + key
            APP_CONFIG[key.lower()] = value
    env_secret = os.environ.get('BUSTAG_SECRET_KEY')
    if env_secret:
        APP_CONFIG['auth.secret_key'] = env_secret
    env_admin_password = os.environ.get('BUSTAG_ADMIN_PASSWORD')
    if env_admin_password:
        APP_CONFIG['auth.admin_password'] = env_admin_password
    env_missav_cookie = os.environ.get('BUSTAG_MISSAV_COOKIE')
    if env_missav_cookie is not None:
        APP_CONFIG['missav.cookie'] = env_missav_cookie
    env_missav_proxy = os.environ.get('BUSTAG_MISSAV_PROXY')
    if env_missav_proxy is not None:
        APP_CONFIG['missav.proxy'] = env_missav_proxy
    env_missav_user_agent = os.environ.get('BUSTAG_MISSAV_USER_AGENT')
    if env_missav_user_agent is not None:
        APP_CONFIG['missav.user_agent'] = env_missav_user_agent
    env_missav_probe_url = os.environ.get('BUSTAG_MISSAV_PROBE_URL')
    if env_missav_probe_url is not None:
        APP_CONFIG['missav.probe_url'] = env_missav_probe_url
    logger.debug(APP_CONFIG)
    return APP_CONFIG


def format_datetime(dt):
    format = '%Y-%m-%d %H:%M:%S'
    return dt.strftime(format)


def to_localtime(utc_dt):
    local_tz = pytz.timezone('Asia/Shanghai')
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    format = '%Y-%m-%d %H:%M:%S'
    local_dt = local_tz.normalize(local_dt)
    return local_dt.strftime(format)


def check_model_folder():
    model_path = get_data_path(MODEL_PATH)
    abs_path = os.path.abspath(model_path)
    if not os.path.exists(abs_path):
        print(f'created model folder: {abs_path}')
        os.makedirs(abs_path, exist_ok=True)


def init(force: bool = False):
    global _initialized
    if _initialized and not force:
        return APP_CONFIG
    check_testing()
    setup_logging()
    config = load_config()
    check_model_folder()
    _initialized = True
    return config
