# Source Coverage Usage

This guide documents the source coverage surface added by the coverage platform line.

The coverage layer is an executable registry plus metadata-only discovery monitors and read-only
MCP reporting. It is not candidate creation, evidence-grade ingestion, artifact download, backfill,
or downstream publication.

For the downstream-facing semantics of registry, monitor, discovery, candidate, evidence, and
runtime-health states, see:

```text
docs/SOURCE_STATUS_CONTRACT.md
```

## Current Coverage

Executable registry:

```text
config/sources.yaml
```

Current source counts:

```text
registered sources: 65
metadata_adapter_validated: 9
monitor_validated: 17
inventory_only: 39
provincial inventory-only sources: 32
RSS/Atom discovery sources: BOC_CANARIAS, BOC_CANTABRIA, BOCM, BOCYL, BOE, BOIB, BOJA, BOP_BADAJOZ, BOP_LUGO, DOE, DOG
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, BOP_BARCELONA, BOP_BIZKAIA, BOP_CASTELLON, BOP_MALAGA, BOP_SEVILLA, BOP_VALENCIA
BOP_ALICANTE runtime health: degraded/manual-review
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
candidate_creation_allowed=true: 0
evidence_grade_allowed=true: 0
```

Discovery output paths, when writes are explicitly requested:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

Controlled execution is documented in:

```text
docs/SOURCE_COVERAGE_RUN_PLAN.md
```

## Registry CLI

List registered sources:

```bash
official-sources sources list
```

Inspect one source:

```bash
official-sources sources status --source BOCYL
official-sources sources status --source BOPV
```

Use the registry to answer coverage questions such as:

- which sources exist;
- which jurisdiction level each source belongs to;
- which access methods are declared;
- whether a source is inventory-only, monitorable, metadata-adapter validated, paused, or deprecated;
- whether candidate creation or evidence-grade promotion is allowed.

### Source-Tree Validation Entrypoint

If the installed `official-sources` console script is stale, validate coverage against the current
source tree instead:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli sources list
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOIB
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOC_CANTABRIA
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source DOE
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOC_CANARIAS
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source DOG
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_LUGO
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOCM
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_BADAJOZ
```

Expected current source-tree status for the RSS-003, RSS-004, and RSS-005 sources:

```text
BOIB: operational_status=monitor_validated monitor_support=available
BOC_CANTABRIA: operational_status=monitor_validated monitor_support=available
DOE: operational_status=monitor_validated monitor_support=available
BOC_CANARIAS: operational_status=monitor_validated monitor_support=available
DOG: operational_status=monitor_validated monitor_support=available
BOP_LUGO: operational_status=monitor_validated monitor_support=available
BOCM: operational_status=monitor_validated monitor_support=available
BOP_BADAJOZ: operational_status=monitor_validated monitor_support=available
```

To refresh the local console script for development, reinstall the project in editable mode from
the repository root:

```bash
python -m pip install -e ".[dev]"
```

## RSS/Atom Discovery CLI

RSS/Atom discovery is metadata-only. It emits discovery records with:

```text
classification_status=unclassified
candidate_status=not_candidate
evidence_status=not_evidence
```

Preview one source without writing JSONL:

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
```

Write JSONL only when explicitly requested:

```bash
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit 10 --write
```

RSS/Atom monitor rules:

- one source per command;
- broad runs such as `--source ALL`, `--source *`, or comma-separated sources are refused;
- default mode is preview;
- `--write` writes metadata-only JSONL under `data/rss_monitor/`;
- records are not candidates;
- records are not evidence-grade.

## API Discovery CLI

API discovery is metadata-only. BOPV uses the official API access method declared in the registry.

Preview BOPV without writing JSONL:

```bash
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 1
```

Write JSONL only when explicitly requested:

```bash
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 10 --write
```

API monitor rules:

- one source per command;
- broad runs such as `--source ALL`, `--source *`, or comma-separated sources are refused;
- non-API sources are refused by the API monitor;
- default mode is preview;
- `--write` writes metadata-only JSONL under `data/api_monitor/`;
- records are not candidates;
- records are not evidence-grade.

## HTML Discovery CLI

