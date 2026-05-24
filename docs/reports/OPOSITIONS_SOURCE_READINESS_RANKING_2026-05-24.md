# Oposiciones Source Readiness Ranking

Date: 2026-05-24

Task: `TASK-OPOSITIONS-SOURCES-001`

Scope: rank existing `official-sources` sources for alert-grade oposiciones/public employment monitoring.

This is a docs-only report. It is based only on existing local documentation and reports under `docs/` and `docs/reports/`. No VPS checks were run, no database/schema/code/tests were modified, no candidates or artifacts were created, and no downstream project was touched.

## Decision Summary

First dry-run recommendation:

| Rank | Source | Recommendation | Reason |
| ---: | --- | --- | --- |
| 1 | BOE | yes | Mature state source; strong national public-employment relevance; metadata/candidate machinery already exercised. |
| 2 | DOGV | yes | Validated 30-day metadata and candidate workflow; public selection notices are known to appear in metadata. |
| 3 | BOCYL | yes | Validated metadata/candidate workflow; `concurso-oposicion` appeared as an observed title pattern. |
| 4 | BOPV | yes | Metadata and small candidate workflow exist; staffing/provision and `oposiciones` terms are known in metadata, but evidence support is still incomplete. |
| 5 | BOJA | yes | Pilot/autonomous workflow is validated; broad official metadata and issuing bodies are useful, though oposiciones-specific calibration is not yet documented. |
| 6 | BORM | yes, constrained | Candidate workflow exists and job-board terms were explicitly filtered for aid monitoring; title truncation and evidence access blockers require narrow dry-run scope. |
| 7 | BOA | no | Local metadata adapter exists, but no documented completed 30-day metadata window; not ready for candidate/alert dry-run from docs evidence alone. |
| 8 | DOGC | no | Local adapter exists, but current docs require VPS smoke before broad backfill; candidate dry-run is explicitly not ready. |
| 9 | BDNS | no | Primary grants registry, not a bulletin or oposiciones source; useful as a negative/non-oposiciones control. |

## Ranking Criteria

For alert-grade oposiciones monitoring, readiness means:

- document-level metadata can be obtained without artifact downloads;
- title and issuing-body fields are good enough for deterministic first-pass classification;
- official URL is preserved and can support user-facing review links;
- territory can be normalized;
- likely oposiciones signals exist in the documented source surface;
- false-positive families are known enough to control a first dry-run;
- the first dry-run can remain separate from evidence-grade `source_candidates`.

This report does not claim any source is evidence-grade for oposiciones. Alert-grade output should remain separate from source-candidate/evidence promotion.

## Source Assessments

### 1. BOE

| Dimension | Assessment |
| --- | --- |
| Metadata availability | High. BOE is the mature project source with summary backfills, selected candidate workflows, artifact policy, and dedupe behavior already documented. |
| Title quality | High for official notice discovery, but broad. Existing candidate reports show titles are rich enough for triage and also noisy enough to need filters. |
| `official_url` quality | High. BOE identifiers and official links are central to existing evidence and citation flows. |
| Issuing body quality | High. Departments and ministries are available and useful for routing and exclusions. |
| Territory quality | High for state-level `ES`; autonomous/local repeated notices may still need related-group dedupe. |
| Likely oposiciones signal | High. State public employment, selection, appointment, list, tribunal, correction, and deadline notices belong naturally in BOE monitoring. |
| False positive risks | Very high volume; generic `convocatoria` can mean grants, subsidies, awards, procurement-like notices, or non-employment calls. University service names and procedural notices can also mislead keyword matching. |
| First dry-run inclusion | Yes. Use as the baseline state source, with strict alert-grade-only output and no automatic source-candidate creation. |

### 2. DOGV

| Dimension | Assessment |
| --- | --- |
| Metadata availability | High. DOGV has a metadata MVP, controlled 30-day metadata backfill, source-aware candidate dry-runs, limited candidate creation, and metadata triage documented. |
| Title quality | High. Existing DOGV reports show direct document titles can separate scholarships, employment-related notices, corrections, and selection/public appointment noise. |
| `official_url` quality | High. DOGV audit documents canonical result URLs, metadata JSON, dynamic XML, and direct PDF URL preservation. |
| Issuing body quality | Medium-high. Section/subsection and DOGV metadata are available, though source-specific profile rules are still needed. |
| Territory quality | High for `ES-VC` / Comunitat Valenciana. |
| Likely oposiciones signal | High. Existing DOGV dry-run notes explicitly mention staff selection and public employment notices matching through `convocatoria`, `empleo`, and department terms. Those were noise for aid monitoring but are useful for oposiciones alerts. |
| False positive risks | High. `subvenciones`, `becas`, `convocatoria`, `empleo`, and section labels can mix scholarships, grants, labor aids, project subsidies, corrections, and public selection notices. |
| First dry-run inclusion | Yes. Use a DOGV-specific oposiciones profile; do not reuse the aid profile directly. |

### 3. BOCYL

