# Hermes Freshness Observation Producer Smoke - 2026-06-13

Status: completed

Correction:

```text
This smoke used /opt/official-sources/app/official-sources.sqlite on VPS.
That is not the SQLite database used by the systemd BOE daily service.
See docs/reports/hermes-critical-source-observations-2026-06-13.md for the corrected
real-runtime smoke against /opt/official-sources/data/official_sources.sqlite.
```

Task:

```text
TASK-HERMES-FRESHNESS-OBSERVATION-PRODUCER-SMOKE-001
```

Related PRs:

```text
PR #45: docs(hermes): map freshness observations for critical sources
PR #46: feat(hermes): produce freshness observations from runtime state
```

## Purpose

Validate the merged freshness observation producer against local and VPS runtime state before any
scheduler or systemd activation.

The smoke checks whether the producer can find real operational observations for:

```text
BOE
BDNS
BOCM
```

The expected safe result is either:

```text
- JSONL observations are written from real existing runtime state; or
- the command fails closed with no output file when no observations exist.
```

## Contract

Allowed:

```text
- run official-sources hermes freshness-observations manually
- read existing monitor JSONL state
- read existing SQLite ingestion_runs with the producer read-only path
- write only the explicit smoke output JSONL when observations exist
- document local and VPS results
```

Forbidden:

```text
- scheduler activation
- systemd/timer changes
- live fetches
- ingest-monitor-date
- SQLite writes
- registry mutation
- official_documents/evidence/candidates creation
- product/downstream writes
- automatic issues
```

## Local Smoke

Local HEAD after PR #46 merge:

```text
69762bf
```

Local runtime preconditions:

```text
official-sources.sqlite: absent
.venv/Scripts/official-sources.exe: present
data directories present:
- provincial_audit
- review_exports
```

Command:

```powershell
$smokeRoot = Join-Path $env:TEMP (
  "hermes-freshness-observation-producer-smoke-" + (Get-Date -Format "yyyyMMdd-HHmmss")
)
New-Item -ItemType Directory -Path $smokeRoot | Out-Null
$outputPath = Join-Path $smokeRoot "freshness-observations.jsonl"

.\.venv\Scripts\official-sources.exe hermes freshness-observations `
  --runtime-root . `
  --source BOE `
  --source BDNS `
  --source BOCM `
  --output $outputPath
```

Observed output:

```text
SMOKE_ROOT=C:\Users\rome_\AppData\Local\Temp\hermes-freshness-observation-producer-smoke-20260613-201321
OUTPUT_EXISTS=False
EXIT_CODE=2
no freshness observations found
```

Interpretation:

```text
GO: fail-closed behavior confirmed.
No local BOE/BDNS/BOCM observation was fabricated.
No output JSONL was created without a real observation.
```

## VPS Alignment

VPS:

```text
157.90.22.40
alias: mcpspain-official-sources-vps
checkout: /opt/official-sources/app
```

Before alignment:

```text
HEAD: 912b89f
strict-audit expected_head_sha: 912b89fb88fc324456ce00809aa451de987a005b
systemctl --failed: 0 loaded units listed
```

The VPS checkout was fast-forwarded to merged main:

```text
912b89f..69762bf
```

The external strict-audit contract was updated to:

```text
expected_head_sha: 69762bfd67bab3cce87ab6cd5b03b6fce40ba6b6
approved_reason: PR #44-#46 freshness observation producer chain
```

No systemd unit or timer was changed.

## VPS Producer Smoke

Command:

```bash
cd /opt/official-sources/app

SMOKE_ROOT=/tmp/hermes-freshness-observation-producer-smoke-20260613-2018
mkdir -p "$SMOKE_ROOT"
OUTPUT="$SMOKE_ROOT/freshness-observations.jsonl"

/opt/official-sources/app/.venv/bin/official-sources \
  hermes freshness-observations \
  --runtime-root /opt/official-sources/app \
  --db-path /opt/official-sources/app/official-sources.sqlite \
  --source BOE \
  --source BDNS \
  --source BOCM \
  --output "$OUTPUT"
```

Observed output:

```text
SMOKE_ROOT=/tmp/hermes-freshness-observation-producer-smoke-20260613-2018
OUTPUT=/tmp/hermes-freshness-observation-producer-smoke-20260613-2018/freshness-observations.jsonl
OUTPUT_EXISTS=false
EXIT_CODE=2
no freshness observations found
```

Runtime evidence:

```text
monitor discovery JSONL files under data/rss_monitor, data/api_monitor, data/html_monitor: 0
SQLite ingestion_runs for BOE/BDNS/BOCM grouped by source/status: []
```

Interpretation:

```text
GO: fail-closed behavior confirmed.
The VPS runtime currently has no BOE/BDNS/BOCM observation inputs.
The producer did not create a false JSONL.
The result remains missing-input, not healthy freshness.
```

## Post-Smoke VPS Checks

Git status:

```text
## main...origin/main
```

Strict audit:

```text
VERDICT: GO
expected_head_sha: 69762bfd67bab3cce87ab6cd5b03b6fce40ba6b6
actual_head_sha: 69762bfd67bab3cce87ab6cd5b03b6fce40ba6b6
remote_head_observed_sha: 69762bfd67bab3cce87ab6cd5b03b6fce40ba6b6
git_worktree_clean: True
failed gates: none
warnings: none
```

Systemd:

```text
0 loaded units listed
```

## Conclusion

```text
producer command: works
local smoke: GO fail-closed
VPS smoke: GO fail-closed
real BOE/BDNS/BOCM observations: missing
scheduler activation: still NO-GO
```

The producer is ready to consume existing observation state, but the current local and VPS runtime
state still does not contain real BOE/BDNS/BOCM observations.

The next useful task is not scheduler activation. It is producing or obtaining real monitor/runtime
observation inputs for the critical sources, starting with BOE/BOCM RSS monitor outputs and a BDNS
observation path.
