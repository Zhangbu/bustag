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
CONDA_BIN="${BUSTAG_CONDA_BIN:-}"

if [[ -z "${CONDA_BIN}" ]]; then
  if command -v conda >/dev/null 2>&1; then
    CONDA_BIN="$(command -v conda)"
  else
    CONDA_BIN="/home/zjxfun/miniconda3/bin/conda"
  fi
fi

if [[ ! -x "${CONDA_BIN}" ]]; then
  echo "Conda executable not found: ${CONDA_BIN}"
  exit 1
fi

cd "${ROOT_DIR}"

if [[ "$#" -gt 0 ]]; then
  exec "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" "$@"
fi

exec "${CONDA_BIN}" run -n "${CONDA_ENV_NAME}" python bustag/app/index.py
