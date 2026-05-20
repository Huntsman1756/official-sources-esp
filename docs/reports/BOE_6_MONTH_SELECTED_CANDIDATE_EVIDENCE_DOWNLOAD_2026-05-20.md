# BOE 6-Month Selected Candidate Evidence Download - 2026-05-20

## Scope

This report documents scoped XML/HTML evidence download for the selected 6-month BOE candidate batch.

Selected source candidate IDs:

```text
32, 36, 40, 42, 44, 49, 56, 57, 58, 60, 68, 69, 72
```

This task downloaded only XML and HTML artifacts for those 13 `source_candidates`.

This task did not download PDF, did not download artifacts by full date range, did not run BOE summary backfills, did not run candidate discovery, did not create more candidates, did not approve candidates, did not publish anything, and did not write to downstream projects.

## Deployment State

- Deployed commit: `cee8413`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- Pre-run DB validation: valid

## Selected Candidates Verified

All selected candidates existed and had:

```text
review_status=human_review_required
```

| Candidate ID | Official identifier | Publication date | Matched keywords | Score |
|---:|---|---|---|---:|
| 32 | `BOE-B-2026-16238` | `2026-05-19` | `subvenciones`, `discapacidad` | 4 |
| 36 | `BOE-B-2026-14182` | `2026-05-05` | `subvenciones`, `convocatoria`, `convocatoria de subvenciones` | 6 |
| 40 | `BOE-B-2026-14244` | `2026-05-05` | `becas` | 2 |
| 42 | `BOE-B-2026-13661` | `2026-05-01` | `ayudas` | 2 |
| 44 | `BOE-B-2026-13592` | `2026-04-30` | `ayudas` | 2 |
| 49 | `BOE-B-2026-13482` | `2026-04-29` | `becas` | 2 |
| 56 | `BOE-B-2026-13408` | `2026-04-28` | `ayudas` | 2 |
| 57 | `BOE-B-2026-12992` | `2026-04-25` | `becas` | 2 |
| 58 | `BOE-B-2026-12993` | `2026-04-25` | `becas` | 2 |
| 60 | `BOE-B-2026-13097` | `2026-04-25` | `ayudas` | 2 |
| 68 | `BOE-B-2026-12557` | `2026-04-22` | `ayuda`, `subvenciones` | 4 |
| 69 | `BOE-B-2026-12558` | `2026-04-22` | `subvenciones` | 2 |
| 72 | `BOE-B-2026-12566` | `2026-04-22` | `subvenciones`, `convocatoria` | 3 |

## Pre-Run State

| Item | Count |
|---|---:|
| `source_candidates` | 75 |
| `source_candidates.human_review_required` | 75 |
| `artifact_download_attempts` | 366 |
| `document_files.html` | 124 |
| `document_files.xml` | 124 |
| `document_files.pdf` | 118 |
| `document_files.raw_api_response` | 21,627 |

Pre-run artifact directory size:

```text
23M
```

## Pre-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_before_6m_selected_xml_html_20260520_073614.sqlite
```

Result:

- Status: created successfully
- Size: 44M

## Command Executed

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-boe-artifacts \
  --candidate-ids 32,36,40,42,44,49,56,57,58,60,68,69,72 \
  --types xml,html
```

No date-level artifact download was run.

No PDF was requested.

## Download Result

| Metric | Value |
|---|---:|
| Selected candidates | 13 |
| Artifact types | `xml,html` |
| Expected maximum attempts | 26 |
| Actual new attempts | 26 |
| Downloaded | 26 |
| Skipped | 0 |
| Changed | 0 |
| Failed | 0 |
| Retries | 0 |
| Throttle events | 25 |

HTTP status summary:

```text
xml:200:13
html:200:13
```

Attempt summary:

| Type | HTTP status | Status | Count | Retries | Throttle events |
|---|---:|---|---:|---:|---:|
| `xml` | 200 | `success` | 13 | 0 | 12 |
| `html` | 200 | `success` | 13 | 0 | 13 |

## XML/HTML Availability

| Candidate ID | Official identifier | XML | HTML | PDF |
|---:|---|---:|---:|---:|
| 32 | `BOE-B-2026-16238` | 1 | 1 | 0 |
| 36 | `BOE-B-2026-14182` | 1 | 1 | 0 |
| 40 | `BOE-B-2026-14244` | 1 | 1 | 0 |
| 42 | `BOE-B-2026-13661` | 1 | 1 | 0 |
| 44 | `BOE-B-2026-13592` | 1 | 1 | 0 |
| 49 | `BOE-B-2026-13482` | 1 | 1 | 0 |
| 56 | `BOE-B-2026-13408` | 1 | 1 | 0 |
| 57 | `BOE-B-2026-12992` | 1 | 1 | 0 |
| 58 | `BOE-B-2026-12993` | 1 | 1 | 0 |
| 60 | `BOE-B-2026-13097` | 1 | 1 | 0 |
| 68 | `BOE-B-2026-12557` | 1 | 1 | 0 |
| 69 | `BOE-B-2026-12558` | 1 | 1 | 0 |
| 72 | `BOE-B-2026-12566` | 1 | 1 | 0 |

All selected candidates now have XML and HTML artifacts.

No selected candidate has a PDF artifact from this task.

## Post-Run State

| Item | Before | After |
|---|---:|---:|
| `artifact_download_attempts` | 366 | 392 |
| `document_files.html` | 124 | 137 |
| `document_files.xml` | 124 | 137 |
| `document_files.pdf` | 118 | 118 |
| Artifact directory size | 23M | 24M |
| `source_candidates` | 75 | 75 |
| `source_candidates.human_review_required` | 75 | 75 |

DB validation after download:

```text
valid
```

## Integrity Notes

- XML and HTML artifacts have stored SHA-256 values.
- XML and HTML artifacts have stored source snapshot hashes.
- `content_changed_at` is null for all selected XML/HTML artifacts.
- Signature status is `not_checked`, as expected for this artifact type workflow.
- No failed artifact downloads were recorded for this run.

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

## Post-Run Backup

Backup path:

```text
/opt/official-sources/data/backups/official_sources_after_6m_selected_xml_html_20260520_073759.sqlite
```

Result:

- Status: created successfully after DB validation
- Size: 44M

## Known Limitations

- This task downloaded evidence only; it did not review the XML/HTML contents.
- No PDF artifacts were downloaded.
- `source_candidates.review_status` intentionally remains `human_review_required`.
- Operational triage labels from `TASK-005D` remain report-only and were not written to the database.
- The previous 6-month summary backfill still has the known `2026-05-20` BOE summary `404` failure; this task did not retry or reinterpret that date.

## Next Recommended Task

Recommended next task:

```text
TASK-005F - 6-month selected candidate evidence review
```

Review the XML/HTML evidence for the 13 selected candidates and classify them operationally into:

```text
accept_for_downstream_pilot
needs_more_evidence
out_of_scope
false_positive
defer
```

PDF should remain on-demand and only be requested for candidates that still need more evidence after XML/HTML review.
