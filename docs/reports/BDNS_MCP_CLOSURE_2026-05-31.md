# BDNS MCP Closure - 2026-05-31

## Scope

This closure finalizes the BDNS grants remediation track for `official-sources`.

Implemented scope:

- BDNS safe metadata catalog preview and ingestion.
- BDNS grant-call metadata enrichment from local catalogs.
- BDNS grant-call JSONL export for downstream staging.
- Scoped BDNS concesiones preview and ingestion by `--num-conv`.
- Sanitized BDNS concesiones JSONL export.
- Private MCP read-only cache views for stored BDNS grant calls, catalog entries, and scoped
  concesiones.

Out of scope by design:

- Global BDNS concesiones ingestion.
- Public MCP exposure.
- MCP live BDNS fetching or write tools.
- Automatic downstream import, publication, candidate approval, eligibility decisions, or legal
  interpretation.
- Beneficiary field exposure by default.

## Privacy Boundary

`ingest-bdns-concesiones` requires `--num-conv`; broad/global concesiones ingestion is disabled.

Beneficiary name and person-id fields are redacted by default during concesiones parsing/storage.
MCP concesiones output does not expose `beneficiary_name` or `beneficiary_person_id`.

The `--include-beneficiary-fields` flag exists only for explicit privacy-reviewed operations.

## Local Verification

Commands run from `G:\_Proyectos\mcpspain\official-sources`:

```text
pytest -q
ruff check .
git diff --check
```

Result:

```text
626 passed, 1 warning
All checks passed
git diff --check: no errors
```

## VPS Verification

VPS:

```text
mcpspain-official-sources-vps
/opt/official-sources/app
/opt/official-sources/data/official_sources.sqlite
```

Post-change backup:

```text
/opt/official-sources/data/backups/official_sources_bdns_closure_20260531_151800.sqlite
```

Database validation:

```text
current_version=10
latest_version=10
status=valid
```

Stored BDNS counts after the bounded smoke:

```text
bdns_catalog_entries=603
bdns_concession_entries=5
schema_version=10
```

Sanitized concesiones export:

```text
/opt/official-sources/data/exports/bdns_concessions_877699_sanitized.jsonl
records_exported=5
```

MCP read-only smoke:

```text
grant_calls 2
concessions 2 BDNS:concesion:SB152503793
has_beneficiary_name False
pii_literal_present False
catalog_entries 2
```

Public listener check:

```text
No official-sources, MCP, FastMCP, Uvicorn, or Python listener was found.
```

## Operator Commands

Catalog refresh:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-bdns-catalog --catalog sectores
```

Grant-call export:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  export-bdns-grants --output /opt/official-sources/data/exports/bdns_grants_enriched.jsonl
```

Scoped concesiones ingest:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-bdns-concesiones --num-conv 877699 --page-size 5 --max-pages 1
```

Sanitized concesiones export:

```bash
official-sources --db-path /opt/official-sources/data/official_sources.sqlite \
  export-bdns-concessions --num-conv 877699 \
  --output /opt/official-sources/data/exports/bdns_concessions_877699_sanitized.jsonl
```

## Closure Status

BDNS is now usable as a private, review-first grants registry source family in `official-sources`.
The project remains cache-first and read-only from MCP. Downstream products must still consume
exports or MCP outputs through their own staging/review gates.
