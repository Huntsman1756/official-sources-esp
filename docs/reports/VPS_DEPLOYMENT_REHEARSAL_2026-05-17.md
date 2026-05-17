# VPS Deployment Rehearsal - 2026-05-17

## Scope

TASK-004A was performed on a private VPS over SSH as `root`.

The deployment installed `official-sources` under `/opt/official-sources`, configured a
dedicated service user, initialized and migrated SQLite, created a verified backup, rehearsed
restore on a temporary copy, enabled systemd timers, and verified that MCP was not exposed.

No public MCP, public API, Docker, Nginx, Cloudflare Tunnel, downstream integration, RAG, new
source adapter, legal interpretation, automatic approval, or automatic publication was added.

## Environment

- Host: `ubuntu-4gb-nbg1-8`
- OS: Ubuntu 24.04.4 LTS
- Kernel: Linux 6.8.0-111-generic x86_64
- Python: `/usr/bin/python3.12`
- Git: `/usr/bin/git`
- systemd: `255`
- Deployment path: `/opt/official-sources`
- Application commit: `c5b6350`
- Repository: `https://github.com/Huntsman1756/official-sources-esp.git`

## Commands Run

SSH baseline:

```bash
ssh -i C:\Users\rome_\.ssh\esdata_root_vps_ed25519 root@<redacted-public-ip> \
  'set -eu; whoami; hostname -f; date -Is; cat /etc/os-release | head -n 5; uname -a; command -v python3.12; command -v git; systemctl --version | head -n 1'
```

VPS preparation:

```bash
mkdir -p /opt/official-sources/app
mkdir -p /opt/official-sources/data/artifacts
mkdir -p /opt/official-sources/data/backups
mkdir -p /opt/official-sources/logs
useradd --system --home /opt/official-sources --shell /usr/sbin/nologin official-sources 2>/dev/null || true
chown -R official-sources:official-sources /opt/official-sources
```

Application installation:

```bash
sudo -u official-sources git clone https://github.com/Huntsman1756/official-sources-esp.git /opt/official-sources/app
cd /opt/official-sources/app
sudo -u official-sources git rev-parse --short HEAD
sudo -u official-sources python3.12 -m venv .venv
sudo -u official-sources .venv/bin/python -m pip install --upgrade pip
sudo -u official-sources .venv/bin/python -m pip install -e .
sudo -u official-sources .venv/bin/official-sources --help
```

Environment file:

```bash
cat > /opt/official-sources/.env <<EOF
OFFICIAL_SOURCES_DB_PATH=/opt/official-sources/data/official_sources.sqlite
OFFICIAL_SOURCES_ARTIFACT_DIR=/opt/official-sources/data/artifacts
OFFICIAL_SOURCES_BOE_REQUESTS_PER_SECOND=1
OFFICIAL_SOURCES_BOE_MAX_RETRIES=5
OFFICIAL_SOURCES_BOE_BACKOFF_BASE_SECONDS=1
OFFICIAL_SOURCES_BOE_BACKOFF_MAX_SECONDS=30
OFFICIAL_SOURCES_BOE_JITTER_SECONDS=0.25
EOF
chown root:official-sources /opt/official-sources/.env
chmod 600 /opt/official-sources/.env
```

Database migration and validation:

```bash
CLI=/opt/official-sources/app/.venv/bin/official-sources
DB=/opt/official-sources/data/official_sources.sqlite
sudo -u official-sources $CLI --db-path $DB db status
sudo -u official-sources $CLI --db-path $DB db migrate
sudo -u official-sources $CLI --db-path $DB db validate
```

Backup and restore-copy rehearsal:

```bash
BACKUP=/opt/official-sources/data/backups/official_sources_20260517_170440.sqlite
sudo -u official-sources $CLI --db-path $DB db backup --output $BACKUP
cp $BACKUP /tmp/official_sources_restore_test.sqlite
chown official-sources:official-sources /tmp/official_sources_restore_test.sqlite
sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db status
sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db migrate
sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite db validate
sudo -u official-sources $CLI --db-path /tmp/official_sources_restore_test.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts status --date today
```

Systemd installation:

```bash
cd /opt/official-sources/app
cp deploy/systemd/official-sources-boe-daily.service /etc/systemd/system/
cp deploy/systemd/official-sources-boe-daily.timer /etc/systemd/system/
cp deploy/systemd/official-sources-integrity-check.service /etc/systemd/system/
cp deploy/systemd/official-sources-integrity-check.timer /etc/systemd/system/
systemctl daemon-reload
systemctl cat official-sources-boe-daily.service
systemctl cat official-sources-integrity-check.service
systemctl enable official-sources-boe-daily.timer official-sources-integrity-check.timer
systemctl start official-sources-boe-daily.timer official-sources-integrity-check.timer
systemctl status official-sources-boe-daily.timer --no-pager
systemctl status official-sources-integrity-check.timer --no-pager
```

