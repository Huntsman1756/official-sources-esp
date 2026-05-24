# Oposiciones Source Alerts Schema Report

Date: 2026-05-24

Task: `TASK-OPOSITIONS-ALERT-GRADE-002`

Scope: define a proposed `source_alerts` / `opposition_alerts` schema for alert-grade monitoring.

This was a documentation/design-only task. No DB schema was modified, no migration was created, no code was implemented, no VPS operation was run, no candidates were created, no artifacts were downloaded, and no downstream project was touched.

## Files Created

```text
docs/OPOSITIONS_SOURCE_ALERTS_SCHEMA.md
docs/reports/OPOSITIONS_SOURCE_ALERTS_SCHEMA_2026-05-24.md
```

## Proposed Schema Summary

The proposed model captures fast monitoring alerts for oposiciones/public employment notices.

Core fields:

```text
id
source_code
source_name
territory_code
territory_name
publication_date
detected_at
title
normalized_title
official_url
bulletin_identifier
document_identifier
issuing_body
section
alert_type
confidence
matched_terms
matched_rules
dedupe_key
related_group_key
review_status
evidence_grade_status
source_document_id
source_candidate_id
metadata_json
created_at
updated_at
```

## Required Fields

Minimum required:

```text
source_code
publication_date
title
official_url
alert_type
confidence
dedupe_key
detected_at
review_status
evidence_grade_status
```

Important defaults:

```text
review_status=new
evidence_grade_status=none
source_candidate_id=null
```

## Enum Decisions

`alert_type`:

```text
convocatoria
bolsa
bases
lista_provisional
lista_definitiva
tribunal
fecha_examen
plazo
subsanacion
correccion
nombramiento
adjudicacion
other
```

`confidence`:

```text
high
medium
low
```

`review_status`:

```text
new
reviewed
dismissed
duplicate
promoted_to_evidence_review
```

`evidence_grade_status`:

```text
none
requested
created
rejected
```

## Dedupe Strategy

Same-source dedupe priority:

```text
1. source_code + document_identifier + alert_type
2. source_code + official_url + alert_type
3. source_code + publication_date + normalized_title + issuing_body + alert_type
```

Cross-source related notices should use:

```text
related_group_key
```

Purpose:

```text
group BOE/autonomous/provincial/local repetitions
avoid duplicate user notifications
preserve each official publication as its own record
```

## Relationship With Existing Tables

`official_documents`:

```text
source_alerts may reference official_documents through source_document_id.
```

`source_candidates`:

```text
source_alerts must not create source_candidates automatically.
source_candidate_id remains null until explicit promotion.
```

`candidate_evidence_reviews`:

```text
only after evidence-grade promotion.
```

`document_files`:

```text
not required for alert-grade.
artifact download belongs to evidence-grade promotion.
```

## Recommended Storage Architecture

Recommendation:

```text
Design in official-sources.
Prototype storage closer to oposiciones2.0 first.
Only centralize after dry-run validation.
Prefer a dual model for the first prototype.
```

Dual model:

```text
official-sources produces alert-grade JSON or dry-run output
oposiciones2.0 stores product alerts
explicit promotion requests point back to official-sources
```

Reason:

```text
This protects source_candidates and the evidence-grade pipeline while allowing faster product iteration.
```

## Risks

Key risks:

```text
mixing alert-grade with evidence-grade
false positives
duplicate user alerts
fragile source identifiers
privacy issues in public employment lists
anti-bot pressure if trying to enrich alerts too aggressively
product claims that overstate evidence quality
```

Controls:

```text
official_url required
confidence required
source_candidate_id null by default
no automatic promotion
no automatic downstream/publication
dedupe_key plus related_group_key
explicit review_status and evidence_grade_status
```

## Migration Deferral

No migration was created.

The schema must be reviewed before implementation.

Pre-implementation requirements:

```text
dry-run on existing official_documents
classifier rule design
dedupe quality check
storage location decision
privacy policy for personal-data-heavy lists
export/import contract if using dual model
```

## Next Recommended Task

```text
TASK-OPOSITIONS-ALERT-GRADE-003 - Prototype alert-grade dry-run from existing metadata
```

Scope should remain:

```text
dry-run only
no DB migration
no candidates
no artifacts
no downstream
no VPS write operation
```
