from bustag.app.index import create_app, initialize_runtime
from bustag.spider import db as spider_db


def test_create_app_initializes_runtime():
    app = create_app(start_background_scheduler=False)
    assert app is not None
    assert spider_db.is_initialized() is True


def test_healthz_route_registered():
    app = create_app(start_background_scheduler=False)
    rules = {route.rule for route in app.routes}
    assert '/healthz' in rules
    assert '/task/<task_id>' in rules


def test_db_init_is_idempotent():
    spider_db.init()
    spider_db.init()
    assert spider_db.is_initialized() is True


def test_initialize_runtime_idempotent_without_scheduler():
    initialize_runtime(start_background_scheduler=False)
    initialize_runtime(start_background_scheduler=False)
    assert spider_db.is_initialized() is True
