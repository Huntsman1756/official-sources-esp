# Official Sources Platform Status - 2026-05-21

## Scope

This report summarizes the current `official-sources` platform state after the BOE, BOJA,
EduAyudas, and `la-ayuda` pilots.

This was a documentation-only status task.

No code was changed. No candidates were created. No artifacts were downloaded. No downstream
repositories were touched. Nothing was approved or published.

## Executive Summary

`official-sources` is now validated as a reusable official-evidence platform, not a single-project
tool for EduAyudas.

Validated platform pattern:

```text
official source metadata/evidence
-> official-sources storage, citation, integrity, and review metadata
-> downstream evidence contract/export
-> downstream-owned staging/review
-> downstream-owned draft/publication gates
```

Three pilots have now exercised the pattern:

| Pilot | Status | Publication result |
|---|---|---|
| BOE -> EduAyudas | Validated in local/dev and staging-oriented import paths | No automatic publication |
| BOJA -> official-sources | Validated through reviewed evidence decisions | No downstream import or publication |
| BOE -> la-ayuda | Validated through non-public draft/internal review | No public route or publication |

## BOE Status

BOE is the mature Tier 1 source in the platform.

Validated capabilities include:

- daily publication ingestion;
- XML/HTML/PDF artifact handling;
- citation and integrity metadata;
- controlled BOE summary backfills;
- deterministic candidate prefiltering;
- candidate evidence review decisions;
- downstream evidence export.

Latest 6-month BOE pilot state:

| Metric | Value |
|---|---:|
| Source candidates after 6-month batch | 75 |
| Selected evidence review candidates | 13 |
| Accepted for downstream pilot | 5 |
| EduAyudas-routed exports | 4 |
| la-ayuda-routed export | 1 |
| Downstream publication from `official-sources` | 0 |

Accepted downstream routing:

```text
EduAyudas: 36, 40, 49, 60
la-ayuda: 69
```

BOE remains the best source for validating downstream contract behavior because it already has
stable XML/HTML evidence and mature artifact handling.

## BOJA Status

BOJA is the first validated autonomous/statutory territory source.

Validated BOJA chain:

```text
BOJA metadata
-> official_documents
-> source_candidates
-> triage
-> detail endpoint enrichment
-> scoped PDF download
-> PDF evidence review
-> candidate_evidence_reviews
-> no downstream import
-> no approval
-> no publication
```

Final BOJA pilot metrics:

| Metric | Value |
|---|---:|
| 30-day BOJA documents | 1500 |
| BOJA source candidates created | 25 |
| Selected for evidence | 10 |
| PDFs downloaded | 10 |
| Accepted for downstream pilot | 4 |
| Out of scope after evidence review | 6 |
| Downstream writes | 0 |
| Publications | 0 |

Key BOJA technical findings:

- `search_pagination` is useful for metadata but lacks evidence URLs.
- `GET /api/v0/boja/{bid}` is required for PDF URL enrichment.
- BOJA needs source-specific profile `boja-ayudas`; the BOE `la-ayuda` profile overmatches.
- PDF URLs required canonicalization from `juntadeandalucia.es` to `www.juntadeandalucia.es`.
- Only PDF evidence is currently validated for BOJA.

BOJA is viable as a metadata-first autonomous source, but it should not be imported downstream
automatically.

## EduAyudas Integration Status

EduAyudas has validated `official-sources` as a downstream evidence consumer.

Validated EduAyudas chain:

```text
official-sources evidence
-> EduAyudas official_source_evidence
-> EduAyudas source_candidates pending_review
-> EduAyudas aid_program draft
-> structured evidence link
-> admin review
-> no publication
```

Recent platform cleanup also added a guarded EduAyudas local/dev fallback path for imports when
local REST is unavailable:

```text
--local-db-fallback
```

Safety constraints preserved:

- local/dev only;
- localhost-only database target;
- no production Supabase;
- no `aid_programs` unless a dedicated draft task explicitly authorizes it;
- no `acceptCandidate`;
- no publication.

Current operational note:

```text
EduAyudas Flow B/profile/evaluation QA is currently being repaired by another agent.
Do not continue TASK-012/TASK-013 work from this repository status thread.
```

The current EduAyudas product QA blocker is downstream-specific and should remain in the EduAyudas
repo.

## la-ayuda Pilot Status

