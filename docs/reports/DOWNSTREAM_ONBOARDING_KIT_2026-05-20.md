# Downstream Onboarding Kit - 2026-05-20

## Summary

TASK-PLATFORM-001 created a reusable downstream onboarding kit for projects that consume
`official-sources`.

The kit generalizes the validated BOE-to-EduAyudas local/dev path and the BOJA pilot without
creating new integrations, candidates, artifacts, or downstream writes.

## Files Created

```text
docs/DOWNSTREAM_ONBOARDING.md
docs/examples/downstream_evidence_contract.example.json
docs/examples/downstream_profile.example.yaml
docs/reports/DOWNSTREAM_ONBOARDING_KIT_2026-05-20.md
```

## Files Updated

```text
docs/DOWNSTREAM_CONTRACT.md
docs/ROADMAP.md
docs/SOURCES_POLICY.md
docs/VALIDATION.md
```

## Decisions Made

The onboarding kit makes these platform decisions explicit:

- `official-sources` is an official evidence platform, not a downstream publisher.
- Downstream projects must provide their own staging, review, and publication gates.
- Evidence import must not publish records.
- `accept_for_downstream_pilot` and `likely_relevant` are not approval states.
- Integrity and citation metadata are required downstream fields, not optional notes.
- Projects without candidate/evidence staging need foundation work before integration.

## How This Generalizes Beyond EduAyudas

EduAyudas validated the first downstream path, but the kit separates the general platform contract
from EduAyudas-specific implementation details.

The reusable model is:

```text
official-sources reviewed evidence
-> downstream evidence staging
-> downstream source_candidate pending_review
-> optional draft after human decision
-> downstream-owned publication gate
```

This applies to:

- EduAyudas;
- la-ayuda after foundation;
- oposiciones2.0;
- renta-verificable;
- subvenciones;
- contratosabiertos.

Each project can define its own domain model while preserving official identifier, citation,
integrity, artifact, and review metadata.

## Required Downstream Capabilities

A new downstream must implement at least:

```text
candidate/evidence staging
pending_review workflow
source_url storage
official_identifier storage
citation_json storage
source_snapshot_hash
content_sha256
hashes_match
has_integrity_warning
integrity_warning_reason
artifact availability
manual review state
publication gate
admin/staff review surface
```

If these are missing, the correct next task is downstream foundation, not evidence import.

## Supported Integration Patterns

The kit documents five supported patterns:

| Pattern | Description |
| --- | --- |
| Pattern A | Manual export/import. |
| Pattern B | Preview-only import. |
| Pattern C | Evidence staging write. |
| Pattern D | Candidate creation as `pending_review`. |
| Pattern E | Draft creation after explicit human decision. |

Publication remains outside `official-sources` in every pattern.

## Anti-Patterns Documented

The guide documents anti-patterns including:

- `official-sources` writing directly to public tables;
- evidence import creating published records;
- treating `likely_relevant` as approved;
- treating PDF availability as verification;
- bypassing official-source review through generic accept flows;
- exposing MCP publicly;
- storing only free-text source notes;
- ignoring integrity warnings.

## Project-Specific Recommendations

### EduAyudas

Validated local/dev pattern exists. Production still needs a remote-safe import path.

### la-ayuda

Recommended next downstream foundation target. It needs evidence/candidate staging before importing
reserved evidence.

### oposiciones2.0

Likely needs BOE plus autonomous/provincial sources. Build foundation first.

### renta-verificable

High-risk fiscal domain. Requires tax authority sources and explicit legal/fiscal review gates;
BOE alone is not enough.

### subvenciones

BDNS is likely primary. BOE/BOJA evidence can be supporting context.

### contratosabiertos

PLACSP is likely primary. `official-sources` can provide contextual official references, not the
main procurement data model.

## Validation

Documentation validation:

```text
git diff --check: passed
```

No code changes were made. The Python test suite was not run for this documentation-only task.

## Recommended Next Task

Recommended next task:

```text
TASK-LAAYUDA-FOUNDATION - add evidence/candidate staging model
```

Reason:

- BOE and BOJA have validated `official-sources` as a reusable evidence platform.
- EduAyudas is already validated in local/dev.
- `la-ayuda` has reserved evidence but lacks safe staging/review foundation.

Alternative next tasks remain available after the foundation decision:

```text
TASK-AUTO-011 - Export BOJA accepted evidence for EduAyudas staging
TASK-AUTO-BOCM-001 - BOCM source audit or MVP research
TASK-AUTO-DOGV-001 - DOGV endpoint discovery
```
