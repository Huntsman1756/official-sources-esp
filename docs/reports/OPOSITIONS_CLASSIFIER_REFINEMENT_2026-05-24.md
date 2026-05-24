# Oposiciones alert-grade classifier refinement

Date: 2026-05-24

Task: `TASK-OPOSITIONS-CLASSIFIER-002`

## Summary

The alert-grade oposiciones classifier was refined after the per-source VPS baseline showed excessive noise.

The main change is that generic call language is no longer enough by itself:

```text
convocatoria
se convoca
resolucion
anuncio
```

The classifier now requires public-employment/process context for generic convocatoria-style matches and excludes common non-oposiciones contexts.

No storage was added.
No DB schema changed.
No `source_alerts` table was created.
No `source_candidates` were created.
No artifacts were downloaded.

## Code changes

Code commit:

```text
1f71ee5 fix: refine oposiciones alert classifier
```

Changed file:

```text
src/official_sources/cli.py
```

Rules changed:

- added broader public-employment context terms;
- added hard exclusions for grants, procurement, expropriation and non-employment opposition procedures;
- made `convocatoria` / `se convoca` insufficient unless process context is present;
- preserved `medio ambiente` as a confidence/noise signal instead of an automatic exclusion, because valid public-employment notices can include environmental job categories;
- kept the dry-run output read-only and unchanged structurally.

Added process context:

```text
admitidos
excluidos
plazas
cuerpo
escala
subescala
turno libre
promocion interna
tribunal calificador
fecha de examen
```

Added exclusion/noise coverage:

```text
beca
becas
ayuda
ayudas
contratacion publica
contratacion
licitacion
contrato
contrato de servicios
expropiacion
expropiaciones
levantamiento de actas
actas previas
ocupacion
informacion publica
subvencion
subvenciones
premios
convenio
convenios
urbanismo
autorizacion ambiental
procedimiento nacional de oposicion
```

## Tests added

Changed file:

```text
tests/test_cli.py
```

New coverage:

- `convocatoria` alone is not enough;
- `se convoca` alone is not enough;
- scholarship/grant style notices are excluded;
- expropriation notices are excluded;
- procurement and contract notices are excluded even if they mention `personal laboral`;
- non-employment `procedimiento nacional de oposicion` is excluded;
- valid `proceso selectivo` is detected;
- valid `bolsa de trabajo` is detected;
- valid `lista provisional` is detected;
- valid `tribunal` is detected;
- valid `fecha de examen` is detected;
- specific alert type priority remains ahead of generic `convocatoria`;
- dry-run still creates no `source_candidates`.

## Local validation

Validation before VPS deploy:

```text
git diff --check: OK
rtk python -m pytest -q: 438 passed, 1 warning
rtk python -m ruff check .: OK
rtk python -m ruff format --check .: OK
```

The warning is the existing Starlette `python_multipart` pending deprecation warning.

## VPS deployment

VPS deployed commit:

```text
1f71ee5
```

The VPS was fast-forwarded from:

