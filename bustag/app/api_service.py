"""Shared API helpers for Bottle/FastAPI dual-stack stage."""
from __future__ import annotations

import uuid
from typing import Any

from bustag import __version__
from bustag.app.schedule import get_task_info


def generate_request_id() -> str:
    return uuid.uuid4().hex


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
