# BOCYL Candidate Batch Preflight - 2026-05-21

## Scope

This preflight prepares a limited BOCYL candidate creation batch from the stored
30-day metadata window.

Rules for this preparation:

- do not connect to the VPS;
- do not create candidates;
- do not use `--write`;
- do not touch any real database;
- do not download PDF/XML/HTML artifacts;
- do not write downstream evidence;
- do not modify unrelated sources.

## Inputs Reviewed

Reports:

- `docs/reports/BOCYL_30_DAY_METADATA_BACKFILL_2026-05-21.md`
- `docs/reports/BOCYL_30_DAY_CANDIDATE_DRY_RUN_2026-05-21.md`
- `docs/reports/BOCYL_CANDIDATE_PROFILE_REFINEMENT_2026-05-21.md`

Code and tests:

- `src/official_sources/cli.py`
- `tests/test_cli.py`

## Test Coverage Check

Existing tests cover the required safety surface:

| Requirement | Status |
| --- | --- |
| `find-source-candidates --source BOCYL` | covered |
| `bocyl-ayudas` profile | covered |
| `vivienda` in department name does not overmatch | covered |
| environmental / urban planning noise excluded | covered |
| dry-run does not write | covered |
| write mode requires explicit `--write` | covered by shared candidate command path |

No additional tests are required for this preflight.

## Prior Dry-Run Result

Input window:

```text
source_code=BOCYL
date_range=2026-04-21 -> 2026-05-20
BOCYL official_documents=773
```

Refined profile dry-run:

| metric | value |
| --- | ---: |
| documents scanned | 773 |
| matches total before filters | 435 |
| matches after filters | 21 |
| documents matched | 21 |
| candidates created | 0 |
| excluded by keyword rules | 414 |
| match rate after filters | 2.72% |

Expected limited batch size:

```text
expected_candidates_created=21
upper_bound_with_limit_25=21
```

The expected count assumes the production database still contains the same BOCYL
30-day metadata window and no existing BOCYL candidates for these matched
documents. If existing candidates are present, the command should skip them and
create fewer than 21.

## Recommended Supervisor Command

Run only after a fresh database backup and validation on the operational host:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BOCYL \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile bocyl-ayudas \
  --project-key bocyl-ayudas \
  --write \
  --limit 25
```

This is intentionally limited to metadata-only candidate creation. It must not
be combined with artifact download, evidence export, downstream writes, or any
approval/publication step.

## Required Backups

Before the write command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output /opt/official-sources/data/backups/official_sources_before_bocyl_candidate_batch_20260521.sqlite
```

After the write command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate

/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db backup \
  --output /opt/official-sources/data/backups/official_sources_after_bocyl_candidate_batch_20260521.sqlite
```

Record both backup paths in the final operational report.

## Safety Checks

Before running the write command, confirm:

- deployed CLI includes `find-source-candidates --source BOCYL`;
- deployed CLI includes `--profile bocyl-ayudas`;
- database validation returns `valid`;
- BOCYL document count is still `773` for `2026-04-21 -> 2026-05-20`;
- `source_candidates` count is recorded before the run;
- artifact download attempt count and artifact directory size are recorded
  before the run;
- no MCP or downstream service is exposed for this task.

During the run, confirm:

- command output reports `source=BOCYL`;
- command output reports `profile=bocyl-ayudas`;
- command output reports `write_mode=write`;
- `candidates_created` is no more than `21`;
- all created candidates remain `human_review_required`;
- no artifact download command is invoked.

After the run, confirm:

- database validation still returns `valid`;
- `source_candidates` increased by the reported `candidates_created` count;
- BOCYL official document count remains unchanged;
- artifact download attempt count remains unchanged;
- artifact directory size remains unchanged;
- no downstream evidence files are exported;
- no candidate is approved or published.

## Stop Conditions

Stop immediately and do not continue with downstream work if any condition is
observed:

- database validation fails before or after the command;
- BOCYL source/profile is not available in the deployed CLI;
- dry-run expectations are not reproducible before write mode;
- command scans a date range other than `2026-04-21 -> 2026-05-20`;
- command reports `candidates_created > 21`;
- command creates candidates outside BOCYL;
- any artifact download attempt count changes;
- artifact directory size changes unexpectedly;
- any candidate is created with a review status other than
  `human_review_required`;
- any downstream export, approval, publication, or MCP exposure occurs.

## Final Operational Report

Write the final operational report to:

```text
docs/reports/BOCYL_CANDIDATE_BATCH_OPERATIONAL_2026-05-21.md
```

The report must include:

- exact deployed commit;
- exact command run;
- pre-run and post-run database validation output;
- pre-run and post-run backup paths;
- before/after counts for BOCYL official documents, `source_candidates`,
  artifact download attempts, and artifact directory size;
- candidate creation count and skipped-existing count if reported;
- sampled created candidate identifiers;
- confirmation that no artifacts, downstream files, approvals, publications, or
  MCP exposure occurred;
- any stop condition encountered, or explicit confirmation that none occurred.
