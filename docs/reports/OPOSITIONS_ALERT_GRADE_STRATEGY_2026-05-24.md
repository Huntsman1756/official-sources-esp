# Oposiciones Alert-Grade Strategy Report

Date: 2026-05-24

Task: `TASK-OPOSITIONS-ALERT-GRADE-001`

Scope: define an alert-grade strategy and data contract for oposiciones/public employment monitoring.

This was a documentation-only task. No code was implemented, no DB schema was changed, no VPS operation was run, no candidates were created, no artifacts were downloaded, and no downstream project was touched.

## Summary

The decision is:

```text
Keep alert-grade separate from evidence-grade.
Do not store alert-grade records as source_candidates by default.
Do not allow automatic promotion from alert-grade to downstream/publication/evidence-grade.
```

The strategy is documented in:

```text
docs/OPOSITIONS_ALERT_GRADE_STRATEGY.md
```

## Evidence-Grade vs Alert-Grade

Evidence-grade remains the current `official-sources` standard:

```text
official source metadata
source_snapshot_hash
content hash
citation
integrity status
artifact availability
manual review
candidate_evidence_reviews
downstream export only after review
```

Alert-grade is a separate fast-monitoring track:

```text
fast detection
metadata-first
official URL required
no artifact required by default
confidence score
deduplication
no downstream publication
```

Alert-grade can support an Opositar-style product more quickly, but it is not evidence-grade.

## Proposed Data Contract

Minimum proposed alert-grade contract:

```yaml
source_code: BOE | BOJA | DOGV | BOCYL | BOPV | BORM | BOA | DOGC | BOP | ...
source_name: string
territory_code: string
territory_name: string
publication_date: YYYY-MM-DD
title: string
official_url: string
bulletin_identifier: string | null
document_identifier: string | null
issuing_body: string | null
alert_type: convocatoria | bolsa | bases | lista_provisional | lista_definitiva | tribunal | fecha_examen | plazo | subsanacion | correccion | nombramiento | adjudicacion | other
confidence: high | medium | low
matched_terms: string[]
dedupe_key: string
detected_at: ISO timestamp
review_status: new | reviewed | dismissed | promoted_to_evidence_review
evidence_grade_status: none | requested | created | rejected
```

Required minimum fields:

```text
source_code
publication_date
title
official_url
alert_type
confidence
dedupe_key
detected_at
```

## Relationship With source_candidates

`source_candidates` remain evidence/downstream candidates.

Alert-grade records must not be inserted into `source_candidates` by default.

Future models can be considered:

```text
source_alerts
opposition_alerts
monitored_items
```

But this task intentionally did not implement any of them.

## Recommended Architecture

Recommendation:

```text
Design the alert-grade contract in official-sources.
Keep implementation separate until schema and operational boundaries are explicit.
Prototype alert-grade behavior closer to oposiciones2.0 or in a dry-run-only official-sources track.
```

Rationale:

```text
official-sources already has the source registry and normalization discipline.
oposiciones2.0 has product-specific alerting needs.
Mixing alert-grade with source_candidates would risk weakening the evidence-grade pipeline.
```

## Promotion Path

Alert-grade promotion must be explicit:

```text
alert detected
-> reviewed
-> evidence requested
-> official artifact/metadata fetched
-> citation/integrity created
-> source_candidate or evidence record created
-> human review
-> downstream/publication decision
```

No automatic promotion is allowed.

## Risks

Documented risks:

```text
false positives
duplicate alerts
fragile provincial sources
CAPTCHA/anti-bot
PDF-only sources
over-alerting users
legal/publication risk if treated as verified evidence
mixing alert-grade with evidence-grade
```

Controls:

```text
official_url required
confidence required
dedupe_key required
weak terms not enough alone
no automatic source_candidate creation
no automatic downstream/publication
explicit promotion path
```

## Next Recommended Tasks

```text
TASK-OPOSITIONS-ALERT-GRADE-002 - Define source_alerts schema proposal
TASK-OPOSITIONS-SOURCES-001 - Rank sources for oposiciones monitoring
TASK-OPOSITIONS-CLASSIFIER-001 - Deterministic alert type classifier design
TASK-BOP-PROVINCIAL-001 - Provincial bulletin platform family audit
TASK-OPOSITIONS-ALERT-GRADE-003 - Prototype alert-grade dry-run from existing metadata
```

Recommended immediate next step:

```text
TASK-OPOSITIONS-ALERT-GRADE-002 - Define source_alerts schema proposal
```

Still docs/design only. No DB migration until the boundary is reviewed.
