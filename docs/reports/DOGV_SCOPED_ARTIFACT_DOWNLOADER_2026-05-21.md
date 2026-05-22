# DOGV Scoped Artifact Downloader - 2026-05-21

## Summary

TASK-AUTO-DOGV-007B adds scoped DOGV PDF artifact download support.

The new path is intentionally narrow: it only supports explicit DOGV candidate IDs and explicit PDF
downloads from persisted `url_pdf` values. It does not infer DOGV URLs, does not support DOGV
date-level downloads, and does not enable DOGV HTML or XML artifact downloads.

## Command Added

Preferred command:

```bash
official-sources download-source-artifacts \
  --source DOGV \
  --candidate-ids 101,102,103,104,106,108,109,111,117,124 \
  --types pdf
```

The legacy command remains backwards compatible:

```bash
official-sources download-boe-artifacts --source BOE ...
official-sources download-boe-artifacts --source BOJA ...
```

The legacy command also accepts `--source DOGV`, but DOGV still follows the same strict scoped PDF
guards.

## DOGV Safety Rules

```text
--source DOGV is explicit
--candidate-ids is required
--types pdf is required
--document-ids is rejected for DOGV
--date is rejected for DOGV
more than 10 DOGV candidate IDs is rejected
missing url_pdf is recorded as skipped
non-DOGV selected candidates are rejected
download uses persisted url_pdf only
HTML/XML DOGV downloads are unsupported
```

URL validation:

```text
scheme=https
host=dogv.gva.es
path starts with /datos/
path ends with .pdf
```

## Implementation Notes

Files changed:

```text
src/official_sources/cli.py
src/official_sources/sources/dogv/artifacts.py
tests/test_cli.py
docs/SOURCES_POLICY.md
docs/VALIDATION.md
docs/reports/DOGV_SELECTED_CANDIDATE_EVIDENCE_DOWNLOAD_2026-05-21.md
```

The DOGV downloader reuses the existing artifact storage and attempt-recording flow:

```text
document_files
artifact_download_attempts
SHA-256 over raw response bytes
source-specific artifact cache directory: dogv/
```

No source candidate creation, status mutation, downstream write, approval, or publication is part of
the downloader.

## Tests Added

New coverage includes:

```text
DOGV scoped PDF download uses persisted url_pdf
candidate IDs restrict download to selected DOGV documents only
non-DOGV candidate is rejected under --source DOGV
missing DOGV url_pdf is recorded as skipped
DOGV date-level artifact download is rejected
DOGV requires explicit --types pdf
PDF hash is computed from raw bytes
artifact_download_attempts is recorded
document_files is recorded
source_candidates count is unchanged
BOE/BOJA existing artifact tests still pass
download-source-artifacts help lists DOGV and scoped options
```

## Validation

Local validation command set:

```text
git diff --check
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

Result:

```text
git diff --check: passed
pytest: 323 passed
ruff check: passed
ruff format --check: passed
```

## DOGV-007 Retry Decision

DOGV-007 can be retried after this change is deployed.

Retry scope:

```text
candidate_ids=101,102,103,104,106,108,109,111,117,124
source=DOGV
types=pdf
expected_max_attempts=10
```

The retry must still create pre/post backups, verify DB state, verify candidate statuses, verify
artifact counts, and check MCP privacy.
