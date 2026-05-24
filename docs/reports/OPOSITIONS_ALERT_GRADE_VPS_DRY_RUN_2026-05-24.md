# Oposiciones alert-grade VPS dry-run

Date: 2026-05-24

Task: `TASK-OPOSITIONS-ALERT-GRADE-004`

## Summary

The `dry-run-opposition-alerts` prototype was deployed to the VPS and executed against existing metadata only.

The command remained read-only:

- no DB rows inserted, updated, or deleted;
- no `source_alerts` table exists or was created;
- no `source_candidates` were created;
- no artifacts were downloaded;
- no downstream output was written.

The classifier produced useful signal, but the first VPS run also showed heavy overmatching and a limit-biased sample. Storage or product import should not be implemented yet.

## Deployed commit

VPS repository:

```text
previous_head=843a3d0
deployed_head=a731431
pull=fast-forward
```

Relevant deployed commit:

```text
a731431 feat: add oposiciones alert-grade dry-run
```

The editable install was refreshed on the VPS before running the command.

Note: `pip install -e .` emitted non-blocking warnings about an invalid stale distribution named `~fficial-sources` inside the VPS virtualenv. The CLI installed and executed correctly.

## Command

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  dry-run-opposition-alerts \
  --source BOE,DOGV,BOCYL,BOPV,BORM \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --limit 500 \
  --format json
