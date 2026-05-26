# Official-sources Hermes VPS auditor - 2026-05-26

## Purpose

Move the autonomous Hermes audit loop off the local Windows machine and onto the project VPS.

The VPS auditor is intentionally read-only. It can inspect the `official-sources` checkout, write
reports to its own state directory, and recommend the next Codex-reviewed task. It must not modify
the repo, deploy, migrate, restart services, create candidates, create evidence-grade records,
download PDFs, or write downstream product repos.

## Deployment Shape

Installer:

```text
tools/hermes-official-sources/vps/install-vps-auditor.sh
```

Runtime paths:

```text
/opt/hermes-official-sources-auditor
/var/lib/hermes-official-sources-auditor
/opt/official-sources/app
```

Systemd units:

```text
official-sources-hermes-auditor.service
official-sources-hermes-auditor.timer
```

Default schedule:

```text
05:30 UTC daily, with RandomizedDelaySec=20m
```

## Runtime Policy

- Runs as user/group `official-sources`.
- Uses Hermes CLI from a dedicated virtualenv.
- Uses persistent Hermes home at `/var/lib/hermes-official-sources-auditor`.
- Writes only to `/var/lib/hermes-official-sources-auditor`.
- Reads the repo from `/opt/official-sources/app`.
- Uses `ProtectSystem=strict`, `ProtectHome=true`, `NoNewPrivileges=true`, and read-only repo path.

## Model Policy

- Default model: `qwen3.6`.
- Concurrency: systemd service is one-shot and single-process.
- No embeddings, TTS, STT, War Room, or Kanban in this phase.

## Operational Next Step

After install, run one manual smoke:

```text
systemctl start official-sources-hermes-auditor.service
systemctl status official-sources-hermes-auditor.service --no-pager
ls -lt /var/lib/hermes-official-sources-auditor/reports
```

Then inspect the latest report before trusting the timer.
