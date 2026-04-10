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

RID="precheck-$(date +%s)"
MISSING_TASK_ID="missing-${RID}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

HEALTH_URL="${BASE_URL%/}/healthz"
TASK_URL="${BASE_URL%/}/task/${MISSING_TASK_ID}"

HEALTH_HEADERS="${TMP_DIR}/health.headers"
HEALTH_BODY="${TMP_DIR}/health.body"
TASK_HEADERS="${TMP_DIR}/task.headers"
TASK_BODY="${TMP_DIR}/task.body"

echo "[precheck] stack=${TARGET_STACK} base_url=${BASE_URL} rid=${RID}"

HEALTH_CODE=$(curl -sS -o "${HEALTH_BODY}" -D "${HEALTH_HEADERS}" -w "%{http_code}" -H "X-Request-ID: ${RID}" "${HEALTH_URL}")
TASK_CODE=$(curl -sS -o "${TASK_BODY}" -D "${TASK_HEADERS}" -w "%{http_code}" -H "X-Request-ID: ${RID}" "${TASK_URL}")

python3 - <<'PY' \
  "${TARGET_STACK}" "${RID}" \
  "${HEALTH_CODE}" "${HEALTH_HEADERS}" "${HEALTH_BODY}" \
  "${TASK_CODE}" "${TASK_HEADERS}" "${TASK_BODY}" "${MISSING_TASK_ID}"
import json
import sys
from pathlib import Path

expected_stack = sys.argv[1]
rid = sys.argv[2]
health_code = int(sys.argv[3])
health_headers_path = Path(sys.argv[4])
health_body_path = Path(sys.argv[5])
task_code = int(sys.argv[6])
task_headers_path = Path(sys.argv[7])
task_body_path = Path(sys.argv[8])
missing_task_id = sys.argv[9]


def parse_headers(path: Path) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        headers[k.strip().lower()] = v.strip()
    return headers


health_headers = parse_headers(health_headers_path)
health_payload = json.loads(health_body_path.read_text(encoding='utf-8'))

if health_code != 200:
    raise SystemExit(f"health status code expected 200, got {health_code}, body={health_payload}")
if health_payload.get('status') != 'ok':
    raise SystemExit(f"health status expected ok, got {health_payload}")
if health_payload.get('framework') != expected_stack:
    raise SystemExit(f"framework mismatch: expected={expected_stack}, body={health_payload}")
if health_payload.get('request_id') != rid:
    raise SystemExit(f"health request_id mismatch: expected={rid}, body={health_payload}")
if health_headers.get('x-request-id') != rid:
    raise SystemExit(f"health response header x-request-id mismatch: expected={rid}, headers={health_headers}")


task_headers = parse_headers(task_headers_path)
task_payload = json.loads(task_body_path.read_text(encoding='utf-8'))

if task_code != 404:
    raise SystemExit(f"task missing status code expected 404, got {task_code}, body={task_payload}")
if task_payload.get('success') is not False:
    raise SystemExit(f"task missing success expected false, got {task_payload}")
if task_payload.get('task_id') != missing_task_id:
    raise SystemExit(f"task_id mismatch: expected={missing_task_id}, body={task_payload}")
if task_payload.get('request_id') != rid:
    raise SystemExit(f"task request_id mismatch: expected={rid}, body={task_payload}")
error = task_payload.get('error', {})
if error.get('code') != 'task_not_found':
    raise SystemExit(f"error code mismatch: expected task_not_found, body={task_payload}")
if task_headers.get('x-request-id') != rid:
    raise SystemExit(f"task response header x-request-id mismatch: expected={rid}, headers={task_headers}")

print('[precheck] PASS health + task error contract')
PY

echo "[precheck] suggested rollback: export BUSTAG_WEB_STACK=bottle"
echo "[precheck] after rollback restart, rerun: $0 bottle ${BASE_URL}"
