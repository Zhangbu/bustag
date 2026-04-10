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


def test_slow_threshold_default_and_invalid(monkeypatch):
    monkeypatch.delenv('BUSTAG_API_SLOW_MS', raising=False)
    assert api_service.get_slow_request_threshold_ms() == api_service.DEFAULT_API_SLOW_MS

    monkeypatch.setenv('BUSTAG_API_SLOW_MS', 'oops')
    assert api_service.get_slow_request_threshold_ms() == api_service.DEFAULT_API_SLOW_MS

    monkeypatch.setenv('BUSTAG_API_SLOW_MS', '-1')
    assert api_service.get_slow_request_threshold_ms() == api_service.DEFAULT_API_SLOW_MS

    monkeypatch.setenv('BUSTAG_API_SLOW_MS', '123.5')
    assert api_service.get_slow_request_threshold_ms() == 123.5


def test_metrics_record_and_snapshot():
    api_service.reset_api_metrics_for_test()
    api_service.record_api_metric('fastapi', '/healthz', 200, 10.0, slow=False)
    api_service.record_api_metric('bottle', '/task/abc', 404, 2000.0, slow=True)

    snapshot = api_service.get_api_metrics_snapshot()
    assert snapshot['total'] == 2
    assert snapshot['slow'] == 1
    assert snapshot['by_framework']['fastapi'] == 1
    assert snapshot['by_framework']['bottle'] == 1
    assert snapshot['by_path']['/healthz'] == 1
    assert snapshot['by_path']['/task/abc'] == 1
    assert snapshot['by_status']['200'] == 1
    assert snapshot['by_status']['404'] == 1


def test_observed_path_and_slow_predicate():
    assert api_service.is_api_observed_path('/healthz') is True
    assert api_service.is_api_observed_path('/task/1') is True
    assert api_service.is_api_observed_path('/model') is False
    assert api_service.should_warn_slow_request(100.0, 50.0) is True
    assert api_service.should_warn_slow_request(49.9, 50.0) is False
