# Oposiciones Alert-Grade Strategy

This document defines a proposed `alert-grade` monitoring track for public employment and oposiciones notices.

It is a strategy and data-contract document only. It does not change the database schema, implement new commands, create candidates, run backfills, download artifacts, or change downstream behavior.

## Core Decision

```text
evidence-grade != alert-grade
```

The existing `official-sources` model remains evidence-grade. It is intentionally conservative and is the correct standard for formal evidence, human review, and downstream-safe exports.

An oposiciones product can use a faster alert-grade model, but alert-grade records must stay separate from `source_candidates` and must never be promoted automatically to downstream or publication use.

## Evidence-Grade

Evidence-grade records are suitable for formal source-backed workflows.

Characteristics:

```text
official source metadata
source_snapshot_hash
content hash
citation
integrity status
artifact availability when needed
manual review
candidate_evidence_reviews
downstream export only after review
no automatic publication
```

Appropriate for:

```text
la-ayuda
EduAyudas
subvenciones
BDNS
evidence-backed downstream workflows
```

Evidence-grade sources can support alerting, but their evidence standard must not be lowered to move faster.

## Alert-Grade

Alert-grade records are suitable for fast monitoring and product triage.

Characteristics:

```text
fast detection
metadata-first
official URL required
no artifact required by default
no downstream publication
confidence score
deduplication
human or product review before user-facing claims
```

Alert-grade is not proof-grade. It can say that a notice may matter to a user, but it cannot replace formal evidence review.

## Minimum Data Contract

Proposed alert-grade record:

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

Required minimum:

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

No alert-grade item should be user-facing unless it has an official URL and a clear confidence level.

## Alert Types

`convocatoria`

Opening of a public employment process, usually with bases, places, requirements, and application rules.

`bolsa`

Creation or update of a job pool, temporary employment list, substitute list, or similar mechanism.

`bases`

Publication or amendment of the rules governing a process.

`lista_provisional`

Provisional admitted/excluded list, provisional merits list, or similar provisional result.

`lista_definitiva`

Final admitted/excluded list, final merits list, or similar final result.

`tribunal`

Appointment, change, or publication of the selection board or examining committee.

`fecha_examen`

Exam date, call to exercise, venue assignment, or schedule.

`plazo`

Opening, extension, or reminder of submission/claim/application deadlines.

`subsanacion`

Correction period for missing documentation, defects, exclusions, or application errors.

`correccion`

Correction of errors affecting a process, bases, list, or previous notice.

`nombramiento`

Appointment related to a public employment process. This must not include unrelated political or administrative appointments.

`adjudicacion`

Awarding of positions, destinations, posts, or placements after a process.

## Classification Strategy

Use deterministic first-pass matching before any LLM or product-specific ranking.

Strong signals:

```text
convocatoria
proceso selectivo
oposición
oposiciones
bolsa de trabajo
lista provisional
lista definitiva
tribunal calificador
plazo de presentación
subsanación
nombramiento
personal funcionario
personal laboral
estabilización
concurso-oposición
fecha de examen
```

Weak or noisy terms:

```text
empleo
trabajo
resolución
anuncio
ayuntamiento
administración
```

Noise and exclusions:

```text
contratación pública
licitación
subvenciones
premios
convenios
urbanismo
medio ambiente
nombramientos no relacionados con procesos selectivos
```

Weak terms are not enough alone. A notice should need strong signals or useful co-occurrence, such as `ayuntamiento` plus `bolsa de trabajo`, or `resolución` plus `lista definitiva` plus a role name.

## Deduplication Strategy

The dedupe key should prefer stable official identifiers:

```text
source_code
official_url
document_identifier
publication_date
normalized title
issuing_body
alert_type
```

Suggested priority:

```text
1. source_code + document_identifier + alert_type
2. source_code + official_url + alert_type
3. source_code + publication_date + normalized_title + issuing_body + alert_type
```

Cross-source duplicate handling must account for repeated notices across:

```text
BOE
autonomous bulletins
provincial bulletins
local/provincial repeats
```

Do not collapse all cross-source duplicates blindly. A BOE notice and a provincial notice may both be relevant if they represent different legal publication moments. Instead, group related alerts and mark a primary official URL.

## Source Coverage Strategy

### Evidence-Grade Track

Sources with reliable metadata and evidence flows can remain evidence-grade:

```text
BOE
BOJA
DOGV
BOCYL
BDNS
BOPV if evidence flow is reliable
BORM only for metadata/candidates while evidence remains blocked
other autonomous sources after validation
```

### Alert-Grade Track

Alert-grade is appropriate for broad monitoring:

```text
autonomous bulletins
provincial bulletins
local/provincial sources
PDF-only sources
RSS/HTML-only sources
sources with fragile evidence download but stable index pages
```

Alert-grade can move faster because it does not require artifact download by default, but it must retain official URLs and clear confidence labels.

## Relationship With source_candidates

`source_candidates` remain evidence/downstream candidates.

Alert-grade items must not be stored as `source_candidates` by default.

Possible future tables or models:

```text
source_alerts
opposition_alerts
monitored_items
```

Any future schema must preserve separation:

```text
source_candidates = evidence/downstream pipeline
source_alerts / opposition_alerts = monitoring/notification pipeline
```

## Relationship With oposiciones2.0

### Option A: Inside official-sources

Pros:

```text
centralized source ingestion
shared source registry
reuse normalization/dedupe
single audit trail for source monitoring
```

Cons:

```text
risk of mixing evidence-grade and alert-grade
larger scope
more complex DB model
harder operational discipline
```

### Option B: Separate in oposiciones2.0

Pros:

```text
product-specific
faster iteration
alert-focused
less risk to evidence-grade pipeline
clearer product ownership
```

Cons:

```text
duplicated source logic
less shared infrastructure
possible drift from official source registry
more integration work if evidence is later requested
```

Recommendation:

```text
Design the alert-grade contract in official-sources, but do not implement storage yet.
Prototype product behavior in a separate alert-grade track, likely closer to oposiciones2.0.
Only centralize later if the boundary between source_alerts and source_candidates is explicit in schema, CLI, docs, and validation.
```

## Promotion Path

Alert-grade can request evidence-grade review, but must not become evidence-grade automatically.

Promotion flow:

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

Promotion requirements:

```text
official evidence fetch
integrity/citation review
human review
evidence-grade conversion
```

Until that conversion is complete:

```text
evidence_grade_status=none or requested
```

## Risks

Main risks:

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

Risk controls:

```text
official_url required
confidence required
dedupe_key required
weak terms not enough alone
no automatic downstream/publication
no automatic source_candidate creation
explicit promotion path
clear UX labels for unreviewed alerts
```

## Recommended Next Tasks

```text
TASK-OPOSITIONS-ALERT-GRADE-002 - Define source_alerts schema proposal
TASK-OPOSITIONS-SOURCES-001 - Rank sources for oposiciones monitoring
TASK-OPOSITIONS-CLASSIFIER-001 - Deterministic alert type classifier design
TASK-BOP-PROVINCIAL-001 - Provincial bulletin platform family audit
TASK-OPOSITIONS-ALERT-GRADE-003 - Prototype alert-grade dry-run from existing metadata
```

The first implementation task should still be dry-run only:

```text
no VPS writes
no DB schema migration
no candidates
no artifacts
no downstream
```
