# BOE candidate evidence review model - 2026-05-17

## Summary

TASK-004D added a separate operational evidence review model for BOE source candidates and
documented an explicit PDF-on-demand policy.

This task did not approve candidates, publish anything, write to downstream projects, add a
public API, expose MCP publicly, add legal classification, use LLM review, use RAG, or download
PDFs.

## Model Changes

Added `candidate_evidence_reviews` as a separate operational table.

The table stores:

- current evidence review status;
- operational evidence label;
- notes;
- selected-for-evidence and selected-for-PDF decisions;
- XML/HTML/PDF availability snapshots;
- integrity warning snapshot;
- reviewer and timestamp metadata.

Allowed `evidence_review_status` values:

- `not_reviewed`
- `evidence_selected`
- `evidence_downloaded`
- `evidence_reviewed`
- `needs_more_evidence`
- `false_positive`
- `out_of_scope`

Allowed `evidence_label` values:

- `likely_relevant`
- `unclear`
- `false_positive`
- `out_of_scope`

`source_candidates.review_status` remains publication-safe. The evidence commands do not move
it away from `human_review_required`.

## Migration Result

Local migration validation result:

```text
current_version=7
latest_version=7
status=valid
```

Added migration:

```text
0007_candidate_evidence_reviews
```

## Evidence Commands

Added read-only evidence status command:

```bash
official-sources candidate-evidence-status --candidate-ids 1,3,10
official-sources candidate-evidence-status --date-from YYYY-MM-DD --date-to YYYY-MM-DD --profile la-ayuda
```

Output includes:

- `candidate_id`
- `official_identifier`
- `title`
- `review_status`
- `evidence_review_status`
- `evidence_label`
- `xml_available`
- `html_available`
- `pdf_available`
- `integrity_warning`
- `selected_for_pdf`
- `official_url`

The command does not print full legal text by default.

Added safe operational marking command:

```bash
official-sources mark-candidate-evidence \
  --candidate-id ID \
  --evidence-label likely_relevant \
  --evidence-review-status evidence_downloaded \
  --notes "XML/HTML downloaded for evidence review"
```

The command records evidence review metadata only. It does not approve the candidate and does
not write outside the local `official-sources` database.

## Candidate Evidence Statuses

Pilot context before this task:

```text
date_range=2026-04-18..2026-05-17
source_documents=3896
candidates_created=25
review_status_distribution=human_review_required:25
likely_relevant=10
unclear=13
false_positive=2
selected_for_evidence=1,3,10,11,14,17,18,20,21,23
xml_downloaded=10
html_downloaded=10
pdf_downloaded=0
artifact_http_status_summary=html:200:10,xml:200:10
```

Known false-positive candidate IDs from the pilot report:

```text
false_positive=19,22
```

The local code supports recording these labels. The VPS marking step was not completed because
the configured SSH host did not contain the expected `official-sources` deployment or database.

## PDF Policy

PDF is on-demand.

Rules implemented and documented:

- PDF is never downloaded by default.
- PDF requires explicit `--candidate-ids` or `--document-ids`.
- PDF is rejected for date-scoped downloads.
- PDF must not be downloaded for all candidates automatically.
- PDF must not be downloaded for all documents in a date range automatically.
- PDF should normally be used only for likely relevant candidates, final evidence selection,
  official PDF validation, or direct human review requests.
- PDF downloads create normal `artifact_download_attempts` rows.
- PDF integrity is tracked like other `document_files`.

Supported explicit command:

```bash
official-sources download-boe-artifacts --candidate-ids 1,3,10 --types pdf
```

## Downstream Contract

`docs/DOWNSTREAM_CONTRACT.md` now documents candidate evidence metadata:

```json
{
  "candidate": {
    "candidate_id": 1,
    "review_status": "human_review_required",
    "evidence_review_status": "evidence_downloaded",
    "evidence_label": "likely_relevant"
  },
  "evidence": {
    "xml_available": true,
    "html_available": true,
    "pdf_available": false,
    "pdf_policy": "on_demand",
    "integrity_warning": false
  }
}
```

Documented interpretation:

- downstream projects can consume evidence metadata;
- downstream projects must still create and maintain their own review workflow;
- `likely_relevant is not approval`;
- `false_positive` is operational review, not a legal conclusion;
- PDF absence does not mean evidence is invalid;
- PDF presence does not mean candidate is approved.

## Local Validation

Local validation completed successfully:

```text
rtk python -m pytest -q
206 passed

rtk python -m ruff check .
All checks passed

rtk python -m ruff format --check .
58 files already formatted
```

## VPS Follow-up

Attempted target: the configured private SSH alias.

Observed blocker:

- `/opt/official-sources/app` was not present.
- No `official-sources` user was present.
- No `official-sources` systemd units were present.
- No `official_sources.sqlite` or `official-sources.sqlite` database was found in scoped
  searches.
- No Docker container or volume with an `official` source name was present.
- Existing official-looking service names belonged to the separate `esdata` application.

No VPS migration was run.

No candidate labels were recorded on the VPS.

No false-positive labels were recorded on the VPS.

No PDF downloads were run.

No downstream writes were performed.

## DB Validation

Local DB validation passed through the test suite and migration tests.

VPS DB validation was not run because the expected deployment/database was not found on the
available SSH target.

## Artifact Size

Pilot context:

```text
artifact_size_before=22M
artifact_size_after=23M
```

This task did not download additional artifacts locally or on the VPS.

## MCP Privacy

No MCP server code path was changed.

Existing tests still verify that MCP tools do not perform artifact downloads and that docs do
not instruct public MCP exposure.

The available VPS target did not show an `official-sources`, MCP, Python, Uvicorn, or FastMCP
listener associated with this project during investigation.

## Known Limitations

- The evidence model stores one current evidence review row per candidate. It does not keep a
  full event history.
- Availability status is derived from current `document_files` in read paths; stored
  availability columns are snapshots from the last evidence mark.
- VPS operational marking remains pending until the correct deployment host/path/database is
  confirmed.
- The two known false-positive labels remain pending on the VPS for the same reason.
- PDF signature validation is still not implemented; PDF files are hashed and audited only.

## Next Recommended Task

TASK-004D-FOLLOWUP1: confirm the correct VPS deployment target and database path, then run:

```bash
official-sources db migrate
official-sources db validate
official-sources mark-candidate-evidence --candidate-id 1 --evidence-label likely_relevant --evidence-review-status evidence_downloaded
official-sources candidate-evidence-status --candidate-ids 1,3,10,11,14,17,18,20,21,23
official-sources db validate
```

Do not download PDFs during that follow-up unless explicitly authorized.
