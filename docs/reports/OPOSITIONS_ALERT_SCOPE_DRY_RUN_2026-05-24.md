# Oposiciones alert scope dry-run

Date: 2026-05-24

Task: `TASK-OPOSITIONS-CLASSIFIER-004`

## Summary

`alert_scope` was added to the oposiciones alert-grade dry-run output.

The dry-run now separates:

```text
strict
broad
review_only
```

This keeps the two-tier product decision explicit:

```text
strict = default user-facing candidate alerts
broad = useful public-employment material for optional filters/review
review_only = weak or ambiguous material, not user-facing by default
```

No storage was implemented.
No DB schema was changed.
No `source_alerts` table was created.
No `source_candidates` were created.
No artifacts were downloaded.
No downstream output was written.

## Code changes

Code commit:

```text
6501618 feat: add alert scope to oposiciones dry-run
```

Changed:

```text
src/official_sources/cli.py
tests/test_cli.py
docs/OPOSITIONS_ALERT_GRADE_STRATEGY.md
docs/OPOSITIONS_SOURCE_ALERTS_SCHEMA.md
docs/examples/oposiciones_alerts.example.jsonl
```

Output contract change:

```yaml
alert_scope: strict | broad | review_only
```

The summary now includes:

```text
alerts_by_scope
```

## Alert types refined

The dry-run keeps existing strict-oriented types:

```text
convocatoria
bolsa
bases
lista_provisional
lista_definitiva
tribunal
fecha_examen
plazo
subsanacion
correccion
```

It now also emits broad public-employment types:

```text
ope
provision_puestos
libre_designacion
concurso_meritos
universidad_profesorado
nombramiento
adjudicacion
other
```

## Tests added

Added or updated tests for:

- strict process alerts include `alert_scope=strict`;
- bolsa, lista provisional, tribunal and fecha examen remain strict;
- OPE is typed as `ope` and scoped broad;
- libre designacion is typed as `libre_designacion` and scoped broad;
- university/professor notices are typed as `universidad_profesorado` and scoped broad;
- generic nombramiento is emitted as `review_only`;
- JSON and JSONL outputs include `alert_scope`;
- existing false-positive exclusions still exclude grants, expropriation, procurement and non-employment opposition procedures;
- dry-run remains read-only and does not create `source_candidates`.

## Local validation

```text
git diff --check: OK
rtk python -m pytest -q: 439 passed, 1 warning
rtk python -m ruff check .: OK
rtk python -m ruff format --check .: OK
```

The warning is the existing Starlette `python_multipart` pending deprecation warning.

## VPS deployment

VPS deployed commit:

```text
6501618
```

The VPS was fast-forwarded:

```text
1f71ee5 -> 6501618
```

The editable install was refreshed.

Note: the VPS virtualenv still emits non-blocking warnings about a stale invalid distribution named `~fficial-sources`. The CLI installed and executed correctly.

DB validation before and after:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## VPS dry-run

First-prototype sources:

```text
BORM,BOJA,BOCYL,DOGV
```

Range:

```text
2026-04-21 -> 2026-05-20
```

Initial command used `--limit 1000`, matching the task prompt, but the result was truncated:

```text
alerts_found=1000
truncated=true
```

The same read-only command was rerun with `--limit 2000` to capture a complete distribution:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  dry-run-opposition-alerts \
  --source BORM,BOJA,BOCYL,DOGV \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --limit 2000 \
  --format json
