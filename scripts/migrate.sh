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
BACKUP_FLAG="${BUSTAG_MIGRATE_BACKUP_FLAG:---backup}"

cd "${ROOT_DIR}"

exec /home/zjxfun/miniconda3/bin/conda run -n "${CONDA_ENV_NAME}" \
  python -m bustag.main migrate "${BACKUP_FLAG}" "$@"
