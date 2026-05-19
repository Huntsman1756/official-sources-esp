# BOE PDF review decisions applied - 2026-05-17

## Scope

This report records the controlled application of PDF review recommendations to the operational
`candidate_evidence_reviews` model.

This task did not change `source_candidates.review_status`, approve candidates, publish anything,
write to downstream projects, download more artifacts, call BOE, run backfills, run candidate
discovery, expose MCP, or expose SQLite.

No raw legal text is included.

## VPS State

```text
deployed_commit=4e960dc
schema_current_version=8
schema_latest_version=8
pending_migrations=0
journal_mode=wal
synchronous=normal
db_validation_before=valid
```

Pre-run source candidate status:

```text
human_review_required | 25
```

## Decisions Applied

All updates were applied through `official-sources mark-candidate-evidence`.

Decision distribution after applying PDF review recommendations:

```text
accept_for_downstream_pilot=6
defer=1
out_of_scope=3
```

Accepted for downstream pilot:

```text
1,11,17,18,20,21
```

Deferred:

```text
3
```

Out of scope:

```text
10,14,23
```

These are operational evidence review decisions only. They are not approval or publication.

## Evidence Availability Summary

| Candidate ID | Manual decision | Evidence label | Evidence status | XML | HTML | PDF | Integrity warning | Downstream fit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | `EduAyudas` |
| 3 | `defer` | `unclear` | `evidence_reviewed` | true | true | true | false | `unclear` |
| 10 | `out_of_scope` | `out_of_scope` | `out_of_scope` | true | true | false | false | `neither` |
| 11 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | `both` |
| 14 | `out_of_scope` | `out_of_scope` | `out_of_scope` | true | true | false | false | `neither` |
| 17 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | `EduAyudas` |
| 18 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | false | false | `both` |
| 20 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | true | false | `EduAyudas` |
| 21 | `accept_for_downstream_pilot` | `likely_relevant` | `evidence_reviewed` | true | true | true | false | `EduAyudas` |
| 23 | `out_of_scope` | `out_of_scope` | `out_of_scope` | true | true | true | false | `neither` |

PDF availability:

```text
pdf_available_candidate_ids=3,20,21,23
```

No new artifacts were downloaded during this task.

## Source Candidate Review Status

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

Artifact directory size before and after applying decisions:

```text
before=23M
after=23M
```

No unexpected artifact growth was observed.

## Backups

Verified backup before applying PDF review decisions:

```text
backup_path=/opt/official-sources/data/backups/official_sources_before_pdf_review_apply_20260519_074921.sqlite
verification=quick_check
source_check=ok
backup_check=ok
size_bytes=10055680
status=success
```

Verified backup after DB validation:

```text
backup_path=/opt/official-sources/data/backups/official_sources_after_pdf_review_apply_20260519_075006.sqlite
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

- These are operational evidence review decisions, not approval or publication.
- `official-sources` still does not write to downstream projects.
- PDF signature validation is not implemented; PDFs are cached and hashed only.
- Candidate `3` is deferred for product-scope reasons and may need a future youth-opportunity
  review path outside the immediate pilot.

## Next Recommended Task

TASK-004B-PRECHECK: review la-ayuda / EduAyudas downstream readiness before integration. Confirm
the downstream project has candidate/evidence storage, a `pending_review` workflow, citation
storage, integrity hash storage, and an admin/review mechanism before connecting it to
`official-sources`.
