# BOE human review decisions applied - 2026-05-17

## Scope

This report records the controlled application of human review decisions to the operational
`candidate_evidence_reviews` model and the on-demand PDF download for the selected candidates.

This task did not approve candidates, publish anything, write to downstream projects, run BOE
range ingestion, run candidate discovery, expose MCP, or expose SQLite.

No raw legal text is included.

## Deployment State

Initial VPS state before code update:

```text
deployed_commit=04e1d02
schema_current_version=7
schema_latest_version=7
pending_migrations=0
journal_mode=wal
synchronous=normal
db_validation=valid
source_candidate_review_status=human_review_required:25
```

Code deployed for this task:

```text
deployed_commit=f05e357
schema_current_version=8
schema_latest_version=8
applied_migrations=8
db_validation=valid
```

Migration `0008_candidate_manual_review_fields` adds operational manual review metadata to
`candidate_evidence_reviews`:

- `manual_decision`
- `manual_notes`
- `needs_pdf`
- `downstream_project_fit`

## Decisions Applied

All updates were applied through `official-sources mark-candidate-evidence`.

```text
reviewer=Dani
reviewed_at=2026-05-17
manual_decision=accept_for_downstream_pilot:4,needs_more_evidence:4,out_of_scope:2
evidence_status=evidence_reviewed:likely_relevant:4,needs_more_evidence:unclear:4,out_of_scope:out_of_scope:2
```

Accepted for downstream pilot:

```text
1,11,17,18
```

Needs more evidence:

```text
3,20,21,23
```

Out of scope:

```text
10,14
```

These are operational review decisions only. `source_candidates.review_status` was not changed.

## PDF Download

PDF was downloaded only for candidates with `needs_pdf=yes`:

```text
pdf_candidate_ids=3,20,21,23
```

Download command was scoped by candidate IDs and `--types pdf`.

Download result:

```text
selected_documents=4
artifact_types=pdf
downloaded=4
skipped=0
changed=0
failed=0
retries=0
throttle_events=3
http_status_summary=pdf:200:4
```

No PDFs were downloaded for candidates `1,10,11,14,17,18`.

## Evidence Availability

Post-run candidate evidence status:

| Candidate ID | Manual decision | Evidence label | Evidence status | XML | HTML | PDF | Integrity warning | Selected for PDF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | false |
| 3 | `needs_more_evidence` | `unclear` | `needs_more_evidence` | true | true | true | false | true |
| 10 | `out_of_scope` | `out_of_scope` | `out_of_scope` | true | true | false | false | false |
| 11 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | false |
| 14 | `out_of_scope` | `out_of_scope` | `out_of_scope` | true | true | false | false | false |
| 17 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | false |
| 18 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | false |
| 20 | `needs_more_evidence` | `unclear` | `needs_more_evidence` | true | true | true | false | true |
| 21 | `needs_more_evidence` | `unclear` | `needs_more_evidence` | true | true | true | false | true |
| 23 | `needs_more_evidence` | `unclear` | `needs_more_evidence` | true | true | true | false | true |

PDF availability after the run:

```text
pdf_available_candidate_ids=3,20,21,23
total_pdf_files=118
```

## Candidate Review Status

`source_candidates.review_status` remained unchanged:

```text
human_review_required | 25
```

## Database Validation

Post-run validation:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## Artifact Size

Artifact directory size:

```text
before_pdf_download=23M
after_pdf_download=23M
```

The size display remained at `23M`; four PDF artifacts were added through audited scoped
downloads.

## Backups

Verified backup before applying decisions:

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_human_review_apply_20260519_073859.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=10055680
status=success
```

Verified backup after DB validation:

```text
backup_path=/opt/official-sources/data/backups/official_sources_after_human_review_apply_20260519_074038.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=10055680
status=success
```

## MCP Privacy

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
result=no_matching_public_listener
```

No public MCP listener or SQLite exposure was found.

## Known Limitations

- Manual decisions are operational evidence metadata, not approval or publication.
- `official-sources` still has no downstream integration.
- The four PDFs are downloaded and hashed, but PDF signature validation is not implemented.
- Candidate IDs `3,20,21,23` still need human evidence review after PDF inspection.
- Candidate IDs `10,14` are out of scope for the pilot but remain stored as evidence records.

## Next Recommended Task

TASK-004G: inspect the downloaded PDFs for candidates `3,20,21,23`, update their operational
manual decisions, and keep downstream approval/publication outside `official-sources`.
