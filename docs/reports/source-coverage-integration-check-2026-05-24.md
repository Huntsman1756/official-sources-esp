# Source coverage integration check - 2026-05-24

Task: `TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001`

## Scope

This is an integration/control check for the source coverage platform line. It validates the
combined registry, RSS monitor, API monitor, and MCP coverage/discovery surfaces after the coverage
commits were integrated into one branch.

Branch used:

```text
codex/task-source-coverage-integration-check-001
```

Base:

```text
707c4cd feat: expose API discovery output through MCP
```

This check did not add sources, ingestion behavior, candidates, evidence-grade records, PDFs,
artifacts, backfills, RSS/API writes, downstream writes, VPS operations, production DB operations,
or LLM classification.

## Commits Confirmed

Each expected coverage-line commit is present in the integration branch:

| commit | status | subject |
| --- | --- | --- |
| `fc5544c` | present | `docs/config: add canonical executable source registry` |
| `c672854` | present | `feat: add RSS discovery monitor pilot` |
| `b175bc8` | present | `feat: expose source coverage through MCP` |
| `453fd89` | present | `feat: expand RSS discovery monitor sources` |
| `6c49cdc` | present | `docs: add source coverage v1 snapshot` |
| `fcd8c30` | present | `feat: add BOPV API discovery adapter` |
| `a707315` | present | `docs: add source coverage v1.1 snapshot` |
| `707c4cd` | present | `feat: expose API discovery output through MCP` |

Command used:

```bash
git merge-base --is-ancestor <commit> HEAD
```

## Registry Results

`config/sources.yaml` loads and validates through `official_sources.source_registry`.

Observed source counts:

```text
total=22
candidate_creation_allowed={False: 22}
evidence_grade_allowed={False: 22}
operational_status={'metadata_adapter_validated': 9, 'inventory_only': 12, 'paused': 1}
monitor_support={'available': 9, 'none': 12, 'planned': 1}
```

CLI sanity:

```bash
PYTHONPATH=src python -c "from official_sources.cli import main; raise SystemExit(main())" sources list
PYTHONPATH=src python -c "from official_sources.cli import main; raise SystemExit(main())" sources status --source BOCYL
PYTHONPATH=src python -c "from official_sources.cli import main; raise SystemExit(main())" sources status --source BOPV
```

Results:

- `sources list` returned 22 sources.
- `sources status --source BOCYL` returned `candidate_creation_allowed=False` and
  `evidence_grade_allowed=False`.
- `sources status --source BOPV` returned `candidate_creation_allowed=False` and
  `evidence_grade_allowed=False`.

## RSS Monitor Results

Live preview commands were run one source at a time, with `--limit 1` and without `--write`:

```bash
PYTHONPATH=src python -c "from official_sources.cli import main; raise SystemExit(main())" rss monitor --source BOE --date 2026-05-24 --limit 1
PYTHONPATH=src python -c "from official_sources.cli import main; raise SystemExit(main())" rss monitor --source BOJA --date 2026-05-24 --limit 1
PYTHONPATH=src python -c "from official_sources.cli import main; raise SystemExit(main())" rss monitor --source BOCYL --date 2026-05-24 --limit 1
```

Results:

| source | result | records | format | safety |
| --- | --- | ---: | --- | --- |
| `BOE` | ok | 1 | `rss` | `candidate_status=not_candidate`, `evidence_status=not_evidence` |
| `BOJA` | ok | 1 | `atom` | `candidate_status=not_candidate`, `evidence_status=not_evidence` |
| `BOCYL` | ok | 1 | `rss` | `candidate_status=not_candidate`, `evidence_status=not_evidence` |

Broad RSS run was refused:

```bash
PYTHONPATH=src python -c "from official_sources.cli import run; raise SystemExit(run(['rss','monitor','--source','ALL','--date','2026-05-24','--limit','1']))"
```

Result:

```text
exit_code=2
rss monitor accepts one source at a time; broad runs are not allowed
```

## API Monitor Results

Live BOPV preview was run with `--limit 1` and without `--write`:

```bash
PYTHONPATH=src python -c "from official_sources.cli import run; raise SystemExit(run(['api','monitor','--source','BOPV','--date','2026-05-24','--limit','1']))"
```

Result:

```text
records=1
api_id=2026/05/1813
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

Broad API run was refused:

```text
exit_code=2
api monitor accepts one source at a time; broad runs are not allowed
```

Non-API source was refused for the API monitor:

```text
exit_code=2
BOCYL does not have a validated api access method
```

## MCP Sanity Results

MCP sanity was run through `official_sources.mcp.tools` with `PYTHONPATH=src`.

Registry/coverage results:

```text
list_sources_count 22
bocyl_status metadata_adapter_validated
bopv_status metadata_adapter_validated
monitorable_subset {'BOE': ['api', 'html', 'rss', 'xml'], 'BOJA': ['api', 'atom'], 'BOCYL': ['rss'], 'BOPV': ['api', 'html', 'xml']}
```

Discovery-reader results used temporary fixture JSONL outside the repo:

```text
empty_status empty 0
rss_read ok ['rss'] not_candidate
api_read ok ['api'] not_evidence
unknown unknown_source
```

This confirms:

- `list_sources` returns 22 sources.
- `get_source_status` works for `BOCYL` and `BOPV`.
- `list_monitorable_sources` includes `BOE`, `BOJA`, `BOCYL`, and `BOPV` as monitorable through
  their declared access methods.
- `list_latest_discovery_entries` returns empty safely when no JSONL exists.
- `list_latest_discovery_entries` reads existing RSS JSONL.
- `list_latest_discovery_entries` reads existing API JSONL.
- MCP did not fetch live RSS/API data.
- MCP did not write RSS/API JSONL.

## Test Results

Validation commands:

```bash
git diff --check
python -m ruff check src tests
python -m pytest -q
```

Results:

```text
git diff --check: ok
python -m ruff check src tests: ok
python -m pytest -q: 488 passed, 1 warning
```

The warning is the existing Starlette `python_multipart` pending deprecation warning.

## Guardrail Confirmation

This integration check did not create:

- `source_candidates`
- evidence-grade records
- PDFs
- artifact files
- downstream product writes
- backfills
- RSS JSONL writes
- API JSONL writes
- VPS operations
- production DB operations
- LLM classification

MCP remained read-only:

- no live RSS fetches from MCP;
- no live API fetches from MCP;
- no writes from MCP.
