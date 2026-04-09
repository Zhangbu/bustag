from bustag.app import api_service


def test_build_healthz_payload():
    payload = api_service.build_healthz_payload('bottle')
    assert payload['status'] == 'ok'
    assert payload['framework'] == 'bottle'
    assert 'version' in payload


def test_build_task_status_payload_found(monkeypatch):
    monkeypatch.setattr(api_service, 'get_task_info', lambda task_id: {'id': task_id, 'status': 'success'})
    status, payload = api_service.build_task_status_payload('task-1')
    assert status == 200
    assert payload == {
        'success': True,
        'task': {'id': 'task-1', 'status': 'success'},
    }


def test_build_task_status_payload_not_found(monkeypatch):
    monkeypatch.setattr(api_service, 'get_task_info', lambda _task_id: None)
    status, payload = api_service.build_task_status_payload('missing-id')
    assert status == 404
    assert payload == {
        'success': False,
        'message': '任务不存在',
        'task_id': 'missing-id',
    }
