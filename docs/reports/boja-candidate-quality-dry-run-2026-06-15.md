# BOJA Candidate Quality Dry-run

Date: 2026-06-15
Task: `TASK-OFFICIAL-SOURCES-BOJA-CANDIDATE-QUALITY-DRY-RUN-001`

## Scope

Improve BOJA `boja-ayudas` dry-run quality for EduBecas-style education-aid review.

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
documents_scanned=1500
source=BOJA
matches_total=372
matches_after_filters=36
documents_matched=36
candidates_created=0
write_mode=dry_run
```

Observed noise in the 36 dry-run matches:

- public employment and selection notices, including disability/public-selection context;
- FPE notification notices where a grant/benefit term appeared in a non-reviewable notice;
- youth housing/rent notices without student context;
- education procedure notices such as B2 certificate and admission lottery/procedure records;
- resolved scholarship notices that are not activable calls.

## Change

Tightened the BOJA-specific `boja-ayudas` profile without changing the shared autonomous profile for
BOA, DOGC, BOPV, BORM, or other CCAA sources.

The BOJA branch keeps:

- student-facing university scholarship and aid calls;
- school/FP student mobility or stay calls;
- official BOJA education-aid notices with direct student/alumnado context.

The BOJA branch excludes:

- broad `discapacidad`, `joven`, and `jovenes` keyword matches without education-aid context;
- public employment and selection notices;
- FPE notification/subsanacion/archive notices;
- non-student housing/rent notices;
- education procedure notices that do not create aid opportunities;
- resolved scholarship notices where the title indicates an already closed resolution.

## Validation

Focused regression:

```text
python -m pytest tests/test_cli.py -k boja_profile -q
5 passed, 107 deselected
```

CLI regression:

```text
python -m pytest tests/test_cli.py -q
112 passed
```

Full repository tests:

```text
python -m pytest -q
820 passed, 2 warnings
```

Post-change dry-run against a local copy of the VPS SQLite DB, with `PYTHONPATH=src` to force the
worktree code:

```text
documents_scanned=1500
source=BOJA
matches_total=364
matches_after_filters=5
documents_matched=5
candidates_created=0
write_mode=dry_run
excluded_by_keyword_rules=359
```

Preserved candidate families:

- `BOJA:disposition.2026.95.6`: UHU Master talent scholarships for students;
- `BOJA:disposition.2026.94.5`: UHU Campus Rural external-practice aid for university students;
- `BOJA:disposition.2026.92.1`: EU stays call for FP and arts/design pupils;
- `BOJA:disposition.2026.90.5`: UPO/Santander economic aid scholarships for degree/master students;
- `BOJA:disposition.2026.78.70`: Fundacion Malaga Becas Talento call, BOJA announcement snapshot only.

Artifact status for the preserved dry-run set:

- 4/5 preserved documents have BOJA PDF URLs with `document_files` PDF hashes and integrity checks;
- 5/5 have BOJA API snapshot hashes and integrity checks;
- `BOJA:disposition.2026.78.70` is limited to the BOJA API snapshot in the current SQLite copy and should stay manual-review only until a direct artifact URL is confirmed.

## Decision

```text
TASK-OFFICIAL-SOURCES-BOJA-CANDIDATE-QUALITY-DRY-RUN-001: DONE
Validation: GO
Candidate writes: 0
Evidence-grade writes: 0
Artifact/PDF downloads: 0
Downstream writes: 0
Runtime/systemd/timer changes: 0
```

BOJA is now a cleaner dry-run source for EduBecas-style educational aid review. The downstream
EduBecas side can create a no-write preview package from the preserved BOJA evidence, but should
still avoid writes until a scoped staging/import task explicitly widens the contract.
