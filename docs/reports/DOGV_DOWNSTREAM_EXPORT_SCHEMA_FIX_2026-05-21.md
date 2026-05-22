# DOGV Downstream Export Schema Fix - 2026-05-21

## Summary

TASK-AUTO-DOGV-012B aligned the DOGV downstream evidence export with the common downstream
contract used by `la-ayuda`.

Root cause:

```text
DOGV downstream exports omitted the required top-level version_date field.
la-ayuda correctly rejected candidate 117 preview with: Missing or invalid version_date.
```

Fix:

```json
"version_date": null
```

DOGV does not currently expose a distinct version date for the exported official-document evidence,
so `null` is the explicit contract-compatible value.

## Files Changed

```text
src/official_sources/downstream_export.py
src/official_sources/cli.py
tests/test_downstream_export.py
docs/examples/downstream_evidence_contract.example.json
docs/reports/DOGV_DOWNSTREAM_EXPORT_SCHEMA_FIX_2026-05-21.md
```

## Export Fields Fixed

The downstream evidence export now includes:

```text
version_date=null
citation.version_date=null
```

The export also preserves:

```text
source_code
resource_type
official_identifier
title
publication_date
official_url
citation
integrity
artifacts
official_sources_candidate
```

No raw PDF text, raw XML, raw HTML, local artifact paths, secrets, downstream writes, candidate
creation, approvals, or publication behavior are introduced by this change.

## Command Added

```bash
official-sources export-downstream-evidence \
  --candidate-ids 101,102,103,104,106,108,109,111,117,124 \
  --output-dir /opt/official-sources/data/downstream_exports/2026-05-21/dogv
```

The command writes one JSON per candidate and groups output by `downstream_project_fit`.

Expected groups for the DOGV batch:

```text
eduayudas/
la-ayuda/
```

## Tests Added

Coverage added for:

```text
DOGV export includes version_date
version_date may be null
citation.version_date is present
BOE/BOJA exports keep the same nullable contract
exported JSON preserves integrity hashes
exported JSON omits local paths and raw PDF text
CLI export writes grouped JSON with version_date
```

## Local Validation

Completed locally:

```text
git diff --check: OK
rtk python -m pytest -q: 327 passed
rtk python -m ruff check .: OK
rtk python -m ruff format --check .: OK
```

## Regenerated Export Files

To be completed on the VPS after deployment:

```text
/opt/official-sources/data/downstream_exports/2026-05-21/dogv/eduayudas/
/opt/official-sources/data/downstream_exports/2026-05-21/dogv/la-ayuda/
```

Target candidates:

```text
101,102,103,104,106,108,109,111,117,124
```

## la-ayuda Retry Readiness

After successful deployment and regeneration, DOGV candidate `117` can be copied again into
`la-ayuda` and retried with:

```text
TASK-AUTO-DOGV-012C - Rerun DOGV candidate 117 preview in la-ayuda
```

## Known Limitations

This change fixes the evidence contract shape only. It does not extract normalized downstream
benefit fields such as amount, eligibility, deadline, application channel, or documentation
requirements.
