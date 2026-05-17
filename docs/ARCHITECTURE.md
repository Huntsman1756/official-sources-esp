# Architecture

## Stack

- Python 3.12+.
- SQLite for MVP storage.
- `httpx` for BOE HTTP access.
- `pytest` and `ruff` for validation.
- FastMCP for the final read-only MCP interface.

## BOE HTTP Runtime Policy

The BOE official API documentation describes endpoints, formats, and HTTP status codes, but it does not clearly publish operational request quotas. `official-sources` therefore applies a conservative internal policy to BOE summary ingestion, artifact downloads, consolidated law retrieval, consolidated index retrieval, and consolidated block retrieval.

Default policy:

```text
OFFICIAL_SOURCES_BOE_REQUESTS_PER_SECOND=1
OFFICIAL_SOURCES_BOE_MAX_RETRIES=5
OFFICIAL_SOURCES_BOE_BACKOFF_BASE_SECONDS=1
OFFICIAL_SOURCES_BOE_BACKOFF_MAX_SECONDS=30
OFFICIAL_SOURCES_BOE_JITTER_SECONDS=0.25
```

The implementation uses `httpx` plus an internal finite retry/backoff wrapper. `retryhttp` was not adopted in TASK-003F because it is not available in the current offline validation environment and the repository has no lockfile workflow in place for adding and verifying that dependency. Equivalent behavior is covered by mocked HTTP tests: 429 and 503 retry, transient 5xx retry, `Retry-After` handling, finite retry limits, retry counts, and throttle/backoff audit fields.

Retry and throttle information is recorded on `ingestion_runs` and `artifact_download_attempts` through `throttle_triggered`, `retry_count`, and final HTTP status fields.

For BOE daily summary ingestion, a `404 Not Found` response from
`/datosabiertos/api/boe/sumario/{fecha}` is treated as the controlled status
`no_publication`. This means BOE was reached successfully, but no summary exists for the
requested date. The run stores `last_http_status=404`, zero document counts, and a clear
message. The CLI exits with status code `0` for this condition so the systemd daily service
does not fail on expected no-publication days. Network errors, server errors after finite
retries, malformed successful responses, database errors, and schema errors still use
`failed` and exit non-zero.

Operational status output intentionally separates daily summary HTTP state from artifact
download HTTP state. `summary_*` fields come from the latest BOE summary ingestion run with an
observed HTTP status. `artifact_*` fields come from `artifact_download_attempts`, grouped by
artifact type and HTTP status, for example `xml:200:114,html:200:114,pdf:200:114`. Legacy
`ingestion_status` and `last_http_status` are retained as aliases for summary status fields.

## Dependency Direction

Correct dependency direction:

```text
storage/core -> source adapters -> normalization -> internal API -> MCP tools
```

The MCP layer is an interface on top of the core system. It is not the core architecture, and storage is not designed around agent calls.

## Layers

- `storage`: schema initialization and repository functions.
- `sources/boe`: date validation, BOE summary fetch, parsing, controlled artifact download, ingestion run handling, and persistence.
- `normalization`: deterministic text cleanup only, with XML/HTML extraction for stored official artifacts.
- `citation`: answers where a document came from.
- `integrity`: answers whether the stored artifact matches what was ingested.
- `api`: read-only local query functions.
- `mcp`: read-only FastMCP tools backed by the API layer.
- `cli`: operational command-line runner for scheduled ingestion, artifact download, integrity checks, and status reporting.

## Future Optional Layers

- Git/Markdown export.
- Search or RAG index.
- Additional official source adapters.
- Downstream project connectors.

These are not part of MVP-001.

## Official Publication Hierarchy

The official publication hierarchy is governed by `docs/decisions/ADR-001-official-publication-hierarchy.md`.

Current implementation is Tier 1 only:

- BOE daily publications.
- BOE controlled XML/HTML/PDF artifacts.
- BOE consolidated legislation.
- BOE consolidated index and block retrieval.

Future tiers are conceptual only until explicitly scheduled:

- Tier 2: autonomous/statutory territory official journals, including Ceuta and Melilla with explicit modeling notes.
- Tier 3: provincial/local bulletins and municipal gazettes where required.
- Tier 4: EUR-Lex/DOUE and separate TED/OJ S procurement support.

BOE must not be used as a generic synonym for official bulletins. Autonomous, provincial, local, and EU sources require independent source adapters.

## Artifact Download Layer

BOE artifact downloads are source-adapter behavior, not MCP behavior. The downloader reads stored `url_xml`, `url_html`, and `url_pdf` values from `official_documents`, validates that they are HTTPS BOE URLs, fetches bytes with `httpx`, writes them to the local cache, and records them in `document_files`.

Each attempted artifact download also creates an `artifact_download_attempts` row. This table records what happened while trying to fetch an artifact. It does not replace `integrity_checks`.

```text
artifact_download_attempts = what happened when trying to fetch an artifact
integrity_checks = what happened when comparing artifact content hashes
```

The local cache layout is:

```text
data/artifacts/boe/YYYY/MM/DD/<external_id>/
```

Expected filenames are:

- `document.xml`
- `document.html`
- `document.pdf`

XML and HTML may produce deterministic `document_texts` rows. PDF is stored and hashed only.

## Operational CLI

The CLI entry point is `official-sources`. It supports:

```bash
official-sources db status
official-sources db backup --output PATH
official-sources db migrate
official-sources db validate
official-sources ingest-boe-summary --date YYYY-MM-DD
official-sources ingest-boe-range --date-from YYYY-MM-DD --date-to YYYY-MM-DD
official-sources download-boe-artifacts --date YYYY-MM-DD --types xml,html,pdf
official-sources integrity-check --date YYYY-MM-DD
official-sources find-boe-candidates --date-from YYYY-MM-DD --date-to YYYY-MM-DD --keywords "..."
official-sources status --date YYYY-MM-DD
```

The CLI uses the same SQLite storage and artifact cache as the Python API. It accepts `--db-path` and `--artifact-dir`, with command-line arguments taking precedence over environment variables.

This command shape is intended to be run later from `systemd` timers on a private VPS. It is intentionally separate from MCP so operational writes are not exposed to agents.

Range ingestion is deliberately summary-only. It reuses the conservative BOE HTTP request
policy with a shared client-side limiter across the date range, finite retries, retry/backoff
audit fields, and explicit range limits. It does not download XML, HTML, or PDF artifacts.

Keyword candidate prefiltering is a local metadata filter over stored BOE document titles and
metadata. It creates `source_candidates` with `review_status=human_review_required`; it does
not parse full content, perform legal classification, approve candidates, or publish anything.

## SQLite Migration Layer

Persistent SQLite schema changes are managed by `official_sources.storage.migrations`.

```text
storage/schema.py = canonical latest schema for fresh equivalence checks
storage/migrations = ordered upgrade path for persistent databases
storage/database.py = connection helper plus migration-backed initialization
```

Migrations are Python modules because SQLite upgrade steps need a small amount of conditional logic, especially `ALTER TABLE ... ADD COLUMN` only when a column is missing. This avoids destructive table rebuilds for the current migration set.

Implemented migrations:

- `0001_initial`: source, document, file, text, candidate, ingestion, and integrity tables.
- `0002_artifact_download_attempts`: artifact download audit table.
- `0003_consolidated_legislation`: consolidated law, version, block, reference, and integrity tables.
- `0004_consolidated_index_blocks`: official consolidated block endpoint metadata columns.
- `0005_request_audit_fields`: request retry/throttle audit columns for ingestion runs and artifact download attempts.
- `0006_ingestion_no_publication_status`: allows `ingestion_runs.status='no_publication'` for controlled BOE daily-summary 404 responses.

The runner stores applied versions in `schema_migrations` with version, name, checksum, timestamp, and execution time. Pending migrations are applied in ascending order and inside transactions where SQLite allows it. Checksum mismatches fail before applying additional migrations.

Schema changes must not be applied by silently recreating SQLite files because that would destroy ingestion history, stored official artifacts, source snapshot hashes, integrity events, and human review state.

The backup command uses SQLite's online backup API to copy the database to an operator-provided path. It runs `PRAGMA quick_check` on source and backup by default, compares application-table row counts, and enforces a minimum backup size. `--full-check` runs `PRAGMA integrity_check` for manual audits and diagnostics. Restore remains manual by design: operators must stop services and timers, copy the active database aside, replace the database file, run `db status`, `db migrate`, `db validate`, and perform a read-only smoke check before restarting services.

VPS deployment requires the sequence documented in `docs/PRE_DEPLOY_VPS_CHECKLIST.md`: local validation, backup, restore rehearsal, migration, validation, smoke checks, systemd checks, and rollback readiness.

## Consolidated Legislation Layer

BOE consolidated legislation is modelled separately from daily BOE publication documents.

```text
daily BOE document = what was officially published on a given date
consolidated law = current or versioned consolidated state of a legal norm
```

The implemented source adapter fetches a single consolidated law by official identifier from:

```text
/datosabiertos/api/legislacion-consolidada/id/{id}
```

It stores normalized metadata, cached version metadata, deterministic text blocks, raw payload hashes, and consolidated-law integrity events. It does not implement search, legal interpretation, legal advice, custom version diffing, or RAG.

TASK-003B adds two narrow official text endpoints:

```text
/datosabiertos/api/legislacion-consolidada/id/{id}/texto/indice
/datosabiertos/api/legislacion-consolidada/id/{id}/texto/bloque/{id_bloque}
```

The index endpoint is parsed into stored block metadata, including official block ID, parent block ID when present, block path, block title, block type, order, source URL, raw payload hash, and source snapshot hash. Nested index fixtures preserve parent-child relationships; the code does not infer legal meaning from the hierarchy.

The block endpoint fetches one official BOE block by `official_identifier` and `block_id`, validates both path segments, hashes raw XML bytes before parsing, stores the selected current block text, and records integrity metadata when the official payload hash changes. The adapter does not compare legal versions or decide legal effect.

Consolidated legislation tools are read-only through MCP. Operational fetching is exposed through the CLI, not MCP.

## systemd Templates

The `deploy/systemd` directory contains minimal service and timer templates for:

- daily BOE ingestion and artifact download;
- local cached artifact integrity checks.

The templates assume `/opt/official-sources/app` as `WorkingDirectory`, `/opt/official-sources/.env` as the environment file, `/opt/official-sources/app/.venv/bin/official-sources` as the CLI executable, and data under `/opt/official-sources/data`. They run as the non-root `official-sources` user. They are safe templates for a private VPS and do not expose public network services.

## No Automatic Publication

The system may store candidates, evidence, and review status. It must not approve or publish downstream data automatically. The default candidate review status is `human_review_required`.

`official-sources` must not write into downstream projects. Downstream integrations remain outside the implemented scope.