`la-ayuda` validated a second downstream shape that is not Supabase-first.

Validated chain:

```text
official-sources evidence JSON
-> la-ayuda evidence staging
-> la-ayuda candidate staging
-> draft benefit file
-> final internal review
-> no public route
-> no publication
```

Key outcome:

```text
status=draft
reviewStatus=pendiente_revision
decision=ready_for_internal_editorial_review
public route=not generated
```

The `la-ayuda` pilot proved that the same evidence contract can support a content/file-based
downstream without creating public pages automatically.

Do not continue editing `la-ayuda` from this repository unless a separate task explicitly targets
that repo.

## Downstream Onboarding Kit

The downstream onboarding kit is in place:

```text
docs/DOWNSTREAM_ONBOARDING.md
docs/DOWNSTREAM_IMPORT_CHECKLIST.md
docs/DOWNSTREAM_CONTRACT.md
docs/examples/downstream_evidence_contract.example.json
docs/examples/downstream_profile.example.yaml
```

The kit defines:

- what `official-sources` is and is not;
- required downstream staging/review capabilities;
- evidence contract fields;
- preview/import/write patterns;
- candidate and draft creation boundaries;
- anti-patterns;
- project-specific notes for EduAyudas, `la-ayuda`, oposiciones2.0, renta-verificable,
  subvenciones, and contratosabiertos.

The key rule remains:

```text
Importing official evidence is not approval and must never publish.
```

## Main Technical Debt

Current technical and operational debt:

| Area | Debt | Suggested handling |
|---|---|---|
| BOJA ingestion | No BOJA range command; date loops were used | Add a range wrapper only after source expansion is prioritized |
| BOJA evidence | No HTML/XML flow, PDF-only validated | Keep PDF-only until a scoped HTML/XML design exists |
| Autonomous sources | Only BOJA is implemented | Audit DOGV/BOCM before adding more adapters |
| Candidate profiles | Profiles are source-specific and still young | Keep deterministic profile reports before candidate creation |
| Downstream imports | Production rollout remains project-owned | Keep preview/evidence/candidate/draft steps separate |
| EduAyudas | Current product QA is being repaired elsewhere | Do not duplicate work in this thread |
| la-ayuda | Draft is internal-review-ready, not publishable | Any publication checklist belongs in `la-ayuda` |
| MCP/API | MCP remains private/read-only; no public API | Do not expose without a separate auth/security task |
| Search/RAG | No vector/RAG layer | Keep out of scope until source/review workflows stabilize |

## Strategic Options

### Option A - Source Expansion

Start a new autonomous source audit/MVP:

```text
TASK-AUTO-BOCM-001 - BOCM source audit / MVP research
TASK-AUTO-DOGV-001 - DOGV source audit / MVP research
```

Use this option if the priority is coverage.

### Option B - Backfill Expansion

Extend BOE or BOJA metadata windows:

```text
BOE 12-month backfill
BOJA 3-month metadata-only backfill
```

Use this option if the priority is candidate volume and review queue depth.

### Option C - Downstream Hardening

Wait for EduAyudas repair to finish, then rerun the downstream import/QA path from that repo.

Use this option if the priority is product readiness.

### Option D - Platform Readability

Continue small cleanup tasks only when they reduce operator friction, such as improving source
profile docs or adding operational summaries.

Use this option if the priority is maintainability.

## Recommendation

Recommended next strategic decision:

```text
Wait for the EduAyudas repair to finish, then choose between source expansion and downstream hardening.
```

If work must continue immediately without touching EduAyudas, the cleanest next task is:

```text
TASK-AUTO-BOCM-001 - BOCM source audit / MVP research
```

Rationale:

- BOE and BOJA already validate the platform pattern.
- `la-ayuda` already validates a second downstream pattern.
- EduAyudas is actively being repaired elsewhere.
- A new source audit can proceed independently if kept metadata-only and non-writing.

## Safety Status

Current safety guarantees across the platform:

- No automatic downstream publication.
- No automatic candidate approval.
- No `acceptCandidate` bypass for official-source evidence.
- Evidence review decisions remain operational metadata, not legal advice.
- Downstream projects own final product fit and publication.
- MCP remains private/read-only.
- Raw legal text is not included in default downstream JSON exports.

## Validation

Documentation validation for this status task:

```text
git diff --check: passed
```
