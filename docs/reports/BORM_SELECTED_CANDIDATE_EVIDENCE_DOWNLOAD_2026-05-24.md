# BORM Selected Candidate Evidence Download

Date: 2026-05-24

Task: `TASK-AUTO-BORM-008B`

Scope: scoped BORM PDF evidence download for selected candidate IDs only.

## Deployed Commit

```text
843a3d0 feat: add scoped BORM artifact download
```

The deployed code includes scoped BORM PDF downloader support, strict official-host validation, redirect handling, and explicit PDF request headers:

```text
Accept: application/pdf
User-Agent: official-sources/1.0
```

## Selected Candidates

```text
151,152,153,154,155,156,157,158,159,161,162,163
```

Selected candidate count:

```text
12
```

All selected candidates remained:

```text
review_status=human_review_required
```

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-source-artifacts \
  --source BORM \
  --candidate-ids 151,152,153,154,155,156,157,158,159,161,162,163 \
  --types pdf
```

## Download Result

The BORM downloader support was added successfully, but the operational VPS download did not complete successfully.

Attempt history:

```text
initial_attempt_commit=9f373a3
selected_documents=12
downloaded=1
failed=11
failure=http_302_redirect
artifact_download_attempts=482 -> 494
BORM_pdf_document_files=0 -> 1
```

After redirect handling was added:

```text
retry_commit=ee93a9e
selected_documents=12
downloaded=0
failed=12
failure=final_url_not_official_borm_host
```

After explicit PDF/user-agent headers were added:

```text
final_retry_commit=843a3d0
selected_documents=12
downloaded=0
failed=12
failure=final_url_not_official_borm_host
```

Root operational blocker:

```text
BORM redirects the VPS requests to validate.perfdrive.com before serving the PDF.
The downloader correctly rejects the final non-official host.
```

The implementation did not store the validation HTML as evidence.

## Counters

Artifact attempts:

```text
before=482
after=518
```

BORM PDF document files:

```text
before=0
after=1
selected_candidate_pdf_files=1
```

Artifact size:

```text
before_bytes=28857411
after_bytes=29154791
before_human=30M
after_human=30M
```

BORM PDF attempt status distribution:

```text
success http_status=200: 1
failed http_status=302: 11
failed http_status=null: 24
```

`http_status=null` corresponds to failures raised after the final redirect URL failed official BORM host validation.

Source candidates:

```text
source_candidates_total=163
selected_candidates=12
selected_review_status=human_review_required:12
```

No source candidates were created or updated by this task.

## DB Validation

```text
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate

database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## Backups

Pre-run backup:

```text
/opt/official-sources/data/backups/official_sources_before_borm_selected_evidence_download_20260524_112807.sqlite
```

Post-run backup:

```text
/opt/official-sources/data/backups/official_sources_after_borm_selected_evidence_download_20260524_113844.sqlite
```

## MCP Privacy

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching listener
```

## Known Limitations

- BORM PDF download support exists and is scoped, but current VPS requests are blocked by BORM's browser validation layer.
- Only 1 of 12 selected PDFs is stored; evidence review for the selected BORM batch should not start yet.
- XML is not available in selected candidate metadata.
- HTML evidence remains unimplemented because the stored HTML URL is an official SPA route and has not been proven to return complete legal text.

## Next Recommended Task

```text
TASK-AUTO-BORM-008C — Resolve BORM VPS PDF access blocker
```

Recommended scope:

```text
diagnose official BORM PDF access from VPS
do not bypass official host validation
do not store browser-validation HTML
identify whether BORM offers a stable alternative official artifact endpoint
retry only the same selected candidate IDs if a safe official route exists
```

Do not proceed to `TASK-AUTO-BORM-009` until the selected evidence set is complete or the missing evidence is explicitly re-triaged.
