"""FastAPI application entry for staged dual-stack migration."""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from bustag.app.api_service import build_healthz_payload, build_task_status_payload
from bustag.app.index import initialize_runtime


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def create_fastapi_app(start_background_scheduler: bool = False) -> FastAPI:
    """Create FastAPI app while reusing existing runtime initialization."""
    initialize_runtime(start_background_scheduler=start_background_scheduler)

    app = FastAPI(title="bustag-api")

    @app.get('/healthz')
    def healthz() -> dict[str, str]:
        return build_healthz_payload('fastapi')

    @app.get('/task/{task_id}')
    def task_status(task_id: str) -> dict[str, Any] | JSONResponse:
        status_code, payload = build_task_status_payload(task_id)
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=payload)
        return payload

    return app


app = create_fastapi_app(start_background_scheduler=_as_bool(os.environ.get('BUSTAG_START_SCHEDULER'), default=False))
