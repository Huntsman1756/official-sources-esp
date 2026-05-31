# official-sources

`official-sources` is reusable infrastructure for ingesting, normalizing, tracing, auditing, and
reporting coverage for official public-source documents.

The first ingestion tier covers Spanish BOE state-level sources. The source-coverage tier also
maintains an executable registry of official sources and metadata-only RSS/API/HTML discovery monitors.
This is not a public product and does not approve, publish, summarize with LLMs, or integrate with
downstream projects automatically.

## Why This Exists

Many civic, legal, fiscal, subsidy, public-employment, transparency, and accountability projects need the same reliable base layer:

```text
official source -> ingestion -> normalized document -> citation -> integrity check -> candidate extraction -> human review -> safe publication
```

This repository provides the source and audit layer. Human review remains mandatory for downstream use.

## MVP Scope

- Tier 1 BOE state-level official source support only.
- BOE daily summary ingestion from the official BOE open-data API.
- Executable source registry at `config/sources.yaml`.
- Metadata-only source discovery monitors for selected official RSS/Atom/API/HTML access methods.
- Read-only MCP source coverage tools.
- SQLite storage for sources, documents, files, texts, candidates, ingestion runs, and integrity checks.
- Raw-source traceability through official URLs and source snapshot hashes.
- Controlled download of stored official BOE XML, HTML, and PDF artifact URLs.
- Audited artifact download attempts for success, skipped, failed, and changed outcomes.
- Read-only BOE consolidated legislation retrieval by official identifier.
- Official BOE consolidated legislation text index retrieval.
- Official BOE consolidated legislation text block retrieval and block citations.
- Stable citation generation.
- Integrity hash comparison and reviewable change events.
- Read-only internal query functions.
- Read-only FastMCP interface with structured outputs.
- Conservative BOE HTTP retry/backoff policy for 429, 503, and transient 5xx responses.
- Verified SQLite backup with default `quick_check`, row-count comparison, and minimum size checks.

## Non-Goals

- EUR-Lex adapters.
- Autonomous/statutory territory, provincial, local, or municipal bulletin adapters.
- RAG, embeddings, or vector databases.
- Git/Markdown export.
- UI, authentication, Docker, or production deployment.
- LLM extraction, legal interpretation, automatic approval, or automatic publication.

## Install

```bash
python -m pip install -e ".[dev]"
```

`uv` can also be used:

```bash
uv sync --extra dev
```

## Run Tests

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

## CLI

The package exposes an operational CLI:

```bash
official-sources --db-path official-sources.sqlite --artifact-dir data/artifacts <command>
```

