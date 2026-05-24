# BOA Next Operation Prep - 2026-05-24

## Scope

Task: `TASK-AUTO-BOA-NEXT-PREP`.

This report prepares the next BOA VPS operation from local repository evidence only.

Guardrails applied:

- no VPS connection;
- no ingestion;
- no source candidates;
- no artifact downloads;
- no downstream work;
- no changes outside this report.

## Inputs Reviewed

- `src/official_sources/sources/boa/client.py`
- `src/official_sources/sources/boa/parser.py`
- `src/official_sources/sources/boa/ingestion.py`
- `src/official_sources/cli.py`
- `docs/reports/BOA_ADAPTER_MVP_LOCAL_2026-05-23.md`
- `docs/reports/BOA_BACKFILL_PREFLIGHT_2026-05-23.md`
- `docs/reports/BOA_BACKFILL_RUNBOOK_2026-05-23.md`
- `docs/reports/BOA_CANDIDATE_DRY_RUN_PREFLIGHT_2026-05-23.md`
- `docs/reports/CANDIDATE_SOURCE_SUPPORT_BOPV_BOA_BORM_DOGC_2026-05-23.md`
- `docs/reports/CANDIDATE_DRY_RUN_PREFLIGHT_SYNTHESIS_2026-05-23.md`
- `docs/reports/NEXT_SOURCE_OPERATION_SYNTHESIS_2026-05-23.md`
- `docs/reports/PREFLIGHT_AND_BOPV_BACKFILL_INTEGRATION_2026-05-23.md`
- `docs/VALIDATION.md`

## Current BOA State

BOA has a metadata-only one-date ingestion adapter:

```text
official-sources ingest-boa-date --date YYYY-MM-DD
```

The adapter uses the official BOA CGI JSON endpoint by publication date:

```text
CMD=VERLST&BASE=BOLE&DOCS=1-250&SEC=OPENDATABOAJSONAPP&OUTPUTMODE=JSON&SORT=-PUBL&SEPARADOR=&PUBL=YYYYMMDD
```

Important adapter facts:

- the adapter stores metadata and one `raw_api_response` document file row per BOA document;
- it does not create `source_candidates`;
- it does not download PDFs or other artifact files;
- it preserves official BOA URLs as metadata;
- no-publication dates are represented as `status=no_publication`;
- `documents_fetched=250` is a hard pagination/completeness risk because the request window is `DOCS=1-250` and there is no pagination guard.

Candidate scanning support for BOA now exists locally:

```text
find-source-candidates --source BOA --profile boa-ayudas
```

That support does not by itself make BOA ready for a candidate dry-run. A candidate dry-run is only meaningful after the BOA 30-day metadata window exists in the VPS database and is validated.

## Evidence For Next Step

Local reports show:

- BOA adapter MVP and local preflight are complete.
- BOA 30-day metadata-only runbook is complete.
- BOA was ready for separately approved VPS metadata-only backfill.
- The BOA candidate dry-run preflight originally blocked on candidate CLI support and on the missing BOA 30-day metadata window.
- Candidate CLI support has since been added for `BOA` and `boa-ayudas`.
- No local report or `docs/VALIDATION.md` entry records a completed BOA 30-day metadata backfill.
- No local report named `BOA_30_DAY_METADATA_BACKFILL_*.md` is present.

Decision:

```text
next_step=BOA 30-day metadata-only backfill
```

Do not run a BOA candidate dry-run as the next operation unless an operator first verifies, from VPS evidence, that the BOA 30-day metadata backfill already completed successfully for the target range and that no date reached the `documents_fetched=250` stop condition.

## Recommended Operation

Recommended task:

```text
TASK-AUTO-BOA-004 - Controlled BOA 30-day metadata backfill
```

Recommended range:

```text
source_code=BOA
date_from=2026-04-21
date_to=2026-05-20
dates_expected=30
```

Recommended command source:

```text
docs/reports/BOA_BACKFILL_RUNBOOK_2026-05-23.md
```

Use that runbook's full backup, validation, loop, stop-condition, and post-run reporting procedure. The core ingestion command inside the loop is:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  ingest-boa-date --date "$d"
```

Do not combine this with a candidate command, artifact download, downstream export, or another source backfill.

## Backup Requirement

A fresh pre-run backup is mandatory before the first BOA date command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output "/opt/official-sources/data/backups/official_sources_before_boa_30d_backfill_${STAMP}.sqlite"
```

