"""
Bottle web application for bustag.

This module provides the web interface for the bustag application,
including routes for browsing, tagging, and managing items.
"""
import os
import sys
import traceback
import uuid
from multiprocessing import freeze_support
from urllib.parse import quote

import bottle
from bottle import hook, redirect, request, response, route, run, static_file, template

from bustag import __version__
from bustag.app.local import add_local_fanhao, load_tags_db
from bustag.app.schedule import add_download_job, fetch_data, get_task_info, start_scheduler
from bustag.app.tasks import task_queue
import bustag.model.classifier as clf
from bustag.spider import db
from bustag.spider.db import (
    DBError,
    ItemRate,
    LocalItem,
    RATE_TYPE,
    RATE_VALUE,
    User,
    db as dbconn,
    get_items,
    get_local_items,
)
from bustag.spider.sources import get_source
from bustag.util import APP_CONFIG, get_data_path, init as init_app_config, logger

APP_DIR = os.path.dirname(os.path.realpath(__file__))
if getattr(sys, 'frozen', False):
    APP_DIR = sys._MEIPASS

PUBLIC_ROUTES = ['/login', '/static', '/healthz']
_SECRET_KEY = None
_RUNTIME_INITIALIZED = False
_SCHEDULER_STARTED = False


def _setup_template_path():
    views_dir = os.path.join(APP_DIR, 'views')
    if views_dir not in bottle.TEMPLATE_PATH:
        bottle.TEMPLATE_PATH.insert(0, views_dir)


def _get_secret_key() -> str:
    global _SECRET_KEY
    if _SECRET_KEY:
        return _SECRET_KEY
    _SECRET_KEY = APP_CONFIG.get('auth.secret_key') or os.environ.get('BUSTAG_SECRET_KEY') or str(uuid.uuid4())
    return _SECRET_KEY


def initialize_runtime(start_background_scheduler: bool = False):
    """Initialize config/db and optionally scheduler in explicit app lifecycle."""
    global _RUNTIME_INITIALIZED, _SCHEDULER_STARTED

    if not _RUNTIME_INITIALIZED:
        init_app_config()
        db.init()
        _setup_template_path()
        _RUNTIME_INITIALIZED = True

    if start_background_scheduler and not _SCHEDULER_STARTED:
        start_scheduler()
        _SCHEDULER_STARTED = True


def create_app(start_background_scheduler: bool = False):
    """Create and initialize bottle application."""
    initialize_runtime(start_background_scheduler=start_background_scheduler)
    return bottle.default_app()


def is_logged_in():
    """Check if user is logged in."""
    username = request.get_cookie('user', secret=_get_secret_key())
    return username is not None


def require_login():
    """Check if current route requires login."""
    path = request.path
    for public_route in PUBLIC_ROUTES:
        if path.startswith(public_route):
            return False
    return True


def _get_model_page_context(error_msg=None, selected_model=None):
    model_metadata = None
    model_scores = None
    model_options = clf.list_models()
    try:
        _, model_scores, model_metadata = clf.load()
    except FileNotFoundError:
        model_scores = None

    training_task_id = request.query.get('task_id')
    training_task = get_task_info(training_task_id) if training_task_id else None

    return {
        'path': request.path,
        'model_scores': model_scores,
        'model_metadata': model_metadata,
        'model_options': model_options,
        'error_msg': error_msg,
        'selected_model': selected_model,
        'training_task_id': training_task_id,
        'training_task': training_task,
    }


def _train_model_task(model_name: str):
    """Background task body for model training."""
    _, model_scores, model_metadata = clf.train(model_name=model_name)
    return {
        'model_name': model_name,
        'model_scores': model_scores,
        'model_metadata': model_metadata,
    }


@hook('before_request')
def _connect_db():
    """Connect to database before each request."""
    dbconn.connect(reuse_if_open=True)


@hook('after_request')
def _close_db():
    """Close database connection after each request."""
    if not dbconn.is_closed():
        dbconn.close()


@hook('before_request')
def _auth_check():
    """Check authentication for protected routes."""
    if require_login() and not is_logged_in():
        redirect('/login')


@route('/healthz')
def healthz():
    """Liveness endpoint for container/runtime health checks."""
    return {'status': 'ok', 'version': __version__}