For development validation against the current source tree, especially if an installed
`official-sources` console script may be stale, use:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOIB
```

Refresh the local console script with an editable install from the repository root:

```bash
python -m pip install -e ".[dev]"
```

Command-line options override environment variables:

- `OFFICIAL_SOURCES_DB`
- `OFFICIAL_SOURCES_DB_PATH`
- `OFFICIAL_SOURCES_ARTIFACT_DIR`

## Database Migrations

Persistent SQLite databases must be upgraded with migrations, not by deleting or recreating the file.

Before running migrations on a persistent installation, create a database backup.

```bash
official-sources --db-path official-sources.sqlite db status
official-sources --db-path official-sources.sqlite db backup --output backups/official_sources_YYYYMMDD_HHMMSS.sqlite
official-sources --db-path official-sources.sqlite db migrate
official-sources --db-path official-sources.sqlite db validate
```

`db status` reports the current schema version, latest version, pending migration count, database path, and status. `db backup` copies the SQLite file with the SQLite online backup API, verifies the source and backup with `PRAGMA quick_check` by default, compares application-table row counts, enforces a minimum backup size, and refuses to overwrite existing output unless `--force` is explicit. `db migrate` applies pending migrations in order and records checksums in `schema_migrations`. `db validate` verifies required tables, columns, the migration metadata table, and that the current version matches the latest migration.

Backup verification options:

```bash
official-sources --db-path official-sources.sqlite db backup --output backups/official_sources_YYYYMMDD_HHMMSS.sqlite
official-sources --db-path official-sources.sqlite db backup --output backups/official_sources_YYYYMMDD_HHMMSS.sqlite --quick-check
official-sources --db-path official-sources.sqlite db backup --output backups/official_sources_YYYYMMDD_HHMMSS.sqlite --full-check
official-sources --db-path official-sources.sqlite db backup --output backups/official_sources_YYYYMMDD_HHMMSS.sqlite --no-verify
```

The migration system is local and deterministic. It does not call BOE APIs, MCP tools, downstream projects, or external network resources.

Restore is a manual operational process. See `docs/BACKUP_AND_RESTORE.md`.

Before VPS deployment or update, follow `docs/PRE_DEPLOY_VPS_CHECKLIST.md`.

The official publication hierarchy is documented in `docs/decisions/ADR-001-official-publication-hierarchy.md`. BOE is a state-level source, not a generic synonym for official bulletins.

## Source Coverage Usage

The coverage platform is documented in `docs/SOURCE_COVERAGE_USAGE.md`.
Source status semantics for downstream consumers are documented in `docs/SOURCE_STATUS_CONTRACT.md`.
Downstream-demand prioritization for the shared MCP/upstream model is documented in
`docs/MCP_DOWNSTREAM_SOURCE_NEEDS_MATRIX.md`.
Stable downstream case taxonomy is documented in `docs/MCP_CASE_TAXONOMY.md`.
The consumer-aware MCP contract is documented in
`docs/MCP_DOWNSTREAM_DEMAND_CONTRACT.md`.
The read-only downstream integration closure and smoke matrix are documented in
`docs/MCP_DOWNSTREAM_INTEGRATION_CLOSURE.md`.
The MCP smoke checker `check_downstream_integration_smokes` validates that the current
consumer-specific MCP planning calls still match that read-only matrix.
The final read-only upstream v1 closure is documented in
`docs/MCP_READONLY_UPSTREAM_V1_FINAL_CLOSURE.md`.
`eduayudas` evidence-packet planning is documented in
`docs/MCP_EDUAYUDAS_EVIDENCE_PACKET_PROFILE.md`.
`la-ayuda` source-resolver planning is documented in
`docs/MCP_LAAYUDA_SOURCE_RESOLVER_PROFILE.md`.
`renta-verificable` fiscal-reference planning is documented in
`docs/MCP_RENTA_FISCAL_REFERENCE_PROFILE.md`.

Quick registry commands:

```bash
official-sources sources list
official-sources sources status --source BOCYL
```

Metadata-only monitor previews:

```bash
official-sources rss monitor --source BOE --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOJA --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOIB --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOC_CANTABRIA --date YYYY-MM-DD --limit 1
official-sources rss monitor --source DOE --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOC_CANARIAS --date YYYY-MM-DD --limit 1
official-sources rss monitor --source DOG --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOP_LUGO --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOCM --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOP_BADAJOZ --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOP_GUADALAJARA --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOR --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOP_CACERES --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOP_HUELVA --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 1
official-sources html monitor --source BON --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOPA --date YYYY-MM-DD --limit 1
official-sources html monitor --source DOCM --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ALBACETE --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ALICANTE --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ARABA_ALAVA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_AVILA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_BARCELONA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_BIZKAIA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_BURGOS --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_CASTELLON --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_CORDOBA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_GIRONA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_GIPUZKOA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_GRANADA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_JAEN --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_LAS_PALMAS --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_LEON --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_LLEIDA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_MALAGA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_PALENCIA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_PONTEVEDRA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_SEGOVIA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_SEVILLA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_SANTA_CRUZ_TENERIFE --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_SORIA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_TARRAGONA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_TERUEL --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_TOLEDO --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_VALENCIA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_VALLADOLID --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ZAMORA --date YYYY-MM-DD --limit 1
```

Monitor output writes require explicit `--write`. RSS/API/HTML discovery records are not
candidates and are not evidence-grade records. Registry presence, monitor validation, and monitor
health do not mean product readiness; `BOP_ALICANTE` remains degraded/manual-review and must not be
counted in all-green source claims.

## BDNS Grants Operations

BDNS / SNPSAP is treated as a grants registry source family, not as a bulletin. BDNS operations are
CLI-only; they are not MCP write tools and they do not create downstream records, approve grants, or
publish product content.

Safe metadata catalog previews and ingestion:

```bash
official-sources --db-path official-sources.sqlite preview-bdns-catalog --catalog sectores
official-sources --db-path official-sources.sqlite ingest-bdns-catalog --catalog sectores
official-sources --db-path official-sources.sqlite preview-bdns-catalog --catalog organos --id-admon C
official-sources --db-path official-sources.sqlite ingest-bdns-catalog --catalog organos --id-admon C
```

Grant-call export for downstream staging:

```bash
official-sources --db-path official-sources.sqlite \
  export-bdns-grants --output data/exports/bdns-grants.jsonl --limit 100
