# Source registry - 2026-05-24

Task: `TASK-SOURCE-REGISTRY-001`

## Why This Was Added

`docs/OFFICIAL_BULLETIN_REGISTRY.md` was a static coverage inventory. The project now needs a
machine-readable source coverage contract that future MCP reporting, source monitors, and adapter
planning can use without treating documentation tables as runtime data.

The executable registry is:

```text
config/sources.yaml
```

## Registry Fields

Each source entry includes:

- `source_code`
- `name`
- `jurisdiction`
- `jurisdiction_level`
- `official_landing_url`
- `access_methods`
- `operational_status`
- `mcp_support`
- `monitor_support`
- `backfill_support`
- `evidence_adapter`
- `candidate_creation_allowed`
- `evidence_grade_allowed`
- `last_verified_at`
- `limitations`
- `notes`

The registry separates public identity from operational access:

```text
official_landing_url = public canonical landing page
access_methods[].url = technical endpoint/feed/page used by adapters or future monitors
```

## Status Definitions

`operational_status` is restricted to:

- `inventory_only`
- `monitor_candidate`
- `monitor_validated`
- `metadata_adapter_validated`
- `evidence_grade`
- `paused`
- `blocked`
- `deprecated`

`access_methods[].status` is restricted to:

- `inventory`
- `candidate`
- `validated`
- `paused`
- `blocked`
- `deprecated`

The current registry uses only:

- operational statuses: `metadata_adapter_validated`, `paused`, `inventory_only`
- access method statuses: `validated`, `paused`

Ambiguous values such as `partial`, `ok`, `active`, and `unknown` are rejected by validation.

## Sources Included

Registered source count: 22.

Initial code-backed or adapter-backed entries:

- BOE
- BDNS
- BOJA
- BOA
- BOCYL
- DOGC
- BORM
- BOPV
- DOGV

Paused operational entry:

- BOCM

Inventory-only entries:

- DOUE
- BOPA
- BOIB
- BOC_CANARIAS
- BOC_CANTABRIA
- DOCM
- DOE
- DOG
- BOR
- BON
- BOCCE
- BOME

## Validation

Validation lives in:

```text
src/official_sources/source_registry.py
tests/test_source_registry.py
```

It enforces:

- unique `source_code`
- uppercase stable source identifiers
- explicit `operational_status`
- explicit `jurisdiction_level`
- explicit `access_methods`, even when empty
- `type` and `status` for every access method
- explicit `candidate_creation_allowed`
- explicit `evidence_grade_allowed`
- no `evidence_grade` operational status unless evidence-grade permission is explicitly enabled
- evidence-grade permission may be enabled only for sources with existing evidence support in code/docs
- `monitor_support=validated` only with at least one validated RSS/Atom/API/XML/HTML method
- validated access methods must include a URL or a clear notes justification

## Read-Only Reporting

Read-only CLI commands were added:

```bash
official-sources sources list
official-sources sources status --source BOCYL
```

These commands read the YAML registry only. They do not open SQLite, ingest data, create
candidates, create evidence records, download artifacts, or write downstream outputs.

## Guardrail Confirmation

This task did not create:

- source candidates
- evidence-grade records
- PDFs or downloaded source artifacts
- backfill runs
- monitor runs
- production DB operations
- VPS operations
- downstream product writes

## Next Recommended Task

```text
TASK-SOURCE-RSS-MONITOR-001 - RSS/Atom discovery monitor
```

Suggested pilots:

- BOCYL as the first real autonomous bulletin pilot
- BOE as a secondary positive control
