# Oposiciones Source Alerts Schema Proposal

This document proposes a future `source_alerts` / `opposition_alerts` schema for alert-grade monitoring of public employment and oposiciones notices.

This is a design document only. It does not modify the database schema, add migrations, implement code, run backfills, touch the VPS, create candidates, download artifacts, or write downstream.

## Purpose

`source_alerts` is a proposed model for fast monitoring of official notices that may matter to an oposiciones product.

It is not evidence-grade.

Its job is to capture:

```text
what was detected
where it was detected
why it matched
how confident the system is
whether it needs review or evidence escalation
```

It must stay separate from `source_candidates`.

```text
source_candidates = evidence/downstream pipeline
source_alerts / opposition_alerts = monitoring/notification pipeline
```

## Proposed Model

Proposed fields:

```yaml
id: uuid
source_code: string
source_name: string
territory_code: string
territory_name: string
publication_date: date
detected_at: timestamp
title: string
normalized_title: string
official_url: string
bulletin_identifier: string | null
document_identifier: string | null
issuing_body: string | null
section: string | null
alert_type: enum
confidence: enum
matched_terms: string[]
matched_rules: string[]
dedupe_key: string
related_group_key: string | null
review_status: enum
evidence_grade_status: enum
source_document_id: string | null
source_candidate_id: string | null
metadata_json: json
created_at: timestamp
updated_at: timestamp
```

## Field Semantics

`id`

Stable internal UUID for the alert record.

`source_code`

Canonical source code, such as `BOE`, `BOJA`, `DOGV`, `BOCYL`, `BOPV`, `BORM`, `BOA`, `DOGC`, or future `BOP_*` codes.

`source_name`

Human-readable source name.

`territory_code`

Territory code for filtering and routing. Prefer stable codes where available, such as `ES`, `ES-AN`, `ES-CL`, or provincial/local codes.

`territory_name`

Human-readable territory name.

`publication_date`

Official publication date of the source notice.

`detected_at`

Timestamp when the alert was detected by the monitoring pipeline.

`title`

Official title or best available official notice title.

`normalized_title`

Normalized title used for dedupe and matching. This should be lowercase, accent-normalized if needed, whitespace-normalized, and punctuation-normalized.

`official_url`

Required official URL. Alert-grade records without official URLs should not be stored except as rejected diagnostics.

`bulletin_identifier`

Issue or bulletin identifier when available.

`document_identifier`

Official document identifier when available.

`issuing_body`

Department, municipality, institution, or official issuing body.

`section`

Source section, category, or official index block if available.

`alert_type`

Classification for the kind of public employment notice.

`confidence`

First-pass confidence label. This is product confidence, not evidence-grade verification.

`matched_terms`

Terms that contributed to the match.

`matched_rules`

Deterministic rule identifiers that fired, such as `strong_proceso_selectivo`, `lista_definitiva`, or `noise_licitacion_excluded`.

`dedupe_key`

Primary key for same-source deduplication.

`related_group_key`

Optional cross-source grouping key. It groups related notices without deleting them.

`review_status`

Product/editorial review state for alert-grade.

`evidence_grade_status`

Whether this alert has requested or produced an evidence-grade item.

`source_document_id`

Optional reference to an existing `official_documents` record.

`source_candidate_id`

Optional reference to a `source_candidates` record only after explicit promotion. It remains null by default.

`metadata_json`

Source-specific extra metadata that should not become first-class fields yet.

`created_at` / `updated_at`

Internal timestamps.

## Enums

### alert_type

Allowed values:

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

Definitions:

```text
convocatoria = opening of a public employment process
bolsa = temporary job pool or substitute list
bases = rules for a process
lista_provisional = provisional admitted/excluded/result list
lista_definitiva = final admitted/excluded/result list
tribunal = selection board or committee notice
fecha_examen = exam date, venue, call, or schedule
plazo = application, claim, or correction deadline
subsanacion = correction period for documentation or defects
correccion = correction of an earlier notice
nombramiento = appointment related to a selection process
adjudicacion = award of posts, destinations, or placements
other = relevant but not classifiable yet
```

### confidence

Allowed values:

```text
high
medium
low
```

Suggested interpretation:

```text
high = strong employment-process signal and low noise
medium = likely relevant but needs product/editorial review
low = weak match, useful for review queues but not user-facing alerts
```

### review_status

Allowed values:

```text
new
reviewed
dismissed
duplicate
promoted_to_evidence_review
```

Definitions:

```text
new = detected and not reviewed
reviewed = accepted for alert-grade use
dismissed = not useful for the alert product
duplicate = same alert already exists
promoted_to_evidence_review = manually escalated to evidence-grade review
```

### evidence_grade_status

Allowed values:

```text
none
requested
created
rejected
```

Definitions:

```text
none = no evidence-grade action requested
requested = explicit request to fetch/review evidence
created = evidence-grade source_candidate or evidence record exists
rejected = evidence-grade conversion was rejected or blocked
```

## Required and Optional Fields

Minimum required fields:

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

Strongly recommended fields:

```text
source_name
territory_code
territory_name
normalized_title
matched_terms
matched_rules
created_at
updated_at
```

Optional fields:

```text
bulletin_identifier
document_identifier
issuing_body
section
related_group_key
source_document_id
source_candidate_id
metadata_json
```

Rules:

```text
official_url is required.
confidence is required.
source_candidate_id must be null unless explicit promotion has happened.
evidence_grade_status must default to none.
review_status must default to new.
```

## Dedupe Strategy

Same-source dedupe priorities:

