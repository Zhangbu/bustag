import bustag.app.wsgi as wsgi


def test_resolve_web_stack_default(monkeypatch):
    monkeypatch.delenv('BUSTAG_WEB_STACK', raising=False)
    assert wsgi.resolve_web_stack() == 'bottle'


def test_resolve_web_stack_invalid_fallback(monkeypatch):
    monkeypatch.setenv('BUSTAG_WEB_STACK', 'legacy')
    assert wsgi.resolve_web_stack() == 'bottle'


def test_create_server_app_fastapi(monkeypatch):
    monkeypatch.setenv('BUSTAG_WEB_STACK', 'fastapi')
    monkeypatch.setenv('BUSTAG_START_SCHEDULER', '1')

    monkeypatch.setattr(wsgi, '_create_fastapi', lambda start_background_scheduler=False: ('fastapi', start_background_scheduler))
    monkeypatch.setattr(wsgi, '_create_bottle', lambda start_background_scheduler=False: ('bottle', start_background_scheduler))

    app = wsgi.create_server_app()
    assert app == ('fastapi', True)


def test_create_server_app_bottle(monkeypatch):
    monkeypatch.setenv('BUSTAG_WEB_STACK', 'bottle')
    monkeypatch.setenv('BUSTAG_START_SCHEDULER', '0')

    monkeypatch.setattr(wsgi, '_create_fastapi', lambda start_background_scheduler=False: ('fastapi', start_background_scheduler))
    monkeypatch.setattr(wsgi, '_create_bottle', lambda start_background_scheduler=False: ('bottle', start_background_scheduler))

    app = wsgi.create_server_app()
    assert app == ('bottle', False)