The backup is acceptable only if the command reports:

```text
verification=quick_check
source_check=ok
backup_check=ok
status=success
```

If the backfill completes without a stop condition, create a post-run backup with the same verification expectations:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output "/opt/official-sources/data/backups/official_sources_after_boa_30d_backfill_${STAMP}.sqlite"
```

## Validations

Pre-run validations:

- remote worktree is clean;
- deployed commit is the approved commit for the operation;
- `official-sources --help` lists `ingest-boa-date`;
- database validation reports `status=valid`;
- fresh pre-run backup succeeds and verifies;
- pre-run counts are captured for BOA documents, BOA ingestion runs, `source_candidates`, `artifact_download_attempts`, BOA `document_files` by `file_type`, and artifact directory size.

Per-date validations:

- command exits `0`;
- output contains no `status=failed`;
- `last_http_status=200`;
- `source_snapshot_hash` is not `none`;
- `documents_fetched < 250`;
- `retry_count=0`;
- `throttle_triggered=0`;
- processed date remains inside `2026-04-21` through `2026-05-20`.

Post-run validations:

- database validation reports `status=valid`;
- 30 target dates are accounted for unless the report records a stop condition;
- failed-date count is `0`;
- no BOA date has `documents_fetched >= 250`;
- `source_candidates` count is unchanged;
- `artifact_download_attempts` count is unchanged;
- BOA `document_files` contain only `raw_api_response`;
- artifact directory size is unchanged except for explicitly explained pre-existing unrelated state;
- post-run backup succeeds and verifies.

## Stop Conditions

Stop immediately and report without resuming if any of these occur:

- any command exits non-zero;
- database validation fails;
- pre-run backup cannot be created or verified;
- deployed CLI does not include `ingest-boa-date`;
- deployed commit is not the approved commit;
- `status=failed`;
- `last_http_status` is not `200`;
- `source_snapshot_hash=none`;
- `documents_fetched >= 250`;
- any other sign that BOA `DOCS=1-250` may have truncated the result set;
- `retry_count > 0`;
- `throttle_triggered != 0`;
- repeated slow responses, timeout symptoms, HTTP 429, or HTTP 5xx;
- candidate count changes;
- artifact download attempt count changes;
- BOA creates any `document_files.file_type` other than `raw_api_response`;
- a command runs outside the target range;
- any candidate, artifact download, downstream, or unrelated source command is accidentally run.

If stopped on `documents_fetched >= 250`, do not mark that date as complete. The next task must inspect BOA pagination/completeness behavior before a resume.

## If Backfill Is Already Complete

If an operator discovers current VPS evidence that the BOA 30-day metadata backfill already completed, do not repeat the backfill blindly. First require a report or direct checks proving:

- the completed range is exactly `2026-04-21` through `2026-05-20`;
- all 30 dates are accounted for;
- failed-date count is `0`;
- database validation is `status=valid`;
- no date has `documents_fetched >= 250`;
- `source_candidates` and `artifact_download_attempts` did not change during the backfill;
- BOA `document_files` are only `raw_api_response`;
- pre-run and post-run backups exist and verify.

Only after those checks should the next BOA operation become a read-only candidate dry-run:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOA \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile boa-ayudas \
  --dry-run \
  --limit 200
```

That dry-run must remain measurement-only:

- no `--write`;
- no candidate creation;
- no artifact downloads;
- no downstream writes;
- no publication decision.

## Risks

- BOA's `DOCS=1-250` request can hide truncation if a daily issue reaches the requested ceiling.
- BOA no-publication parsing depends on official page text and could break if BOA changes the no-records HTML.
- The candidate profile `boa-ayudas` is a first-pass filter, not production classification.
- Metadata-only matching may overmatch awards, appointments, procurement, corrections, employment, municipal notices, or public-entity grants.
- Running BOA in parallel with another VPS operation would make counts and rollback boundaries harder to audit.
- Repeating a completed backfill without checking current VPS state could add noisy duplicate run records even if document upserts remain idempotent.

## Clear Recommendation

Proceed next with the controlled BOA 30-day metadata-only backfill, using `docs/reports/BOA_BACKFILL_RUNBOOK_2026-05-23.md` as the authoritative operation procedure.

Do not run BOA candidate dry-run next based on this branch's local evidence. Switch to candidate dry-run only if current VPS evidence proves the BOA metadata window is already complete and clean.
