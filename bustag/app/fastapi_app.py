"""FastAPI application entry for staged dual-stack migration."""
from __future__ import annotations

import os
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bustag.app.api_service import (
    build_error_payload,
    build_healthz_payload,
    build_task_status_payload,
    generate_request_id,
)
from bustag.app.index import initialize_runtime
from bustag.util import logger


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _error_response(status_code: int, message: str, code: str, request_id: str) -> JSONResponse:
    payload = build_error_payload(message, code=code, request_id=request_id)
    response = JSONResponse(status_code=status_code, content=payload)
    response.headers['X-Request-ID'] = request_id
    return response


def create_fastapi_app(start_background_scheduler: bool = False) -> FastAPI:
    """Create FastAPI app while reusing existing runtime initialization."""
    initialize_runtime(start_background_scheduler=start_background_scheduler)

    app = FastAPI(title="bustag-api")

    @app.middleware('http')
    async def add_request_context(request: Request, call_next):
        request_id = request.headers.get('X-Request-ID') or generate_request_id()
        request.state.request_id = request_id
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                'API fastapi %s %s -> 500 %.2fms rid=%s',
                request.method,
                request.url.path,
                duration_ms,
                request_id,
            )
            return _error_response(500, '服务器内部错误', 'internal_error', request_id)

        response.headers['X-Request-ID'] = request_id

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            'API fastapi %s %s -> %s %.2fms rid=%s',
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response

    @app.get('/healthz')
    def healthz(request: Request) -> dict[str, str]:
        return build_healthz_payload('fastapi', request_id=request.state.request_id)

    @app.get('/task/{task_id}')
    def task_status(task_id: str, request: Request) -> dict[str, Any] | JSONResponse:
        status_code, payload = build_task_status_payload(task_id, request_id=request.state.request_id)
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=payload)
        return payload

    return app


app = create_fastapi_app(start_background_scheduler=_as_bool(os.environ.get('BUSTAG_START_SCHEDULER'), default=False))
