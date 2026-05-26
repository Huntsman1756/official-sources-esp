# Provincial HTML discovery 002 - 2026-05-24

Task: `TASK-SOURCE-PROVINCIAL-DISCOVERY-002`

## Scope

This task used deterministic MCP recommendations as input and evaluated three provincial
`inventory_only` sources:

```text
BOP_ALBACETE
BOP_ALICANTE
BOP_ALMERIA
```

The task selected at most two sources for metadata-only HTML discovery and did not force unsuitable
sources.

## Sources Evaluated

### BOP_ALBACETE

Selected.

The official surface at `https://bop.dipualba.es` exposes the current bulletin summary as HTML. The
page includes the bulletin date, announcement titles, and official page links. Those page links are
recorded as `official_url` metadata only; the monitor does not download them.

Live preview:

```text
command_started=html monitor source_code=BOP_ALBACETE date=2026-05-25 mode=preview records=1 discovery_metadata_only=true
```

### BOP_ALICANTE

Selected.

The official consultation page at `https://sede.diputacionalicante.es/consultas-bop/` uses a backing
endpoint under the same official site:

```text
https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php
```

The monitor calls that endpoint one date at a time with the same `BOP_CON` parameters used by the
official page. The response contains bulletin metadata and official document URLs. Those URLs are
recorded as metadata only; the monitor does not download PDFs.

Live preview:

```text
command_started=html monitor source_code=BOP_ALICANTE date=2026-05-25 mode=preview records=1 discovery_metadata_only=true
```

### BOP_ALMERIA

Rejected for this task.

The tested official surface resolves to a ZK/JavaScript application:

```text
https://app.dipalme.org/bop/publico.zul
```

It is not a clean deterministic HTML metadata page for this task. `BOP_ALMERIA` remains
`inventory_only` and should only be revisited through a separate endpoint-specific or JS-capable
audit.

## Records

Selected monitors emit metadata-only records under the existing HTML discovery contract:

```text
source_code
page_url
page_format
entry_id
document_id
title
published_at
official_url
summary
raw_page_hash
entry_hash
discovered_at
monitor_run_id
classification_status=unclassified
evidence_status=not_evidence
candidate_status=not_candidate
```

Explicit `--write` output path, if a future task authorizes it:

```text
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

No JSONL output was written in this task.

## Registry Changes

Promoted to metadata-only HTML monitor support:

```text
BOP_ALBACETE: inventory_only -> monitor_validated
BOP_ALICANTE: inventory_only -> monitor_validated
```

Unchanged:

```text
BOP_ALMERIA: inventory_only
```

Current coverage after this task:

```text
total sources: 65
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE
monitor_validated: 6
inventory_only: 49
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

## Safety

Confirmed:

- no `source_candidates` were created;
- no evidence-grade records were created;
- no PDFs or artifacts were downloaded;
- no downstream repositories were touched;
- no backfills were run;
- no broad/all-source run was used;
- no RSS/API/HTML JSONL writes were run;
- no VPS or production DB operations were run;
- no LLM classification was added.

## Validation

Commands run:

```text
$env:PYTHONPATH='src'; python -m pytest tests/test_html_monitor.py -q
$env:PYTHONPATH='src'; python -m pytest tests/test_mcp_tools.py -q
$env:PYTHONPATH='src'; python -m official_sources.cli html monitor --source BOP_ALBACETE --date 2026-05-25 --limit 1
$env:PYTHONPATH='src'; python -m official_sources.cli html monitor --source BOP_ALICANTE --date 2026-05-25 --limit 1
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_ALBACETE
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_ALICANTE
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOP_ALMERIA
```

Results:

```text
tests/test_html_monitor.py: 19 passed
tests/test_mcp_tools.py: 41 passed, 1 warning
BOP_ALBACETE preview: records=1, mode=preview, no --write
BOP_ALICANTE preview: records=1, mode=preview, no --write
BOP_ALMERIA status: inventory_only, monitor_support=none
```

Full validation is recorded in the final task response.

## Next Recommended Task

Add a coverage snapshot before expanding further:

```text
TASK-SOURCE-COVERAGE-V1.5-SNAPSHOT-001
```

Do not add bulk provincial monitoring. Future provincial work should evaluate at most two more
sources and should keep the same metadata-only, preview-first boundaries.
