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

CONDA_ENV_NAME="${BUSTAG_CONDA_ENV:-bustag}"
CONDA_BIN="${BUSTAG_CONDA_BIN:-}"
CRAWL_COUNT="${BUSTAG_CRAWL_COUNT:-}"
RUN_RECOMMEND="${BUSTAG_CRAWL_RECOMMEND_AFTER_DOWNLOAD:-0}"
CRAWL_LOG_DIR="${BUSTAG_CRAWL_LOG_DIR:-${ROOT_DIR}/logs}"

if [[ -z "${CONDA_BIN}" ]]; then
  if command -v conda >/dev/null 2>&1; then
    CONDA_BIN="$(command -v conda)"
  elif [[ -x "/home/ubuntu/miniconda3/bin/conda" ]]; then
    CONDA_BIN="/home/ubuntu/miniconda3/bin/conda"
  elif [[ -x "/home/zjxfun/miniconda3/bin/conda" ]]; then
    CONDA_BIN="/home/zjxfun/miniconda3/bin/conda"
  elif [[ -x "/opt/conda/bin/conda" ]]; then
    CONDA_BIN="/opt/conda/bin/conda"
  fi
fi

if [[ -z "${CONDA_BIN}" ]] || [[ ! -x "${CONDA_BIN}" ]]; then
  echo "Conda executable not found: ${CONDA_BIN}"
  echo "Hint: set BUSTAG_CONDA_BIN in .env, e.g. /home/ubuntu/miniconda3/bin/conda"
  exit 1
fi

cd "${ROOT_DIR}"

mkdir -p "${CRAWL_LOG_DIR}"

RUN_TS="$(date '+%Y%m%dT%H%M%S%Z')"
RUN_START_HUMAN="$(date '+%Y-%m-%d %H:%M:%S %Z')"
DETAIL_LOG="${CRAWL_LOG_DIR}/crawler_${RUN_TS}.log"
SUMMARY_LOG="${CRAWL_LOG_DIR}/crawler_summary.log"

count_items() {
  "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python - <<'PY'
from bustag.spider import db
db.init()
print(db.Item.select().count())
PY
}

BEFORE_COUNT="$(count_items)"

echo "[crawler-once] start ${RUN_START_HUMAN}" | tee -a "${SUMMARY_LOG}"
echo "[crawler-once] detail log: ${DETAIL_LOG}" | tee -a "${SUMMARY_LOG}"

set +e
if [[ -n "${CRAWL_COUNT}" ]]; then
  "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python -m bustag.main download --count "${CRAWL_COUNT}" 2>&1 | tee -a "${DETAIL_LOG}"
else
  "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python -m bustag.main download 2>&1 | tee -a "${DETAIL_LOG}"
fi
DOWNLOAD_EXIT="${PIPESTATUS[0]}"
set -e

if [[ "${RUN_RECOMMEND}" == "1" ]]; then
  "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python -m bustag.main recommend 2>&1 | tee -a "${DETAIL_LOG}" || true
fi

AFTER_COUNT="$(count_items)"
DELTA_COUNT=$((AFTER_COUNT - BEFORE_COUNT))
RUN_END_HUMAN="$(date '+%Y-%m-%d %H:%M:%S %Z')"

if [[ "${DOWNLOAD_EXIT}" -eq 0 ]]; then
  RESULT_TAG="SUCCESS"
else
  RESULT_TAG="FAILED"
fi

{
  echo "[crawler-once] end   ${RUN_END_HUMAN}"
  echo "[crawler-once] result ${RESULT_TAG} exit=${DOWNLOAD_EXIT} before=${BEFORE_COUNT} after=${AFTER_COUNT} delta=${DELTA_COUNT}"
  echo "[crawler-once] -----"
} | tee -a "${SUMMARY_LOG}"

exit "${DOWNLOAD_EXIT}"
