#!/bin/bash
set -euo pipefail

HOST="${BUSTAG_GATE_HOST:-127.0.0.1}"
PORT="${BUSTAG_GATE_PORT:-18080}"
BASE_URL="${BUSTAG_WEB_BASE_URL:-}"
WAIT_SECONDS="${BUSTAG_GATE_WAIT_SECONDS:-45}"
STACKS="${BUSTAG_GATE_STACKS:-bottle fastapi}"
ALLOW_SKIP_MISSING_FASTAPI="${BUSTAG_GATE_ALLOW_SKIP_MISSING_FASTAPI:-1}"

if [[ -z "${BASE_URL}" ]]; then
  PORT="$(python3 - <<'PY' "${HOST}" "${PORT}"
import socket
import sys

host = sys.argv[1]
start_port = int(sys.argv[2])
max_attempt = 20

for port in range(start_port, start_port + max_attempt + 1):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        print(port)
        break
    except OSError:
        pass
    finally:
        sock.close()
else:
    raise SystemExit(f"no available port in range [{start_port}, {start_port + max_attempt}]")
PY
)"
  BASE_URL="http://${HOST}:${PORT}"
fi

TMP_DIR="$(mktemp -d)"
CURRENT_PID=""
cleanup() {
  if [[ -n "${CURRENT_PID}" ]] && kill -0 "${CURRENT_PID}" >/dev/null 2>&1; then
    kill "${CURRENT_PID}" >/dev/null 2>&1 || true
    wait "${CURRENT_PID}" >/dev/null 2>&1 || true
  fi
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

start_stack() {
  local stack="$1"
  local log_file="${TMP_DIR}/serve-web-${stack}.log"

  if [[ "${stack}" != "bottle" ]]; then
    echo "[gate] start_stack only supports bottle runtime check"
    return 1
  fi

  BUSTAG_WEB_STACK="${stack}" BUSTAG_PORT="${PORT}" BUSTAG_START_SCHEDULER=0 \
    python -m bustag.main serve-web \
    --stack "${stack}" \
    --host "${HOST}" \
    --port "${PORT}" \
    --no-start-background-scheduler >"${log_file}" 2>&1 &

  CURRENT_PID=$!
}

run_fastapi_inprocess_check() {
  local rid="gate-fastapi-$(date +%s)"
  local missing_task_id="missing-${rid}"
  python3 - <<'PY' "${rid}" "${missing_task_id}"
import sys

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:
    print("[gate] fastapi dependency not installed, skip in-process check")
    raise SystemExit(10)

from bustag.app.fastapi_app import create_fastapi_app

rid = sys.argv[1]
missing_task_id = sys.argv[2]

app = create_fastapi_app(start_background_scheduler=False)
client = TestClient(app)

health_resp = client.get("/healthz", headers={"X-Request-ID": rid})
if health_resp.status_code != 200:
    raise SystemExit(f"fastapi health status expected 200, got {health_resp.status_code}")
health_payload = health_resp.json()
if health_payload.get("status") != "ok":
    raise SystemExit(f"fastapi health status not ok: {health_payload}")
if health_payload.get("framework") != "fastapi":
    raise SystemExit(f"fastapi framework mismatch: {health_payload}")
if health_payload.get("request_id") != rid:
    raise SystemExit(f"fastapi request_id mismatch: {health_payload}")
if health_resp.headers.get("x-request-id") != rid:
    raise SystemExit(f"fastapi x-request-id header mismatch: {dict(health_resp.headers)}")

task_resp = client.get(f"/task/{missing_task_id}", headers={"X-Request-ID": rid})
if task_resp.status_code != 404:
    raise SystemExit(f"fastapi task status expected 404, got {task_resp.status_code}")
task_payload = task_resp.json()
if task_payload.get("success") is not False:
    raise SystemExit(f"fastapi task success expected false: {task_payload}")
if task_payload.get("task_id") != missing_task_id:
    raise SystemExit(f"fastapi task_id mismatch: {task_payload}")
if task_payload.get("request_id") != rid:
    raise SystemExit(f"fastapi task request_id mismatch: {task_payload}")
if task_payload.get("error", {}).get("code") != "task_not_found":
    raise SystemExit(f"fastapi error code mismatch: {task_payload}")
if task_resp.headers.get("x-request-id") != rid:
    raise SystemExit(f"fastapi task x-request-id header mismatch: {dict(task_resp.headers)}")

print("[gate] fastapi in-process contract check passed")
PY
}

wait_until_ready() {
  local stack="$1"
  local deadline=$((SECONDS + WAIT_SECONDS))
  local url="${BASE_URL%/}/healthz"

  while (( SECONDS < deadline )); do
    local body=""
    body="$(curl -fsS --connect-timeout 1 --max-time 2 "${url}" 2>/dev/null || true)"
    if [[ -n "${body}" ]]; then
      if python3 - <<'PY' "${body}" "${stack}" >/dev/null 2>&1
import json
import sys

payload = json.loads(sys.argv[1])
expected_stack = sys.argv[2]

if payload.get("status") == "ok" and payload.get("framework") == expected_stack:
    raise SystemExit(0)
raise SystemExit(1)
PY
      then
        return 0
      fi
    fi
    sleep 1
  done

  echo "[gate] stack=${stack} failed to become ready in ${WAIT_SECONDS}s"
  if [[ -f "${TMP_DIR}/serve-web-${stack}.log" ]]; then
    echo "[gate] server log:"
    cat "${TMP_DIR}/serve-web-${stack}.log"
  fi
  return 1
}

stop_current_stack() {
  if [[ -z "${CURRENT_PID}" ]]; then
    return 0
  fi
  if kill -0 "${CURRENT_PID}" >/dev/null 2>&1; then
    kill "${CURRENT_PID}" >/dev/null 2>&1 || true
    wait "${CURRENT_PID}" >/dev/null 2>&1 || true
  fi
  CURRENT_PID=""
}

echo "[gate] host=${HOST} port=${PORT} base_url=${BASE_URL} stacks=${STACKS}"

for stack in ${STACKS}; do
  if [[ "${stack}" != "bottle" && "${stack}" != "fastapi" ]]; then
    echo "[gate] unsupported stack in BUSTAG_GATE_STACKS: ${stack}"
    exit 1
  fi

  echo "[gate] verifying stack=${stack}"
  if [[ "${stack}" == "fastapi" ]]; then
    if run_fastapi_inprocess_check; then
      :
    else
      rc=$?
      if [[ ${rc} -eq 10 && "${ALLOW_SKIP_MISSING_FASTAPI}" == "1" ]]; then
        echo "[gate] stack=fastapi skipped (missing dependency, set BUSTAG_GATE_ALLOW_SKIP_MISSING_FASTAPI=0 to fail)"
      else
        exit ${rc}
      fi
    fi
  else
    start_stack "${stack}"
    wait_until_ready "${stack}"
    BUSTAG_WEB_BASE_URL="${BASE_URL}" bash scripts/pre_release_web_check.sh "${stack}" "${BASE_URL}"
    stop_current_stack
  fi
  echo "[gate] stack=${stack} passed"
done

echo "[gate] PASS all configured stacks"
