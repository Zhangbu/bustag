import pytest

pytest.importorskip('fastapi')
pytest.importorskip('httpx')

from fastapi.testclient import TestClient

import bustag.app.fastapi_app as fastapi_app


def _build_client(monkeypatch):
    monkeypatch.setattr(fastapi_app, 'initialize_runtime', lambda start_background_scheduler=False: None)
    app = fastapi_app.create_fastapi_app(start_background_scheduler=False)
    return TestClient(app)


def test_healthz(monkeypatch):
    client = _build_client(monkeypatch)
    resp = client.get('/healthz', headers={'X-Request-ID': 'rid-health'})
    assert resp.status_code == 200
    assert resp.headers['X-Request-ID'] == 'rid-health'
    payload = resp.json()
    assert payload['status'] == 'ok'
    assert payload['framework'] == 'fastapi'
    assert payload['request_id'] == 'rid-health'


def test_task_status_found(monkeypatch):
    client = _build_client(monkeypatch)
    monkeypatch.setattr(
        fastapi_app,
        'build_task_status_payload',
        lambda task_id, request_id=None: (
            200,
            {'success': True, 'task': {'id': task_id, 'status': 'success'}, 'request_id': request_id},
        ),
    )

    resp = client.get('/task/abc123', headers={'X-Request-ID': 'rid-ok'})
    assert resp.status_code == 200
    assert resp.headers['X-Request-ID'] == 'rid-ok'
    assert resp.json() == {
        'success': True,
        'task': {'id': 'abc123', 'status': 'success'},
        'request_id': 'rid-ok',
    }


def test_task_status_not_found(monkeypatch):
    client = _build_client(monkeypatch)
    monkeypatch.setattr(
        fastapi_app,
        'build_task_status_payload',
        lambda task_id, request_id=None: (
            404,
            {
                'success': False,
                'message': '任务不存在',
                'task_id': task_id,
                'request_id': request_id,
                'error': {'code': 'task_not_found', 'message': '任务不存在'},
            },
        ),
    )

    resp = client.get('/task/missing-id', headers={'X-Request-ID': 'rid-404'})
    assert resp.status_code == 404
    assert resp.headers['X-Request-ID'] == 'rid-404'
    assert resp.json() == {
        'success': False,
        'message': '任务不存在',
        'task_id': 'missing-id',
        'request_id': 'rid-404',
        'error': {'code': 'task_not_found', 'message': '任务不存在'},
    }
