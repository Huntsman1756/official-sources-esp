# DOCM Candidate Quality Dry-run

Date: 2026-06-14
Task: `TASK-OFFICIAL-SOURCES-DOCM-CANDIDATE-QUALITY-DRY-RUN-001`

## Scope

Add DOCM support to the generic `find-source-candidates` dry-run path for EduBecas-style
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

Before this task, DOCM was present as HTML-monitor metadata in the live SQLite DB, but the generic
candidate finder rejected it:

```text
official-sources find-source-candidates: error: argument --source: invalid choice: 'DOCM'
```

Read-only upstream counters:

```text
DOCM official_documents: 32
min_date: 2026-06-05
max_date: 2026-06-05
html_url: 32
xml_url: 0
pdf_url: 0
```

Observed candidate-like DOCM titles included:

- real education-aid signal: correction of bases for individual school-transport aid for non-university pupils;
- non-student-facing noise: entrepreneurship support, social-aid notifications, public/local employment or licensing notices;
- university internal collaboration scholarships.

## Change

Added:

- `DOCM` as a supported `find-source-candidates` source;
- `docm-ayudas` profile;
- `ensure_official_source_docm` for deterministic tests;
- DOCM-specific quality rules.

The DOCM branch keeps:

- individual school-transport aid;
- direct education-aid signals for pupils/students, material, comedor, or study aid.

The DOCM branch excludes:

- entrepreneurship/business support;
- social-aid notification rows;
- urbanism, environment, procurement and public-employment/local notices;
- internal university collaboration scholarships.

## Validation

Baseline targeted tests before the change:

```text
python -m pytest tests/test_cli.py -q
109 passed
```

Focused regression after the change:

```text
python -m pytest tests/test_cli.py::test_find_source_candidates_docm_profile_filters_non_student_facing_noise tests/test_cli.py::test_find_source_candidates_supports_new_autonomous_profiles_and_filters_noise -q
2 passed
```

Targeted CLI tests after the change:

```text
python -m pytest tests/test_cli.py -q
110 passed
```

Post-change dry-run against a local copy of the VPS SQLite DB, with `PYTHONPATH=src` to force the
worktree code:

```text
documents_scanned=32
matches_total=18
matches_after_filters=1
documents_matched=1
candidates_created=0
write_mode=dry_run
excluded_by_keyword_rules=17
```

Preserved candidate:

- `DOCM:2026/4175`: correction of bases for individual school-transport aid for pupils in public
  non-university schools in Castilla-La Mancha.

## Decision

```text
TASK-OFFICIAL-SOURCES-DOCM-CANDIDATE-QUALITY-DRY-RUN-001: DONE
Validation: GO
Candidate writes: 0
Evidence-grade writes: 0
Artifact/PDF downloads: 0
Downstream writes: 0
Runtime/systemd/timer changes: 0
```

DOCM is now usable as a read-only dry-run source for EduBecas-style educational aid review. The
downstream EduBecas side can create a no-write preview package from the one preserved DOCM document,
but should still avoid writes until a scoped staging/import task explicitly widens the contract.

