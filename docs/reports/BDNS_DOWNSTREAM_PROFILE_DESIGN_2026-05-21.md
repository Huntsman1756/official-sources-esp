# BDNS Downstream Profile Design

Date: 2026-05-21

## Summary

TASK-BDNS-004-PREP designs downstream BDNS candidate profiles before any real candidate creation.

This is a design-only task. It did not run BDNS candidate extraction, did not create
`source_candidates`, did not ingest concessions, did not download PDFs or attachments, did not touch
downstream projects, did not use MCP, and did not use the project VPS.

BDNS remains a metadata-only grants registry source for this step. Profiles are deterministic
prefilter designs for future dry-runs against stored `grant_call` metadata.

Created profile fixture:

```text
docs/examples/bdns_downstream_profiles.example.yaml
```

## Inputs Reviewed

Reviewed local project context:

- `src/official_sources/cli.py`
- `tests/test_cli.py`
- `docs/DOWNSTREAM_ONBOARDING.md`
- `docs/SOURCES_POLICY.md`
- existing BDNS reports and downstream profile example

Current CLI state:

- BDNS ingestion commands exist for latest calls, one call detail, and bounded search.
- Generic candidate prefiltering exists for BOE/BOJA official documents.
- CLI `--profile` choices currently support `la-ayuda` and `boja-ayudas`, not BDNS profiles.

Design decision:

```text
Do not extend CLI profile choices in this prep task.
```

Reason:

- The task asks to design profiles before creating real candidates.
- Avoiding CLI changes reduces merge risk with parallel agent work.
- BDNS profile behavior should first be validated as deterministic fixtures and docs.

## Profile Model

Profiles target BDNS `grant_call` metadata only.

Primary matching fields:

```text
title
description
description_finalidad
beneficiary_type
instrument_type
sector_activity
territorial_scope
calling_body
budget
application_start_date
application_end_date
base_regulation_url
application_url
raw_metadata
```

Required minimum profile gate:

```text
source_code=BDNS
resource_type=grant_call
official_identifier starts with BDNS:
metadata only
human_review_required if a future candidate is created
```

The profiles must not classify legal eligibility or publication readiness. They only explain why a
stored BDNS call may deserve downstream review.

## Profiles

### `bdns-eduayudas`

Purpose:

```text
Education, scholarship, student, family, and training aid discovery.
```

Strong inclusion signals:

- `beca`, `becas`
- `ayudas al estudio`
- `alumnado`, `estudiantes`
- `familias`
- `libros`, `libros de texto`, `material escolar`
- `comedor escolar`
- `transporte escolar`
- `NEAE`, `necesidades especificas de apoyo educativo`
- `formacion profesional`, `FP`
- `universidad`, `universitario`, `universitaria`
- `matricula`, `movilidad`, `practicas`

Typical downstream fit:

```text
EduAyudas pending_review candidate, never direct publication.
```

Downranking:

- generic `educacion` without aid/student/family context;
- generic `transporte` unless school or student context is present;
- broad training subsidies aimed only at companies unless there is direct student or trainee benefit.

### `bdns-la-ayuda`

Purpose:

```text
Direct aid discovery for people, households, youth, housing, vulnerability, disability, and
dependency workflows.
```

Strong inclusion signals:

- `ayuda`, `ayudas directas`
- `personas`, `familias`
- `joven`, `jovenes`
- `vivienda`, `alquiler`, `bono alquiler`
- `bono social`
- `vulnerabilidad`, `riesgo de exclusion`, `emergencia social`
- `discapacidad`
- `dependencia`
- `mayores`
- `familia numerosa`, `monoparental`

Typical downstream fit:

```text
la-ayuda evidence/candidate staging only, once downstream foundation exists.
```

Downranking:

- generic subsidy calls for associations or entities when no direct person/family benefit is
  visible;
- broad sector calls unless direct household or individual benefit is explicit;
- education-only calls that fit better under `bdns-eduayudas`.

### `bdns-subvenciones`

Purpose:

```text
Broad subsidy and grant-call discovery for public/private beneficiaries, instruments, amounts,
issuing bodies, sectors, and territories.
```

Strong inclusion signals:

