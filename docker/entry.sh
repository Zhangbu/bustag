#!/bin/bash
set -euo pipefail

PORT="${BUSTAG_PORT:-8000}"
WORKERS="${BUSTAG_GUNICORN_WORKERS:-1}"
TIMEOUT="${BUSTAG_GUNICORN_TIMEOUT:-120}"
BIND_ADDR="0.0.0.0:${PORT}"
WEB_STACK="${BUSTAG_WEB_STACK:-bottle}"

if [[ "${WEB_STACK}" == "fastapi" ]]; then
  exec gunicorn \
    bustag.app.wsgi:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "${BIND_ADDR}" \
    --workers "${WORKERS}" \
    --timeout "${TIMEOUT}" \
    --access-logfile - \
    --error-logfile -
fi

exec gunicorn \
  bustag.app.wsgi:app \
  --bind "${BIND_ADDR}" \
  --workers "${WORKERS}" \
  --timeout "${TIMEOUT}" \
  --access-logfile - \
  --error-logfile -
