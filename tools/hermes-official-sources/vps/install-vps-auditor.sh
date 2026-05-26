#!/usr/bin/env bash
set -euo pipefail

: "${HERMES_API_KEY:?HERMES_API_KEY is required}"

HERMES_BASE_URL="${HERMES_BASE_URL:-https://api.nan.builders/v1}"
HERMES_MODEL="${HERMES_MODEL:-qwen3.6}"
APP_ROOT="${APP_ROOT:-/opt/official-sources/app}"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/hermes-official-sources-auditor}"
STATE_ROOT="${STATE_ROOT:-/var/lib/hermes-official-sources-auditor}"
RUN_USER="${RUN_USER:-official-sources}"
RUN_GROUP="${RUN_GROUP:-official-sources}"
SERVICE_NAME="${SERVICE_NAME:-official-sources-hermes-auditor}"
TIMER_ON_CALENDAR="${TIMER_ON_CALENDAR:-*-*-* 05:30:00}"

if [[ ! -d "$APP_ROOT" ]]; then
  echo "ERROR: APP_ROOT does not exist: $APP_ROOT" >&2
  exit 2
fi

if ! id "$RUN_USER" >/dev/null 2>&1; then
  echo "ERROR: run user does not exist: $RUN_USER" >&2
  exit 2
fi

install -d -m 0755 "$INSTALL_ROOT"
install -d -m 0755 "$INSTALL_ROOT/bin"
install -d -m 0750 -o "$RUN_USER" -g "$RUN_GROUP" "$STATE_ROOT"
install -d -m 0750 -o "$RUN_USER" -g "$RUN_GROUP" "$STATE_ROOT/.hermes"
install -d -m 0750 -o "$RUN_USER" -g "$RUN_GROUP" "$STATE_ROOT/reports"
install -d -m 0750 -o "$RUN_USER" -g "$RUN_GROUP" "$STATE_ROOT/logs"
install -d -m 0750 -o "$RUN_USER" -g "$RUN_GROUP" "$STATE_ROOT/tmp"

if [[ ! -x "$INSTALL_ROOT/.venv/bin/hermes" ]]; then
  python3 -m venv "$INSTALL_ROOT/.venv"
  "$INSTALL_ROOT/.venv/bin/python" -m pip install --upgrade pip
  "$INSTALL_ROOT/.venv/bin/python" -m pip install --upgrade hermes-agent
fi

cat > "$STATE_ROOT/.hermes/config.yaml" <<CONFIG
model:
  default: ${HERMES_MODEL}
  provider: custom
  base_url: ${HERMES_BASE_URL}
  api_key: "${HERMES_API_KEY}"
  context_length: 256000

streaming:
  enabled: true

agent:
  max_turns: 12
  verbose: false
  reasoning_effort: medium

terminal:
  backend: local
  cwd: ${APP_ROOT}
  timeout: 120
  lifetime_seconds: 300

sampling:
  temperature: 0.6
  top_p: 0.95
CONFIG

cat > "$STATE_ROOT/.hermes/SOUL.md" <<'SOUL'
Eres official-sources-hermes-vps-auditor.

Mision:
- Auditar el repositorio official-sources en modo read-only desde el VPS.
- Detectar bloqueos, drift documental y proponer el siguiente trabajo pequeno para Codex.
- Mantener memoria/sesiones/reportes persistentes en este perfil VPS.

Reglas no negociables:
- No modifiques archivos del repo.
- No ejecutes deploy, git commit, git push, migraciones ni operaciones productivas.
- No crees source_candidates, evidence-grade records, PDFs ni writes downstream.
- No reinicies servicios.
- Si algo no se puede verificar desde el filesystem actual, responde UNKNOWN.
- Cita rutas concretas del repo.
- Codex/humano decide cualquier implementacion.
SOUL

chown "$RUN_USER:$RUN_GROUP" "$STATE_ROOT/.hermes/config.yaml" "$STATE_ROOT/.hermes/SOUL.md"
chmod 0640 "$STATE_ROOT/.hermes/config.yaml" "$STATE_ROOT/.hermes/SOUL.md"