Systemd service smoke check:

```bash
systemctl start official-sources-integrity-check.service
systemctl --no-pager --full status official-sources-integrity-check.service
journalctl -u official-sources-integrity-check.service -n 50 --no-pager
```

MCP privacy checks:

```bash
ss -tulpn
ps -ef | grep official | grep -v grep || true
systemctl list-timers official-sources-boe-daily.timer official-sources-integrity-check.timer --no-pager
```

## Results

Application installation:

- Repository cloned under `/opt/official-sources/app`.
- Deployed commit: `c5b6350`.
- Virtual environment created at `/opt/official-sources/app/.venv`.
- Package installed with `python -m pip install -e .`.
- `official-sources --help` printed CLI usage successfully.

Directory and ownership:

- `/opt/official-sources`, `app`, `data`, `data/artifacts`, `data/backups`, and `logs` exist.
- Service user exists: `official-sources`.
- Persistent data paths are owned by `official-sources:official-sources`.
- `/opt/official-sources/.env` is `root:official-sources` with mode `600`.

Database:

- Initial state: `current_version=0`, `latest_version=5`, pending migrations present.
- Migration applied versions `1,2,3,4,5`.
- Final validation: `current_version=5 latest_version=5 status=valid`.

Backup and restore rehearsal:

- Backup path: `/opt/official-sources/data/backups/official_sources_20260517_170440.sqlite`.
- Verified backup completed with `quick_check` on source and backup.
- Backup size: `106496` bytes.
- Restore rehearsal used `/tmp/official_sources_restore_test.sqlite`.
- Restore-copy status: `current_version=5 latest_version=5 pending_migrations=0 status=up_to_date`.
- Restore-copy migration: `applied_migrations=none status=up_to_date`.
- Restore-copy validation: `current_version=5 latest_version=5 status=valid`.
- The active database was not overwritten.

Smoke checks:

- Active DB `db validate`: `status=valid`.
- Restore-copy `status --date today`: no documents yet, no failed downloads, no integrity warnings.
- No live BOE consolidated-law smoke checks were run.

Systemd:

- `official-sources-boe-daily.timer`: enabled and active.
- `official-sources-integrity-check.timer`: enabled and active.
- Next BOE daily trigger: `2026-05-18 07:30:00 UTC`.
- Next integrity trigger: `2026-05-18 12:00:00 UTC`.
- Manual `official-sources-integrity-check.service` smoke run finished with `status=0/SUCCESS`.
- BOE daily service was not manually started to avoid an unrequested immediate live BOE ingestion.

MCP privacy:

- MCP was not started as a daemon.
- `MCP_PROCESS_COUNT=0`.
- No `official-sources` process was listening.
- Public listeners observed: SSH on port 22 only, plus local systemd-resolved DNS listeners.
- No Cloudflare Tunnel, Nginx proxy, Docker public port mapping, or public MCP listener was configured.

## Failures

- The first `.env` verification command failed due shell quoting in a `sed` expression after the
  file had already been created. The file was then verified with `ls -l` and `cut -d= -f1`.
- A root-run `git rev-parse` command reported Git dubious ownership because the repository is
  correctly owned by `official-sources`. Re-running Git as `official-sources` returned `c5b6350`.
- Some remote command output was visually truncated by the local command wrapper; follow-up
  targeted commands confirmed the key deployment states.

## Manual Steps Remaining

- Let the BOE daily timer run at its scheduled time and inspect:

```bash
journalctl -u official-sources-boe-daily.service -n 100 --no-pager
```

- If desired, manually run the BOE daily service during an approved window:

```bash
systemctl start official-sources-boe-daily.service
journalctl -u official-sources-boe-daily.service -n 100 --no-pager
```

- Keep MCP private. Start it only through stdio, localhost, SSH tunnel, or private VPN.

## Rollback

Never restore over an active SQLite database while ingestion, artifact download, MCP or API
processes are running.

Rollback sequence:

1. Stop timers and services.
2. Back up the current broken DB aside.
3. Restore a previous known-good backup.
4. Run `db validate`.
5. Run read-only smoke checks.
6. Restart timers and services.
7. Inspect logs.
