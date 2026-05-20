# BOJA Pagination Guard - 2026-05-20

## Summary

TASK-AUTO-002B adds pagination and completeness checks to the BOJA metadata MVP before any controlled BOJA date-range backfill.

The adapter now either fetches the complete result set for one BOJA publication date or marks the ingestion as incomplete/failed. It must not silently store page 0 as complete when the official API indicates more results may exist.

No BOJA backfill, candidate extraction, PDF download, downstream write, MCP exposure, approval, publication, RAG, or legal interpretation was implemented.

## BOJA Pagination Metadata

The implemented endpoint remains:

```text
GET https://datos.juntadeandalucia.es/api/v0/boja/get/search_pagination
```

A controlled live metadata check with:

```text
date_from=2026-05-19
date_to=2026-05-19
size=2
page=0
```

returned top-level pagination fields:

```text
hits=2
total_hits=72
results=[...]
```

The checked response did not expose `totalPages`, `has_next`, `first`, `last`, or an echoed page number. The adapter therefore uses `total_hits` as the completeness target and treats missing `total_hits` as ambiguous pagination metadata.

## Implemented Behavior

`official-sources ingest-boja-date --date YYYY-MM-DD` now:

- fetches page 0;
- reads `total_hits`;
- continues fetching page 1, page 2, and later pages until all expected documents are collected;
- deduplicates documents by stable external ID;
- stores documents only when the complete result set is available;
- records `pages_fetched`;
- records `pagination_complete=true` only after completeness is proven;
- keeps BOJA ingestion metadata-only.

Empty BOJA date behavior:

```text
total_hits=0
results=[]
pages_fetched=1
pagination_complete=true
status=no_publication
```

Ambiguous or incomplete behavior:

```text
missing total_hits -> status=failed, pagination_complete=false
max pages reached before total_hits -> status=failed, pagination_complete=false
unique collected documents < total_hits -> status=failed, pagination_complete=false
```

Incomplete runs do not store partial BOJA documents.

## Max-Page Guard

The default page safety limit is:

```text
OFFICIAL_SOURCES_BOJA_MAX_PAGES_PER_DATE=20
```

If the environment variable is absent, the internal default is `20`. Values less than or equal to zero are rejected.

If the adapter reaches the max-page limit before satisfying `total_hits`, the ingestion run is marked as failed and reports that pagination exceeded the configured safety limit.

## Hash Strategy

For multi-page BOJA ingestion, the adapter computes a deterministic combined raw payload hash from the ordered raw page payloads:

```text
sha256(page0_raw + "\n---BOJA-PAGE---\n" + page1_raw + ...)
```

The combined payload is stored as the `raw_api_response` document file payload for the documents in that date ingestion run, and the combined hash is stored as `source_snapshot_hash`.

Hashes are computed from raw official API bytes, not normalized fields. They are integrity signals only and do not imply electronic signature validation.

## CLI Output

`ingest-boja-date` now prints:

```text
pages_fetched=<n>
pagination_complete=true|false
documents_fetched=<n>
documents_new=<n>
documents_updated=<n>
status=<status>
```

Example controlled live smoke output:

```text
status=success pages_fetched=1 pagination_complete=true documents_fetched=72 documents_new=72 documents_updated=0 retry_count=0 throttle_triggered=0 last_http_status=200
```

## Tests Added

Added fixture coverage for:

```text
tests/fixtures/boja_date_page_0.json
tests/fixtures/boja_date_page_1.json
tests/fixtures/boja_date_ambiguous_pagination.json
```

Added tests for:

- single-page BOJA ingestion output;
- multi-page BOJA ingestion;
- final-page detection through `total_hits`;
- storing all documents across pages;
- duplicate protection by external ID;
- max-page safety failure;
- ambiguous pagination metadata failure;
- deterministic combined raw payload hash;
- no PDF download by default;
- no candidate creation;
- no downstream writes.

## Live Smoke

A single-date live smoke was run against a temporary local database:

```bash
rtk powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path 'G:\tmp\official-sources-boja-pagination-smoke-20260520' | Out-Null; python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-pagination-smoke-20260520\official_sources_boja_pagination.sqlite' ingest-boja-date --date 2026-05-19"
rtk powershell -NoProfile -Command "python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-pagination-smoke-20260520\official_sources_boja_pagination.sqlite' db validate"
```

Result:

```text
status=success
pages_fetched=1
pagination_complete=true
documents_fetched=72
documents_new=72
documents_updated=0
last_http_status=200
db_validate=status=valid
```

No PDF download, candidate extraction, downstream write, approval, publication, or range backfill was run.

## Validation

Validation executed:

```bash
rtk python -m pytest tests/test_boja_adapter.py tests/test_cli_boja.py -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Current validation status is recorded in `docs/VALIDATION.md`.

## Backfill Readiness

BOJA 30-day metadata backfill can now start as a controlled metadata-only task, provided that it includes:

- pre-run and post-run DB backups;
- no PDF download;
- no candidate extraction;
- no downstream writes;
- per-date reporting of `pages_fetched` and `pagination_complete`;
- stop/report behavior for any incomplete date.

## Known Limitations

- The API response checked exposes `total_hits`, but not `totalPages` or `has_next`.
- Completeness depends on BOJA continuing to provide reliable `total_hits`.
- The default safety limit is 20 pages per date.
- No BOJA range command is implemented yet.
- No BOJA PDF download, text extraction, candidate extraction, or downstream export is implemented.