```text
1. source_code + document_identifier + alert_type
2. source_code + official_url + alert_type
3. source_code + publication_date + normalized_title + issuing_body + alert_type
```

`dedupe_key` should be generated from the best available priority.

Suggested examples:

```text
BORM:842820:convocatoria
BOE:https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-00000:lista_definitiva
BOPVA:2026-05-20:bolsa-tecnico-administracion-general:ayuntamiento-x:bolsa
```

Cross-source grouping should use `related_group_key`, not dedupe deletion.

Purpose:

```text
Group related BOE, autonomous, provincial, or local notices.
Avoid sending duplicate product alerts.
Preserve each official publication as its own record.
```

Potential group key inputs:

```text
normalized role/process name
issuing_body
territory_code
alert_type
year
```

Do not collapse related records into one canonical record unless an editorial rule explicitly chooses a primary alert for notification.

## Relationship With Existing Tables

### official_documents

`source_alerts` may reference `official_documents` through `source_document_id`.

Use this when the notice already exists in the evidence-grade metadata store.

Rule:

```text
source_alerts can read from official_documents, but official_documents do not imply source_alerts.
```

### source_candidates

`source_alerts` must not create `source_candidates` automatically.

`source_candidate_id` remains null unless an explicit promotion workflow creates an evidence-grade candidate.

Rule:

```text
source_candidates remain evidence/downstream candidates.
source_alerts remain monitoring/product alerts.
```

### candidate_evidence_reviews

`candidate_evidence_reviews` apply after evidence-grade promotion, not before.

An alert-grade record can request evidence review, but it should not create a review record until a source candidate or evidence-grade record exists.

### document_files

`source_alerts` do not require artifacts.

If an alert is promoted, artifact download belongs to the evidence-grade workflow and must follow scoped source-specific rules.

## Promotion Workflow

Allowed promotion path:

```text
source_alert detected
-> reviewed
-> evidence requested
-> evidence-grade source_candidate created
-> candidate_evidence_reviews
-> downstream/export decision
```

Required controls:

```text
manual review or explicit operator action
official evidence fetch when needed
citation/integrity creation
no automatic downstream export
no automatic publication
```

State transitions:

```text
review_status=new -> reviewed
evidence_grade_status=none -> requested
source_candidate_id=null until created
review_status=promoted_to_evidence_review only after explicit promotion
evidence_grade_status=created only after an evidence-grade record exists
```

## Storage Location Options

### Option A: Inside official-sources DB

Pros:

```text
shared source registry
reuse official_documents
centralized source audit trail
consistent source codes and territory handling
easier promotion to evidence-grade
```

Cons:

```text
risk of mixing alert-grade and evidence-grade
larger DB scope
more migrations
more operational care on VPS
harder to iterate product-specific alert rules
```

### Option B: Inside oposiciones2.0 DB

Pros:

```text
product-specific
faster iteration
clear user-facing ownership
less risk to evidence-grade source pipeline
alerts can match product UX directly
```

Cons:

```text
duplicated source metadata
possible drift from official-sources registry
harder evidence-grade promotion
needs import/export contract
```

### Option C: Dual Model

Shape:

```text
official-sources produces alert-grade JSON or dry-run output
oposiciones2.0 stores product alerts
explicit promotion requests point back to official-sources
```

Pros:

```text
keeps evidence pipeline clean
allows product iteration
retains official source provenance
supports later centralization if needed
```

Cons:

```text
requires a stable export contract
requires synchronization rules
requires careful duplicate handling across systems
```

Recommendation:

```text
Design in official-sources.
Prototype storage closer to oposiciones2.0 first.
Only centralize after dry-run validation.
Prefer the dual model for the first prototype.
```

## Indexing Proposal

If implemented in a relational store, suggested indexes:

```text
source_code + publication_date
alert_type + publication_date
dedupe_key unique or near-unique
related_group_key
review_status
territory_code
confidence
evidence_grade_status
source_document_id
source_candidate_id
```

Uniqueness:

```text
dedupe_key should be unique within the chosen storage scope if confidence in the key is high.
If source-specific dedupe is not stable enough, use near-unique dedupe with duplicate review_status.
```

## Privacy, Legal and Safety Notes

Alert-grade is not verified evidence.

Rules:

```text
no automatic publication
no legal claims beyond official notice metadata
official_url required
confidence label required
weak matches should not be user-facing by default
all user-facing text must distinguish alerts from verified evidence
```

Safety notes:

```text
Do not imply that an alert is a confirmed eligibility result.
Do not imply that a user qualifies for a process.
Do not publish private personal data extracted from lists without a specific policy.
Do not bypass anti-bot protections to enrich alert-grade records.
```

## Migration Deferral

No DB migration should be created from this document directly.

Required before implementation:

```text
review schema with official-sources evidence boundary in mind
decide storage location
test dry-run output from existing metadata
define product import/export contract if using dual model
validate dedupe quality
define privacy policy for public-employment lists
```

Implementation must be a separate task.

## Next Tasks

Recommended next tasks:

```text
TASK-OPOSITIONS-ALERT-GRADE-003 - Prototype alert-grade dry-run from existing metadata
TASK-OPOSITIONS-CLASSIFIER-001 - Deterministic alert type classifier design
TASK-OPOSITIONS-SOURCES-001 - Rank sources for oposiciones monitoring
TASK-BOP-PROVINCIAL-001 - Provincial bulletin platform family audit
```

Recommended immediate next task:

```text
TASK-OPOSITIONS-ALERT-GRADE-003 - Prototype alert-grade dry-run from existing metadata
```

Constraint:

```text
dry-run only
no DB migration
no source_candidates
no artifacts
no downstream
no VPS write operation
```
