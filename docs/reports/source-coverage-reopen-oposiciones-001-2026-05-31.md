# Source Coverage Reopen For Oposiciones

Date: 2026-05-31

Task: `TASK-SOURCE-COVERAGE-REOPEN-OPOSICIONES-001`

## Scope

This task reopens source coverage only for the downstream demand class:

```text
public_employment_alerts
consumer: oposiciones2.0
```

It adds metadata-only provincial HTML discovery support for:

```text
BOP_CASTELLON
BOP_SEVILLA
```

## Registry Change

Current registry counts after this task:

```text
registered sources: 65
metadata_adapter_validated: 9
monitor_validated: 17
inventory_only: 39
monitor_support=available: 26
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Both sources remain non-candidate and non-evidence:

```text
BOP_CASTELLON candidate_creation_allowed=false evidence_grade_allowed=false
BOP_SEVILLA candidate_creation_allowed=false evidence_grade_allowed=false
```

## Source Notes

`BOP_CASTELLON` uses the official current-bulletin HTML page:

```text
https://bop.dipcas.es/PortalBOP/
```

The parser extracts current-page announcement metadata and records PDF endpoints as
`official_url` metadata only. It does not download PDFs.

`BOP_SEVILLA` uses the official public bulletin landing page:

```text
https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/
```

The monitor follows the latest public bulletin detail link and extracts announcement metadata from
that public detail page. It does not download PDFs or artifacts.

## Safety

This task did not:

- create candidates;
- create evidence-grade records;
- download PDFs or artifacts;
- write discovery JSONL by default;
- write downstream repositories;
- run broad backfills;
- change Hermes, systemd, VPS, or production data;
- change `BOP_ALICANTE` runtime status.

`BOP_ALICANTE` remains `degraded/manual-review` and must not be counted in all-green monitored
provincial claims.

## Live Preview Validation

Preview validation was run without `--write`:

```text
python -m official_sources.cli html monitor --source BOP_CASTELLON --date 2026-05-31 --limit 1
python -m official_sources.cli html monitor --source BOP_SEVILLA --date 2026-05-31 --limit 1
```

Results:

| Source | Status | Records | Candidate | Evidence | Classification | Example document |
| --- | --- | ---: | --- | --- | --- | --- |
| `BOP_CASTELLON` | OK | 1 | `not_candidate` | `not_evidence` | `unclassified` | `165893` |
| `BOP_SEVILLA` | OK | 1 | `not_candidate` | `not_evidence` | `unclassified` | `BOP-SE-2026-102001` |

No discovery JSONL was written.

## Next Source Work

The next `oposiciones2.0` public-employment alert candidates should come from the remaining
downstream-demand matrix, not from broad registry completion:

```text
BOP_AVILA
BOP_PONTEVEDRA
BOP_SORIA
BOP_CORDOBA
BOP_GRANADA
BOP_LEON
BOP_PALENCIA
BOP_SALAMANCA
```
