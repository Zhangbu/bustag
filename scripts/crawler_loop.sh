#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  if ! bash -n "${ENV_FILE}" >/dev/null 2>&1; then
    echo "Invalid .env syntax: ${ENV_FILE}"
    echo "Hint: quote values that contain spaces or parentheses."
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

INTERVAL_SECONDS="${BUSTAG_CRAWL_INTERVAL_SECONDS:-3600}"
LOCK_FILE="${BUSTAG_CRAWL_LOCK_FILE:-/tmp/bustag-crawler.lock}"

if ! [[ "${INTERVAL_SECONDS}" =~ ^[0-9]+$ ]] || [[ "${INTERVAL_SECONDS}" -lt 1 ]]; then
  echo "Invalid BUSTAG_CRAWL_INTERVAL_SECONDS: ${INTERVAL_SECONDS}"
  exit 1
fi

cd "${ROOT_DIR}"

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  echo "crawler loop is already running: lock=${LOCK_FILE}"
  exit 1
fi

trap 'echo "[crawler-loop] stop $(date '\''+%Y-%m-%d %H:%M:%S %Z'\'')"; exit 0' INT TERM

echo "[crawler-loop] started interval=${INTERVAL_SECONDS}s lock=${LOCK_FILE}"
cycle=0
while true; do
  cycle=$((cycle + 1))
  cycle_start="$(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "[crawler-loop] cycle=${cycle} start ${cycle_start}"
  if bash scripts/crawler_once.sh; then
    echo "[crawler-loop] cycle=${cycle} result=SUCCESS"
  else
    rc=$?
    echo "[crawler-loop] cycle=${cycle} result=FAILED exit=${rc}"
  fi
  cycle_end="$(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "[crawler-loop] cycle=${cycle} end   ${cycle_end}"
  sleep "${INTERVAL_SECONDS}"
done
