# BOJA No-Publication Probe - 2026-05-20

## Summary

TASK-AUTO-003B inspected BOJA empty-date and HTTP error behavior after the controlled BOJA 30-day metadata backfill stopped on `2026-04-25`.

The probe confirmed that the BOJA official API can return HTTP 400 with a generic JSON body for valid dates that appear to have no publication issue. The adapter now classifies only the observed narrow BOJA 400 shape as `no_publication`.

No BOJA backfill, candidate extraction, PDF download, downstream write, MCP exposure, approval, publication, RAG, or legal interpretation was run.

## Endpoint Probed

Official endpoint:

```text
GET https://datos.juntadeandalucia.es/api/v0/boja/get/search_pagination
```

Query shape:

```text
order_by=date
mode=DESC
size=200
page=0
date_from=YYYY-MM-DD
date_to=YYYY-MM-DD
```

## Probe Dates

The probe made one request per date:

| date | reason |
| --- | --- |
| 2026-04-25 | failed date from TASK-AUTO-003 |
| 2026-04-26 | following day |
| 2026-04-27 | following Monday / publication day check |
| 2026-05-01 | possible non-working day |
| 2026-05-19 | known successful date |

## Observed Behavior

| date | http_status | content_type | body_shape | results_count | hits | total_hits | observed body/error shape | classification |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 2026-04-25 | 400 | application/json | object | n/a | n/a | n/a | `{"status":400,"message":"Bad request"}` | no_publication |
| 2026-04-26 | 400 | application/json | object | n/a | n/a | n/a | `{"status":400,"message":"Bad request"}` | no_publication |
| 2026-04-27 | 200 | application/json | object | 44 | 44 | 44 | `hits`, `total_hits`, `results` | success |
| 2026-05-01 | 400 | application/json | object | n/a | n/a | n/a | `{"status":400,"message":"Bad request"}` | no_publication |
| 2026-05-19 | 200 | application/json | object | 72 | 72 | 72 | `hits`, `total_hits`, `results` | success |

The 400 body does not explicitly say "no publication". The classification is based on the combination of:

- valid ISO date inputs;
- the same query shape succeeding for publication dates;
- weekend/non-working dates consistently returning the same generic BOJA JSON error;
- no `results`, `hits`, or `total_hits` in the 400 response.

## Classification Rules

BOJA ingestion now uses these rules:

| response | classification |
| --- | --- |
| `200` with `results_count > 0`, `total_hits`, and complete pagination | `success` |
| `200` with `results=[]` and `total_hits=0` | `no_publication` |
| `400` with exactly observed BOJA generic body `{"status":400,"message":"Bad request"}` | `no_publication` |
| `400` with validation/request-specific body | `failed` |
| `404` | `failed` unless future evidence proves an official no-publication body |
| `5xx` after retries | `failed` |
| network errors after retries | `failed` |
| missing `total_hits` in a `200` response | `failed` / incomplete |
| pagination incomplete or max-page exhaustion | `failed` / incomplete |

This does not copy BOE Sunday semantics. BOJA has a separate source-specific rule.

## Implementation

The adapter now detects the observed BOJA no-publication HTTP 400 body inside `ingest_boja_date`.

When matched, it records:

```text
status=no_publication
documents_fetched=0
documents_new=0
documents_updated=0
last_http_status=400
pages_fetched=0
pagination_complete=true
```

The ingestion run keeps an explicit message explaining that the 400 was classified from observed empty-date API behavior.

Other 400 responses remain failures.

## Controlled Live Re-Test

After tests passed, a single-date live re-test was run for `2026-04-25` against a temporary local database:

```bash
rtk powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path 'G:\tmp\official-sources-boja-400-probe-20260520' | Out-Null; python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-400-probe-20260520\official_sources_boja_400.sqlite' ingest-boja-date --date 2026-04-25; python -c 'import sys; sys.path.insert(0, ''src''); from official_sources.cli import main; main()' --db-path 'G:\tmp\official-sources-boja-400-probe-20260520\official_sources_boja_400.sqlite' db validate"
```

Result:

```text
status=no_publication
pages_fetched=0
pagination_complete=true
documents_fetched=0
documents_new=0
documents_updated=0
last_http_status=400
db_validate=status=valid
```

No PDF download, candidate extraction, downstream write, approval, publication, or range backfill was run.

## Tests

Added tests for:

- `200` with results remains `success`;
- `200` empty fixture remains `no_publication`;
- observed BOJA `400 {"status":400,"message":"Bad request"}` becomes `no_publication`;
- BOJA `400` validation-style body remains `failed`;
- `404` remains `failed`;
- `5xx` remains `failed`;
- pagination incomplete remains `failed`;
- `last_http_status=400` is persisted for observed no-publication;
- no PDF download;
- no candidates;
- no downstream writes.

## Backfill Recommendation

`TASK-AUTO-003` can be resumed from the failed date after this fix is deployed to the VPS.

Recommended next task:

```text
TASK-AUTO-003C - Resume controlled BOJA 30-day metadata backfill
```

Scope:

- deploy the hardening commit to the VPS;
- resume the same target range from `2026-04-25` through `2026-05-20`;
- keep metadata-only behavior;
- no PDFs;
- no candidates;
- no downstream.

## Known Limitations

- The BOJA 400 no-publication body is generic and does not explicitly say "no publication".
- The rule is intentionally narrow and source-specific.
- Other BOJA 400 bodies still fail.
- No BOJA range command exists yet.
- No BOJA candidate extraction, PDF download, text extraction, downstream export, or downstream integration exists yet.