| Dimension | Assessment |
| --- | --- |
| Metadata availability | High. BOCYL has documented 30-day metadata backfill, profile refinement, limited candidate creation, and metadata-only triage. |
| Title quality | Medium-high. Titles are useful enough to identify scholarships and also an observed `concurso-oposicion` notice. |
| `official_url` quality | Medium-high. BOCYL reports state XML/PDF/HTML URLs are preserved as metadata. |
| Issuing body quality | Medium. Existing reports rely on department/type context and note that generic terms need department/title context. |
| Territory quality | High for `ES-CL` / Castilla y Leon. |
| Likely oposiciones signal | Medium-high. The BOCYL triage observed `concurso-oposicion laboral con plazas de discapacidad intelectual`; this was a false positive for aid monitoring but a direct positive family for oposiciones monitoring. |
| False positive risks | High. Generic `convocatoria`, housing/planning/environment, sectoral subsidies, and scholarship/aid notices can dominate if not source-specific. |
| First dry-run inclusion | Yes. Include with explicit positive patterns for `oposicion`, `concurso-oposicion`, `bolsa`, `plazas`, `lista`, `tribunal`, and weak treatment of generic `convocatoria`. |

### 4. BOPV

| Dimension | Assessment |
| --- | --- |
| Metadata availability | Medium-high. BOPV has local metadata adapter work, 30-day candidate dry-run/calibration, small candidate creation, and metadata triage documented. |
| Title quality | Medium-high. Document XML metadata includes title, section, subsection, and organism metadata. Existing dry-run notes show staffing/provision notice patterns. |
| `official_url` quality | High for metadata. Official HTML/XML/PDF/EPUB URLs are preserved from issue XML. |
| Issuing body quality | High. BOPV reports show issuer fields such as Departamento de Educacion and Lanbide. |
| Territory quality | High for `ES-PV` / Pais Vasco. |
| Likely oposiciones signal | Medium-high. Existing calibration found `oposiciones`, `contratacion`, staffing/provision, and employment terms in metadata; those were exclusion/noise terms for aid monitoring but are relevant for oposiciones alerts. |
| False positive risks | Medium-high. Raw metadata can include neighboring broad terms, so classification should inspect title/issuer first and avoid raw-metadata-only positives. Training, grants, Lanbide employment aids, and education-center subsidies can look employment-related without being selection notices. |
| First dry-run inclusion | Yes. Include metadata/title-only, but keep evidence download out of scope because BOPV artifact downloader support was still blocked in the preflight. |

### 5. BOJA

| Dimension | Assessment |
| --- | --- |
| Metadata availability | High. BOJA has validated pilot metadata, 30-day candidate dry-run, BOJA-specific profile, limited candidate batch, and metadata triage documented. |
| Title quality | Medium-high. Existing reports show title summaries are good enough to distinguish university scholarships, FPE notifications, housing/rent aid, and procedural notices. |
| `official_url` quality | Medium. BOJA candidate rows did not expose direct public/PDF URLs in one metadata query used for triage, so evidence fields must be verified before evidence work. For alert-grade, this is acceptable only if an official URL is present in the alert output. |
| Issuing body quality | High. Reports show useful issuers/departments such as Universidades, Desarrollo Educativo y Formacion Profesional, Empleo, and Fomento/Vivienda. |
| Territory quality | High for `ES-AN` / Andalucia. |
| Likely oposiciones signal | Medium. BOJA is a major autonomous bulletin and likely carries public employment notices, but the current reports reviewed here focus on aid/scholarship candidate work rather than oposiciones-specific signal validation. |
| False positive risks | High. Housing, municipal, institutional grants, FPE procedural notifications, disability recognition, and broad `convocatoria`/`ayudas` terms can overwhelm generic matching. |
| First dry-run inclusion | Yes. Include because the source workflow is validated, but treat results as exploratory until BOJA-specific oposiciones terms are calibrated. |

### 6. BORM

| Dimension | Assessment |
| --- | --- |
| Metadata availability | Medium-high. BORM has metadata backfill/candidate dry-run, profile calibration, limited candidate creation, and metadata triage documented. |
| Title quality | Medium. Reports warn that some BORM titles are abbreviated or truncated in stored official metadata. |
| `official_url` quality | Medium. Metadata preserves official HTML and PDF URLs, but XML URLs were absent in reviewed candidate metadata. |
| Issuing body quality | Medium. Enough context exists for aid triage, but title truncation makes issuer/body context more important. |
| Territory quality | High for `ES-MC` / Region de Murcia. |
| Likely oposiciones signal | Medium. The BORM aid profile explicitly filters `bolsa de trabajo` / `bolsa de empleo`, which are negative for aid monitoring but promising for oposiciones/job-alert monitoring. |
| False positive risks | High. Job-board terms can include non-oposicion labor pools, youth contests, entity grants, employability programs, and procedural notices. Evidence access is also constrained by documented PerfDrive/Radware blocking for PDF/HTML from the VPS. |
| First dry-run inclusion | Yes, constrained. Include only as metadata/title dry-run with no artifact access and no promotion; use it to measure whether `bolsa`, `empleo publico`, `oposicion`, and appointment/list terms are recoverable from titles. |

