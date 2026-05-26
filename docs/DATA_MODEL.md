# Data Model

## Schema Versioning

SQLite schema changes are tracked in `schema_migrations`.

Fields:

- `id`
- `version`
- `name`
- `checksum`
- `applied_at`
- `execution_time_ms`

`schema.py` remains the canonical latest schema definition used by tests to verify migrated databases have the expected latest tables and columns. Runtime initialization delegates to the migration runner so existing persistent databases are upgraded in place rather than recreated.

Current migrations:

- `0001_initial`
- `0002_artifact_download_attempts`
- `0003_consolidated_legislation`
- `0004_consolidated_index_blocks`
- `0005_request_audit_fields`
- `0006_ingestion_no_publication_status`
- `0007_candidate_evidence_reviews`
- `0008_candidate_manual_review_fields`

Before running migrations on a persistent installation, create a database backup.

Operational commands:

```bash
official-sources --db-path official-sources.sqlite db status
official-sources --db-path official-sources.sqlite db migrate
official-sources --db-path official-sources.sqlite db validate
```

For persistent file-backed databases, runtime connections enable:

```text
PRAGMA journal_mode=WAL
PRAGMA synchronous=NORMAL
```

WAL lets readers continue while a writer is active, which fits the VPS model where ingestion or
artifact jobs write while MCP/API/local query paths read. SQLite remains single-writer; WAL is
an operational concurrency improvement, not a substitute for PostgreSQL if write concurrency
becomes heavy. In-memory test databases do not enable WAL by default.

Migrations preserve existing rows and avoid destructive schema resets. Failed migrations are not marked as applied. If an already-applied migration checksum differs from the migration code, migration and validation fail.

## Tables

### official_sources

Stores canonical source registries. Required fields: `id`, `code`, `name`, `jurisdiction`, `region_code`, `base_url`, `access_type`, `reliability_level`, `created_at`, `updated_at`.

Initial source:

- `code`: `BOE`
- `jurisdiction`: `state`
- `region_code`: `ES`
- `access_type`: `official_api`
- `reliability_level`: `canonical`

TASK-AUTO-002 adds a BOJA source record without adding source-specific tables:

- `code`: `BOJA`
- `jurisdiction`: `autonomous`
- `region_code`: `ES-AN`
- `access_type`: `official_api`
- `reliability_level`: `canonical`

### official_documents

Stores normalized official document metadata. Required fields include source link, external official identifier, publication date, title, department, section, document type, official URLs, raw metadata JSON, and timestamps.

`external_id` stores the official source identifier when available. BOE uses identifiers such
as `BOE-A-YYYY-NNNNN`. BOJA stores the stable API `id` with a source prefix, for example
`BOJA:disposition.2026.94.5`, to avoid ambiguity with identifiers from other sources.

### document_files

Stores fetched artifacts and hashes.

Downloaded BOE artifacts use a predictable local cache:

```text
data/artifacts/boe/YYYY/MM/DD/<external_id>/
```

Expected filenames:

- `document.xml`
- `document.html`
- `document.pdf`

Allowed `file_type` values:

- `pdf`
- `xml`
- `html`
- `json`
- `raw_api_response`

Allowed `signature_status` values:

- `not_checked`
- `valid_signature`
- `invalid_signature`
- `no_signature`
- `unavailable`

Default: `not_checked`.

### source_snapshot_hash

`source_snapshot_hash` is the SHA-256 hash of the raw source payload before parsing, normalization, cleaning or transformation.

The raw source payload may be:

- the raw BOE API response body;
- the raw BOJA API JSON response body;
- the raw XML document;
- the raw HTML document;
- the raw downloaded PDF file;
- the raw daily summary response.

For each stored hash, the input is the exact byte payload used for that file record. It must not be calculated from normalized text, parsed fields, cleaned HTML, extracted article text, LLM output, or summaries.

### document_texts

Stores deterministic extracted text only. Allowed `text_type` values:

- `raw_text`
- `clean_text`
- `structured_text`

MVP-001 does not store LLM summaries in this table.

XML and HTML artifact text extraction is deterministic and fixture-tested. PDF text extraction is not implemented in this task; PDF files are stored only as raw bytes with hashes and metadata.

### document_references

Stores deterministic references only when feasible. Example `reference_type` values include `law`, `decree`, `order`, `resolution`, `correction`, `call`, and `unknown`.

### source_candidates

Stores project-specific candidate evidence for human review. Allowed `extraction_status` values:

- `raw_detected`
- `parsed_candidate`
- `evidence_linked`
- `human_review_required`
- `human_accepted`
- `rejected`

Allowed `review_status` values:

- `human_review_required`
- `human_accepted`
- `rejected`

Default: `human_review_required`.

`review_status` is publication-safe state. Operational evidence labels must not be stored in
this field.

Avoid generic confidence scores. Evidence fields are preferred.

### candidate_evidence_reviews

Stores operational evidence review metadata for source candidates. This is not candidate
approval, legal classification, or a publication workflow.

Allowed `evidence_review_status` values:

- `not_reviewed`
- `evidence_selected`
- `evidence_downloaded`
- `evidence_reviewed`
- `needs_more_evidence`
- `false_positive`
- `out_of_scope`

Allowed `evidence_label` values:

- `likely_relevant`
- `unclear`
- `false_positive`
- `out_of_scope`

The table preserves notes, evidence selection, PDF selection, artifact availability snapshots,
integrity warning snapshots, reviewer metadata, and timestamps. Read paths derive current
XML/HTML/PDF availability from `document_files` so the status command reflects downloaded
artifacts.

`likely_relevant` is an operational label only. It must not change
`source_candidates.review_status` away from `human_review_required`.

### ingestion_runs

