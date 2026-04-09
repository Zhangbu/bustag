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
    resp = client.get('/healthz')
    assert resp.status_code == 200
    payload = resp.json()
    assert payload['status'] == 'ok'
    assert payload['framework'] == 'fastapi'


def test_task_status_found(monkeypatch):
    client = _build_client(monkeypatch)
    monkeypatch.setattr(fastapi_app, 'get_task_info', lambda task_id: {'id': task_id, 'status': 'success'})

    resp = client.get('/task/abc123')
    assert resp.status_code == 200
    assert resp.json() == {
        'success': True,
        'task': {'id': 'abc123', 'status': 'success'},
    }


def test_task_status_not_found(monkeypatch):
    client = _build_client(monkeypatch)
    monkeypatch.setattr(fastapi_app, 'get_task_info', lambda _task_id: None)

    resp = client.get('/task/missing-id')
    assert resp.status_code == 404
    assert resp.json() == {
        'success': False,
        'message': '任务不存在',
        'task_id': 'missing-id',
    }
