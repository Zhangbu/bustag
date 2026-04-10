"""WSGI/ASGI entrypoint selector for production servers (e.g. gunicorn)."""
from __future__ import annotations

import os

from bustag.app.index import create_app


SUPPORTED_WEB_STACKS = {'bottle', 'fastapi'}


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


def resolve_web_stack(default: str = 'bottle') -> str:
    raw = os.environ.get('BUSTAG_WEB_STACK', default)
    stack = (raw or default).strip().lower()
    if stack not in SUPPORTED_WEB_STACKS:
        return default
    return stack


def _create_bottle(start_background_scheduler: bool):
    return create_app(start_background_scheduler=start_background_scheduler)


def _create_fastapi(start_background_scheduler: bool):
    from bustag.app.fastapi_app import create_fastapi_app

    return create_fastapi_app(start_background_scheduler=start_background_scheduler)


def create_server_app():
    start_background_scheduler = _as_bool(os.environ.get('BUSTAG_START_SCHEDULER'), default=True)
    web_stack = resolve_web_stack(default='bottle')
    if web_stack == 'fastapi':
        return _create_fastapi(start_background_scheduler)
    return _create_bottle(start_background_scheduler)


app = create_server_app()
