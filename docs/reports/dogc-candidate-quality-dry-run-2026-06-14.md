# DOGC Candidate Quality Dry-run

Date: 2026-06-14
Task: `TASK-OFFICIAL-SOURCES-DOGC-CANDIDATE-QUALITY-DRY-RUN-001`

## Scope

Improve DOGC `dogc-ayudas` dry-run quality for EduBecas-style education-aid review.

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

Live VPS dry-run before the rule change:

```text
documents_scanned=279
matches_total=95
matches_after_filters=4
documents_matched=4
candidates_created=0
write_mode=dry_run
```

Observed dry-run matches:

- comedor escolar / menjador aid for compulsory and early-childhood pupils;
- mobility grants for young students;
- public employment/selection notice that matched only because the title mentioned vulnerable young people;
- internal institutional practice scholarships for the Department of Language Policy.

## Change

Added DOGC-specific `dogc-ayudas` exclusion logic without changing shared BOPV, BOA, or BORM behavior.

The DOGC branch keeps:

- `ajuts individuals de menjador` / comedor-school aid;
- student mobility grants for young students.

The DOGC branch excludes:

- public employment and selection notices in Catalan (`oferta publica d'ocupacio`, `proces de seleccio`, `llista d'admissions`, `personal laboral fix`);
- internal/institutional practice scholarships (`beques per fer practiques al Departament`, `entitats adscrites`, OSIC-style practice grants).

## Validation

Baseline targeted tests before the change:

```text
python -m pytest tests/test_dogc_adapter.py tests/test_cli_dogc.py tests/test_cli.py -q
123 passed
```

Focused regression after the change:

```text
python -m pytest tests/test_cli.py::test_find_source_candidates_dogc_profile_filters_selection_and_internal_practice_noise tests/test_cli.py::test_find_source_candidates_supports_new_autonomous_profiles_and_filters_noise -q
2 passed
```

Targeted tests after the change:

```text
python -m pytest tests/test_dogc_adapter.py tests/test_cli_dogc.py tests/test_cli.py -q
124 passed
```

Post-change dry-run against a local copy of the VPS SQLite DB, with `PYTHONPATH=src` to force the
worktree code:

```text
documents_scanned=279
matches_total=95
matches_after_filters=2
documents_matched=2
candidates_created=0
write_mode=dry_run
excluded_by_keyword_rules=93
```

Preserved candidates:

- `DOGC:CVE-DOGC-A-26145019-2026`: `ajuts individuals de menjador` for pupils;
- `DOGC:CVE-DOGC-A-26149058-2026`: individual mobility scholarships for young students.

## Decision

```text
TASK-OFFICIAL-SOURCES-DOGC-CANDIDATE-QUALITY-DRY-RUN-001: DONE
Validation: GO
Candidate writes: 0
Evidence-grade writes: 0
Artifact/PDF downloads: 0
Downstream writes: 0
Runtime/systemd/timer changes: 0
```

DOGC is now a cleaner dry-run source for EduBecas-style educational aid review. The downstream
EduBecas side can create a no-write preview package from the two preserved DOGC documents, but
should still avoid writes until a scoped staging/import task explicitly widens the contract.

