# Strict opposition alert export

Date: 2026-06-14

## Task

`TASK-OFFICIAL-SOURCES-STRICT-CONTRACT-DEPLOY-001`

## Summary

Exposed the strict alert export contract needed by `oposiciones2.0` while
preserving the dry-run/no-write boundary in `official-sources`.

## Changes

- Added `--scope {all,strict}` to `dry-run-opposition-alerts`.
- Added `BOP_ALICANTE`, `BOP_VALENCIA`, and `BOP_CASTELLON` to the supported
  opposition alert source codes.
- Added `detected_at` to emitted alert records.
- Added downstream-compatible aliases:

```text
published_at
url
raw_excerpt
evidence
```

- Added strict-scope filtering so `--scope strict` excludes broad/review-only
  alert records.
- Kept writes disabled:

```text
source_candidates=false
artifacts=false
external_output=false
db writes from dry-run: none
```

## Validation

Local worktree:

```text
python -m pytest tests/test_cli.py -q -k "opposition_alerts or does_not_expose"
7 passed, 101 deselected
```

```text
python -m pytest tests/test_cli.py -q
108 passed
```

CLI help after implementation:

```text
dry-run-opposition-alerts ... [--scope {all,strict}]
Supported: BOE, BOJA, DOGV, BOCYL, BOPV, BORM, BOA, DOGC,
BOP_ALICANTE, BOP_VALENCIA, BOP_CASTELLON.
```

## Deployment

Remote VPS:

```text
host: mcpspain-official-sources-vps
path: /opt/official-sources/app
before: 1045bf7
after: 66116ca
method: git fetch + git merge --ff-only FETCH_HEAD
remote status after deploy: clean
```

The deployed CLI now exposes:

```text
--scope {all,strict}
BOP_ALICANTE
BOP_VALENCIA
BOP_CASTELLON
```

No service restart was required because the CLI imports the editable source
tree under `/opt/official-sources/app/src`.

## Downstream Smoke

`oposiciones2.0` reran the real-channel smoke against the deployed VPS:

```text
source=DOGV
date_from=2026-05-20
date_to=2026-05-20
scope=strict
limit=10
```

Result:

```text
REAL CHANNEL CALLABLE: GO
REAL EXPORT FETCHED: GO
NORMALIZATION: GO
FETCH VERIFIER: GO
REVIEW LOOP PREVIEW: GO
PRODUCT WRITES: 0
PUBLICATION: NO-GO
```

Key counts:

```text
records_read=10
valid_records=10
rejected_records=0
records_written=10
db_writes=0
notifications_sent=0
product_writes=0
```

## Decision

```text
TASK-OFFICIAL-SOURCES-STRICT-CONTRACT-DEPLOY-001: CODE GO / DEPLOY GO / DOWNSTREAM SMOKE GO
```

Still out of scope:

```text
Hermes classification
DraftProcessProposal creation
autopack
scheduler/timer
publication
digest/email
```
