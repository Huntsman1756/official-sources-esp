# BOPV Evidence Download Preflight - 2026-05-24

## Scope

Prepared the next BOPV/EHAA selected evidence download.

This was a local documentation-only preflight. No VPS connection was made, no artifacts were
downloaded, no database writes were performed, and no downstream project was touched.

## Inputs Reviewed

- `docs/reports/BOPV_30_DAY_CANDIDATE_BATCH_2026-05-23.md`
- `docs/reports/BOPV_30_DAY_CANDIDATE_TRIAGE_2026-05-23.md`
- `docs/reports/BOPV_CANDIDATE_PROFILE_DRY_RUN_2026-05-23.md`
- `docs/reports/BOPV_CANDIDATE_PROFILE_CALIBRATION_2026-05-23.md`
- `src/official_sources/sources/bopv/client.py`
- `src/official_sources/sources/bopv/parser.py`
- `src/official_sources/sources/bopv/ingestion.py`
- `src/official_sources/cli.py`

## Target Candidates

Selected by the metadata-only BOPV triage:

```text
candidate_ids=147,149,150
```

Candidate context:

| Candidate ID | Official identifier | Publication date | Triage classification | Evidence action |
| ---: | --- | --- | --- | --- |
| 147 | `BOPV:BOPV-2026-05-2602039a` | 2026-05-15 | `unclear` | `download_xml_or_html` |
| 149 | `BOPV:BOPV-2026-04-2601788a` | 2026-04-30 | `likely_relevant` | `download_xml_or_html` |
| 150 | `BOPV:BOPV-2026-04-2601716a` | 2026-04-24 | `unclear` | `download_xml_or_html` |

Candidate `148` remains excluded from this evidence batch because triage classified it as
`out_of_scope`.

## Evidence Type Recommendation

Preferred evidence type:

```text
xml,html
```

Do not include PDF in the first BOPV evidence download.

Rationale:

- BOPV ingestion already stores official document XML, HTML, and PDF URLs from the official issue
  XML.
- XML is the best first evidence type because it is structured, deterministic, and suitable for
  text extraction and future review automation.
- HTML is a useful official rendering fallback for human review and can catch presentation context
  that may be awkward in XML text extraction.
- PDF should stay deferred because the platform policy is PDF-on-demand only and XML/HTML are
  available for BOPV records.

## Downloader Support Status

Current status:

```text
bopv_downloader_supported=false
implementation_required=true
documentation_only_gap=false
```

Observed support:

- `download-source-artifacts --source` currently accepts `BOE`, `BOJA`, `DOGV`, and `BOCYL`.
- `download-boe-artifacts --source` currently accepts `BOE`, `BOJA`, `DOGV`, and `BOCYL`.
- There is no `BOPVArtifactDownloader`.
- There is no `BOPV_ARTIFACT_FIELDS` map.
- There is no BOPV artifact URL validator.
- `_artifact_downloader_for_source()` falls back to `BOEArtifactDownloader` for unsupported
  sources, but BOPV cannot reach that path because argparse does not accept `--source BOPV`.

Conclusion:

```text
Do not run a BOPV evidence download until scoped BOPV artifact downloader support is implemented
and tested.
```

This is a code support gap, not a documentation-only gap.

## Required Implementation Before Download

Minimum implementation scope for a future task:

- add `BOPV` to the supported `download-source-artifacts --source` choices;
- add a `BOPVArtifactDownloader` that reuses the existing audited artifact downloader behavior;
- add `BOPV_ARTIFACT_FIELDS` for `xml`, `html`, and explicit `pdf`;
- validate BOPV artifact URLs as official `https://www.euskadi.eus/bopv2/datos/...` URLs;
- cache files under `data/artifacts/bopv/YYYY/MM/DD/<external_id>/`;
- require explicit `--candidate-ids` for BOPV in the first implementation;
- reject BOPV date-level downloads;
- reject `--document-ids` initially unless tests explicitly cover that path;
- keep PDF allowed only when explicitly requested and scoped by IDs;
- add tests for source acceptance, candidate scoping, source mismatch rejection, XML/HTML download,
  missing URL skips, and date-level rejection.

## Future Command

After BOPV downloader support exists, the intended scoped command is:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-source-artifacts \
  --source BOPV \
  --candidate-ids 147,149,150 \
  --types xml,html
```

Expected maximum attempts:

```text
3 candidates x 2 artifact types = 6 attempts
```

PDF, if later needed after XML/HTML review, must be a separate scoped command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-source-artifacts \
  --source BOPV \
  --candidate-ids <explicit_ids> \
  --types pdf
```

## Stop Conditions

Stop before any download if:

- the deployed CLI does not accept `download-source-artifacts --source BOPV`;
- selected candidate IDs are not exactly `147,149,150` unless a new triage report updates scope;
- any selected candidate is missing or does not belong to source `BOPV`;
- any selected candidate is no longer `human_review_required`;
- any selected document lacks both `url_xml` and `url_html`;
- BOPV URL validation fails or a URL is not on the official `www.euskadi.eus` host;
- the command would use `--date` or any date-level artifact scope;
- the command would include PDF together with XML/HTML in the first run;
- database validation fails before the operation;
- backup creation fails before the operation;
- MCP or public listener checks show an unexpected official-sources service exposure.

Stop during or after download if:

- more than 6 XML/HTML attempts are recorded;
- any document outside candidates `147,149,150` receives a BOPV XML/HTML file;
- `source_candidates` count changes;
- any `review_status` changes;
- any downstream file or project is touched;
- any artifact is downloaded from a non-official host;
- DB validation fails after the operation.

## Validation and Backups Needed

Before download:

```text
db validate: required
pre-run sqlite backup: required
selected candidate/source/status check: required
selected URL availability check: required
MCP privacy listener check: required
```

After download:

```text
db validate: required
post-run sqlite backup: required
artifact_download_attempts count reconciliation: required
document_files delta reconciliation: required
selected candidate status unchanged check: required
source_candidates unchanged check: required
MCP privacy listener check: required
```

Local implementation validation before deployment:

```text
rtk git diff --check
rtk python -m pytest tests/test_cli.py -q
rtk python -m pytest tests/test_bopv_adapter.py tests/test_cli_bopv.py -q
rtk python -m pytest -q
rtk python -m ruff check .
rtk python -m ruff format --check .
```

## Risks

- BOPV selected candidates `147` and `150` may still be institutional education-center grants, not
  direct citizen/student/family aid.
- Candidate `149` may still benefit special employment centers or employers rather than individuals;
  XML/HTML review must confirm beneficiary and application mechanics.
- BOPV document XML may require source-specific text extraction checks after download; generic XML
  extraction is a good first pass but should not be treated as semantic review.
- Adding BOPV support by falling through to the BOE downloader would be unsafe because BOE URL
  validation only allows BOE hosts.
- Broadening the command to date-level BOPV downloads would exceed the selected-candidate evidence
  scope.

## Next Recommended Task

```text
TASK-AUTO-BOPV-007A - Enable scoped BOPV XML/HTML artifact downloader
```

Recommended scope:

```text
source=BOPV
candidate_ids required
types=xml,html by default
pdf explicit only
no date-level downloads
no downstream
tests first
```

Only after that implementation is merged and deployed should `TASK-AUTO-BOPV-007` run the selected
candidate evidence download.
