#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORT_DIR="${BUSTAG_CRAWL_EXPORT_DIR:-${ROOT_DIR}/exports}"
DB_FILE="${BUSTAG_DB_FILE:-${ROOT_DIR}/data/bus.db}"

mkdir -p "${EXPORT_DIR}"

if [[ ! -f "${DB_FILE}" ]]; then
  echo "DB file not found: ${DB_FILE}"
  exit 1
fi

TS="$(date '+%Y%m%dT%H%M%S%Z')"
SNAPSHOT="${EXPORT_DIR}/busdb_${TS}.db"

cp "${DB_FILE}" "${SNAPSHOT}"
sha256sum "${SNAPSHOT}" > "${SNAPSHOT}.sha256"

cat <<MSG
[export] snapshot: ${SNAPSHOT}
[export] checksum: ${SNAPSHOT}.sha256
[export] transfer example:
  scp ubuntu@<server>:${SNAPSHOT} ./
  scp ubuntu@<server>:${SNAPSHOT}.sha256 ./
MSG
