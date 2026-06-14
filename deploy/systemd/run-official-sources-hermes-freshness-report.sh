#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/official-sources/app}"
STATE_ROOT="${STATE_ROOT:-/var/lib/hermes-official-sources-auditor}"
OFFICIAL_SOURCES_BIN="${OFFICIAL_SOURCES_BIN:-${APP_ROOT}/.venv/bin/official-sources}"

exec "${OFFICIAL_SOURCES_BIN}" hermes scheduled-freshness-report \
  --repo-root "${APP_ROOT}" \
  --state-root "${STATE_ROOT}" \
  --official-sources-bin "${OFFICIAL_SOURCES_BIN}"