```

The export is JSONL over stored local BDNS grant-call records. It is a staging input only and must
remain behind product-side review before publication or candidate creation.

Business grants radar export and static dashboard:

```bash
official-sources --db-path official-sources.sqlite \
  export-bdns-business-grants --output data/exports/bdns-business-grants.jsonl --min-score 0.35

official-sources --db-path official-sources.sqlite \
  export-bdns-business-dashboard --output data/exports/bdns-business-radar.html --min-score 0.35
```

These commands rank stored BDNS grant calls for companies, SMEs, self-employed workers, and related
economic-activity topics. The score is an auditable review aid, not an eligibility decision or
automatic product import.

Concesiones are scoped to one convocatoria:

```bash
official-sources --db-path official-sources.sqlite \
  preview-bdns-concesiones --num-conv CODIGO_BDNS --page-size 10

official-sources --db-path official-sources.sqlite \
  ingest-bdns-concesiones --num-conv CODIGO_BDNS --page-size 10 --max-pages 1
```

Stored concesiones can be exported as sanitized JSONL:

```bash
official-sources --db-path official-sources.sqlite \
  export-bdns-concessions --num-conv CODIGO_BDNS --output data/exports/bdns-concessions.jsonl
```

Global concesiones ingestion is disabled: `ingest-bdns-concesiones` requires `--num-conv`.
Beneficiary name and person-id fields are redacted by default in concesiones parsing/storage. Use
`--include-beneficiary-fields` only for an explicit privacy-reviewed operation.

The private MCP server exposes read-only cache views for stored BDNS grant calls, business-grants
ranking, catalog entries, and scoped concesiones. MCP does not run BDNS live fetches or write
downstream records.

BDNS final verification checklist:

- run `db validate` after migrations and after any BDNS write command;
- confirm BDNS catalog/concesiones commands report `status=success`;
- confirm no source candidates, product records, or downstream writes were created;
- confirm no artifact downloads were triggered by BDNS catalog/export/concesiones commands;
- confirm concesiones runs were scoped with `--num-conv` and beneficiary fields stayed redacted
  unless explicitly approved;
- confirm `export-bdns-grants` output path and record count before handing the file to a downstream
  staging workflow.

## Ingest A BOE Summary

```bash
official-sources --db-path official-sources.sqlite ingest-boe-summary --date 2024-05-29
```

The command creates an `ingestion_runs` row before fetching. Failed attempts are also recorded.
For `/datosabiertos/api/boe/sumario/{fecha}`, BOE documents `404` as requested
information not existing. Daily summary ingestion treats that case as `no_publication`: the
source was reached, no summary exists for the requested date, `last_http_status=404` is
persisted, document counts stay at zero, and the CLI exits successfully so systemd does not
report an infrastructure failure. Real network, server, parsing, storage, and schema failures
still use `failed` and exit non-zero.

## Download BOE Artifacts

Artifact downloads are driven by official URLs already stored on `official_documents`; there is no arbitrary URL downloader.

```bash
official-sources \
  --db-path official-sources.sqlite \
  --artifact-dir data/artifacts \
  download-boe-artifacts --date 2024-05-29 --types xml,html,pdf
```

Downloaded files are cached under:

```text
data/artifacts/boe/YYYY/MM/DD/<external_id>/
```

Expected filenames are `document.xml`, `document.html`, and `document.pdf`.

Scoped evidence downloads are available for candidate/document review workflows:

```bash
official-sources \
  --db-path official-sources.sqlite \
  --artifact-dir data/artifacts \
  download-boe-artifacts --candidate-ids 1,2,3 --types xml,html
