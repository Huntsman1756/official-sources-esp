# BOPV 30-Day Candidate Triage

Date: 2026-05-24

Scope: metadata-only review of the four BOPV/EHAA candidates created by `TASK-AUTO-BOPV-005`.

Candidate IDs reviewed:

```text
147,148,149,150
```

No artifacts were downloaded. No candidates were created. No `review_status` values were changed. No downstream project was touched.

## VPS State

Database validation before and after review:

```text
database_path=/opt/official-sources/data/official_sources.sqlite current_version=8 latest_version=8 status=valid
```

Safety counters remained unchanged during review:

```text
source_candidates_total=150
BOPV source_candidates=4
BOPV review_status_distribution=human_review_required:4
artifact_download_attempts=482
artifact_bytes=28857411
```

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result: no matching listeners.

## Candidate Triage

| Candidate | Official identifier | Date | Department | Metadata signal | Classification | Evidence action | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 147 | `BOPV:BOPV-2026-05-2602039a` | 2026-05-15 | Departamento de Educacion | FP, subvenciones, bases reguladoras, centros privados concertados | `unclear` | `download_xml_or_html` | Education/FP scope is relevant, but apparent beneficiary is educational centers rather than direct citizens/students. |
| 148 | `BOPV:BOPV-2026-05-2601909a` | 2026-05-08 | Departamento de Ciencia, Universidades e Innovacion | ayudas, bases reguladoras, universidades, proyectos de investigacion | `out_of_scope` | `do_not_download` | Research project funding appears institutional/project-oriented, not a direct citizen/family/student aid. |
| 149 | `BOPV:BOPV-2026-04-2601788a` | 2026-04-30 | Lanbide-Servicio Publico Vasco de Empleo | ayudas, convocatoria, empleo, discapacidad | `likely_relevant` | `download_xml_or_html` | Employment/disability signal may fit a future social-aid review, but metadata suggests aid to special employment centers, so evidence should confirm beneficiary and application mechanics. |
| 150 | `BOPV:BOPV-2026-04-2601716a` | 2026-04-24 | Departamento de Educacion | FP, subvenciones, bases reguladoras, centros concertados | `unclear` | `download_xml_or_html` | Education/FP scope is relevant, but apparent beneficiary is educational centers/projects rather than direct citizens/students. |

## Distribution

```text
reviewed=4
likely_relevant=1
unclear=2
out_of_scope=1
false_positive=0
```

## Selected Evidence Candidates

Recommended for a future scoped XML/HTML evidence download:

```text
147
149
150
```

Candidate `148` should not be downloaded in the next evidence batch unless the downstream scope is expanded to institutional research grants.

## Noise Observations

The calibrated BOPV profile is clean but still produces some entity/project grants:

- Education/FP terms can match grants to centers rather than direct student/family support.
- University terms can match research-project calls that are likely outside `la-ayuda` and `EduAyudas`.
- Employment/disability terms need evidence review because the beneficiary may be a center/employer, not the person.

This is acceptable for a first batch of four candidates, but candidate evidence review should keep downstream routing conservative.

## Status Verification

Post-review checks:

```text
source_candidates_total=150
BOPV source_candidates=4
BOPV review_status_distribution=human_review_required:4
artifact_download_attempts=482
artifact_bytes=28857411
DB validation=status=valid schema_version=8
MCP privacy=no matching official/mcp/python/uvicorn/fastmcp listeners
```

No state changes were made during triage.

## Next Recommended Task

```text
TASK-AUTO-BOPV-007 — BOPV selected candidate evidence download
```

Recommended scope:

```text
candidate_ids=147,149,150
types=xml,html
pdf=defer
```

Do not download evidence for candidate `148` in the next scoped batch.
