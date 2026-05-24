# Oposiciones Alert Dry-Run Output Contract

Date: 2026-05-24

Task: `TASK-OPOSITIONS-ALERT-CONTRACT-001`

Scope: define the JSON output contract for alert-grade dry-run exports for oposiciones/public
employment monitoring.

This is a documentation-only contract. No DB schema was changed, no code was implemented, no tests
were modified, no VPS operation was run, no candidates were created, no artifacts were downloaded, no
downstream project was touched, and no EduAyudas, `la-ayuda`, or `oposiciones2.0` work was performed.

## Format Decision

Decision:

```text
Use JSONL as the primary export format.
Allow a JSON array only for small human review samples.
```

Rationale:

- JSONL supports streaming, append-safe logs, large source windows, and partial failure handling.
- Each line can be validated independently and imported idempotently by `oposiciones2.0`.
- A JSON array is convenient for fixtures and review snippets, but it forces the full export into one
  document and is a weaker fit for scheduled dry-runs.

Primary file naming convention:

```text
opposition-alerts-dry-run-YYYYMMDDTHHMMSSZ.jsonl
```

Optional companion summary:

```text
opposition-alerts-dry-run-YYYYMMDDTHHMMSSZ.summary.json
```

## JSONL Record Envelope

Each JSONL line must be one UTF-8 JSON object.

Record types:

```text
alert
warning
error
summary
```

Recommended order:

```text
alert records first
warning and error records as they occur
one final summary record
```

The final `summary` line is required even when zero alerts are produced.

## Alert Record Required Fields

Required fields for `record_type=alert`:

```text
schema_version
record_type
run_id
source_code
source_name
territory_code
territory_name
publication_date
detected_at
title
normalized_title
official_url
alert_type
confidence
matched_terms
matched_rules
dedupe_key
dry_run
write_intent
review_status
evidence_grade_status
```

Required semantics:

- `schema_version` must start at `opposition_alert_dry_run.v1`.
- `record_type` must be `alert`.
- `run_id` must be stable for every line in one export.
- `publication_date` must use `YYYY-MM-DD`.
- `detected_at` must be an ISO-8601 UTC timestamp.
- `official_url` must point to the official source page or official document landing page.
- `matched_terms` must be an array, empty only when a deterministic non-term rule matched.
- `matched_rules` must identify the classifier rules that produced the alert.
- `dedupe_key` must be deterministic for the same source notice and alert type.
- `dry_run` must be `true`.
- `write_intent` must be `none`.
- `review_status` must be `new`.
- `evidence_grade_status` must be `none`.

Allowed `alert_type` values:

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

Allowed `confidence` values:

```text
high
medium
low
```

## Alert Record Optional Fields

Optional fields for `record_type=alert`:

```text
bulletin_identifier
document_identifier
issuing_body
section
subsection
source_document_id
official_document_hash
language
municipality
province_code
province_name
employment_body
role_name
vacancy_count
deadline_date
deadline_text
exam_date
list_status
related_group_key
source_metadata
classifier_notes
privacy_flags
```

Rules for optional fields:

- Unknown optional scalar values must be `null`, not omitted, when the field is part of a fixed export
  profile.
- `source_document_id` may reference local official-sources metadata, but consumers must treat it as an
  opaque upstream pointer.
- `official_document_hash` is optional because alert-grade dry-runs may be metadata-only.
- `privacy_flags` should flag personal-data-heavy list notices before product import.
- `source_metadata` may contain source-specific fields, but consumers must not rely on it for core
  deduplication.

## Dedupe Fields

Required same-source dedupe fields:

```text
source_code
alert_type
dedupe_key
```

Recommended `dedupe_key` priority:

```text
1. source_code + document_identifier + alert_type
2. source_code + canonical official_url + alert_type
3. source_code + publication_date + normalized_title + issuing_body + alert_type
```

Optional cross-source grouping:

```text
related_group_key
```

`related_group_key` should group repeated notices about the same process across BOE, autonomous,
provincial, and local bulletins. It must not collapse the upstream records themselves; each official
publication remains its own alert record.

## Sample JSONL Output

