"""Shared API response builders for Bottle/FastAPI dual-stack stage."""
from __future__ import annotations

from typing import Any

from bustag import __version__
from bustag.app.schedule import get_task_info


def build_healthz_payload(framework: str) -> dict[str, str]:
    return {'status': 'ok', 'version': __version__, 'framework': framework}


def build_task_status_payload(task_id: str) -> tuple[int, dict[str, Any]]:
    task = get_task_info(task_id)
    if task is None:
        return 404, {'success': False, 'message': '任务不存在', 'task_id': task_id}
    return 200, {'success': True, 'task': task}
