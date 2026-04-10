#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

CONDA_ENV_NAME="${BUSTAG_CONDA_ENV:-bustag}"
CONDA_BIN="${BUSTAG_CONDA_BIN:-/home/zjxfun/miniconda3/bin/conda}"
CRAWL_COUNT="${BUSTAG_CRAWL_COUNT:-}"
RUN_RECOMMEND="${BUSTAG_CRAWL_RECOMMEND_AFTER_DOWNLOAD:-0}"

if [[ ! -x "${CONDA_BIN}" ]]; then
  echo "Conda executable not found: ${CONDA_BIN}"
  exit 1
fi

cd "${ROOT_DIR}"

echo "[crawler-once] start $(date '+%Y-%m-%d %H:%M:%S %Z')"
if [[ -n "${CRAWL_COUNT}" ]]; then
  "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python -m bustag.main download --count "${CRAWL_COUNT}"
else
  "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python -m bustag.main download
fi

if [[ "${RUN_RECOMMEND}" == "1" ]]; then
  "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python -m bustag.main recommend || true
fi

echo "[crawler-once] done  $(date '+%Y-%m-%d %H:%M:%S %Z')"