```jsonl
{"schema_version":"opposition_alert_dry_run.v1","record_type":"alert","run_id":"opositions-alert-dry-run-20260524T090000Z","source_code":"BOE","source_name":"Boletin Oficial del Estado","territory_code":"ES","territory_name":"Espana","publication_date":"2026-05-24","detected_at":"2026-05-24T09:00:00Z","title":"Resolucion por la que se convocan pruebas selectivas para ingreso en el Cuerpo Administrativo","normalized_title":"resolucion por la que se convocan pruebas selectivas para ingreso en el cuerpo administrativo","official_url":"https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-00001","bulletin_identifier":"BOE-A-2026-00001","document_identifier":"BOE-A-2026-00001","issuing_body":"Ministerio de Hacienda","section":"II. Autoridades y personal","alert_type":"convocatoria","confidence":"high","matched_terms":["pruebas selectivas","ingreso","cuerpo administrativo"],"matched_rules":["oposiciones.convocatoria.pruebas_selectivas","oposiciones.convocatoria.ingreso"],"dedupe_key":"BOE:BOE-A-2026-00001:convocatoria","related_group_key":"convocatoria:cuerpo-administrativo:ministerio-hacienda:2026","dry_run":true,"write_intent":"none","review_status":"new","evidence_grade_status":"none","privacy_flags":[],"source_metadata":{"source_document_id":12345}}
{"schema_version":"opposition_alert_dry_run.v1","record_type":"alert","run_id":"opositions-alert-dry-run-20260524T090000Z","source_code":"BOCM","source_name":"Boletin Oficial de la Comunidad de Madrid","territory_code":"ES-MD","territory_name":"Comunidad de Madrid","publication_date":"2026-05-24","detected_at":"2026-05-24T09:00:02Z","title":"Correccion de errores de la convocatoria de una bolsa de empleo temporal","normalized_title":"correccion de errores de la convocatoria de una bolsa de empleo temporal","official_url":"https://www.bocm.es/boletin/CM_Orden_BOCM/2026/05/24/BOCM-20260524-10.PDF","bulletin_identifier":"BOCM-20260524-10","document_identifier":"BOCM-20260524-10","issuing_body":"Ayuntamiento de ejemplo","section":"III. Administracion Local","alert_type":"correccion","confidence":"medium","matched_terms":["correccion de errores","bolsa de empleo"],"matched_rules":["oposiciones.correccion.correccion_errores","oposiciones.bolsa.bolsa_empleo"],"dedupe_key":"BOCM:BOCM-20260524-10:correccion","related_group_key":null,"dry_run":true,"write_intent":"none","review_status":"new","evidence_grade_status":"none","privacy_flags":["local_entity_notice"],"source_metadata":{"source_document_id":67890}}
```

## Warning Record Shape

Warning records describe recoverable issues. They must not imply that any write occurred.

Required fields:

```text
schema_version
record_type
run_id
severity
code
message
source_code
occurred_at
dry_run
write_intent
```

Optional fields:

```text
publication_date
official_url
document_identifier
details
```

Sample:

```json
{
  "schema_version": "opposition_alert_dry_run.v1",
  "record_type": "warning",
  "run_id": "opositions-alert-dry-run-20260524T090000Z",
  "severity": "warning",
  "code": "missing_document_identifier",
  "message": "The source record had an official URL but no stable document identifier.",
  "source_code": "BOP",
  "publication_date": "2026-05-24",
  "official_url": "https://example.invalid/bop/notice/123",
  "document_identifier": null,
  "occurred_at": "2026-05-24T09:00:03Z",
  "dry_run": true,
  "write_intent": "none",
  "details": {
    "fallback_dedupe_strategy": "source_code + publication_date + normalized_title + issuing_body + alert_type"
  }
}
```

## Error Record Shape

Error records describe non-recoverable failures for one source, date, or record. They do not mean the
whole export failed unless the summary says so.

Required fields:

```text
schema_version
record_type
run_id
severity
code
message
source_code
occurred_at
retryable
dry_run
write_intent
```

Optional fields:

```text
publication_date
stage
details
```

Sample:

