# Oposiciones alert-grade per-source baseline

Date: 2026-05-24

Task: `TASK-OPOSITIONS-ALERT-GRADE-004B`

## Summary

This task reran the `dry-run-opposition-alerts` prototype per source to remove the global `--limit 500` bias observed in the first VPS dry-run.

The run was read-only:

- no DB rows inserted, updated, or deleted;
- no `source_alerts` table created;
- no `source_candidates` created;
- no artifacts downloaded;
- no downstream output written.

The per-source baseline confirms real signal across the autonomous sources, but also confirms that the classifier is still too broad for storage or user-facing alert delivery.

## VPS state

VPS deployed commit:

```text
cec0fdd docs: add oposiciones alert-grade VPS dry-run report
```

DB validation before and after:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

The editable install remained functional. The VPS virtualenv still emits a non-blocking warning about a stale invalid distribution named `~fficial-sources`; the CLI executed correctly.

## Commands

Main per-source command shape:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  dry-run-opposition-alerts \
  --source "$SOURCE" \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --limit 1000 \
  --format json
```

Executed sources:

```text
BOE
DOGV
BOCYL
BOPV
BORM
BOJA
```

BOJA was included as an optional source because it had metadata for the target range and the CLI supports it.

BOA and DOGC were not run because they had no metadata in the target range:

```text
BOA=0
DOGC=0
```

Raw JSON outputs were saved outside Git:

```text
/opt/official-sources/data/reports_tmp/opositions_alert_grade_per_source_2026-05-24/
```

The raw JSON files were not committed.

## Source inventory

Target range:

```text
2026-04-21 -> 2026-05-20
```

Documents available in range:

| Source | Documents |
| --- | ---: |
| BOE | 3984 |
| BOJA | 1500 |
| DOGV | 1113 |
| BOCYL | 773 |
| BORM | 549 |
| BOPV | 489 |
| BOA | 0 |
| DOGC | 0 |

Total measured documents:

```text
8408
```

## Per-source results

No measured source hit `--limit 1000`.

| Source | Documents scanned | Alerts found | Alert rate | Truncated |
| --- | ---: | ---: | ---: | --- |
| BOE | 3984 | 261 | 6.55% | no |
| BOJA | 1500 | 426 | 28.40% | no |
| DOGV | 1113 | 371 | 33.33% | no |
| BOCYL | 773 | 223 | 28.85% | no |
| BOPV | 489 | 97 | 19.84% | no |
| BORM | 549 | 151 | 27.50% | no |

Total alerts:

```text
1529
```

The rates are too high for storage. They are acceptable for a raw classifier baseline, but not for `source_alerts` creation or product import.

## Alert type distribution

### BOE

| Type | Alerts |
| --- | ---: |
| convocatoria | 255 |
| other | 4 |
| subsanacion | 2 |

Confidence:

```text
high=257
medium=4
low=0
```

Top terms:

```text
convocatoria=225
se convoca=30
personal laboral=3
subsanacion=2
licitacion=1
oposicion=1
```

### BOJA

| Type | Alerts |
| --- | ---: |
| convocatoria | 365 |
| other | 27 |
| bases | 8 |
| correccion | 8 |
| lista_provisional | 7 |
| nombramiento | 3 |
| bolsa | 2 |
| lista_definitiva | 2 |
| subsanacion | 2 |
| fecha_examen | 1 |
| tribunal | 1 |

Confidence:

```text
high=372
medium=54
low=0
```

Top terms:

```text
convocatoria=169
se convoca=138
proceso selectivo=61
pruebas selectivas=33
personal funcionario=12
oposicion=9
empleo publico=9
correccion=8
```

### DOGV

| Type | Alerts |
| --- | ---: |
| convocatoria | 204 |
| other | 60 |
| nombramiento | 28 |
| lista_provisional | 21 |
| bolsa | 16 |
| correccion | 16 |
| lista_definitiva | 14 |
| bases | 6 |
| adjudicacion | 5 |
| fecha_examen | 1 |

Confidence:

```text
high=248
medium=123
low=0
```

Top terms:

```text
convocatoria=96
se convoca=92
oposiciones=54
empleo publico=52
pruebas selectivas=46
proceso selectivo=46
nombramientos=27
lista provisional=21
```

### BOCYL

| Type | Alerts |
| --- | ---: |
| convocatoria | 149 |
| other | 33 |
| bolsa | 9 |
| lista_definitiva | 9 |
| lista_provisional | 7 |
| correccion | 5 |
| tribunal | 4 |
| bases | 3 |
| subsanacion | 3 |
| fecha_examen | 1 |

Confidence:

```text
high=179
medium=44
low=0
```

Top terms:

```text
convocatoria=82
proceso selectivo=48
se convoca=32
empleo publico=22
bolsa de empleo=9
relacion definitiva=9
oposicion=7
relacion provisional=7
```

### BOPV

| Type | Alerts |
| --- | ---: |
| convocatoria | 72 |
| other | 11 |
| bases | 5 |
| subsanacion | 5 |
| correccion | 2 |
| lista_definitiva | 1 |
| nombramiento | 1 |

Confidence:

```text
high=78
medium=19
low=0
```

Top terms:

```text
convocatoria=40
se convoca=33
empleo publico=7
subsanacion=5
convenio=3
bases reguladoras=3
personal laboral=2
correccion de errores=2
```

### BORM

| Type | Alerts |
| --- | ---: |
| convocatoria | 61 |
| lista_provisional | 37 |
| tribunal | 16 |
| other | 12 |
| bases | 9 |
| bolsa | 9 |
| fecha_examen | 2 |
| lista_definitiva | 2 |
| nombramiento | 2 |
| correccion | 1 |

Confidence:

```text
high=116
medium=35
low=0
```

Top terms:

```text
convocatoria=44
provisional de aspirantes=33
relacion provisional=25
miembros del tribunal=16
pruebas selectivas=16
lista provisional=12
medio ambiente=11
bases reguladoras=9
```

## Dedupe observations

Each per-source run reported no duplicate groups:

| Source | Groups | Duplicate groups |
| --- | ---: | ---: |
| BOE | 261 | 0 |
| BOJA | 426 | 0 |
| DOGV | 371 | 0 |
| BOCYL | 223 | 0 |
| BOPV | 97 | 0 |
| BORM | 151 | 0 |

This is expected because the runs were isolated by source. Cross-source grouping still needs a separate combined analysis once the classifier is less noisy.

## False positive observations

The baseline confirms the main false positive classes from the first global run:

```text
becas / ayudas educativas
expropiaciones
licitaciones / contratacion publica
subvenciones
procedimiento nacional de oposicion unrelated to public employment
nombramientos not related to selection process
urbanismo / medio ambiente
convenios / personal laboral in collective agreement context
```

Observed source-specific patterns:

- BOE: many `convocatoria` matches are not employment notices; they include scholarships, expropriation notices and generic administrative calls.
- BOJA: strong signal exists for SAS and public employment, but `se convoca` also catches scholarships, expropriations and university non-oposiciones notices.
- DOGV: useful public employment signals appear, but generic assembly calls and research-contract notices remain noisy.
- BOCYL: good signal for local and regional employment, but education grants and Erasmus-type items still leak.
- BOPV: provision/free-designation notices may be relevant depending on product scope, but grants and convenios leak.
- BORM: strong tribunal/lista provisional signal exists, but `medio ambiente` appears as a noisy matched term even inside real process notices and should not automatically demote true employment items.

## Source quality ranking

Current ranking for alert-grade oposiciones monitoring, based on this baseline:

| Rank | Source | Assessment |
| ---: | --- | --- |
| 1 | BORM | Best structured signal for tribunal/lista/proceso sequences; lower volume and useful titles. |
| 2 | BOCYL | Good local/regional employment signal, moderate volume, manageable refinement. |
| 3 | DOGV | High volume but rich process vocabulary; useful after excluding generic convocatorias and research-contract noise. |
| 4 | BOJA | High volume and strong employment content, but too many generic convocatoria matches. |
| 5 | BOPV | Useful, but product scope must decide whether libre designacion/provision notices are alerts. |
| 6 | BOE | Broadest and noisiest; needs stronger employment-context gating before storage. |

## Recommended classifier refinements

Before any storage/import:

1. Require public-employment context for `convocatoria` and `se convoca`.
2. Do not treat `convocatoria` alone as high confidence.
3. Exclude or downrank scholarships/grants:

```text
beca
becas
ayuda
ayudas
subvencion
subvenciones
```

unless the alert product explicitly includes grants, which this oposiciones layer should not.

4. Exclude expropriation and public-information contexts:

```text
expropiacion
actas previas
ocupacion
informacion publica
levantamiento de actas
```

5. Exclude procurement and contracting contexts:

```text
licitacion
formalizacion de contratos
contrato de servicios
suministro
expediente de contratacion
```

6. Treat `personal laboral` as weak unless paired with:

```text
proceso selectivo
pruebas selectivas
concurso-oposicion
bolsa
oferta publica de empleo
aspirantes
admitidos
excluidos
tribunal
```

7. Exclude `procedimiento nacional de oposicion` when it refers to non-employment administrative opposition procedures.
8. Improve type assignment so `listas provisionales/definitivas` are not classified as generic `convocatoria`.
9. Add source-specific confidence tuning for BOE and BOJA, where generic legal wording is especially noisy.

## Schema contract assessment

The current dry-run JSON contract remains sufficient for measurement.

Recommended additions before product import:

- `run_id`;
- `source_run_id`;
- `is_limit_truncated`;
- per-source scan counters in combined runs;
- `exclusion_reason` for sampled exclusions;
- duplicate group examples for cross-source grouping.

No DB migration should be created yet.

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

MCP privacy check:

```text
ss scan for official|mcp|python|uvicorn|fastmcp returned no matching public listener output
```

## Decision

The per-source baseline is useful and removes the original `--limit 500` bias.

However, the classifier is not ready for persistent `source_alerts`, product import, or user-facing alert delivery.

Do not implement storage yet.

## Next recommended task

```text
TASK-OPOSITIONS-CLASSIFIER-002 — Refine alert-grade classifier from per-source baseline
```

The first refinement should be test-driven and focus on reducing generic `convocatoria` false positives while preserving high-value employment-process signals such as:

```text
bolsa de empleo
oferta publica de empleo
proceso selectivo
pruebas selectivas
lista provisional
lista definitiva
tribunal
fecha examen
concurso-oposicion
```
