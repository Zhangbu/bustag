#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="${BUSTAG_DB_FILE:-${ROOT_DIR}/data/bus.db}"
SNAPSHOT_PATH="${1:-}"

if [[ -z "${SNAPSHOT_PATH}" ]]; then
  echo "Usage: $0 <snapshot.db>"
  exit 1
fi

if [[ ! -f "${SNAPSHOT_PATH}" ]]; then
  echo "snapshot not found: ${SNAPSHOT_PATH}"
  exit 1
fi

if [[ -f "${SNAPSHOT_PATH}.sha256" ]]; then
  (cd "$(dirname "${SNAPSHOT_PATH}")" && sha256sum -c "$(basename "${SNAPSHOT_PATH}").sha256")
fi

mkdir -p "$(dirname "${DB_FILE}")"

if [[ -f "${DB_FILE}" ]]; then
  BACKUP_FILE="${DB_FILE}.bak.$(date '+%Y%m%dT%H%M%S%Z')"
  cp "${DB_FILE}" "${BACKUP_FILE}"
  echo "[import] backup: ${BACKUP_FILE}"
fi

cp "${SNAPSHOT_PATH}" "${DB_FILE}"
echo "[import] db replaced: ${DB_FILE}"
