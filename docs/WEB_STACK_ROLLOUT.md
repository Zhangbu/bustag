# Web Stack Rollout Guide

## Goal

Safely switch default runtime from Bottle to FastAPI with rollback readiness.

## Preconditions

- `BUSTAG_WEB_STACK` switch is available in runtime env.
- Service restart operation is ready (systemd/docker/k8s rollout).
- Health endpoint is reachable from deployment environment.

## Quick Commands

- FastAPI drill: `make web-drill-fastapi`
- Bottle rollback drill: `make web-drill-bottle`
- FastAPI pre-release check: `make web-precheck-fastapi`
- Bottle pre-release check: `make web-precheck-bottle`
- Pipeline release gate (both stacks): `make web-release-gate`（通过 `scripts/start.sh` 在 conda 环境执行）

## Rollout Steps

1. Set `BUSTAG_WEB_STACK=fastapi` and restart service.
2. Run `make web-precheck-fastapi`.
3. Observe API logs/metrics for error rate and slow requests.
4. Keep rollback command ready: `export BUSTAG_WEB_STACK=bottle` then restart.

## Pipeline Gate Integration

- Release pipeline can run `make web-release-gate` as mandatory pre-release step.
- Script behavior:
  - Boot Bottle by `python -m bustag.main serve-web --stack bottle` and verify API contract via `scripts/pre_release_web_check.sh`.
  - Stop Bottle process cleanly.
  - Verify FastAPI by in-process contract checks (`fastapi.testclient`), no external ASGI server required.
  - Fail fast on first contract mismatch or startup timeout.
- Recommended env overrides in CI:
  - `BUSTAG_GATE_HOST` (default `127.0.0.1`)
  - `BUSTAG_GATE_PORT` (default `18080`)
  - `BUSTAG_GATE_WAIT_SECONDS` (default `45`)
  - `BUSTAG_GATE_STACKS` (default `bottle fastapi`)
  - `BUSTAG_GATE_ALLOW_SKIP_MISSING_FASTAPI` (default `1`, set `0` in strict CI)

## Rollback Steps

1. Set `BUSTAG_WEB_STACK=bottle`.
2. Restart service.
3. Run `make web-precheck-bottle`.
4. Confirm `/healthz` framework field is `bottle` and contract checks pass.