### 7. BOA

| Dimension | Assessment |
| --- | --- |
| Metadata availability | Medium. BOA has a local metadata-only adapter and preflight/runbook, but no local report records a completed 30-day metadata backfill. |
| Title quality | Unknown for oposiciones at 30-day scale. Existing docs validate metadata normalization but not alert quality. |
| `official_url` quality | Medium-high. BOA adapter preserves official BOA URLs and PDF URLs as metadata only. |
| Issuing body quality | Unknown-medium. Expected to be available from metadata, but no oposiciones dry-run evidence is documented. |
| Territory quality | High for `ES-AR` / Aragon. |
| Likely oposiciones signal | Unknown-medium. As an autonomous bulletin, it likely contains public-employment notices, but the reviewed docs do not yet prove a usable metadata window or source profile. |
| False positive risks | Unknown. Existing docs warn BOA may use sections/departments differently from other sources and that a BOA-specific profile is likely needed. |
| First dry-run inclusion | No. First complete and validate a BOA 30-day metadata-only backfill, then run a read-only candidate/alert dry-run. |

### 8. DOGC

| Dimension | Assessment |
| --- | --- |
| Metadata availability | Medium locally, low operationally. DOGC has a local one-date metadata adapter, but current docs require a VPS smoke before any broad metadata backfill. |
| Title quality | Unknown-medium. Catalan titles and section labels likely need DOGC-specific keyword and exclusion rules before scoring is meaningful. |
| `official_url` quality | High in adapter design. Official HTML, XML, RDF, Turtle, and PDF URLs are preserved as metadata only. |
| Issuing body quality | Unknown-medium. Metadata normalization exists, but no 30-day validated alert window is documented. |
| Territory quality | High for `ES-CT` / Catalunya. |
| Likely oposiciones signal | Unknown-medium. DOGC is likely relevant as an autonomous bulletin, but current reports do not validate oposiciones signal quality. |
| False positive risks | High until calibrated: Catalan terminology, section differences, pagination ceiling risk, and documented TLS/connectivity risk. |
| First dry-run inclusion | No. Run only after the prepared DOGC VPS smoke and a validated metadata window; add a DOGC-specific oposiciones profile first. |

### 9. BDNS

| Dimension | Assessment |
| --- | --- |
| Metadata availability | High for its domain. BDNS has a metadata-only adapter MVP for `convocatorias` / grant calls and profile design for subsidy downstreams. |
| Title quality | High for grants/subsidies, not public employment. |
| `official_url` quality | High for BDNS public convocatoria URLs. |
| Issuing body quality | High for grant-call monitoring. |
| Territory quality | Medium-high for grant registry purposes; not bulletin territory hierarchy. |
| Likely oposiciones signal | Low. BDNS is a grants/subsidies registry, not an official bulletin for public-employment notices. |
| False positive risks | Very high if included in oposiciones monitoring. `convocatoria` in BDNS means grant/subsidy call, not opposition/public employment call. |
| First dry-run inclusion | No. Use only as a negative/non-oposiciones control to prove the classifier does not treat every `convocatoria` as an oposiciones alert. |

## First Dry-Run Shape

Recommended first dry-run source set:

```text
BOE
DOGV
BOCYL
BOPV
BOJA
BORM
```

Excluded from first dry-run:

```text
BOA  - wait for completed and validated 30-day metadata window
DOGC - wait for VPS smoke and validated metadata window
BDNS - non-oposiciones grants registry; use as negative control only
```

Operational constraints for the dry-run:

- alert-grade only;
- no `source_candidates` writes;
- no artifact downloads;
- no downstream writes;
- no automatic promotion to evidence-grade;
- require `official_url`, `publication_date`, `title`, `source_code`, `territory_code`, `alert_type`, `confidence`, and `dedupe_key`;
- treat generic `convocatoria` as weak unless paired with public-employment terms;
- treat grants/subsidies, scholarships, housing aid, procurement-like notices, award/result-only records, and entity funding as exclusions unless the title clearly indicates public-employment process relevance.

Suggested high-signal positive terms for the first deterministic profile:

```text
oposicion
oposiciones
concurso-oposicion
proceso selectivo
personal funcionario
personal laboral
bolsa de empleo
bolsa de trabajo
plazas
lista provisional
lista definitiva
tribunal
fecha de examen
nombramiento
adjudicacion de destinos
toma de posesion
```

Weak or ambiguous terms:

```text
convocatoria
empleo
contratacion
provision
seleccion
bolsa
```

These should require title, issuer, or section context before producing anything above low confidence.

## Merge Risk

Low for this task if kept to this file. The only owned path is:

```text
docs/reports/OPOSITIONS_SOURCE_READINESS_RANKING_2026-05-24.md
```

Potential semantic conflict: parallel work may update BOA, DOGC, BOPV, or BORM readiness after this report. If so, this ranking should be treated as a snapshot based on local docs available on 2026-05-24, not as live VPS truth.
