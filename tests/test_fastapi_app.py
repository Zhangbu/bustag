import pytest

pytest.importorskip('fastapi')
pytest.importorskip('httpx')

from fastapi.testclient import TestClient

from bustag.app import api_service
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


def test_internal_error_has_unified_payload(monkeypatch):
    client = _build_client(monkeypatch)

    def _raise_error(_task_id, request_id=None):
        raise RuntimeError('boom')

    monkeypatch.setattr(fastapi_app, 'build_task_status_payload', _raise_error)

    resp = client.get('/task/explode', headers={'X-Request-ID': 'rid-500'})
    assert resp.status_code == 500
    assert resp.headers['X-Request-ID'] == 'rid-500'
    assert resp.json() == {
        'success': False,
        'message': '服务器内部错误',
        'request_id': 'rid-500',
        'error': {'code': 'internal_error', 'message': '服务器内部错误'},
    }


def test_metrics_recorded_for_fastapi_paths(monkeypatch):
    api_service.reset_api_metrics_for_test()
    client = _build_client(monkeypatch)

    resp = client.get('/healthz', headers={'X-Request-ID': 'rid-metric'})
    assert resp.status_code == 200

    snapshot = api_service.get_api_metrics_snapshot()
    assert snapshot['total'] >= 1
    assert snapshot['by_framework'].get('fastapi', 0) >= 1
    assert snapshot['by_path'].get('/healthz', 0) >= 1
    assert snapshot['by_status'].get('200', 0) >= 1
