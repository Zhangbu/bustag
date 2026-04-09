"""FastAPI application entry for staged dual-stack migration."""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from bustag import __version__
from bustag.app.index import initialize_runtime
from bustag.app.schedule import get_task_info


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_fastapi_app(start_background_scheduler: bool = False) -> FastAPI:
    """Create FastAPI app while reusing existing runtime initialization."""
    initialize_runtime(start_background_scheduler=start_background_scheduler)

    app = FastAPI(title="bustag-api", version=__version__)

    @app.get('/healthz')
    def healthz() -> dict[str, str]:
        return {'status': 'ok', 'version': __version__, 'framework': 'fastapi'}

    @app.get('/task/{task_id}')
    def task_status(task_id: str) -> dict[str, Any] | JSONResponse:
        task = get_task_info(task_id)
        if task is None:
            return JSONResponse(
                status_code=404,
                content={'success': False, 'message': '任务不存在', 'task_id': task_id},
            )
        return {'success': True, 'task': task}

    return app


app = create_fastapi_app(start_background_scheduler=_as_bool(os.environ.get('BUSTAG_START_SCHEDULER'), default=False))
