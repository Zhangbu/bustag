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

cd "${ROOT_DIR}"

python - <<'PY'
from __future__ import annotations

from bustag.util import APP_CONFIG, init as init_app_config

init_app_config()

from bustag.spider.sources import get_source, list_sources

if 'missav' not in list_sources():
    raise SystemExit('missav source is unavailable. install dependencies (curl_cffi) first')

source = get_source('missav')
root_url = APP_CONFIG.get('download.root_path') or 'https://missav.ai'
source.configure(root_url)

probe_url = APP_CONFIG.get('missav.probe_url')
if probe_url:
    url = probe_url
else:
    url = source.build_page_urls(1, 1)[0]

html = source.fetch(url)
if not html or len(html.strip()) < 120:
    raise SystemExit(f'missav probe failed: empty/short body from {url}')

print(f'[missav-probe] PASS url={url} body_len={len(html)}')
PY
