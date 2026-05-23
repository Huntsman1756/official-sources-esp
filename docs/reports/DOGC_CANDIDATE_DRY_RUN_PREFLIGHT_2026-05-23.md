# DOGC Candidate Dry-Run Preflight - 2026-05-23

## Scope

Task: `TASK-AUTO-DOGC-004-PREP`.

This is a local/docs-only readiness check for a future DOGC candidate dry-run.

Explicitly not performed:

- No VPS access.
- No candidate creation.
- No artifact downloads.
- No downstream writes.
- No unrelated adapter changes.
- No DOGC live request or production database operation.

## Files Reviewed

- `src/official_sources/sources/dogc/client.py`
- `src/official_sources/sources/dogc/ingestion.py`
- `src/official_sources/sources/dogc/parser.py`
- `src/official_sources/cli.py`
- `tests/test_dogc_adapter.py`
- `tests/test_cli_dogc.py`
- `tests/test_cli.py`
- `docs/reports/DOGC_ADAPTER_MVP_LOCAL_2026-05-23.md`
- `docs/reports/DOGC_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/PREFLIGHT_AND_BOPV_BACKFILL_INTEGRATION_2026-05-23.md`

## Adapter Readiness

DOGC has a metadata-only one-date adapter:

```text
official-sources ingest-dogc-date --date YYYY-MM-DD
```

The adapter stores official document metadata and raw API response records. It preserves official
HTML, XML, RDF, Turtle, and PDF URLs as metadata, but does not download those artifacts. Existing
tests and reports cover the local fixture path, no-publication path, citation construction, and
metadata-only safety checks.

Important adapter behavior for candidate readiness:

- `calendarDOGC` is called before date search to preserve `numDOGC` when available.
- `searchDOGC` receives publication date bounds in `DD/MM/YYYY`.
- `documentDOGC` is used to enrich date-search rows and normalize final external IDs to
  `DOGC:<CVE>`.
- Empty `resultSearch` is treated as controlled `no_publication`.
- `source_candidates` and artifact download tables are not touched by DOGC ingestion.

## Candidate CLI Support

`find-source-candidates` does not currently support DOGC on this branch.

Current source allowlist in `src/official_sources/cli.py`:

```text
BOE, BOJA, DOGV, BOCM, BOCYL, BDNS
```

`DOGC` is absent from `SOURCE_CANDIDATE_SOURCE_CODES`, so a future command with
`--source DOGC` would be rejected by argparse before scanning stored documents. Existing generic
source-filter tests cover `DOGV`, `BOCM`, and `BDNS`, but not DOGC.

Current candidate profiles:

```text
la-ayuda, boja-ayudas, dogv-ayudas, bocyl-ayudas
```

There is no DOGC-specific profile. Using the generic `la-ayuda` profile directly against Catalan
DOGC metadata would likely produce unstable or biased measurements because DOGC titles and metadata
may be in Catalan and the current source-specific profiles were tuned for other bulletins.

## Recommended Command

Do not run a DOGC candidate dry-run yet.

The command shape should only be used after DOGC is explicitly added to
`SOURCE_CANDIDATE_SOURCE_CODES`, a DOGC-specific profile exists, and a stored DOGC metadata window is
available:

```bash
official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source DOGC \
  --date-from 2026-04-24 \
  --date-to 2026-05-23 \
  --profile dogc-ayudas \
  --dry-run \
  --limit 200
```

For a first measurement run, keep it dry-run only. Do not combine it with `--write`, artifact
download commands, downstream export commands, evidence-review commands, or ingestion/backfill loops.

## Preflight Risks

### TLS / Connectivity

The DOGC backfill preflight recorded a local live probe failure before an HTTP status:

```text
[SSL:_SSLV3_ALERT_HANDSHAKE_FAILURE] ssl/tls alert handshake failure
```

This does not directly block scanning already stored metadata, but it blocks confidence in any
candidate dry-run plan that depends on first creating or refreshing the DOGC 30-day metadata window.
A single-date VPS smoke must succeed before any DOGC backfill is used as the candidate dry-run input.

### Pagination

`searchDOGC` currently uses:

```text
page=1
numResultsByPage=100
```

The adapter does not paginate beyond page 1. If any date has more than 100 DOGC results, the stored
metadata window may be incomplete and the candidate dry-run would undercount relevant documents.
This is a stop condition for the metadata-prep phase before candidate dry-run.

### Date Search Stability

DOGC date search uses exact publication-date bounds and then enriches each result through
`documentDOGC`. The fixture path is stable, but live date behavior still needs confirmation on VPS.
Risk points:

- `calendarDOGC` may report no DOGC for the date while search behavior changes.
- `searchDOGC` may return mixed or missing issue identifiers.
- `documentDOGC` may omit `CVE` or return a `dateDOGC` different from the target date.
- Catalan titles and section labels may require DOGC-specific keyword and exclusion rules before
  candidate scoring is meaningful.

## Likely DOGC-Specific Profile Need

DOGC should get a dedicated profile before any candidate dry-run is treated as a quality signal.

Minimum profile requirements:

- Catalan and Spanish aid vocabulary, not just generic `ayuda` / `beca` terms.
- DOGC section and department exclusions tuned to DOGC metadata.
- Weak-match rules to avoid counting generic public procurement, awards, appointments, and purely
  organizational notices.
- A small fixture or stored-document sample report showing matched, excluded, and missed DOGC
  examples before any write-mode candidate task.

The initial profile should be measurement-oriented and conservative. It should be expected to change
after the first dry-run review.

## Stop Conditions

Stop and report without running a DOGC candidate dry-run if any of these are true:

- `find-source-candidates --source DOGC` is still unsupported.
- No DOGC-specific profile exists.
- The target DOGC metadata window has not been ingested and validated.
- A DOGC metadata-prep run hits TLS handshake failure, timeout, non-200 status, or `status=failed`.
- Any DOGC date appears to require pagination beyond page 1 / 100 results.
- `documentDOGC` returns missing `CVE`, mixed/missing `numDOGC`, or mismatched publication dates.
- `db validate` is not `status=valid`.
- Candidate count changes during a supposed dry-run.
- Artifact download attempts or PDF/HTML/XML file rows are created.
- Any downstream export, evidence-review state, approval, or publication command is chained.

## Sequencing Against BOA and BORM

DOGC should run after BOA and BORM for candidate dry-run preparation.

Reasoning:

- DOGC candidate scanning is not enabled in the current `find-source-candidates` allowlist.
- DOGC has known live TLS/connectivity risk from local preflight.
- DOGC has a pagination ceiling risk at 100 date-search results.
- DOGC likely needs a new `dogc-ayudas` profile before dry-run results are meaningful.
- BORM had the cleanest local backfill readiness among BOA, DOGC, and BORM, with no pagination cursor
  risk for the current-year 30-day window.
- BOA is also more operationally straightforward than DOGC, with the documented `documents_fetched=250`
  stop condition.

If candidate dry-runs for BOA or BORM are not yet source-allowlisted either, they also need explicit
CLI support and source-specific profiles before scanning. DOGC should still remain behind them until
its TLS, pagination, and profile risks are resolved.

## Readiness Decision

DOGC is not ready for candidate dry-run execution today.

It is ready for the next local preparation step: add explicit `find-source-candidates --source DOGC`
support, add a conservative DOGC-specific candidate profile, and test that dry-run mode scans only
DOGC stored metadata without creating candidates. After that, run a separate metadata-window readiness
check based on validated DOGC ingestion results before scheduling any dry-run on the VPS.
