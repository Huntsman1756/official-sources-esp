# BORM Scoped Artifact Downloader

Date: 2026-05-24

Task: `TASK-AUTO-BORM-008B`

Scope: add scoped BORM artifact download support for selected candidates only.

No VPS evidence download was performed as part of the implementation commit. The first operational run must stay scoped to explicit candidate IDs.

## Command Added

`download-source-artifacts` now accepts:

```text
--source BORM
```

Supported BORM artifact type:

```text
pdf
```

Expected operational command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  --artifact-dir /opt/official-sources/data/artifacts \
  download-source-artifacts \
  --source BORM \
  --candidate-ids 151,152,153,154,155,156,157,158,159,161,162,163 \
  --types pdf
```

## Implementation

Added:

```text
src/official_sources/sources/borm/artifacts.py
BORMArtifactDownloader
BORM_ARTIFACT_FIELDS
validate_borm_artifact_url
```

Wired BORM into:

```text
src/official_sources/cli.py
download-source-artifacts --source choices
download-boe-artifacts --source choices
artifact downloader selection
artifact field selection
BORM-specific argument validation
```

## Guardrails

BORM downloads require:

```text
explicit --source BORM
explicit --candidate-ids
explicit --types pdf
```

Rejected:

```text
date-level BORM artifact downloads
document-id BORM artifact downloads
non-BORM candidates under --source BORM
missing pdf_url
unsupported BORM artifact types
invalid hosts
invalid non-service PDF paths
more than 12 BORM candidate IDs
```

URL validation:

```text
scheme=https
host=borm.es or www.borm.es
path starts with /services/anuncio/
path ends with /pdf
```

PDF requests also send explicit official-source headers:

```text
Accept: application/pdf
User-Agent: official-sources/1.0
```

These headers avoid BORM returning an intermediate browser validation page while preserving the final URL host/path validation.

PDF remains explicit and scoped; it is not downloaded by default.

## Tests Added

Added coverage in `tests/test_cli.py` for:

- CLI help lists `BORM`.
- Scoped BORM PDF download uses persisted `pdf_url`.
- Candidate IDs only; unselected BORM documents are not touched.
- Missing `pdf_url` is skipped and audited.
- Non-BORM candidate rejected under `--source BORM`.
- Date-level BORM artifact download rejected.
- Document-ID BORM artifact download rejected.
- Missing explicit `--types pdf` rejected.
- Invalid BORM PDF host rejected.
- Invalid BORM PDF path rejected.
- Official BORM redirects followed.
- BORM PDF requests include explicit PDF and user-agent headers.
- PDF bytes are hashed and stored in `document_files`.
- `artifact_download_attempts` rows are recorded.
- No extra source candidates are created by artifact download.

Existing BOE/BOJA/DOGV/BOCYL behavior remains covered by the full test suite.

## Validation

```text
rtk git diff --check: passed
rtk python -m pytest -q: 434 passed, 1 warning
rtk python -m ruff check .: passed
rtk python -m ruff format --check .: passed
```

## Operational Status

BORM-008 can run after deploying this code to VPS.

Required first-run constraints:

```text
candidate_ids=151,152,153,154,155,156,157,158,159,161,162,163
types=pdf
expected_max_attempts=12
backup before download
DB validation before/after
source_candidates.review_status must remain human_review_required
artifact_download_attempts increase must not exceed 12
MCP privacy check required
post-run backup required
```

## Known Limitations

- BORM XML artifact download is not supported because selected candidate metadata has no `url_xml`.
- BORM HTML artifact download is not enabled yet because the stored HTML URL is an official SPA route and has not been proven to return complete legal text.
- This implementation supports only PDF evidence, scoped by explicit candidate IDs.