@route('/task/<task_id>')
def task_status(task_id):
    """Task status API for background jobs."""
    task = get_task_info(task_id)
    if task is None:
        response.status = 404
        return {'success': False, 'message': '任务不存在', 'task_id': task_id}
    return {'success': True, 'task': task}


@route('/login', method=['GET', 'POST'])
def login():
    """Handle user login."""
    error = None
    if request.method == 'POST':
        username = request.forms.get('username')
        password = request.forms.get('password')
        user = User.authenticate(username, password)
        if user:
            response.set_cookie('user', username, secret=_get_secret_key(), httponly=True, samesite='lax')
            logger.info(f'User logged in: {username}')
            redirect('/')
        else:
            error = '用户名或密码错误'
    return template('login', path=request.path, error=error)


@route('/logout')
def logout():
    """Handle user logout."""
    response.delete_cookie('user')
    redirect('/login')


@route('/static/<filepath:path>')
def send_static(filepath):
    """Serve static files."""
    return static_file(filepath, root=os.path.join(APP_DIR, 'static'))


def _remove_extra_tags(item):
    """Limit the number of tags displayed per category."""
    limit = 10
    tags_dict = item.tags_dict
    tags = ['genre', 'star']
    for tag_type in tags:
        tags_dict[tag_type] = tags_dict[tag_type][:limit]


@route('/')
def index():
    """Main page showing recommended items."""
    rate_type = RATE_TYPE.SYSTEM_RATE.value
    rate_value = int(request.query.get('like', RATE_VALUE.LIKE.value))
    page = int(request.query.get('page', 1))
    items, page_info = get_items(rate_type=rate_type, rate_value=rate_value, page=page)
    for item in items:
        _remove_extra_tags(item)
    today_update_count = db.get_today_update_count()
    today_recommend_count = db.get_today_recommend_count()
    msg = f'今日更新 {today_update_count} , 今日推荐 {today_recommend_count}'
    return template('index', items=items, page_info=page_info, like=rate_value, path=request.path, msg=msg)


@route('/tagit')
def tagit():
    """Page for tagging items."""
    rate_value = request.query.get('like', None)
    rate_value = None if rate_value == 'None' else rate_value
    rate_type = None
    if rate_value:
        rate_value = int(rate_value)
        rate_type = RATE_TYPE.USER_RATE
    page = int(request.query.get('page', 1))
    items, page_info = get_items(rate_type=rate_type, rate_value=rate_value, page=page)
    for item in items:
        _remove_extra_tags(item)
    return template('tagit', items=items, page_info=page_info, like=rate_value, path=request.path)


@route('/tag/<fanhao>', method='POST')
def tag(fanhao):
    """Handle tagging action for an item."""
    formid = None
    if request.POST.submit:
        formid = request.POST.formid
        item_rate = ItemRate.get_by_fanhao(fanhao)
        rate_value = request.POST.submit
        if not item_rate:
            rate_type = RATE_TYPE.USER_RATE
            ItemRate.saveit(rate_type, rate_value, fanhao)
            logger.debug(f'add new item_rate for fanhao:{fanhao}')
        else:
            item_rate.rate_value = rate_value
            item_rate.save()
            logger.debug(f'updated item_rate for fanhao:{fanhao}')
    page = int(request.query.get('page', 1))
    like = request.query.get('like')
    url = f'/tagit?page={page}&like={like}'
    if formid:
        url += f'#{formid}'
    redirect(url)


@route('/correct/<fanhao>', method='POST')
def correct(fanhao):
    """Handle correction action for an item rating."""
    formid = None
    if request.POST.submit:
        formid = request.POST.formid
        is_correct = int(request.POST.submit)
        item_rate = ItemRate.get_by_fanhao(fanhao)
        if item_rate:
            item_rate.rate_type = RATE_TYPE.USER_RATE
            if not is_correct:
                rate_value = item_rate.rate_value
                rate_value = 1 if rate_value == 0 else 0
                item_rate.rate_value = rate_value
            item_rate.save()
            logger.debug(f'updated item fanhao: {fanhao}, {"and correct the rate_value" if not is_correct else ""}')
    page = int(request.query.get('page', 1))
    like = int(request.query.get('like', 1))
    url = f'/?page={page}&like={like}'
    if formid:
        url += f'#{formid}'
    redirect(url)


@route('/model')
def other_settings():
    """Show model training status and scores."""
    context = _get_model_page_context()
    return template('model', **context)


