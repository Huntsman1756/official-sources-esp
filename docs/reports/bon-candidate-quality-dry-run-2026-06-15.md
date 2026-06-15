# BON Candidate Quality Dry-run

Date: 2026-06-15
Task: `TASK-OFFICIAL-SOURCES-BON-CANDIDATE-QUALITY-DRY-RUN-001`

## Scope

Add BON support to the generic `find-source-candidates` dry-run path for EduBecas-style
education-aid review.

Allowed:

- local candidate-rule changes;
- local tests;
- read-only VPS evidence;
- local dry-run against a copied SQLite DB.

Forbidden:

- source candidate writes;
- evidence-grade promotion;
- artifact/PDF downloads;
- EduBecas/downstream writes;
- runtime, systemd, timer, cap, or Hermes changes;
- direct mutation of the VPS SQLite DB.

## Baseline

BON had upstream metadata but was not accepted by `find-source-candidates`:

```text
official-sources find-source-candidates --source BON ...
error: argument --source: invalid choice: 'BON'
```

Read-only VPS SQLite state:

```text
source=BON
official_documents=46
first_date=2026-06-05
latest_date=2026-06-05
html_urls=46
xml_urls=0
pdf_urls=0
document_files=0
raw_files=0
integrity_checks=0
```

Observed live title-scan signal:

- one student-facing Universidad Pública de Navarra scholarship call;
- public education appointments and director designations;
- university research hiring and administrative staff selection;
- social/dependency aid outside education;
- training-center subsidies for unemployed people;
- university prize notice, kept out of aid preview;
- admission/list/procedure notices;
- environmental and local-government noise.

## Change

Added:

- `BON` as an accepted source for `find-source-candidates`;
- `bon-ayudas` as a documented source-specific profile;
- direct BON education-aid title signals:
  - `becas para estudiantes`;
  - `estudiantes que se matriculen`;
  - `estudios de grado`;
  - `olimpiadas academicas`;
- BON-specific exclusions for non-student-facing notices:
  - appointments, dismissals, public employment and staff-selection notices;
  - research hiring;
  - social/dependency aid;
  - training-center subsidies for unemployed people;
  - prize/TFE notices;
  - admission/list/procedure notices;
  - environmental and local-government notices.

## Validation

Focused regression:

```text
python -m pytest tests/test_cli.py -k bon_profile -q
1 passed, 114 deselected
```

CLI regression:

```text
python -m pytest tests/test_cli.py -q
115 passed
```

Full repository tests:

```text
python -m pytest -q
823 passed, 2 warnings
```

Diff hygiene:

```text
git diff --check
passed
```

Post-change dry-run against a local copy of the VPS SQLite DB, with `PYTHONPATH=src` to force the
worktree code:

```text
documents_scanned=46
source=BON
matches_total=25
matches_after_filters=1
documents_matched=1
candidates_created=0
write_mode=dry_run
excluded_by_keyword_rules=24
```

Preserved candidate:

- `BON:2026.109.23`: Universidad Pública de Navarra scholarships for students enrolling in degree
  studies and selected for academic olympiads.

Artifact/integrity status for the preserved dry-run set:

- 1/1 has official BON HTML URL from the metadata monitor;
- 0/1 has `document_files`;
- 0/1 has PDF URL.

## Decision

```text
TASK-OFFICIAL-SOURCES-BON-CANDIDATE-QUALITY-DRY-RUN-001: DONE
Validation: GO
Candidate writes: 0
Evidence-grade writes: 0
Artifact/PDF downloads: 0
Downstream writes: 0
Runtime/systemd/timer changes: 0
```

BON is now supported by a clean source-specific dry-run profile for EduBecas review. Downstream
EduBecas preview should remain blocked until a separate upstream artifact-integrity task persists
HTML snapshot artifacts or another evidence-grade artifact path for the preserved BON document.
