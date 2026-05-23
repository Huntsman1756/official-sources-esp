# BOA Candidate Dry-Run Preflight - 2026-05-23

## Scope

Task: `TASK-AUTO-BOA-004-PREP`.

This is a local documentation preflight for a future BOA candidate dry-run. No VPS access was used, no
candidate command was executed against production data, no candidates were created, no artifacts were
downloaded, and no unrelated adapters were modified.

## Inputs Reviewed

- `src/official_sources/sources/boa/client.py`
- `src/official_sources/sources/boa/parser.py`
- `src/official_sources/sources/boa/ingestion.py`
- `src/official_sources/cli.py`
- `tests/test_boa_adapter.py`
- `tests/test_cli_boa.py`
- `docs/reports/BOA_ADAPTER_MVP_LOCAL_2026-05-23.md`
- `docs/reports/BOA_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/PREFLIGHT_AND_BOPV_BACKFILL_INTEGRATION_2026-05-23.md`

## Adapter Readiness

BOA has a metadata-only one-date ingestion command:

```text
official-sources ingest-boa-date --date YYYY-MM-DD
```

The adapter uses BOA's official CGI JSON endpoint with a published-date filter:

```text
CMD=VERLST&BASE=BOLE&DOCS=1-250&SEC=OPENDATABOAJSONAPP&OUTPUTMODE=JSON&SORT=-PUBL&SEPARADOR=&PUBL=YYYYMMDD
```

The existing adapter and CLI tests cover source registration, date validation, published-date parsing,
no-publication parsing, document metadata normalization, official URL preservation, metadata-only
ingestion, zero source-candidate writes, zero artifact download attempts, citation generation, and CLI
success/no-publication output.

## Candidate CLI Support

`find-source-candidates` is not ready for BOA yet.

Current CLI support:

```text
--source {BOE,BOJA,DOGV,BOCM,BOCYL,BDNS}
```

Current profile support:

```text
--profile {la-ayuda,boja-ayudas,dogv-ayudas,bocyl-ayudas}
```

Finding:

- `BOA` is not in `SOURCE_CANDIDATE_SOURCE_CODES`.
- There is no BOA-specific candidate profile.
- A future `--source BOA` dry-run will fail argument parsing until the source allowlist is extended.

This task did not implement the allowlist change because the requested output is a docs-only preflight
and the missing support should be paired with a small test update before any VPS dry-run.

## Expected Future Dry-Run

Expected source:

```text
BOA
```

Expected range:

```text
2026-04-21 through 2026-05-20
```

Expected initial profile:

```text
la-ayuda
```

The first BOA dry-run should be measurement only. It should use `--dry-run` or `--no-write` and should
not use `--write`.

## Command To Run Later On VPS

Do not run this until both conditions are true:

1. A metadata-only BOA 30-day VPS backfill has completed successfully for the same range.
2. `find-source-candidates --source BOA` is supported by the deployed CLI.

Recommended future command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOA \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile la-ayuda \
  --dry-run \
  --limit 100
```

If BOA support is added before a source-specific profile exists, treat `--profile la-ayuda` as a noisy
baseline, not as candidate-write readiness.

## Known Risks

- BOA candidate dry-run is blocked by CLI source allowlist support.
- The BOA adapter requests `DOCS=1-250` and does not paginate; the prior preflight requires stopping on
  any date with `documents_fetched=250`.
- BOA stores PDF URLs as metadata but the dry-run should not download PDFs or any other artifact type.
- Candidate matching is metadata/title based, not legal classification.
- The generic `la-ayuda` profile may overmatch BOA notices, especially awards, appointments,
  procurement, administrative corrections, municipal notices, or institutional grants that are not
  direct-person aid opportunities.
- BOA issue metadata may use sections and departments differently from BOE/BOJA/DOGV/BOCYL, so existing
  section filters may not transfer cleanly.

## Source-Specific Profile Decision

A BOA-specific profile is likely needed before any real candidate creation.

Recommended dry-run interpretation:

- If the generic `la-ayuda` filtered match rate is high, do not create BOA candidates.
- If many matches come from non-aid sections, add BOA section or document-type downranking.
- If many matches are public-entity, award, procurement, employment, or correction records, add
  source-specific negative rules before write mode.
- If a small set of direct-person aid notices appears, review them manually before proposing a
  limited write task.

## Stop Conditions

Stop the future BOA candidate dry-run preparation if any of these occur:

- `find-source-candidates --help` does not list `BOA` under `--source`.
- The BOA 30-day metadata backfill is missing, incomplete, or has failed dates.
- Any BOA backfill date reports `documents_fetched=250`.
- Candidate count changes during a supposed dry-run.
- Artifact download attempt count changes during the operation.
- The command requires `--write` to produce useful output.
- The result set is dominated by non-aid administrative notices.
- Database validation fails before or after the operation.

## Readiness

BOA is not yet ready for a VPS candidate dry-run.

Readiness status:

```text
blocked_by_cli_source_allowlist
```

Next safe task:

```text
Add BOA to find-source-candidates source support with a focused CLI test, then rerun this preflight
before any VPS candidate dry-run.
```
