"""Task queue abstraction with an in-process default backend."""
from __future__ import annotations

import os
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any, Callable, Protocol

from bustag.util import logger


class TaskBackend(Protocol):
    backend_name: str

    def submit(self, name: str, func: Callable[..., Any], *args, **kwargs) -> str:
        ...

    def get(self, task_id: str) -> dict[str, Any] | None:
        ...


class InMemoryTaskQueue:
    backend_name = 'memory'

    def __init__(self, max_workers: int = 2):
        self._executor = ThreadPoolExecutor(max_workers=max(1, max_workers), thread_name_prefix='bustag-task')
        self._tasks: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def submit(self, name: str, func: Callable[..., Any], *args, **kwargs) -> str:
        task_id = uuid.uuid4().hex
        created_at = datetime.now(UTC).isoformat()
        record = {
            'id': task_id,
            'name': name,
            'status': 'pending',
            'created_at': created_at,
            'started_at': None,
            'finished_at': None,
            'error': None,
            'result': None,
            'backend': self.backend_name,
        }
        with self._lock:
            self._tasks[task_id] = record
        self._executor.submit(self._run, task_id, func, args, kwargs)
        return task_id

    def _run(self, task_id: str, func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
        with self._lock:
            task = self._tasks[task_id]
            task['status'] = 'running'
            task['started_at'] = datetime.now(UTC).isoformat()

        try:
            result = func(*args, **kwargs)
            with self._lock:
                task = self._tasks[task_id]
                task['status'] = 'success'
                task['result'] = result
                task['finished_at'] = datetime.now(UTC).isoformat()
        except Exception as exc:
            logger.error('Task %s(%s) failed: %s\n%s', task_id, func.__name__, exc, traceback.format_exc())
            with self._lock:
                task = self._tasks[task_id]
                task['status'] = 'failed'
                task['error'] = str(exc)
                task['finished_at'] = datetime.now(UTC).isoformat()

    def get(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return dict(task)


# Backward-compatible alias used by existing tests/imports.
TaskQueue = InMemoryTaskQueue


def create_task_queue(backend: str = 'memory', max_workers: int = 2) -> TaskBackend:
    backend = (backend or 'memory').strip().lower()
    if backend == 'memory':
        return InMemoryTaskQueue(max_workers=max_workers)

    logger.warning('Unsupported task backend "%s", fallback to in-memory queue', backend)
    return InMemoryTaskQueue(max_workers=max_workers)


def create_task_queue_from_env() -> TaskBackend:
    backend = os.environ.get('BUSTAG_TASK_BACKEND', 'memory')
    workers = int(os.environ.get('BUSTAG_TASK_WORKERS', '2'))
    return create_task_queue(backend=backend, max_workers=workers)


task_queue = create_task_queue_from_env()
