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

## Rollout Steps

1. Set `BUSTAG_WEB_STACK=fastapi` and restart service.
2. Run `make web-precheck-fastapi`.
3. Observe API logs/metrics for error rate and slow requests.
4. Keep rollback command ready: `export BUSTAG_WEB_STACK=bottle` then restart.

## Rollback Steps

1. Set `BUSTAG_WEB_STACK=bottle`.
2. Restart service.
3. Run `make web-precheck-bottle`.
4. Confirm `/healthz` framework field is `bottle` and contract checks pass.
