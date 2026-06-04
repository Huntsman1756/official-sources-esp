#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/official-sources/app}"
STATE_ROOT="${STATE_ROOT:-/var/lib/hermes-official-sources-auditor}"
RELEASE_CONTRACT="${RELEASE_CONTRACT:-/etc/official-sources/hermes-audit-contract.yaml}"
OFFICIAL_SOURCES_BIN="${OFFICIAL_SOURCES_BIN:-${APP_ROOT}/.venv/bin/official-sources}"

exec "${OFFICIAL_SOURCES_BIN}" hermes scheduled-audit \
  --repo-root "${APP_ROOT}" \
  --state-root "${STATE_ROOT}" \
  --release-contract "${RELEASE_CONTRACT}" \
  --official-sources-bin "${OFFICIAL_SOURCES_BIN}"