@route('/do-training')
def do_training():
    """Submit model training task to background queue."""
    model_options = clf.list_models()
    model_names = {option['name'] for option in model_options}
    model_name = request.query.get('model', clf.DEFAULT_MODEL_NAME)
    if model_name not in model_names:
        context = _get_model_page_context(error_msg=f'不支持的模型: {model_name}', selected_model=clf.DEFAULT_MODEL_NAME)
        return template('model', **context)

    task_id = task_queue.submit('model_training', _train_model_task, model_name)
    logger.info('Submitted model training task %s with model=%s', task_id, model_name)
    redirect(f'/model?task_id={quote(task_id)}')


@route('/local_fanhao', method=['GET', 'POST'])
def update_local_fanhao():
    """Handle local fanhao upload."""
    msg = ''
    if request.POST.submit:
        fanhao_list = request.POST.fanhao
        tag_like = request.POST.tag_like == '1'
        missing_urls, local_file_count, tag_file_count = add_local_fanhao(fanhao_list, tag_like)
        if len(missing_urls) > 0:
            add_download_job(missing_urls)
            msg = f'上传 {len(missing_urls)} 个番号, {local_file_count} 个本地文件'
            if tag_like:
                msg += f', {tag_file_count} 个打标为喜欢'
    return template('local_fanhao', path=request.path, msg=msg)


@route('/local')
def local():
    """Show local items."""
    page = int(request.query.get('page', 1))
    items, page_info = get_local_items(page=page)
    for local_item in items:
        LocalItem.loadit(local_item)
        _remove_extra_tags(local_item.item)
    return template('local', items=items, page_info=page_info, path=request.path)


@route('/local_play/<id:int>')
def local_play(id):
    """Play a local item."""
    local_item = LocalItem.update_play(id)
    file_path = local_item.path
    logger.debug(file_path)
    redirect(file_path)


@route('/load_db', method=['GET', 'POST'])
def load_db():
    """Handle database file upload."""
    msg = ''
    errmsg = ''
    if request.POST.submit:
        upload = request.files.get('dbfile')
        if upload:
            logger.debug(upload.filename)
            name = get_data_path('uploaded.db')
            upload.save(name, overwrite=True)
            logger.debug(f'uploaded file saved to {name}')
            try:
                tag_file_added, missing_urls = load_tags_db()
            except DBError:
                errmsg = '数据库文件错误, 请检查文件是否正确上传'
            else:
                add_download_job(missing_urls)
                msg = f'上传 {tag_file_added} 条用户打标数据, {len(missing_urls)} 个番号, '
                msg += '  注意: 需要下载其他数据才能开始建模, 请等候一定时间'
        else:
            errmsg = '请上传数据库文件'
    return template('load_db', path=request.path, msg=msg, errmsg=errmsg)


@route('/fetch', method=['GET', 'POST'])
def fetch():
    """手动拉取数据页面"""
    msg = ''
    errmsg = ''

    if request.method == 'POST':
        try:
            start_page = int(request.forms.get('start_page', 1))
            end_page = int(request.forms.get('end_page', 1))
            max_count = int(request.forms.get('max_count', 100))

            if start_page < 1 or end_page < 1:
                errmsg = '页码必须大于0'
            elif start_page > get_source().max_page or end_page > get_source().max_page:
                errmsg = f'页码不能超过{get_source().max_page}'
            elif max_count < 1:
                errmsg = '最大条数必须大于0'
            elif max_count > 1000:
                errmsg = '最大条数不能超过1000'
            else:
                result = fetch_data(start_page, end_page, max_count)
                if result['success']:
                    msg = result['message']
                else:
                    errmsg = result['message']
        except ValueError:
            errmsg = '请输入有效的数字'

    return template('fetch', path=request.path, msg=msg, errmsg=errmsg)


def start_app(host: str = '0.0.0.0', port: int = 8000, debug: bool = True, start_background_scheduler: bool = True):
    """Start the web application server."""
    app = create_app(start_background_scheduler=start_background_scheduler)
    run(app=app, host=host, server='wsgiref', port=port, debug=debug)


if __name__ == '__main__':
    try:
        freeze_support()
        print(f'Bustag server starting: version: {__version__}\\n\\n')
        start_app()
    except Exception:
        print('system error')
        traceback.print_exc()
    finally:
        print('Press Enter to continue ...')
        input()
        os._exit(1)