```text
cec0fdd -> 1f71ee5
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

## VPS dry-run command

Per-source read-only command shape:

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

Sources rerun:

```text
BOE
BOJA
DOGV
BOCYL
BOPV
BORM
```

Raw JSON was saved outside Git:

```text
/opt/official-sources/data/reports_tmp/opositions_alert_classifier_refined_2026-05-24/
```

Raw JSON was not committed.

## Baseline comparison

No source hit `--limit 1000`.

| Source | Documents | Old alerts | New alerts | Reduction |
| --- | ---: | ---: | ---: | ---: |
| BOE | 3984 | 261 | 7 | 97.32% |
| BOJA | 1500 | 426 | 227 | 46.71% |
| DOGV | 1113 | 371 | 307 | 17.25% |
| BOCYL | 773 | 223 | 162 | 27.35% |
| BOPV | 489 | 97 | 48 | 50.52% |
| BORM | 549 | 151 | 130 | 13.91% |

Total:

```text
old_alerts=1529
new_alerts=881
reduction=42.38%
```

The refined alert rate over the measured set is:

```text
881 / 8408 = 10.48%
```

This is a substantial improvement, but still too high for persistent storage or product import without another review/refinement pass.

## New alerts by source and type

### BOE

```text
documents_scanned=3984
alerts_found=7
confidence: medium=7
types: other=7
```

BOE now mostly surfaces Banco de España and auxiliary conversation plaza notices. The previous scholarship, expropriation and procurement false positives were removed from the sample.

### BOJA

```text
documents_scanned=1500
alerts_found=227
confidence: high=174, medium=53
```

Types:

```text
convocatoria=163
other=33
correccion=10
lista_provisional=7
bases=5
nombramiento=3
bolsa=2
fecha_examen=1
lista_definitiva=1
subsanacion=1
tribunal=1
```

BOJA remains high-volume but cleaner. SAS and Junta employment notices are preserved.

### DOGV

```text
documents_scanned=1113
alerts_found=307
confidence: high=201, medium=106
```

Types:

```text
convocatoria=157
other=47
nombramiento=33
lista_provisional=21
bolsa=15
lista_definitiva=14
correccion=12
adjudicacion=5
bases=2
fecha_examen=1
```

DOGV still has volume, but visible samples are mostly employment-process notices.

### BOCYL

```text
documents_scanned=773
alerts_found=162
confidence: high=113, medium=49
```

Types:

```text
convocatoria=86
other=42
lista_definitiva=9
bolsa=7
lista_provisional=7
correccion=5
tribunal=4
bases=1
fecha_examen=1
```

BOCYL improved, but `plazas` can still create noise in environmental-impact notices where it means farm capacity rather than public employment vacancies.

### BOPV

```text
documents_scanned=489
alerts_found=48
confidence: high=6, medium=42
```

Types:

```text
other=32
nombramiento=7
convocatoria=4
correccion=2
bases=1
lista_definitiva=1
subsanacion=1
```

BOPV became much more conservative. Remaining items are mostly provision, appointment and university access/professor notices. Product scope must decide whether all of those are wanted alerts.

### BORM

```text
documents_scanned=549
alerts_found=130
confidence: high=77, medium=53
```

Types:

```text
lista_provisional=37
other=30
convocatoria=29
tribunal=16
bolsa=9
nombramiento=3
fecha_examen=2
lista_definitiva=2
bases=1
correccion=1
```

BORM still has a strong signal, especially tribunal/lista provisional records. University professor and university internal scale notices remain a scope decision rather than a pure parser bug.

## False positives reduced

The refinement reduced the main false positive classes identified in the baseline:

```text
becas / ayudas educativas
expropiaciones
licitaciones / contratacion publica
subvenciones
convenios
procedimiento nacional de oposicion not employment-related
generic convocatoria without public-employment context
```

Most of the old BOE noise disappeared:

```text
BOE old=261
BOE new=7
reduction=97.32%
```

## Remaining risks

Remaining risks before storage:

- `plazas` is ambiguous and can mean public-employment vacancies or physical capacity in environmental/agricultural notices.
- `medio ambiente` appears in valid public-employment roles and in non-employment environmental notices; it should stay as a caution signal, not a hard exclusion.
- BOJA/DOGV still have high volumes because they publish many real employment-process notices, but type assignment can still overuse `convocatoria`.
- BORM university professor and university internal scale notices need a product decision: include academic public employment, downrank, or exclude.
- BOPV free-designation/provision/appointment records need product-scope policy.
- `other` remains too broad and should be split or downranked before product import.

Possible false negatives:

- Some scholarship-like training notices may be excluded even if a future product wanted broader education/workforce alerts. This is acceptable for an oposiciones-only layer.
- Some contract or project-funded research hiring notices may be excluded if they use procurement/grant vocabulary. That is acceptable until product scope explicitly includes research-contract alerts.

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

The refinement is useful and should remain.

Do not implement `source_alerts` storage yet.

The classifier is now good enough for another controlled export/review pass, not for automatic product import.

## Next recommended task

Recommended:

```text
TASK-OPOSITIONS-CLASSIFIER-003 — Review refined per-source samples and scope decisions
```

Focus:

- decide whether university professor notices are in scope;
- decide whether free-designation/provision notices are in scope;
- split or downrank broad `other`;
- refine ambiguous `plazas`;
- improve type assignment for list/appointment/final-result records.

After that, if quality is acceptable:

```text
TASK-OPOSITIONS-ALERT-GRADE-005 — Export dry-run alerts for oposiciones2.0 review
```

Still without DB migration or persistent `source_alerts`.
