# BOPA Candidate Quality Dry-run

Date: 2026-06-15
Task: `TASK-OFFICIAL-SOURCES-BOPA-CANDIDATE-QUALITY-DRY-RUN-001`

## Scope

Add BOPA support to the generic `find-source-candidates` dry-run path for EduBecas-style
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

BOPA had upstream metadata but was not accepted by `find-source-candidates`:

```text
official-sources find-source-candidates --source BOPA ...
error: argument --source: invalid choice: 'BOPA'
```

Read-only VPS SQLite state:

```text
source=BOPA
official_documents=50
first_date=2026-06-05
latest_date=2026-06-05
html_urls=50
xml_urls=0
pdf_urls=0
document_files=0
```

Observed live title-scan signal:

- real student-facing Universidad de Oviedo aid/scholarship calls;
- university collaboration/convenio noise;
- research hiring and technical staff noise;
- local/social-service aid noise;
- agrarian subsidy noise;
- public-sector education staffing/provision notices.

## Change

Added:

- `BOPA` as an accepted source for `find-source-candidates`;
- `bopa-ayudas` as a documented source-specific profile;
- direct BOPA education-aid title signals:
  - `ayudas a estudiantes`;
  - `beca de colaboracion`;
  - `campamentos geologicos`;
  - `campeonatos universitarios`;
  - `equipos deportivos`;
- BOPA-specific exclusions for non-student-facing notices:
  - university convenios and industrial doctoral thesis collaboration;
  - early-opening/user-register/social-service aid notices;
  - public education staffing and service-commission notices;
  - agrarian subsidies;
  - municipal/entity operating subsidies;
  - public-employment/talleres notices;
  - research hiring and technical support staff notices.

## Validation

Focused regression:

```text
python -m pytest tests/test_cli.py -k bopa_profile -q
1 passed, 112 deselected
```

CLI regression:

```text
python -m pytest tests/test_cli.py -q
113 passed
```

Full repository tests:

```text
python -m pytest -q
821 passed, 2 warnings
```

Post-change dry-run against a local copy of the VPS SQLite DB, with `PYTHONPATH=src` to force the
worktree code:

```text
documents_scanned=50
source=BOPA
matches_total=33
matches_after_filters=3
documents_matched=3
candidates_created=0
write_mode=dry_run
excluded_by_keyword_rules=30
```

Preserved candidate families:

- `BOPA:2026-04555`: Universidad de Oviedo aid for students to fund geology camp accommodation;
- `BOPA:2026-04561`: Universidad de Oviedo collaboration scholarship for linguistic-normalization services;
- `BOPA:2026-04572`: Universidad de Oviedo aid for sports teams/university championships.

Artifact/integrity status for the preserved dry-run set:

- 3/3 have official BOPA HTML URLs from the metadata monitor;
- 3/3 have monitor `entry_hash` values in `raw_metadata_json`;
- 0/3 have `document_files`;
- 0/3 have PDF URLs.

## Decision

```text
TASK-OFFICIAL-SOURCES-BOPA-CANDIDATE-QUALITY-DRY-RUN-001: DONE
Validation: GO
Candidate writes: 0
Evidence-grade writes: 0
Artifact/PDF downloads: 0
Downstream writes: 0
Runtime/systemd/timer changes: 0
```

BOPA is now supported by a clean source-specific dry-run profile for EduBecas review. Downstream
EduBecas preview should remain blocked until a separate upstream artifact-integrity task persists
HTML snapshot artifacts or another evidence-grade artifact path for the preserved BOPA documents.
