# Provincial HTML discovery 003 - 2026-05-26

Task: `TASK-SOURCE-PROVINCIAL-DISCOVERY-003`

## Scope

This task evaluated the next provincial BOP sources for metadata-only HTML discovery. It selected at
most two new sources and kept the existing source-specific parser approach.

Hard boundaries kept:

- preview mode only;
- no `--write`;
- no PDF or artifact download;
- no candidates;
- no evidence-grade records;
- no downstream writes;
- no backfills;
- no VPS/prod DB operations;
- no generic provincial HTML framework.

## Recommendation input

Command used:

```powershell
$env:PYTHONPATH='src'; @'
from official_sources.mcp import tools
result = tools.recommend_next_sources(limit=10)
for item in result.get('recommendations', []):
    print(item.get('source_code'), '|', item.get('recommended_task'), '|', item.get('confidence'), '|', item.get('reason'))
'@ | python -
```

Top recommendations after the existing health-check branch:

```text
BOP_ALMERIA
BOP_ARABA_ALAVA
BOP_AVILA
BOP_BADAJOZ
BOP_BARCELONA
BOP_BIZKAIA
BOP_BURGOS
BOP_CACERES
BOP_CADIZ
BOP_CASTELLON
```

`BOP_ALMERIA` still appeared as the first recommendation. That means the deterministic recommender
still ignores prior rejection notes and only uses registry state. It was not selected because prior
work documented the official surface as a ZK/JavaScript app unsuitable for simple deterministic HTML
metadata extraction.

## Sources selected

### BOP_ARABA_ALAVA

Selected because:

- the official BOTHA page supports a date-bounded HTML request using `FechaBotha=DD/MM/YYYY`;
- metadata is visible in the returned HTML;
- no mandatory browser JavaScript rendering is needed for the tested date;
- Spanish `_C.xml` result links can be recorded as metadata-only `official_url`;
- PDF links exist but are not needed for preview and are not downloaded.

Validated access method:

```text
http://www.araba.eus/botha/Inicio/SGBO5001.aspx?FechaBotha={date_ddmmyyyy}
```

Preview:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli html monitor --source BOP_ARABA_ALAVA --date 2026-05-25 --limit 1
```

Result:

```text
records=1
document_id=2026/059/01429
official_url=http://www.araba.eus/botha/Busquedas/Resultado.aspx?File=Boletines/2026/059/2026_059_01429_C.xml&hl=
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
warnings=[]
```

### BOP_AVILA

Selected because:

- the official current-bulletin page is plain HTML;
- metadata is visible in the returned HTML;
- no mandatory browser JavaScript rendering is needed;
- document ids, titles, dates, and official URLs can be extracted without downloading PDFs;
- PDF links are recorded only as metadata.

Validated access method:

```text
https://www.diputacionavila.es/boletin-oficial/
```

Preview:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli html monitor --source BOP_AVILA --date 2026-05-25 --limit 1
```

Result:

```text
records=1
document_id=1118/26
official_url=https://www.diputacionavila.es/bops/2026/25-05-2026/25-05-2026_111826.pdf
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
warnings=["pdf_endpoint_not_downloaded"]
```

## Sources rejected or deferred

### BOP_ALMERIA

Rejected for this task despite appearing in `recommend_next_sources`.

Reason:

- prior work already documented the tested official surface as a ZK/JavaScript application;
- it does not fit the simple deterministic HTML metadata extraction criterion;
- selecting it here would either require JS-capable automation or a separate endpoint audit.

`BOP_ALMERIA` remains `inventory_only`.

### BOP_BADAJOZ and later recommendations

Not selected because the task limit was two sources. Badajoz did show promising HTML/RSS signals
during manual triage, but it should be handled in a later task rather than expanding this task
beyond the agreed limit.

## Registry changes

Promoted:

```text
BOP_ARABA_ALAVA: inventory_only -> monitor_validated
BOP_AVILA: inventory_only -> monitor_validated
```

Both remain:

```text
candidate_creation_allowed=false
evidence_grade_allowed=false
evidence_adapter=false
backfill_support=none
```

## Pattern assessment

The provincial HTML pattern still holds with five total monitored provincial sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_ARABA_ALAVA
BOP_AVILA
```

The shared contract is stable:

- one source per command;
- preview by default;
- metadata-only records;
- deterministic hashes;
- `not_candidate`, `not_evidence`, and `unclassified` safety flags;
- no PDF download.

The extraction layer remains source-specific:

- Araba/Alava uses date-scoped BOTHA HTML with bilingual result links; the parser selects Spanish
  `_C.xml` links to avoid duplicate Basque/Spanish entries.
- Avila uses a current-bulletin HTML page with PDF URLs embedded as metadata-only links.

No generic provincial HTML framework is justified yet.

## Safety confirmation

This task did not:

- write HTML/RSS/API JSONL;
- create `source_candidates`;
- create evidence-grade records;
- download PDFs or artifacts;
- touch downstream repositories;
- run backfills;
- run broad or all-source discovery;
- run VPS or production DB operations;
- add LLM classification.

## Next recommendation

Before adding more sources, improve or document the deterministic recommender so it does not keep
prior rejected sources like `BOP_ALMERIA` at the top without surfacing the rejection note.

Recommended next task:

```text
TASK-MCP-COVERAGE-RECOMMENDATIONS-002
```

Goal: penalize or annotate previously rejected provincial sources using registry limitations and
report-derived notes, without LLMs, live fetches, previews, writes, candidates, or evidence-grade
records.
