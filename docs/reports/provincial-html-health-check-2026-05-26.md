# Provincial HTML health check - 2026-05-26

Task: `TASK-SOURCE-PROVINCIAL-HTML-HEALTH-001`

## Scope

This report checks the currently validated provincial HTML discovery monitors:

- `BOP_A_CORUNA`
- `BOP_ALBACETE`
- `BOP_ALICANTE`

The check used source-tree CLI commands with `PYTHONPATH=src`, date `2026-05-25`, `--limit 1`,
and preview mode only. No `--write` flag was used.

## Registry status sanity

| Source | operational_status | monitor_support | candidate_creation_allowed | evidence_grade_allowed |
| --- | --- | --- | --- | --- |
| `BOP_A_CORUNA` | `monitor_validated` | `available` | `false` | `false` |
| `BOP_ALBACETE` | `monitor_validated` | `available` | `false` | `false` |
| `BOP_ALICANTE` | `monitor_validated` | `available` | `false` | `false` |

## Preview results

| Source | Date | Records | First document_id | First official_url | Warnings |
| --- | --- | ---: | --- | --- | --- |
| `BOP_A_CORUNA` | `2026-05-25` | 1 | `2026/3193` | `https://bop.dacoruna.gal/bopportal/2026_0000003193.html` | none |
| `BOP_ALBACETE` | `2026-05-25` | 1 | `297598` | `https://bop.dipualba.es/servicesajax/descargararchivopaginaBOP/297598` | `pdf_endpoint_not_downloaded` |
| `BOP_ALICANTE` | `2026-05-25` | 1 | `3923` | `https://www.dip-alicante.es/bop2/pdftotal/2026/05/25_96/2026_003923.pdf` | `pdf_endpoint_not_downloaded` |

Each returned preview record retained the metadata-only safety fields:

- `candidate_status=not_candidate`
- `evidence_status=not_evidence`
- `classification_status=unclassified`

## Output check

No JSONL output was written. The check did not use `--write`, and no `data/html_monitor` JSONL
files were found after the previews.

## Health assessment

The health check passed for all three current provincial HTML monitors:

- `BOP_A_CORUNA` remains healthy on a date-scoped HTML page.
- `BOP_ALBACETE` remains healthy for its current-bulletin scoped surface; the PDF-like endpoint is
  recorded only as metadata and was not downloaded.
- `BOP_ALICANTE` remains healthy for the tested date; the PDF URL is recorded only as metadata and
  was not downloaded.

No parser behavior was changed.

## Safety confirmation

This task did not:

- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- write RSS/API/HTML JSONL;
- run backfills;
- run broad or all-source discovery;
- touch downstream repositories;
- run VPS or production DB operations;
- add LLM classification;
- add new sources.

## Next recommendation

After this report is merged, `TASK-SOURCE-PROVINCIAL-DISCOVERY-003` can evaluate at most two more
provincial sources using the pattern-report criteria. The next expansion should remain
metadata-only, preview-first, and source-specific unless repeated duplication justifies small shared
helpers.