```

Raw output was saved outside Git:

```text
/opt/official-sources/data/reports_tmp/opositions_alert_scope_dry_run_2026-05-24_limit2000.json
```

Raw JSON was not committed.

## Dry-run result

```text
documents_scanned=3935
alerts_found=1209
truncated=false
```

Alerts by source:

| Source | Alerts |
| --- | ---: |
| BOJA | 515 |
| DOGV | 358 |
| BOCYL | 186 |
| BORM | 150 |

Alerts by scope:

| Scope | Alerts |
| --- | ---: |
| strict | 457 |
| broad | 634 |
| review_only | 118 |

Scope by source:

| Source | Strict | Broad | Review-only |
| --- | ---: | ---: | ---: |
| BORM | 90 | 47 | 13 |
| BOJA | 137 | 325 | 53 |
| BOCYL | 102 | 71 | 13 |
| DOGV | 128 | 191 | 39 |

Confidence distribution:

| Confidence | Alerts |
| --- | ---: |
| high | 408 |
| medium | 801 |

Confidence by scope:

| Scope | High | Medium |
| --- | ---: | ---: |
| strict | 408 | 49 |
| broad | 0 | 634 |
| review_only | 0 | 118 |

This is the desired shape: all broad and review-only alerts are medium-confidence, while high-confidence is reserved for strict alerts.

## Alerts by type

| Type | Alerts |
| --- | ---: |
| convocatoria | 273 |
| concurso_meritos | 182 |
| nombramiento | 151 |
| ope | 148 |
| libre_designacion | 105 |
| other | 77 |
| lista_provisional | 72 |
| universidad_profesorado | 43 |
| bolsa | 33 |
| provision_puestos | 30 |
| correccion | 28 |
| lista_definitiva | 26 |
| tribunal | 21 |
| bases | 9 |
| fecha_examen | 5 |
| adjudicacion | 5 |
| subsanacion | 1 |

Type by scope:

### Strict

```text
convocatoria=273
lista_provisional=72
bolsa=33
lista_definitiva=26
tribunal=21
correccion=21
bases=6
fecha_examen=5
```

### Broad

```text
concurso_meritos=182
ope=148
libre_designacion=105
other=77
nombramiento=44
universidad_profesorado=43
provision_puestos=30
adjudicacion=5
```

### Review-only

```text
nombramiento=107
correccion=7
bases=3
subsanacion=1
```

## Examples

Strict examples:

- BORM `tribunal`: members of tribunal plus admitted/excluded list for access tests.
- BORM `lista_provisional`: provisional admitted/excluded lists for Servicio Murciano de Salud processes.
- BOJA/BOCYL/DOGV `convocatoria`: explicit process, concurso-oposicion, turno libre, promotion, or pruebas selectivas.

Broad examples:

- BORM `universidad_profesorado`: university professor/public university access notices.
- BORM `provision_puestos`: merit/provision process for public administration posts.
- BOJA/DOGV `ope`: oferta publica de empleo notices.
- `nombramiento` after a completed process.

Review-only examples:

- generic `nombramiento` notices without enough process context;
- weak correction/subsanacion notices where process linkage is ambiguous.

## Observations

The two-tier approach is viable.

The key operational result is that the first-prototype sources produce:

```text
strict=457
broad=634
review_only=118
```

This means storage/import remains premature if the product consumes all alerts, but a strict-only JSON export is now plausible for review.

Remaining issues:

- `broad` is still larger than `strict`, so product defaults must not show broad alerts unless explicitly requested.
- `other=77` in broad remains too vague and should be refined before storage.
- `concurso_meritos` is high-volume; product scope must decide whether it belongs in broad or review-only for first users.
- strict count is still large enough that dedupe, grouping, and source-specific ranking matter before user-facing publication.

## Safety verification

Before VPS dry-run:

```text
source_candidates=163
artifact_download_attempts=518
artifact_size=30M
```

After VPS dry-run:

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

MCP privacy check:

```text
ss scan for official|mcp|python|uvicorn|fastmcp returned no matching public listener output
```

## Decision

The `alert_scope` addition should stay.

Do not create persistent `source_alerts` yet.

The next useful step is a strict-only export for product review, still as a dry-run artifact outside the DB.

## Next recommended task

```text
TASK-OPOSITIONS-ALERT-GRADE-005 — Export strict alert-grade JSON for oposiciones2.0 review
```

Constraints:

- no DB migration;
- no `source_alerts`;
- no writes to `official-sources` DB;
- no downstream publication;
- export strict alerts only from the first-prototype sources;
- include enough metadata for human review in `oposiciones2.0`.
