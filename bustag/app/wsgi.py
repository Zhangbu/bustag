"""WSGI entrypoint for production servers (e.g. gunicorn)."""
import os

from bustag.app.index import create_app


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {'1', 'true', 'yes', 'on'}


app = create_app(start_background_scheduler=_as_bool(os.environ.get('BUSTAG_START_SCHEDULER'), default=True))
