"""Shared API helpers for Bottle/FastAPI dual-stack stage."""
from __future__ import annotations

import os
import threading
import uuid
from typing import Any

from bustag import __version__
from bustag.app.schedule import get_task_info

DEFAULT_API_SLOW_MS = 800.0

_API_METRICS_LOCK = threading.Lock()
_API_METRICS: dict[str, Any] = {
    'total': 0,
    'slow': 0,
    'by_framework': {},
    'by_path': {},
    'by_status': {},
}


def generate_request_id() -> str:
    return uuid.uuid4().hex


def get_slow_request_threshold_ms(default: float = DEFAULT_API_SLOW_MS) -> float:
    raw_value = os.environ.get('BUSTAG_API_SLOW_MS')
    if raw_value is None:
        return default
    try:
        parsed = float(raw_value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def should_warn_slow_request(duration_ms: float, threshold_ms: float) -> bool:
    return duration_ms >= threshold_ms


def is_api_observed_path(path: str) -> bool:
    return path == '/healthz' or path.startswith('/task/')


def record_api_metric(framework: str, path: str, status_code: int, duration_ms: float, *, slow: bool) -> None:
    status_key = str(status_code)
    with _API_METRICS_LOCK:
        _API_METRICS['total'] += 1
        if slow:
            _API_METRICS['slow'] += 1

        by_framework = _API_METRICS['by_framework']
        by_framework[framework] = by_framework.get(framework, 0) + 1

        by_path = _API_METRICS['by_path']
        by_path[path] = by_path.get(path, 0) + 1

        by_status = _API_METRICS['by_status']
        by_status[status_key] = by_status.get(status_key, 0) + 1


def get_api_metrics_snapshot() -> dict[str, Any]:
    with _API_METRICS_LOCK:
        return {
            'total': _API_METRICS['total'],
            'slow': _API_METRICS['slow'],
            'by_framework': dict(_API_METRICS['by_framework']),
            'by_path': dict(_API_METRICS['by_path']),
            'by_status': dict(_API_METRICS['by_status']),
        }


def reset_api_metrics_for_test() -> None:
    with _API_METRICS_LOCK:
        _API_METRICS['total'] = 0
        _API_METRICS['slow'] = 0
        _API_METRICS['by_framework'].clear()
        _API_METRICS['by_path'].clear()
        _API_METRICS['by_status'].clear()


def build_error_payload(
    message: str,
    *,
    code: str,
    request_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        'success': False,
        'message': message,
        'error': {
            'code': code,
            'message': message,
        },
    }
    if request_id:
        payload['request_id'] = request_id
    if extra:
        payload.update(extra)
    return payload


def build_healthz_payload(framework: str, request_id: str | None = None) -> dict[str, str]:
    payload = {'status': 'ok', 'version': __version__, 'framework': framework}
    if request_id:
        payload['request_id'] = request_id
    return payload


def build_task_status_payload(task_id: str, request_id: str | None = None) -> tuple[int, dict[str, Any]]:
    task = get_task_info(task_id)
    if task is None:
        payload = build_error_payload(
            '任务不存在',
            code='task_not_found',
            request_id=request_id,
            extra={'task_id': task_id},
        )
        return 404, payload

    payload: dict[str, Any] = {'success': True, 'task': task}
    if request_id:
        payload['request_id'] = request_id
    return 200, payload
