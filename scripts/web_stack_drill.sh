#!/bin/bash
set -euo pipefail

TARGET_STACK="${1:-}"
BASE_URL="${BUSTAG_WEB_BASE_URL:-http://127.0.0.1:${BUSTAG_PORT:-8000}}"

if [[ -z "${TARGET_STACK}" ]]; then
  echo "Usage: $0 <bottle|fastapi> [base_url]"
  exit 1
fi

if [[ $# -ge 2 ]]; then
  BASE_URL="$2"
fi

if [[ "${TARGET_STACK}" != "bottle" && "${TARGET_STACK}" != "fastapi" ]]; then
  echo "Invalid stack: ${TARGET_STACK}. expected: bottle|fastapi"
  exit 1
fi

RID="drill-$(date +%s)"
HEALTH_URL="${BASE_URL%/}/healthz"

echo "[drill] target stack: ${TARGET_STACK}"
echo "[drill] health url: ${HEALTH_URL}"
echo "[drill] request id: ${RID}"

BODY=$(curl -fsS --connect-timeout 2 --max-time 8 -H "X-Request-ID: ${RID}" "${HEALTH_URL}")

python3 - <<'PY' "${BODY}" "${TARGET_STACK}" "${RID}"
import json
import sys

body = json.loads(sys.argv[1])
expected = sys.argv[2]
rid = sys.argv[3]

if body.get('status') != 'ok':
    raise SystemExit(f"health status not ok: {body}")
if body.get('framework') != expected:
    raise SystemExit(f"framework mismatch: expected={expected}, actual={body.get('framework')}, body={body}")
if body.get('request_id') != rid:
    raise SystemExit(f"request_id mismatch: expected={rid}, actual={body.get('request_id')}, body={body}")
print('[drill] health check passed')
PY

echo "[drill] rollback command: export BUSTAG_WEB_STACK=bottle"
echo "[drill] then restart service and rerun: $0 bottle ${BASE_URL}"