```

Raw output was saved outside Git:

```text
/opt/official-sources/data/reports_tmp/opositions_alert_grade_dry_run_2026-05-24.json
```

The raw JSON was not committed.

## Sources and range

Date range:

```text
2026-04-21 -> 2026-05-20
```

Requested sources:

```text
BOE,DOGV,BOCYL,BOPV,BORM
```

Existing metadata in range:

| Source | Documents in range |
| --- | ---: |
| BOE | 3984 |
| DOGV | 1113 |
| BOCYL | 773 |
| BOPV | 489 |
| BORM | 549 |

Total documents scanned:

```text
6908
```

## Result

The run reached the configured limit:

```text
alerts_found=500
limit=500
```

This means the output is truncated. The run is valid as a safety and signal check, but not as a full coverage measurement.

Alerts by source:

| Source | Alerts |
| --- | ---: |
| BOE | 261 |
| DOGV | 239 |

No BOCYL, BOPV or BORM alerts appeared in this output because the run hit `--limit 500` before those sources contributed visible output. Future measurement should run per source or with a higher limit.

Alerts by type:

| Type | Alerts |
| --- | ---: |
| convocatoria | 396 |
| other | 31 |
| lista_provisional | 18 |
| nombramiento | 14 |
| bolsa | 11 |
| lista_definitiva | 11 |
| correccion | 10 |
| bases | 4 |
| adjudicacion | 3 |
| subsanacion | 2 |

Confidence distribution:

| Confidence | Alerts |
| --- | ---: |
| high | 433 |
| medium | 67 |
| low | 0 |

## Matched rules

Top matched rules:

| Rule | Count |
| --- | ---: |
| `strong_convocatoria` | 396 |
| `medium_process_context` | 31 |
| `strong_lista_provisional` | 18 |
| `strong_nombramiento` | 14 |
| `strong_bolsa` | 11 |
| `strong_lista_definitiva` | 11 |
| `strong_correccion` | 10 |
| `noise_present:medio_ambiente` | 5 |
| `strong_bases` | 4 |
| `strong_adjudicacion` | 3 |
| `strong_subsanacion` | 2 |

Excluded rule counts:

| Rule | Count |
| --- | ---: |
| `excluded_noise:licitacion` | 337 |
| `excluded_noise:subvenciones` | 155 |
| `excluded_noise:medio_ambiente` | 87 |
| `excluded_missing_process_context` | 77 |
| `excluded_noise:urbanismo` | 70 |
| `strong_correccion` | 42 |
| `strong_nombramiento` | 35 |
| `excluded_noise:contrato_de_servicios` | 16 |
| `excluded_noise:premios` | 10 |
| `excluded_noise:convenio` | 9 |
| `excluded_noise:subvencion` | 9 |
| `excluded_noise:convenios` | 1 |

## Dedupe observations

```text
total_groups=486
duplicate_group_count=11
```

The dedupe contract is sufficient for a first dry-run export, but future reports should expose example duplicate groups so reviewers can distinguish true duplicate notices from related BOE/autonomic/provincial repeats.

## Signal observations

Useful signal exists:

- DOGV surfaced an `oferta pública de empleo 2026` item as a plausible alert.
- The classifier detects common public employment vocabulary such as convocatoria, bolsa, lista provisional, lista definitiva, correccion and nombramiento.
- Noise exclusions for licitacion, subvenciones, urbanismo, medio ambiente and contract notices are firing.

However, the current classifier is too broad for storage:

- `strong_convocatoria` overmatches non-oposiciones items when titles use generic legal formulas like `se convoca`.
- BOE scholarship notices matched as `convocatoria`, but they are not public employment alerts.
- An expropriation notice for a photovoltaic project matched because it contains `se convoca`.
- Procurement notices involving `personal laboral` surfaced in medium-confidence samples.
- A wine DOP notice matched through `procedimiento nacional de oposición`, which is a semantic false positive unrelated to public employment.

## False positive examples

Observed false positive patterns:

```text
becas / ayudas educativas
expropiacion / information publica
contratos de suministro o servicios
licitacion
personal laboral inside procurement context
procedimiento nacional de oposicion for non-employment regulatory process
```

The main refinement need is to require public-employment context for generic convocatoria/process terms instead of treating them as strong enough by themselves.

## Contract assessment

The JSON/JSONL output contract is adequate for a prototype dry-run.

Recommended additions before any consumer import:

- explicit `run_id`;
- explicit `is_limit_truncated`;
- per-source scan counters in the summary;
- optional `excluded_samples` for audit reports;
- duplicate group examples, not only counts.

These are output improvements only. They do not require DB schema changes.

## Safety verification

Pre-run counts:

```text
source_candidates=163
artifact_download_attempts=518
artifact_size=30M
```

Post-run counts:

```text
source_candidates=163
artifact_download_attempts=518
artifact_size=30M
```

Verification:

```text
source_candidates unchanged: yes
artifact_download_attempts unchanged: yes
artifact size unchanged: yes
artifacts downloaded: no
DB writes: no
downstream writes: no
```

DB validation before and after:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

MCP privacy check:

```text
ss scan for official|mcp|python|uvicorn|fastmcp returned no matching public listener output
```

## Decision

The prototype is useful as a read-only measurement tool, but the classifier is not ready for persistent `source_alerts`, product import, or user-facing alerts.

Do not implement alert storage yet.

## Next recommended task

Recommended next task:

```text
TASK-OPOSITIONS-CLASSIFIER-002 — Refine classifier from VPS dry-run findings
```

Focus:

- reduce generic `convocatoria` false positives;
- require public-employment context for process terms;
- exclude scholarship/grant contexts;
- exclude expropriation/informacion publica contexts;
- exclude procurement contexts even when titles mention `personal laboral`;
- handle `procedimiento nacional de oposicion` outside employment as noise.

Also recommended:

```text
TASK-OPOSITIONS-ALERT-GRADE-004B — Per-source read-only measurement
```

Run the dry-run per source to remove the `--limit 500` bias:

```bash
official-sources dry-run-opposition-alerts --source BOE --date-from 2026-04-21 --date-to 2026-05-20 --limit 1000 --format json
official-sources dry-run-opposition-alerts --source DOGV --date-from 2026-04-21 --date-to 2026-05-20 --limit 1000 --format json
official-sources dry-run-opposition-alerts --source BOCYL --date-from 2026-04-21 --date-to 2026-05-20 --limit 1000 --format json
official-sources dry-run-opposition-alerts --source BOPV --date-from 2026-04-21 --date-to 2026-05-20 --limit 1000 --format json
official-sources dry-run-opposition-alerts --source BORM --date-from 2026-04-21 --date-to 2026-05-20 --limit 1000 --format json
```

No storage or DB migration should be done before those refinements.
