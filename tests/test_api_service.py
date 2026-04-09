from bustag.app import api_service


def test_build_healthz_payload():
    payload = api_service.build_healthz_payload('bottle', request_id='rid-1')
    assert payload['status'] == 'ok'
    assert payload['framework'] == 'bottle'
    assert payload['request_id'] == 'rid-1'
    assert 'version' in payload


def test_build_error_payload():
    payload = api_service.build_error_payload(
        '任务不存在',
        code='task_not_found',
        request_id='rid-2',
        extra={'task_id': 'abc'},
    )
    assert payload['success'] is False
    assert payload['message'] == '任务不存在'
    assert payload['request_id'] == 'rid-2'
    assert payload['task_id'] == 'abc'
    assert payload['error']['code'] == 'task_not_found'


def test_build_task_status_payload_found(monkeypatch):
    monkeypatch.setattr(api_service, 'get_task_info', lambda task_id: {'id': task_id, 'status': 'success'})
    status, payload = api_service.build_task_status_payload('task-1', request_id='rid-3')
    assert status == 200
    assert payload == {
        'success': True,
        'task': {'id': 'task-1', 'status': 'success'},
        'request_id': 'rid-3',
    }


def test_build_task_status_payload_not_found(monkeypatch):
    monkeypatch.setattr(api_service, 'get_task_info', lambda _task_id: None)
    status, payload = api_service.build_task_status_payload('missing-id', request_id='rid-4')
    assert status == 404
    assert payload['success'] is False
    assert payload['message'] == '任务不存在'
    assert payload['task_id'] == 'missing-id'
    assert payload['request_id'] == 'rid-4'
    assert payload['error']['code'] == 'task_not_found'