- `subvencion`, `subvenciones`
- `ayuda`, `ayudas`
- `convocatoria`
- `bases reguladoras`
- `concurrencia competitiva`, `concesion directa`
- `presupuesto`, `importe`
- `organo`, `entidad convocante`
- `beneficiarios`, `tiposBeneficiarios`
- `sectores`, `regiones`, `territorio`
- `instrumentos`

Typical downstream fit:

```text
Subsidy-focused product review queue.
```

This is the only proposed profile that can keep company/sector-only calls, provided the record is a
BDNS convocatoria and not a concession.

## Exclusion And Downranking Rules

Hard exclusions for all three profiles:

- `resource_type` other than `grant_call`;
- concessions or award records;
- adjudications;
- procurement, tenders, contracts, or public-sector contracting notices;
- closed procedures when `abierto=false` or equivalent metadata says the call is closed;
- missing application deadline when no `application_end_date`, deadline text, or equivalent
  metadata exists;
- records that only describe official publication or registry mechanics without a grant call.

Default downranking for all profiles:

- exclusively public-entity beneficiaries;
- institutional transfer or internal public-administration funding;
- sector-only or company-only calls outside `profile=bdns-subvenciones`;
- generic `convocatoria`, `ayuda`, or `subvencion` without beneficiary, deadline, body, or purpose
  context;
- no amount/budget when the downstream needs amount display, unless the profile allows review with
  missing amount.

Profile-specific hard exclusions:

```text
bdns-eduayudas:
  exclude company-only, sector-only, and administration-only calls unless direct student/family
  benefit is explicit.

bdns-la-ayuda:
  exclude education-only calls that have no household/person vulnerability, housing, disability,
  youth, or dependency signal.

bdns-subvenciones:
  do not exclude company/sector-only calls by default, but keep concessions and closed/no-deadline
  records out.
```

## Deterministic Scoring Proposal

Future implementation should keep scoring simple and explainable:

```text
strong_profile_signal: +3
supporting_profile_signal: +2
generic_grant_signal: +1
fresh_open_deadline: +2
deadline_present: +1
budget_or_amount_present: +1
official_application_or_base_url_present: +1
exclusively_public_entity: -3
sector_or_company_only_non_subvenciones: -3
generic_only: -2
closed_procedure: hard_exclude
missing_deadline: hard_exclude
concession_or_award: hard_exclude
adjudication_or_procurement: hard_exclude
```

Scores are prefilter signals only. They must not become approval, eligibility, ranking, or
publication decisions.

## Future CLI Shape

Recommended future profile keys:

```text
bdns-eduayudas
bdns-la-ayuda
bdns-subvenciones
```

Recommended future command behavior:

```bash
official-sources find-source-candidates \
  --source BDNS \
  --profile bdns-eduayudas \
  --date-from YYYY-MM-DD \
  --date-to YYYY-MM-DD \
  --dry-run \
  --limit 100
```

Before write mode exists for BDNS profiles, require a deterministic dry-run report with:

- scanned records;
- matched records;
- hard exclusions by reason;
- downrank counts by reason;
- sample matches with score reasons;
- zero candidate writes.

## Example Fixture

`docs/examples/bdns_downstream_profiles.example.yaml` records:

- profile keys and downstream targets;
- included metadata fields;
- deterministic keyword groups;
- hard exclusion reasons;
- downranking reasons;
- suggested scoring weights;
- sample synthetic cases.

Synthetic cases are examples only and are not real BDNS candidates.

## Validation Boundary

This prep task does not prove profile precision against live or stored BDNS data. The next safe step
is a dry-run-only task over stored metadata, still with:

```text
no concessions
no candidate creation
no downstream writes
no PDFs or attachments
```

## Merge Risks

Expected merge risk is low because this task adds documentation/example files only.

Potential conflicts:

- another agent may add BDNS profile support to `src/official_sources/cli.py`;
- another agent may add candidate tests in `tests/test_cli.py`;
- profile key naming could diverge if code lands first.

Resolution preference:

```text
Keep these docs as the profile contract, then align future CLI/test names to the three keys:
bdns-eduayudas, bdns-la-ayuda, bdns-subvenciones.
```