HTML discovery is metadata-only. Current provincial HTML discovery supports `BOP_A_CORUNA`,
`BOP_ALBACETE`, `BOP_ALICANTE`, `BOP_BARCELONA`, `BOP_BIZKAIA`, `BOP_CASTELLON`,
`BOP_MALAGA`, `BOP_SEVILLA`, and `BOP_VALENCIA` through source-specific parsers.
`BOP_ALICANTE` remains
`degraded/manual-review` for runtime health and must not be counted in all-green claims. PDF links
may appear as official URLs in records, but the monitor does not download PDFs or artifacts.

Preview BOP_A_CORUNA without writing JSONL:

```bash
official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ALBACETE --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ALICANTE --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_BARCELONA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_BIZKAIA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_CASTELLON --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_MALAGA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_SEVILLA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_VALENCIA --date YYYY-MM-DD --limit 1
```

Write JSONL only when explicitly requested:

```bash
official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_ALBACETE --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_ALICANTE --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_BARCELONA --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_BIZKAIA --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_CASTELLON --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_MALAGA --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_SEVILLA --date YYYY-MM-DD --limit 10 --write
official-sources html monitor --source BOP_VALENCIA --date YYYY-MM-DD --limit 10 --write
```

HTML monitor rules:

- one source per command;
- broad runs such as `--source ALL`, `--source *`, or comma-separated sources are refused;
- non-validated HTML sources are refused by the HTML monitor;
- default mode is preview;
- `--write` writes metadata-only JSONL under `data/html_monitor/`;
- records are not candidates;
- records are not evidence-grade;
- PDFs are not downloaded.

## MCP Coverage Tools

Run the MCP server privately:

```bash
OFFICIAL_SOURCES_DB_PATH=official-sources.sqlite python -m official_sources.mcp.server
```

The coverage and cache-readback tools are read-only. `preview_discovery` is preview-only and may
fetch one explicit source endpoint, but it does not write files or mutate state:

```text
list_sources
get_source_status
list_monitorable_sources
list_latest_discovery_entries
preview_discovery
recommend_next_sources
```

### list_sources

Returns registered sources with coverage status fields such as:

```text
source_code
name
jurisdiction_level
operational_status
monitor_support
evidence_adapter
```

### get_source_status

Input:

```json
{
  "source_code": "BOCYL"
}
```

Returns the full registry entry and safety flags, including:

```text
candidate_creation_allowed
evidence_grade_allowed
access_methods
operational_status
```

### list_monitorable_sources

Returns sources with monitor-capable access methods declared in the registry.

Current expected monitored/discovery sources:

```text
BOE: RSS/API/XML/HTML access methods declared
BOJA: Atom/API access methods declared
BOCYL: RSS access method declared
BOIB: RSS access method declared
BOC_CANTABRIA: RSS access method declared; category-scoped feed
BOCM: RSS access method declared
DOE: RSS access method declared
BOP_BADAJOZ: Atom access method declared
BOP_LUGO: RSS access method declared
BOPV: API/XML/HTML access methods declared
BOP_A_CORUNA: HTML access method declared
BOP_ALBACETE: HTML access method declared
BOP_ALICANTE: HTML access method declared; runtime health degraded/manual-review
BOP_BARCELONA: HTML access method declared
BOP_BIZKAIA: HTML access method declared
BOP_MALAGA: HTML access method declared
BOP_VALENCIA: HTML access method declared
```

### list_latest_discovery_entries

Input:

```json
{
  "source_code": "BOPV",
  "date": "YYYY-MM-DD",
  "limit": 20
}
```

Reads existing JSONL only:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

If the date is omitted, the reader resolves the latest existing dated output directory for the
source. If no JSONL output exists, it returns an empty structured result. It does not fetch live
RSS/API/HTML data and it does not create files.

Entries include a discovery marker:

```text
discovery_type=rss
discovery_type=api
discovery_type=html
```

If several output files exist for the same source/date, entries are returned in deterministic order:
RSS, API, HTML.

### preview_discovery

Input:

```json
{
  "source_code": "BOCYL",
  "date": "YYYY-MM-DD",
  "limit": 1,
  "discovery_type": "rss"
}
```

Runs a one-source metadata-only discovery preview through the MCP layer. The tool supports:

```text
rss: validated RSS/Atom discovery sources
api: BOPV
html: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, BOP_BARCELONA, BOP_BIZKAIA, BOP_CASTELLON, BOP_MALAGA, BOP_SEVILLA, BOP_VALENCIA
```

The default `limit` is `1`; the maximum allowed limit is `10`. If `discovery_type` is omitted, the
tool infers it when exactly one implemented preview type is available for the source.

