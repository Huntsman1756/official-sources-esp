# BOE 6-Month Downstream Evidence Export - 2026-05-20

## Scope

This report documents downstream-ready JSON evidence export for the accepted 6-month BOE candidates.

This task prepared export files only. It did not import into EduAyudas or la-ayuda, did not create downstream candidates, did not create aid records, did not approve candidates, and did not publish anything.

## Deployment State

- Deployed commit: `07346df`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- DB validation: valid

## Export Groups

Exports were created in separate destination groups.

### EduAyudas

Candidate IDs:

```text
36, 40, 49, 60
```

Files:

```text
eduayudas/candidate_36_BOE-B-2026-14182.json
eduayudas/candidate_40_BOE-B-2026-14244.json
eduayudas/candidate_49_BOE-B-2026-13482.json
eduayudas/candidate_60_BOE-B-2026-13097.json
```

### la-ayuda

Candidate ID:

```text
69
```

File:

```text
la-ayuda/candidate_69_BOE-B-2026-12558.json
```

## Export Directory

Export base directory:

```text
/opt/official-sources/data/downstream_exports/2026-05-20
```

Directory size:

```text
32K
```

These JSON files are operational exports under `data/` and were not committed to Git.

## Export Contract

Each JSON file includes:

- `source_code`
- `resource_type`
- `official_identifier`
- `title`
- `publication_date`
- `version_date`
- `official_url`
- `citation`
- `integrity`
- `artifacts`
- `official_sources_candidate`

Each JSON file excludes:

- full legal text
- raw XML
- raw HTML
- local filesystem paths
- secrets
- downstream write instructions

## JSON Validation

Validation result:

```text
passed
```

Checks performed:

| Check | Result |
|---|---|
| 4 EduAyudas files created | passed |
| 1 la-ayuda file created | passed |
| All JSON files parse | passed |
| Required top-level fields exist | passed |
| Required integrity fields exist | passed |
| Required artifact availability fields exist | passed |
| Required official-sources candidate fields exist | passed |
| No local absolute paths in payloads | passed |
| No raw XML/HTML in payloads | passed |
| `manual_decision=accept_for_downstream_pilot` | passed |
| `hashes_match=true` | passed |
| `has_integrity_warning=false` | passed |

## Source Evidence Verified

Accepted evidence routing in `candidate_evidence_reviews`:

| Downstream fit | Count |
|---|---:|
| `EduAyudas` | 4 |
| `la-ayuda` | 1 |

All exported candidates had:

```text
manual_decision=accept_for_downstream_pilot
evidence_label=likely_relevant
evidence_review_status=evidence_reviewed
xml_available=true
html_available=true
pdf_available=false
has_integrity_warning=false
hashes_match=true
```

## DB Mutation Result

The export task did not mutate the SQLite database.

Post-export checks:

| Item | Value |
|---|---:|
| `source_candidates.human_review_required` | 75 |
| `artifact_download_attempts` | 392 |
| `document_files.xml` | 137 |
| `document_files.html` | 137 |
| `document_files.pdf` | 118 |
| Artifact directory size | 24M |

DB validation:

```text
valid
```

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

## Known Limitations

- Export files were generated on the VPS under `data/` and were intentionally not committed.
- No downstream import was performed.
- Candidate `69` is routed to la-ayuda only; la-ayuda still needs an evidence/candidate staging foundation before import.
- EduAyudas import should still use its staged preview/write-evidence flow, not direct aid creation.
- Export files do not contain full legal text by design.

## Next Recommended Task

Recommended next task for EduAyudas:

```text
TASK-005I - Import 4 EduAyudas evidence files into EduAyudas official_source_evidence
```

Recommended next task for la-ayuda:

```text
TASK-LAAYUDA-FOUNDATION - Add evidence/candidate staging model
```

Do not import candidate `69` into la-ayuda until that foundation exists.