```

`--candidate-ids` and `--document-ids` are mutually exclusive with `--date`; they prevent
accidental broad date-level downloads. The default artifact types are `xml,html`. PDF is never
downloaded by default and requires explicit inclusion in `--types`.

## Integrity Check And Status

```bash
official-sources --db-path official-sources.sqlite integrity-check --date 2024-05-29
official-sources --db-path official-sources.sqlite status --date 2024-05-29
```

The integrity command recomputes hashes from local cached artifacts and records integrity events. The status command reports ingestion status, last observed HTTP status, document counts, artifact counts, download attempt counts, failed downloads, and integrity warnings.

`status --date` separates BOE summary ingestion audit fields from artifact download audit
fields. `summary_*` fields describe the daily summary API request, for example
`summary_ingestion_status`, `summary_last_http_status`, `summary_retry_count`, and
`summary_throttle_triggered`. `artifact_*` fields describe XML/HTML/PDF downloads, including
`artifact_download_*`, `artifact_http_status_summary`, `artifact_retry_count`, and
`artifact_throttle_events`. The legacy `ingestion_status` and `last_http_status` fields remain
as aliases for the summary ingestion status and summary HTTP status.

Controlled range ingestion is metadata-only and never downloads artifacts:

```bash
official-sources --db-path official-sources.sqlite \
  ingest-boe-range --date-from 2024-05-01 --date-to 2024-05-31 \
  --skip-existing --continue-on-no-publication
```

Safety defaults are deliberately narrow: `--max-days` defaults to `90`, ranges above `365`
days require `--force`, and ranges above `365` days also require `--confirm-large-range`.
Artifacts remain explicit and on-demand. XML/HTML are candidate evidence layers. PDF is final
evidence/on-demand and is never downloaded by default.

Keyword candidate prefiltering is local-only:

```bash
official-sources --db-path official-sources.sqlite \
  find-boe-candidates --date-from 2024-05-01 --date-to 2024-05-31 \
  --keywords "beca,ayuda,subvencion,convocatoria" \
  --dry-run --limit 50
```

This searches stored BOE titles and metadata only. It does not parse full document content,
does not use LLMs, does not classify legal meaning, and does not approve or publish anything.
Use `--dry-run` or `--no-write` for safe previews; those modes print aggregate counts and sample
matches without writing `source_candidates`. Candidates created by the normal write mode default
to `human_review_required`. Candidate creation is not the default; it requires explicit
`--write`, and `--limit` caps the number of candidates created in write mode.

The `la-ayuda` profile provides a stricter first-pass filter for `la-ayuda` / `EduAyudas`:

```bash
official-sources --db-path official-sources.sqlite \
  find-boe-candidates --date-from 2024-05-01 --date-to 2024-05-31 \
  --profile la-ayuda \
  --dry-run --limit 100
```

Candidate matching normalizes case, accents, and repeated whitespace; applies word boundaries so
short terms such as `bono` do not match inside unrelated words such as `carbono`; handles
multi-word phrases as phrases; supports `--include-sections`, `--exclude-sections`,
`--include-departments`, and `--exclude-departments`; and prints deterministic, explainable scores.
Those scores are prefiltering signals only. They do not approve, publish, rank, or decide legal
or fiscal meaning.

## BOE Consolidated Legislation

The CLI can retrieve one consolidated law by official BOE identifier:

```bash
official-sources --db-path official-sources.sqlite \
  boe-consolidated-get --identifier BOE-A-2024-11111
```

This uses the official BOE OpenData consolidated legislation endpoint:

```text
/datosabiertos/api/legislacion-consolidada/id/{id}
```

The implementation stores consolidated law metadata, one current cached version, deterministic text blocks when the XML structure supports them, raw payload hashes, source snapshot hashes, and consolidated-law integrity events. It does not implement legal interpretation, legal advice, custom version comparison, RAG, or search.

The CLI can also retrieve the official text index and one official text block:

```bash
official-sources --db-path official-sources.sqlite \
  boe-consolidated-index-get --identifier BOE-A-2024-11111