cat > "$INSTALL_ROOT/bin/run-official-sources-hermes-auditor.sh" <<'RUNNER'
#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/official-sources/app}"
STATE_ROOT="${STATE_ROOT:-/var/lib/hermes-official-sources-auditor}"
HERMES_BIN="${HERMES_BIN:-/opt/hermes-official-sources-auditor/.venv/bin/hermes}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
REPORT_DIR="$STATE_ROOT/reports"
LOG_DIR="$STATE_ROOT/logs"
REPORT_PATH="$REPORT_DIR/vps-audit-$STAMP.md"
LOG_PATH="$LOG_DIR/vps-audit-$STAMP.log"

mkdir -p "$REPORT_DIR" "$LOG_DIR"
cd "$APP_ROOT"

QUERY="$(cat <<'PROMPT'
Actua como auditor VPS read-only de official-sources.

Lee primero estos archivos si existen:
- AGENTS.md
- PROJECT_STATE.md
- TASK_QUEUE.md
- docs/SOURCES_POLICY.md
- docs/reports/source-registry-2026-05-24.md
- config/sources.yaml

Objetivo:
- Confirmar si el repo esta listo para que Codex implemente TASK-SOURCE-RSS-MONITOR-001.
- Verificar que BOCYL sigue siendo el piloto correcto y BOE el control positivo.
- Revisar si hay drift relevante en servicios systemd o artefactos locales solo a nivel informativo.

Reglas:
- Modo read-only.
- No escribas archivos.
- No ejecutes comandos destructivos ni reinicios.
- No crees candidates, evidence-grade records, PDFs, DB writes, downstream writes ni deploys.
- Si no puedes verificar algo, escribe UNKNOWN.

Salida markdown:
# official-sources VPS Hermes audit
## Decision
READY_FOR_CODEX_REVIEW | NEEDS_HUMAN_DECISION | BLOCKED | UNKNOWN
## Repo state
## Source monitor readiness
## Boundary checks
## VPS observations
## Recommended next Codex task
## Blockers and UNKNOWN
PROMPT
)"

{
  echo "<!--"
  echo "generated_at: $(date -Is)"
  echo "app_root: $APP_ROOT"
  echo "host: $(hostname -f 2>/dev/null || hostname)"
  echo "-->"
  echo
  HOME="$STATE_ROOT" "$HERMES_BIN" chat -Q --max-turns 8 -q "$QUERY"
} >"$REPORT_PATH" 2>"$LOG_PATH"

echo "report=$REPORT_PATH"
echo "log=$LOG_PATH"
RUNNER

chmod 0755 "$INSTALL_ROOT/bin/run-official-sources-hermes-auditor.sh"
chown -R root:root "$INSTALL_ROOT"
chown "$RUN_USER:$RUN_GROUP" "$STATE_ROOT/reports" "$STATE_ROOT/logs" "$STATE_ROOT/tmp"

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<UNIT
[Unit]
Description=official-sources Hermes read-only auditor
Documentation=https://hermes-agent.nousresearch.com/docs/
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=${RUN_USER}
Group=${RUN_GROUP}
WorkingDirectory=${APP_ROOT}
Environment=HOME=${STATE_ROOT}
Environment=APP_ROOT=${APP_ROOT}
Environment=STATE_ROOT=${STATE_ROOT}
Environment=HERMES_BIN=${INSTALL_ROOT}/.venv/bin/hermes
ExecStart=${INSTALL_ROOT}/bin/run-official-sources-hermes-auditor.sh
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${STATE_ROOT}
ReadOnlyPaths=${APP_ROOT}
UNIT

cat > "/etc/systemd/system/${SERVICE_NAME}.timer" <<UNIT
[Unit]
Description=Run official-sources Hermes read-only auditor

[Timer]
OnCalendar=${TIMER_ON_CALENDAR}
RandomizedDelaySec=20m
Persistent=true
Unit=${SERVICE_NAME}.service

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.timer"

echo "Installed ${SERVICE_NAME}.service and ${SERVICE_NAME}.timer"
echo "Timer schedule: ${TIMER_ON_CALENDAR} UTC with RandomizedDelaySec=20m"
echo "Run manually with: systemctl start ${SERVICE_NAME}.service"
