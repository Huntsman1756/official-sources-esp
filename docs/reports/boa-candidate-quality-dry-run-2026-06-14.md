# BOA Candidate Quality Dry-run

Date: 2026-06-14
Task: `TASK-OFFICIAL-SOURCES-BOA-CANDIDATE-QUALITY-DRY-RUN-001`

## Scope

Improve BOA `boa-ayudas` dry-run quality after the metadata catch-up and URL mapping verification.

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
documents_scanned=1384
matches_total=833
matches_after_filters=21
documents_matched=21
candidates_created=0
write_mode=dry_run
```

Observed noise in the 21 dry-run matches:

- youth/general-social notices: young creators award, youth leisure activities, young volunteers;
- non-student social support: early-childhood care direct payments to families;
- internal/institutional scholarships: Consejo Economico y Social training/practice grant;
- administrative notices: renunciation of language assistant grant beneficiary;
- non-aid education administration: admission/matriculation calendar;
- organisation-facing support: university student associations grants.

## Change

Added BOA-specific `boa-ayudas` exclusion logic without changing the shared autonomous profile for
BOPV, BORM, or DOGC.

The BOA branch keeps:

- material curricular aid;
- comedor escolar grants;
- Erasmus and international mobility scholarships;
- BOA housing/person-context matches preserved by the existing autonomous contract.

The BOA branch excludes:

- non-student-facing youth/social notices;
- internal practice scholarships;
- administrative renunciation notices;
- admission calendar notices;
- student-association organisation grants.

## Validation

Targeted tests:

```text
python -m pytest tests/test_boa_adapter.py tests/test_cli_boa.py tests/test_cli.py -q
122 passed
```

Focused regression:

```text
python -m pytest tests/test_cli.py::test_find_source_candidates_supports_new_autonomous_profiles_and_filters_noise tests/test_cli.py::test_find_source_candidates_boa_profile_filters_non_student_facing_noise -q
2 passed
```

Whitespace:

```text
git diff --check
OK
```

Post-change dry-run against a local copy of the VPS SQLite DB, with `PYTHONPATH=src` to force the
worktree code:

```text
documents_scanned=1384
matches_total=833
matches_after_filters=8
documents_matched=8
candidates_created=0
write_mode=dry_run
excluded_by_keyword_rules=825
matches_by_department=DEPARTAMENTO_DE_EDUCACION,_CIENCIA_Y_UNIVERSIDADES:8
```

Preserved candidate families:

- `2026-06-05`: material curricular call and extract;
- `2026-06-05`: comedor escolar call and extract;
- `2026-06-05`: Erasmus/international mobility extract;
- `2026-05-26`: comedor escolar correction;
- `2026-05-19`: material curricular bases;
- `2026-05-19`: comedor escolar bases.

## Decision

```text
TASK-OFFICIAL-SOURCES-BOA-CANDIDATE-QUALITY-DRY-RUN-001: DONE
Validation: GO
Candidate writes: 0
Evidence-grade writes: 0
Artifact/PDF downloads: 0
Downstream writes: 0
Runtime/systemd/timer changes: 0
```

BOA is now a cleaner dry-run source for EduBecas-style educational aid review. The next loop can
evaluate a no-write downstream evidence preview from these eight BOA documents, but should still
avoid source candidate writes until a scoped task explicitly authorizes them.
