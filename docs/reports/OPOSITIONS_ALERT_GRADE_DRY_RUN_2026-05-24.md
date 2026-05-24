# Oposiciones Alert-Grade Dry-Run Prototype

Date: 2026-05-24

Task: `TASK-OPOSITIONS-ALERT-GRADE-003`

Scope: integrate alert-grade design inputs and implement a minimal read-only dry-run prototype from existing `official_documents` metadata.

## Summary

Implemented a read-only CLI prototype:

```bash
official-sources dry-run-opposition-alerts \
  --source BOE,DOGV,BOCYL,BOPV,BORM \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --limit 200 \
  --format json
```

Supported formats:

```text
json
jsonl
```

The command reads locally stored `official_documents` metadata only.

It does not:

```text
create source_candidates
write source_alerts
modify DB schema
download artifacts
write downstream
touch VPS
```

## Integrated Inputs

Parallel prep reports integrated locally:

```text
docs/reports/OPOSITIONS_DETERMINISTIC_CLASSIFIER_DESIGN_2026-05-24.md
docs/reports/OPOSITIONS_ALERT_DRY_RUN_OUTPUT_CONTRACT_2026-05-24.md
docs/reports/OPOSITIONS_SOURCE_READINESS_RANKING_2026-05-24.md
docs/examples/oposiciones_alerts.example.jsonl
```

## Classifier Prototype

The prototype uses deterministic metadata rules over:

```text
title
department
section
document_type
```

Supported alert types:

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
nombramiento
adjudicacion
other
```

Important rule behavior:

```text
specific alert types win over generic process context
nombramiento requires process context
correccion/plazo/adjudicacion require process context
licitacion/subvenciones/convenios/urbanismo/medio ambiente are excluded unless process context is present
```

Output fields include:

```text
source_document_id
source_candidate_id=null
source_code
source_name
territory_code
territory_name
publication_date
title
normalized_title
official_url
document_identifier
issuing_body
section
alert_type
confidence
matched_terms
matched_rules
dedupe_key
related_group_key
review_status=new
evidence_grade_status=none
metadata_json
```

## Fixture Coverage

Created synthetic JSONL examples:

```text
docs/examples/oposiciones_alerts.example.jsonl
```

Covered positive families:

```text
convocatoria
bolsa
lista_provisional
lista_definitiva
tribunal
fecha_examen
subsanacion
correccion
```

Covered false-positive families:

```text
licitacion
subvencion
nombramiento unrelated
```

## Local Test Result

Targeted validation:

```bash
rtk python -m pytest tests/test_cli.py -q -k "opposition_alerts"
```

Result:

```text
2 passed
```

Tested behavior:

```text
JSON output works
JSONL output works
multiple sources can be scanned
noise exclusions remove licitacion
unrelated nombramiento is excluded
process-related nombramiento is retained
source_candidates remain unchanged
source_candidate_id is null
review_status defaults to new
evidence_grade_status defaults to none
```

## Dry-Run Result

No VPS or persistent local metadata dry-run was run in this task.

Reason:

```text
The task explicitly avoids VPS writes and DB changes.
No local persistent metadata database was present in the workspace.
The prototype was validated against temporary SQLite databases created by tests.
```

The CLI is ready for a future read-only run against a controlled metadata database.

## Known Limitations

Current prototype limitations:

```text
metadata-only title/department/section/document_type matching
no full-text PDF/HTML/XML parsing
no source-specific classifier calibration yet
no cross-source dedupe persistence
no source_alerts table
no oposiciones2.0 import command
no human review UI
```

Potential quality risks:

```text
generic convocatoria noise
employment terms in non-public-employment notices
appointment notices unrelated to processes
source-specific language variants
provincial title truncation
duplicate notices across BOE/autonomic/provincial sources
```

## Next Recommended Tasks

Recommended next step:

```text
TASK-OPOSITIONS-ALERT-GRADE-004 - Run controlled read-only alert dry-run on VPS metadata
```

Rules:

```text
read-only
no DB writes
no migrations
no source_candidates
no artifacts
no downstream
capture documents_scanned, alerts_found, alerts_by_source, alerts_by_type, noise samples
```

Alternative local-first task:

```text
TASK-OPOSITIONS-CLASSIFIER-002 - Calibrate deterministic classifier on existing BOE/DOGV/BOCYL/BOPV/BORM samples
```