```json
{
  "schema_version": "opposition_alert_dry_run.v1",
  "record_type": "error",
  "run_id": "opositions-alert-dry-run-20260524T090000Z",
  "severity": "error",
  "code": "source_window_unavailable",
  "message": "The source could not provide metadata for the requested publication date.",
  "source_code": "BOP",
  "publication_date": "2026-05-24",
  "stage": "metadata_scan",
  "occurred_at": "2026-05-24T09:00:04Z",
  "retryable": true,
  "dry_run": true,
  "write_intent": "none",
  "details": {
    "http_status": 503
  }
}
```

## Summary Metrics Shape

The final JSONL line must be a `summary` record. The same object may also be written to the optional
`.summary.json` companion file.

Required fields:

```text
schema_version
record_type
run_id
started_at
finished_at
dry_run
write_intent
status
sources_requested
sources_scanned
date_from
date_to
documents_scanned
alerts_emitted
warnings_count
errors_count
duplicates_suppressed
by_source
by_alert_type
by_confidence
no_write_guarantees
```

Allowed `status` values:

```text
success
partial_success
failed
```

Sample:

```json
{
  "schema_version": "opposition_alert_dry_run.v1",
  "record_type": "summary",
  "run_id": "opositions-alert-dry-run-20260524T090000Z",
  "started_at": "2026-05-24T09:00:00Z",
  "finished_at": "2026-05-24T09:00:10Z",
  "dry_run": true,
  "write_intent": "none",
  "status": "partial_success",
  "sources_requested": ["BOE", "BOCM", "BOP"],
  "sources_scanned": ["BOE", "BOCM"],
  "date_from": "2026-05-24",
  "date_to": "2026-05-24",
  "documents_scanned": 312,
  "alerts_emitted": 2,
  "warnings_count": 1,
  "errors_count": 1,
  "duplicates_suppressed": 4,
  "by_source": {
    "BOE": {"documents_scanned": 210, "alerts_emitted": 1, "warnings_count": 0, "errors_count": 0},
    "BOCM": {"documents_scanned": 102, "alerts_emitted": 1, "warnings_count": 0, "errors_count": 0},
    "BOP": {"documents_scanned": 0, "alerts_emitted": 0, "warnings_count": 1, "errors_count": 1}
  },
  "by_alert_type": {
    "convocatoria": 1,
    "correccion": 1
  },
  "by_confidence": {
    "high": 1,
    "medium": 1,
    "low": 0
  },
  "no_write_guarantees": {
    "db_schema_modified": false,
    "db_rows_inserted": 0,
    "db_rows_updated": 0,
    "source_candidates_created": 0,
    "artifact_downloads_started": 0,
    "downstream_writes": 0,
    "vps_write_operations": 0
  }
}
```

## Consumption By oposiciones2.0

Expected `oposiciones2.0` consumption model:

```text
1. Read JSONL line by line.
2. Reject records with an unknown schema_version.
3. Import only record_type=alert into product-side dry-run/review storage.
4. Use source_code + alert_type + dedupe_key as the primary idempotency key.
5. Use related_group_key only for grouping notifications, not for overwriting upstream records.
6. Treat confidence as routing metadata, not as verified legal/evidence status.
7. Display warnings/errors to operators, not to end users by default.
8. Require explicit promotion before requesting evidence-grade processing from official-sources.
```

Consumer constraints:

- `oposiciones2.0` must not infer that an alert is verified evidence.
- `oposiciones2.0` must not publish user-facing claims from alert records without its own product review
  policy.
- `oposiciones2.0` must not write back to official-sources from this dry-run export.
- `source_document_id`, when present, is an upstream pointer and not a stable product identifier.

## No-DB And No-Write Guarantees

Dry-run exports covered by this contract must guarantee:

```text
no DB schema changes
no DB row inserts
no DB row updates
no source_candidates creation
no candidate_evidence_reviews creation
no artifact download attempts
no official document enrichment writes
no downstream project writes
no EduAyudas writes
no la-ayuda writes
no oposiciones2.0 writes
no VPS write operations unless a future task explicitly authorizes them
```

The export itself may be written only to an explicitly requested local output path. If no output path is
provided, the dry-run should write to stdout.

## Contract Readiness

Readiness status:

```text
contract_defined_for_review
```

This contract is ready for review before any implementation task. A future implementation should add
fixture validation for JSONL alert, warning, error, and summary records before wiring the export into
any scheduled dry-run.
