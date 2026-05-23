# BOCYL Selected Candidate Evidence Download - 2026-05-21

## Scope

This report records scoped BOCYL XML/HTML evidence downloads for the 10
candidates selected in `BOCYL-006`.

Rules applied:

- evidence was downloaded only for selected candidate IDs;
- no date-range artifact download was run;
- no PDFs were downloaded;
- no candidates were created;
- no `source_candidates.review_status` values were changed;
- no EduAyudas work was performed;
- no `la-ayuda` work was performed;
- no downstream writes were performed;
- no MCP surface was exposed;
- no approvals or publications were performed.

## Context

Selected candidate IDs from triage:

```text
126,128,129,131,134,138,141,142,145,146
```

Previous report:

```text
docs/reports/BOCYL_30_DAY_CANDIDATE_TRIAGE_2026-05-21.md
```

Initial state:

```text
source_candidates=146
BOCYL candidates=21
selected candidates review_status=human_review_required
artifact_download_attempts=442
artifacts=30M
DB valid
```

## Code Changes

BOCYL required scoped artifact downloader support before the VPS operation.

Implemented:

```text
download-source-artifacts --source BOCYL --candidate-ids ... --types xml,html
```

Safety behavior:

- BOCYL is accepted by `download-source-artifacts`;
- BOCYL requires explicit `--candidate-ids`;
- BOCYL rejects `--document-ids`;
- BOCYL rejects date-level downloads;
- selected documents must belong to source `BOCYL`;
- supported types are `xml`, `html`, and explicit `pdf`;
- URLs must use official BOCYL hosts;
- default production BOCYL downloads follow official redirects.

Code commits:

```text
1cf4770 feat: add scoped BOCYL artifact download
e72f623 fix: follow BOCYL artifact redirects
```

Local validation:

```text
rtk python -m pytest -q = 351 passed
rtk python -m ruff check . = passed
rtk python -m ruff format --check . = passed
git diff --check = passed
```

## Candidate URL Availability

All 10 selected candidates had stored official `html`, `xml`, and `pdf` URLs.

| candidate_id | official_identifier | html | xml | pdf |
| ---: | --- | --- | --- | --- |
| 126 | `BOCYL:BOCYL-D-15052026-91-8` | yes | yes | yes |
| 128 | `BOCYL:BOCYL-D-14052026-90-7` | yes | yes | yes |
| 129 | `BOCYL:BOCYL-D-13052026-89-10` | yes | yes | yes |
| 131 | `BOCYL:BOCYL-D-12052026-88-14` | yes | yes | yes |
| 134 | `BOCYL:BOCYL-D-11052026-87-8` | yes | yes | yes |
| 138 | `BOCYL:BOCYL-D-06052026-84-9` | yes | yes | yes |
| 141 | `BOCYL:BOCYL-D-04052026-82-17` | yes | yes | yes |
| 142 | `BOCYL:BOCYL-D-04052026-82-39` | yes | yes | yes |
| 145 | `BOCYL:BOCYL-D-29042026-80-7` | yes | yes | yes |
| 146 | `BOCYL:BOCYL-D-21042026-75-8` | yes | yes | yes |

Evidence type chosen:

```text
xml,html
```

PDF was not used because XML/HTML were available.

## Backups

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_bocyl_evidence_download_20260523_122133.sqlite
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_bocyl_evidence_download_20260523_122519.sqlite
```

## Commands

Primary command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  download-source-artifacts \
  --source BOCYL \
  --candidate-ids 126,128,129,131,134,138,141,142,145,146 \
  --types xml,html
```

## Download Result

Attempt 1:

```text
downloaded=0
failed=20
missing_artifact_url=0
failure_reason=BOCYL HTTP URLs returned 302 redirects
```

No document files were created in attempt 1. The 20 failed attempts were recorded
in `artifact_download_attempts`.

After adding BOCYL redirect handling, the same scoped command was rerun.

Attempt 2:

```text
selected_documents=10
artifact_types=xml,html
downloaded=20
skipped=0
changed=0
failed=0
missing_artifact_url=0
```

## Count Verification

| metric | before | after | delta |
| --- | ---: | ---: | ---: |
| source_candidates total | 146 | 146 | 0 |
| BOCYL candidates | 21 | 21 | 0 |
| artifact_download_attempts | 442 | 482 | +40 |
| document_files total | 27100 | 27120 | +20 |
| BOCYL document_files | 773 | 793 | +20 |
| selected candidate document_files | 10 | 30 | +20 |
| selected XML/HTML files | 0 | 20 | +20 |

Selected file type distribution after download:

```text
html:10
raw_api_response:10
xml:10
```

BOCYL artifact attempt distribution after download:

```text
failed:20
success:20
```

The 20 failures correspond to the controlled first attempt before redirect
handling. The final scoped download completed successfully.

## Status Verification

Candidate status checks:

```text
review_status_distribution=human_review_required:146
selected_review_status_distribution=human_review_required:10
```

DB and privacy:

```text
db_validate_after=valid
mcp_privacy_check=no official/mcp/python/uvicorn/fastmcp listener found
artifact_dir_size_after=30M
```

No downstream writes were performed.

## Known Limitations

The downloaded artifacts have not been reviewed for substantive fit yet. They
only establish scoped official XML/HTML evidence availability for the selected
candidate records.

BOCYL still has 20 failed artifact attempts from the first controlled run. They
are expected audit trail entries for HTTP 302 behavior and should not be treated
as missing evidence for the final successful download.

PDF evidence remains deferred unless XML/HTML are insufficient during review.

## Next Recommended Task

```text
TASK-AUTO-BOCYL-008 - BOCYL selected candidate evidence review
```

Recommended outcomes for review:

```text
accept_for_downstream_pilot
needs_more_evidence
out_of_scope
false_positive
defer
```

Keep review metadata local to `official-sources`; do not write downstream in the
same task.