official-sources --db-path official-sources.sqlite \
  boe-consolidated-block-get --identifier BOE-A-2024-11111 --block-id a1
```

Block content is not printed by default. To print official text explicitly:

```bash
official-sources --db-path official-sources.sqlite \
  boe-consolidated-block-get --identifier BOE-A-2024-11111 --block-id a1 --print-content
```

Index and block retrieval use only official BOE OpenData endpoints:

```text
/datosabiertos/api/legislacion-consolidada/id/{id}/texto/indice
/datosabiertos/api/legislacion-consolidada/id/{id}/texto/bloque/{id_bloque}
```

Block-level MCP output keeps official text inside a structured `content` field. It does not interpret obligations, determine applicability, compare legal versions, perform RAG, or expose broad search.

## Daily Operational Flow

```bash
official-sources ingest-boe-summary --date 2024-05-29
official-sources download-boe-artifacts --date 2024-05-29 --types xml,html,pdf
official-sources integrity-check --date 2024-05-29
official-sources status --date 2024-05-29
```

The CLI also accepts `--date today` for timer use.
On a `no_publication` day, artifact download is skipped because there are no BOE document URLs
to fetch for that date.
`integrity-check` verifies local cached artifacts. Metadata/provenance records with
`local_path=NULL`, such as `raw_api_response`, are reported as `non_local_metadata` rather than
missing files; rows with a stored local path still fail if that file is absent.

## systemd Templates

Minimal templates are provided under `deploy/systemd/`:

- `official-sources-boe-daily.service`
- `official-sources-boe-daily.timer`
- `official-sources-integrity-check.service`
- `official-sources-integrity-check.timer`

They assume this VPS layout:

```text
/opt/official-sources
/opt/official-sources/app
/opt/official-sources/data/official_sources.sqlite
/opt/official-sources/data/artifacts
/opt/official-sources/data/backups
```

The service templates run as the non-root `official-sources` user, read `/opt/official-sources/.env`, and execute `/opt/official-sources/app/.venv/bin/official-sources`.

This is operational packaging, not product deployment. It does not add Docker, a web server, public network services, authentication, or downstream integrations. The MCP server remains read-only and does not expose download commands.

Before deploying updates or running migrations on a VPS, create a backup, restore it to a temporary path, run `db migrate`, run `db validate`, and perform a small read-only smoke check. Stop timers and services before restoring over the active database.

## Run The MCP Server

```bash
OFFICIAL_SOURCES_DB_PATH=official-sources.sqlite python -m official_sources.mcp.server
```

The MCP server name is `official-sources`. Tools are read-only and return structured records. This MCP server has no authentication. Keep MCP private through local stdio, localhost, SSH tunnel, or Tailscale/private network access only; do not expose it through Cloudflare Tunnel, public Nginx, public Docker port mapping, or `0.0.0.0` unless a proper authentication and authorization layer is added.

Downstream projects must consume `official-sources` as evidence only. They remain responsible for their own `pending_review` candidates, review workflow, publication workflow, and legal or fiscal interpretation. See `docs/DOWNSTREAM_CONTRACT.md`.

## Limitations

- MVP parsing is focused on BOE daily summary metadata.
- Artifact download stores XML/HTML/PDF bytes and extracts deterministic text only from XML/HTML.
- Signature validation is not implemented; `signature_status` defaults to `not_checked`.
- PDF files are hashed and stored only; PDF text extraction and electronic signature validation are not implemented.
- Consolidated legislation retrieval is by identifier only; search and own version diffing are future work.
- BOE consolidated legislation search is documented as future work, not implemented.
- Consolidated text index and block retrieval are cached snapshots of official BOE endpoint payloads; stale cache review remains a human responsibility.
- Consolidated block retrieval does not determine whether a block is legally applicable to a user situation.
- Live network calls are not required by tests; fixtures cover the adapter behavior.
- Tier 2 autonomous/statutory territory bulletins, Tier 3 provincial/local bulletins, Tier 4 EUR-Lex/DOUE, and TED/OJ S are conceptual future tiers only.
