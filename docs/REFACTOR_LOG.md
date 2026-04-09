# Bustag Refactor Log

## Round 1
- Time: 2026-04-09 15:30:17 CST
- Branch: `codex/refactor-m1-baseline`
- Scope:
  - Introduced explicit app lifecycle (`initialize_runtime`, `create_app`)
  - Removed db import-time auto-init side effect
  - Added WSGI entrypoint for gunicorn (`bustag.app.wsgi:app`)
  - Added `/healthz` endpoint
  - Updated docker runtime entry script to gunicorn
  - Updated tests for explicit init and fixed CLI recommend test
  - Added staged refactor checklist document
- Files:
  - `bustag/app/index.py`
  - `bustag/app/wsgi.py`
  - `bustag/spider/db.py`
  - `bustag/main.py`
  - `docker/entry.sh`
  - `tests/conftest.py`
  - `tests/test_main.py`
  - `tests/test_app_lifecycle.py`
  - `docs/REFACTOR_CHECKLIST.md`
  - `.env.example`
- Test command:
  - `/home/zjxfun/miniconda3/bin/conda run -n bustag pytest -s`
- Test result:
  - `37 passed, 2 skipped, 1 warning`
- Rollback note:
  - Revert this commit to restore previous lifecycle/runtime behavior.