Mandatory audit table. A row is created for every fetch attempt, including failed attempts.

Allowed `status` values:

- `pending`
- `success`
- `partial`
- `failed`
- `no_publication`

Without this table the system would be a scraper, not auditable infrastructure.

`no_publication` is used for controlled BOE daily summary no-publication outcomes, currently
Sundays with an observed no-summary response unless a specific non-Sunday date is explicitly
allowlisted from empirical BOE API evidence. Non-Sunday technical failures remain `failed`.

### integrity_checks

Stores reviewable integrity events. When a known official artifact is fetched again, the system computes the new hash, compares it with the stored hash, preserves the previous hash when changed, sets `content_changed_at`, sets `change_detected_by`, and creates an integrity check.

Hash changes must not update downstream project data automatically.

Unchanged artifact downloads still update `last_seen_at` and `last_integrity_check_at` and create an integrity check with `changed = 0`. Changed artifact downloads preserve `previous_hash`, set `content_changed_at`, set `change_detected_by`, and create an integrity check with `changed = 1`.

The operational `integrity-check` command verifies local cached files. `document_files` rows with
`local_path = NULL`, such as metadata/provenance `raw_api_response` rows, are not local artifacts
and are reported separately as `non_local_metadata`. Missing files remain failures when a row has a
non-null `local_path`.

### artifact_download_attempts

Stores operational audit rows for attempts to fetch official artifacts.

Required fields:

- `id`
- `document_id`
- `ingestion_run_id`
- `file_type`
- `official_url`
- `status`
- `http_status`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`

Allowed `status` values:

- `success`
- `skipped`
- `failed`
- `changed`

Every artifact download attempt should create a row. Failed attempts store `error_message` without raw legal text or secrets. If an HTTP response exists, `http_status` is stored. Failures before an HTTP response keep `http_status` null.

This table is separate from `integrity_checks`:

```text
artifact_download_attempts = what happened when trying to fetch an artifact
integrity_checks = what happened when comparing artifact content hashes
```

### consolidated_laws

Stores BOE consolidated law metadata separately from daily BOE publication documents.

Fields include:

- `id`
- `source_id`
- `external_id`
- `official_identifier`
- `title`
- `law_type`
- `jurisdiction`
- `department`
- `publication_date`
- `consolidation_status`
- `official_url`
- `raw_metadata_json`
- `created_at`
- `updated_at`

`official_identifier` is the BOE identifier, for example `BOE-A-YYYY-NNNNN`.

### consolidated_law_versions

Stores cached version metadata for a consolidated law.

Fields include:

- `id`
- `consolidated_law_id`
- `version_identifier`
- `version_date`
- `valid_from`
- `valid_to`
- `is_current`
- `official_url`
- `raw_payload_hash`
- `source_snapshot_hash`
- `previous_hash`
- `content_changed_at`
- `created_at`
- `updated_at`

TASK-003 stores one current cached version from the complete official XML response. TASK-003B also stores cached endpoint snapshots for the official text index and official block endpoints using version identifiers such as `BOE-A-YYYY-NNNNN:text-index` and `BOE-A-YYYY-NNNNN:block:a1`.

The version row for an index or block endpoint stores the official endpoint URL, raw payload hash, source snapshot hash, previous hash, and content change timestamp. It does not implement custom version diffing. If future endpoints expose richer version history, that should be added without inventing version metadata.

### consolidated_law_text_blocks

Stores deterministic text blocks parsed from the official XML when reliable.

TASK-003B extends this table with block-level official endpoint metadata:

- `official_block_id`: BOE block identifier used in `/texto/bloque/{id_bloque}`.
- `parent_block_id`: parent BOE block ID when the official index exposes nesting.
- `block_path`: stable stored hierarchy path such as `ti/a1` when available.
- `api_url`: official BOE endpoint URL used for the block or listed by the index.
- `raw_payload_hash`: SHA-256 of the raw official endpoint response bytes before parsing.
- `source_snapshot_hash`: same raw snapshot hash used for integrity comparison.
- `raw_metadata_json`: direct official XML metadata preserved without legal inference.
- `last_seen_at`: latest local observation time for the block row.
- `content_changed_at`: set when a known block endpoint payload changes.
- `previous_hash`: previous raw payload hash when a known block endpoint changes.
- `change_detected_by`: optional ingestion run reference when available.

Index rows may have empty `content` because the official index endpoint contains block metadata, not the text itself. Block endpoint rows store official text in `content`.

Allowed `block_type` values used by the parser include:

- `preamble`
- `article`
- `additional_provision`
- `transitional_provision`
- `derogatory_provision`
- `final_provision`
- `annex`
- `unknown`

If the XML structure is not reliable, future code should store a full-text `unknown` block rather than pretending to have article-level structure.

### consolidated_law_references

Reserved for deterministic references when safe. TASK-003 does not implement LLM extraction or broad reference analysis.

### consolidated_law_integrity_checks

Stores integrity events for cached consolidated law XML payloads. This table is separate from `integrity_checks`, which is tied to `document_files`.

Hashes are computed from raw official XML bytes before parsing. A changed payload preserves the previous hash, sets `content_changed_at`, and records a reviewable integrity event.

## Citation Semantics

Citation metadata answers: where did this document come from?

Consolidated law citations include `source_code`, `resource_type`, `official_identifier`, title, version or publication date, official URL, and optional block metadata.

Block citations use `resource_type = consolidated_law_block` and include `law_title`, `version_date`, `block_id`, `block_type`, `block_identifier`, `block_title`, official BOE block URL, and retrieval timestamp. They cite only official BOE URLs and never generated summaries or third-party mirrors.

## Integrity Semantics

Integrity metadata answers: is the stored artifact identical to what was originally ingested?

These concerns are intentionally separate.
