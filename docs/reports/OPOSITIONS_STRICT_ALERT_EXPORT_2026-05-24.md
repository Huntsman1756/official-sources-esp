# Oposiciones strict alert export

Date: 2026-05-24

Task: `TASK-OPOSITIONS-ALERT-GRADE-005`

## Summary

A controlled strict alert-grade sample was exported for future `oposiciones2.0` manual review.

This was export-only:

- no DB rows inserted, updated, or deleted;
- no `source_alerts` created;
- no `source_candidates` created;
- no artifacts downloaded;
- no downstream repository touched;
- no publication.

The export files were created outside Git on the VPS.

## Deployed commit

VPS deployed commit:

```text
0878b96 docs: add oposiciones alert scope dry-run report
```

The VPS was fast-forwarded before export:

```text
6501618 -> 0878b96
```

DB validation before and after:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

## Export directory

Export directory outside Git:

```text
/opt/official-sources/data/downstream_exports/2026-05-24/oposiciones-alert-grade/
```

Files generated:

```text
strict_alerts.sample.jsonl
strict_alerts.sample.json
summary.json
```

File sizes:

```text
strict_alerts.sample.jsonl: 390K
strict_alerts.sample.json: 427K
summary.json: 1.7K
```

These files were not committed.

## Export method

The current CLI does not implement `--scope strict`, so the export used read-only dry-run output and filtered locally on the VPS.

Per-source read-only dry-runs:

```bash
official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  dry-run-opposition-alerts \
  --source "$SOURCE" \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --limit 2000 \
  --format json
```

Sources:

```text
BORM
BOJA
BOCYL
DOGV
```

Then a local script selected only:

```text
alert_scope=strict
max_alerts=200
per_source_cap=50
```

## Export result

Available strict alerts by source:

| Source | Strict available |
| --- | ---: |
| BORM | 90 |
| BOJA | 137 |
| BOCYL | 102 |
| DOGV | 128 |

Exported sample:

| Source | Exported |
| --- | ---: |
| BORM | 50 |
| BOJA | 50 |
| BOCYL | 50 |
| DOGV | 50 |

Total:

```text
total_exported=200
```

Alert types:

| Type | Count |
| --- | ---: |
| convocatoria | 118 |
| lista_provisional | 27 |
| bolsa | 21 |
| tribunal | 12 |
| lista_definitiva | 10 |
| correccion | 9 |
| fecha_examen | 2 |
| bases | 1 |

Confidence distribution:

| Confidence | Count |
| --- | ---: |
| high | 177 |
| medium | 23 |

Dedupe:

```text
dedupe_group_count=0
```

## Required fields

Every exported alert includes:

```text
source_code
source_name
territory_code
territory_name
publication_date
title
official_url
bulletin_identifier
document_identifier
issuing_body
alert_type
alert_scope
confidence
matched_terms
matched_rules
dedupe_key
related_group_key
review_status
evidence_grade_status
```

Expected defaults verified:

```text
review_status=new
evidence_grade_status=none
alert_scope=strict
```

## Validation

Export validation passed:

- JSONL parses line by line;
- JSON parses;
- `summary.json` parses;
- every alert has `official_url`;
- every alert has `alert_scope=strict`;
- required fields are present;
- count is `200`, within the cap;
- no local filesystem paths detected;
- no obvious secret markers detected;
- no raw PDF/XML/HTML text included.

The first validation attempt used an overly broad secret check for the substring `token`, which matched normal Spanish text. The validation was corrected to check secret-like markers such as `access_token=`, `api_key=`, `password=`, and filesystem paths.

## Safety checks

Before export:

```text
source_candidates=163
artifact_download_attempts=518
artifact_size=30M
```

After export:

```text
source_candidates=163
artifact_download_attempts=518
artifact_size=30M
```

Verification:

```text
source_candidates unchanged: yes
artifact_download_attempts unchanged: yes
artifact size unchanged: yes
artifacts downloaded: no
DB writes: no
downstream writes: no
```

MCP privacy check:

```text
ss scan for official|mcp|python|uvicorn|fastmcp returned no matching public listener output
```

## Suitability for oposiciones2.0 review

The export is suitable for manual review in `oposiciones2.0` because:

- it is strict-only;
- it is capped at 200 records;
- it is balanced across four sources;
- it includes official URLs and dedupe keys;
- it carries `review_status=new` and `evidence_grade_status=none`;
- it does not imply evidence-grade verification;
- it does not require importing into any DB.

It is not suitable for automatic publication or user-facing alerts yet.

## Known limitations

- The CLI does not yet support `--scope strict`; filtering was done with a local VPS script.
- The export is a sample, not full coverage.
- Some strict records may still need type refinement, especially generic `convocatoria`.
- No manual precision score exists yet.
- No `oposiciones2.0` import path was touched or tested.

## Next recommended task

```text
TASK-OPOSICIONES2-REVIEW-001 — Manual review of exported strict alerts
```

Goal:

```text
measure true precision of the 200-record strict sample before designing any import, storage, or source_alerts table
```