Preview output includes:

```text
mode=preview
output_written=false
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

The tool refuses unknown sources, broad/all-source requests, inventory-only sources without an
implemented validated monitor, and `limit > 10`. It may fetch one declared endpoint for preview, but
it does not write JSONL, create files, create candidates, create evidence-grade records, download
PDFs/artifacts, mutate registry state, run backfills, or touch downstream repositories.

### recommend_next_sources

Input:

```json
{
  "limit": 5
}
```

Returns deterministic recommendations for the next source work. The current strategy is:

```text
provincial_html_discovery_pilot
```

The tool scans the registry and recommends provincial `inventory_only` sources with official landing
URLs and no validated monitor yet. It excludes already monitored sources such as `BOP_A_CORUNA`,
`BOP_ALBACETE`, `BOP_ALICANTE`, `BOP_BARCELONA`, `BOP_BIZKAIA`, `BOP_CASTELLON`,
`BOP_MALAGA`, `BOP_SEVILLA`, and `BOP_VALENCIA`.

Each recommendation includes:

```text
source_code
recommended_task
confidence
reason
constraints
discovery_cache_status
latest_cache_date
candidate_creation_allowed
evidence_grade_allowed
```

This tool is deterministic and does not use LLM classification. It does not execute previews, fetch
live sources, write JSONL, create files, create candidates, create evidence-grade records, download
PDFs/artifacts, run backfills, mutate registry state, or touch downstream repositories.

### list_case_taxonomy

Input:

```json
{
  "consumer": "optional consumer alias",
  "demand_class": "optional demand-class filter"
}
```

Returns the stable downstream case taxonomy used by consumer-aware MCP tools.

Implemented demand classes:

```text
public_employment_alerts
education_aid_evidence
benefit_source_discovery
fiscal_reference_resolution
future_grants_registry
```

The response is read-only and preserves:

```text
writes_performed=false
candidate_creation_allowed=false
evidence_grade_allowed=false
product_automation_allowed=false
human_review_required=true
```

This tool does not execute previews, fetch live sources, write JSONL, create candidates, create
evidence-grade records, mutate registry state, decide eligibility, decide fiscal or legal meaning,
approve publication, or touch downstream repositories.

## Safety Boundaries

The coverage surface must preserve these boundaries:

- RSS/API/HTML discovery is metadata-only.
- MCP cache readback is read-only.
- MCP `preview_discovery` may fetch one explicit source in preview mode only.
- MCP `recommend_next_sources` is deterministic and does not execute previews or live fetches.
- MCP `list_case_taxonomy` is deterministic and does not execute previews or live fetches.
- MCP does not write JSONL.
- MCP does not create files.
- `--write` is explicit for CLI monitor output.
- No automatic `source_candidates`.
- No automatic evidence-grade promotion.
- No PDF or artifact download.
- No downstream product writes.
- No backfills from coverage commands.
- No VPS or production DB operation from coverage commands.
- No LLM classification.
- No all-sources-green claim while any registered source is `degraded/manual-review`.
- No product-readiness inference from registry presence, `monitor_validated`, or
  `monitor_support=available`.

Use candidates, evidence-grade records, artifact downloads, backfills, downstream writes, or
production operations only through separate explicit tasks.

## Validation Commands

For a local coverage sanity check:

```bash
official-sources sources list
official-sources sources status --source BOCYL
official-sources sources status --source BOPV
official-sources rss monitor --source BOE --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOJA --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOCYL --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOIB --date YYYY-MM-DD --limit 1
official-sources rss monitor --source BOC_CANTABRIA --date YYYY-MM-DD --limit 1
official-sources rss monitor --source DOE --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ALBACETE --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_ALICANTE --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_BARCELONA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_BIZKAIA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_CASTELLON --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_MALAGA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_SEVILLA --date YYYY-MM-DD --limit 1
official-sources html monitor --source BOP_VALENCIA --date YYYY-MM-DD --limit 1
```

If `official-sources` does not reflect the current source tree, use the module entrypoint shown in
the registry section or refresh the editable install before trusting CLI sanity output.

Run the previews without `--write` unless the task explicitly requires JSONL output.

For operational run sequencing, write authorization, post-run checks, and report templates, follow:

```text
docs/SOURCE_COVERAGE_RUN_PLAN.md
```

For code validation:

```bash
python -m ruff check src tests
python -m pytest -q
git diff --check
```
