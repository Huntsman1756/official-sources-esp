# Project State

Last updated: 2026-05-27

## Current Decision

`TASK-PROVINCIAL-MONITORS-WAVE-003` is implemented locally under the partial-health contract.

Wave 003 adds `BOP_SEVILLA` as a single metadata-only HTML monitor. It does not modify the
`BOP_ALICANTE` degraded/manual-review state introduced by `TASK-BOP-ALICANTE-DEGRADED-DNS-001`.

Current provincial monitor health contract after this wave:

```text
healthy monitored provincial sources: 8
degraded monitored provincial sources: 1
contract: PARTIAL-GO
all-sources-green claim: not allowed
BOP_ALICANTE: still degraded/manual-review due resolver-dependent DNS instability
```

Healthy set:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_LUGO
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
BOP_SEVILLA
```

`BOP_SEVILLA` live preview on `2026-05-27` returned `records=1` in preview mode with
`not_candidate`, `not_evidence`, and `unclassified`; parser validation extracted 33 live
announcement records for the same date. No PDFs/artifacts, candidates, evidence-grade records,
downstream writes, VPS, Hermes, systemd, timers, or `data/html_monitor` output were created.

Report:

```text
docs/reports/provincial-monitors-wave-003-2026-05-27.md
```

## Previous Decision

`TASK-BOP-ALICANTE-DEGRADED-DNS-001` is implemented locally as a health-reporting contract.

`BOP_ALICANTE` is formally treated as `degraded/manual-review` for provincial monitor health
reporting because normal live preview still fails during DNS resolution. This does not remove it
from the registry, does not revert it to `inventory_only`, and does not mark it healthy.

Current provincial monitor health contract:

```text
healthy monitored provincial sources: 7
degraded monitored provincial sources: 1
combined all-sources health: PARTIAL-GO
all-sources-green claim: not allowed
BOP_ALICANTE: excluded from healthy set until normal DNS/live preview recovers
Wave 003: unblocked only under partial-health criteria
```

Healthy set:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_LUGO
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
```

Degraded set:

```text
BOP_ALICANTE
reason: resolver-dependent DNS instability for sede.diputacionalicante.es
```

No `config/sources.yaml`, monitor code, registry status, VPS, Hermes, systemd, timers, candidates,
evidence-grade records, PDF/artifact downloads, downstream writes, or `data/html_monitor` outputs
were changed.

Report:

```text
docs/reports/bop-alicante-degraded-dns-2026-05-27.md
```

## Previous Decision

`TASK-BOP-ALICANTE-HEALTH-REGRESSION-001` is implemented locally as a read-only diagnostic.

`BOP_ALICANTE` still exposes the configured official endpoint when the hostname is resolved through
Google DNS (`195.53.69.137`), and the endpoint returns JSON compatible with the existing parser for
the previously validated date. Normal local monitor execution still fails with
`httpx.ConnectError: [Errno 11002] getaddrinfo failed`, and Cloudflare DNS-over-HTTPS returns
`SERVFAIL` with a delegation error for `diputacionalicante.es`.

Decision:

```text
root cause: resolver-dependent DNS instability
endpoint obsolete: no evidence
parser regression: no evidence
monitor code fix: NO-GO
BOP_ALICANTE healthy-set status: degraded/manual-review
combined provincial health: NO-GO
Wave 003: blocked until Alicante recovers or is explicitly excluded from the healthy set
```

No monitor code, registry status, VPS, Hermes, systemd, timers, candidates, evidence-grade records,
PDF/artifact downloads, downstream writes, or `data/html_monitor` outputs were changed.

Report:

```text
docs/reports/bop-alicante-health-regression-2026-05-27.md
```

## Earlier Decision

`TASK-PROVINCIAL-MONITORS-HEALTH-001` is implemented locally as a documentation-only health check.

The combined provincial monitor health check ran live preview commands on `2026-05-27` for the
currently monitored provincial sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_LUGO
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
```

Result:

```text
OK: 7
FAILED: 1
overall health decision: NO-GO until BOP_ALICANTE endpoint/DNS is reviewed
```

Passing sources returned `records=1` in preview mode with metadata-only statuses:

```text
BOP_A_CORUNA: OK
BOP_ALBACETE: OK
BOP_LUGO: OK
BOP_BARCELONA: OK
BOP_MALAGA: OK
BOP_BIZKAIA: OK
BOP_VALENCIA: OK
```

`BOP_ALICANTE` failed on two live preview attempts:

```text
httpx.ConnectError: [Errno 11002] getaddrinfo failed
endpoint: https://sede.diputacionalicante.es/wp-content/themes/Desarrollo-Diputacion/webservices/wseConsultaAjax.php
```

No writes were performed:

```text
data/html_monitor: absent
data/rss_monitor: absent
no --write used
no candidates
no evidence-grade records
no PDF/artifact downloads
no downstream writes
no VPS, Hermes, systemd, BOE timer, or integrity timer changes
```

Report:

```text
docs/reports/provincial-monitors-health-001-2026-05-27.md
```

Previous completed provincial monitor task:

```text
TASK-PROVINCIAL-MONITORS-WAVE-002
```

`TASK-PROVINCIAL-MONITORS-WAVE-002` is implemented locally.

The second provincial metadata-only monitor wave adds source-specific HTML discovery support for:

```text
BOP_BIZKAIA
BOP_VALENCIA
```

Both monitors emit discovery metadata with `candidate_status=not_candidate`,
`evidence_status=not_evidence`, and `classification_status=unclassified`.

`BOP_BIZKAIA` reads the official current BOB landing page and follows its public latest-bulletin
detail link to parse announcement metadata. `BOP_VALENCIA` reads the official current BOP page
directly and records announcement metadata without trying to invoke JavaScript/AJAX PDF actions.

Current executable registry counts:

```text
total sources: 65
metadata_adapter_validated: 9
monitor_validated: 13
inventory_only: 42
paused: 1
provincial inventory-only sources: 35
RSS/Atom discovery sources: BOC_CANARIAS, BOC_CANTABRIA, BOCYL, BOE, BOIB, BOJA, BOP_LUGO, DOE, DOG
API discovery sources: BOPV
HTML provincial discovery sources: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, BOP_BARCELONA, BOP_BIZKAIA, BOP_MALAGA, BOP_VALENCIA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Live preview validation on `2026-05-27` ran one source at a time, with `--limit 1`, and without
`--write`:

```text
BOP_BIZKAIA: records=1 published_at=2026-05-27 candidate_status=not_candidate evidence_status=not_evidence
BOP_VALENCIA: records=1 published_at=2026-05-27 candidate_status=not_candidate evidence_status=not_evidence
data/html_monitor writes: none
```

The source-specific parsers also extracted current-page records during parser validation:

```text
BOP_BIZKAIA: 34 live records parsed from the public latest-bulletin detail page linked by https://www.bizkaia.eus/es/bob
BOP_VALENCIA: 25 live records parsed from https://bop.dival.es/bop/drvisapi.dll
```

Scope boundaries:

```text
metadata-only previews only
no candidates
no evidence-grade records
no PDF/artifact downloads
no downstream writes
no broad scraping or backfill
no VPS, Hermes, systemd, BOE timer, or integrity timer changes
```

Report:

```text
docs/reports/provincial-monitors-wave-002-2026-05-27.md
```

Previous completed provincial monitor task:

```text
TASK-PROVINCIAL-MONITORS-WAVE-001
```

`TASK-PROVINCIAL-MONITORS-WAVE-001` is implemented locally.

The first provincial metadata-only monitor wave adds source-specific HTML discovery support for:

```text
BOP_BARCELONA
BOP_MALAGA
```

Both monitors read only the official current-bulletin HTML page, emit discovery metadata with
`candidate_status=not_candidate`, `evidence_status=not_evidence`, and
`classification_status=unclassified`, and do not download PDFs or artifacts.

Executable registry counts after Wave 001:

```text
total sources: 65
metadata_adapter_validated: 9
monitor_validated: 11
inventory_only: 44
paused: 1
provincial inventory-only sources: 37
RSS/Atom discovery sources: BOC_CANARIAS, BOC_CANTABRIA, BOCYL, BOE, BOIB, BOJA, BOP_LUGO, DOE, DOG
API discovery sources: BOPV
HTML provincial discovery sources: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, BOP_BARCELONA, BOP_MALAGA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Live preview validation on `2026-05-27` ran one source at a time, with `--limit 1`, and without
`--write`:

```text
BOP_BARCELONA: records=1 published_at=2026-05-27 candidate_status=not_candidate evidence_status=not_evidence
BOP_MALAGA: records=1 published_at=2026-05-27 candidate_status=not_candidate evidence_status=not_evidence
data/html_monitor writes: none
```

The source-specific parsers also extracted more than one live record from the current pages during
parser validation:

```text
BOP_BARCELONA: 20 live records parsed from https://bop.diba.cat/butlleti-del-dia
BOP_MALAGA: 19 live records parsed from http://www.bopmalaga.es/
```

Scope boundaries:

```text
metadata-only previews only
no candidates
no evidence-grade records
no PDF/artifact downloads
no downstream writes
no broad scraping or backfill
no VPS, Hermes, systemd, BOE timer, or integrity timer changes
```

Report:

```text
docs/reports/provincial-monitors-wave-001-2026-05-27.md
```

Previous completed provincial audit task:

```text
TASK-PROVINCIAL-READONLY-BATCH-AUDIT-001
```

`TASK-PROVINCIAL-READONLY-BATCH-AUDIT-001` is implemented locally.

The batch audit ran against the 38 remaining provincial `inventory_only` sources without a
documented technical blocker, excluding `BOP_ALMERIA` and excluding already monitored provincial
sources:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_LUGO
```

The audit used one read-only landing-page request per source with a 5 second timeout and 200 KB
response cap. It did not use login, headless browser automation, anti-bot bypass, broad scraping,
monitor writes, registry status changes, candidate creation, evidence-grade creation, PDF/artifact
downloads, downstream writes, VPS/prod DB operations, Hermes, BOE timer, integrity timer, or
systemd.

Outputs:

```text
docs/reports/provincial-readonly-batch-audit-2026-05-27.md
data/provincial_audit/provincial-readonly-batch-audit-2026-05-27.json
```

Category counts:

```text
rss_or_api_detected: 4
open_data_detected: 7
static_html_viable: 5
stable_form_or_endpoint: 14
unknown: 8
```

Recommended metadata-only pilot candidates by evidence and prior wave weighting:

```text
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
BOP_SEVILLA
```

Defer/manual from this first pass:

```text
BOP_CADIZ
BOP_CIUDAD_REAL
BOP_CUENCA
BOP_GIRONA
BOP_GUADALAJARA
BOP_OURENSE
BOP_TARRAGONA
BOP_ZARAGOZA
```

This audit is planning evidence only. It does not validate or add any new provincial monitor.

Previous completed source-ranking task:

```text
TASK-MCP-SOURCE-RANKING-CLEANUP-001
```

`TASK-MCP-SOURCE-RANKING-CLEANUP-001` is implemented locally.

`recommend_next_sources` no longer treats documented blocked/deferred provincial sources as normal
next candidates. `BOP_ALMERIA` remains in `config/sources.yaml` as `inventory_only` with
`monitor_support=none`, but it is excluded from the normal recommendation ranking because the
documented evaluation found a ZK/JavaScript surface requiring a separate endpoint-specific or
JS-capable audit.

The normal provincial recommendation order now prioritizes the documented pilot waves before the
alphabetical fallback:

```text
BOP_BARCELONA
BOP_MALAGA
BOP_BIZKAIA
BOP_VALENCIA
BOP_SEVILLA
BOP_ZARAGOZA
```

Already monitored provincial sources remain excluded:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
BOP_LUGO
```

This task did not add provincial monitors, run scraping, write discovery JSONL, create candidates,
create evidence-grade records, download PDFs/artifacts, touch downstream repos, run VPS/prod DB
operations, touch Hermes, BOE timer, integrity timer, or systemd.

Report:

```text
docs/reports/source-ranking-cleanup-2026-05-27.md
```

Previous completed infrastructure task:

```text
TASK-HERMES-AUDITOR-CANONICAL-ROOT-001
```

`TASK-HERMES-AUDITOR-CANONICAL-ROOT-001` is completed with manual validation `GO`.

Scheduled validation is still pending the next automatic Hermes timer run.

Hermes now audits the canonical operational checkout:

```text
/opt/official-sources/app
```

The VPS auditor runner/tooling remains separate from the audited repo:

```text
/opt/hermes-official-sources-auditor/bin/run-official-sources-hermes-auditor.sh
```

VPS-applied systemd drop-in, documented here but not versioned in this repository:

```text
/etc/systemd/system/official-sources-hermes-auditor.service.d/canonical-root.conf
```

It defines `APP_ROOT`, `REPO_ROOT`, and `TARGET_REPO` as `/opt/official-sources/app`.

First valid report:

```text
/var/lib/hermes-official-sources-auditor/reports/vps-audit-20260527-044105.md
```

Validation:

```text
manual service run: 0/SUCCESS
failed units: 0
Hermes timer: active/waiting
BOE daily timer: active/waiting
integrity timer: active/waiting
audited repo: main, 9ebf849f1663642071f60023385acc44c9fe5875
RSS monitor: present
TASK-SOURCE-RSS-MONITOR-001: already completed, not current work
```

Hermes reports generated before `2026-05-27 04:41 UTC` are stale/non-authoritative because they
targeted or reasoned from obsolete context.

Repository documentation report:

```text
docs/reports/hermes-auditor-canonical-root-2026-05-27.md
```

This task did not modify BOE daily, integrity-check, source registry, RSS monitor logic, downstream
writes, candidates, evidence-grade records, PDFs/artifacts, or product data.

Previous completed source-platform task:

```text
TASK-SOURCE-RSS-MONITOR-004
```

`TASK-SOURCE-RSS-MONITOR-004` is implemented locally.

The RSS monitor now has three additional metadata-only official RSS sources:

```text
BOC_CANARIAS = official BOC RSS section feed for I. Disposiciones generales
DOG = official DOG complete summary RSS feed
BOP_LUGO = official BOP Lugo RSS feed
```

Current executable registry counts:

```text
total sources: 65
metadata_adapter_validated: 9
monitor_validated: 11
inventory_only: 44
paused: 1
provincial inventory-only sources: 37
RSS/Atom discovery sources: BOC_CANARIAS, BOC_CANTABRIA, BOCYL, BOE, BOIB, BOJA, BOP_LUGO, DOE, DOG
API discovery sources: BOPV
HTML provincial discovery sources: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE, BOP_BARCELONA, BOP_MALAGA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Live preview validation on `2026-05-26` ran one source at a time, with `--limit 1`, and without
`--write`:

```text
BOC_CANARIAS: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
DOG: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
BOP_LUGO: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
data/rss_monitor exists: false
```

Report:

```text
docs/reports/rss-monitor-004-2026-05-26.md
```

This task did not change `src/official_sources/rss_monitor.py`, create candidates, create
evidence-grade records, download PDFs/artifacts, write downstream data, run backfills, run broad
monitoring, touch VPS/prod DB, touch Hermes, or touch systemd.

Previous completed source-platform task:

```text
TASK-DOCS-RSS-MONITOR-STATE-RECONCILIATION-001
```

`TASK-DOCS-RSS-MONITOR-STATE-RECONCILIATION-001` is merged in main.

The RSS monitor baseline is already present in current `main`; `TASK-SOURCE-RSS-MONITOR-001`
must not be reopened or reimplemented. Current repository evidence includes:

```text
src/official_sources/rss_monitor.py
tests/test_rss_monitor.py
docs/reports/rss-monitor-pilot-2026-05-24.md
config/sources.yaml
```

Current validated RSS state:

```text
BOCYL = original RSS pilot source
BOE = current RSS positive/control source, added by later RSS/coverage work
```

Current preview validation on `2026-05-26` ran without `--write`:

```text
BOE:   records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
BOCYL: records=1 feed_format=rss candidate_status=not_candidate evidence_status=not_evidence
data/rss_monitor exists: false
```

The historical report `docs/reports/rss-monitor-pilot-2026-05-24.md` remains true for its original
task boundary: BOE was not used as a control in RSS-001 itself. The current repo state is broader
because later RSS and coverage work added BOE/BOJA and validated integrated RSS previews.

`TASK-SOURCE-RSS-MONITOR-004` has now been opened separately after this reconciliation, so future
RSS work should not reuse RSS-001 or RSS-004. Keep any later RSS task metadata-only and one source
at a time.

Previous completed source-platform task:

```text
TASK-SOURCE-PROVINCIAL-HTML-HEALTH-001
```

`TASK-SOURCE-PROVINCIAL-HTML-HEALTH-001` is implemented locally.

The project now has a health check report for the current provincial HTML discovery monitors:

```text
docs/reports/provincial-html-health-check-2026-05-26.md
```

Health check scope:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
```

Result:

```text
BOP_A_CORUNA: preview OK, records=1
BOP_ALBACETE: preview OK, records=1
BOP_ALICANTE: preview OK, records=1
```

The check used source-tree CLI commands with `PYTHONPATH=src`, preview mode only, date
`2026-05-25`, and `--limit 1`. It did not use `--write`, did not create JSONL output, did not add
sources, did not change parser behavior, did not create candidates/evidence, did not download
PDFs/artifacts, did not touch downstream repos, did not run backfills, did not run broad discovery,
and did not use VPS/prod DB operations or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-PROVINCIAL-PATTERN-REPORT-001
```

`TASK-SOURCE-PROVINCIAL-PATTERN-REPORT-001` is implemented locally.

The project now has a provincial HTML discovery pattern report:

```text
docs/reports/provincial-html-discovery-patterns-2026-05-26.md
```

Decision:

```text
Keep source-specific provincial HTML parsers for now.
Use small shared helpers only where duplication is already proven.
Do not build a broad generic provincial HTML framework yet.
```

Rationale:

```text
BOP_A_CORUNA: date-scoped HTML page with bloqueAnuncio blocks and HTML document URLs.
BOP_ALBACETE: current-bulletin HTML summary with page-link PDF endpoints recorded as metadata only.
BOP_ALICANTE: official consultation page backed by a JSON endpoint, one date at a time.
BOP_ALMERIA: rejected/deferred because the tested official surface is a ZK/JavaScript app.
```

The common contract is real: one-source preview, metadata-only record shape, SHA-256 raw payload and
entry hashes, no PDF download, and `not_candidate`/`not_evidence`/`unclassified` safety flags. The
source extraction mechanics are not yet common enough to justify a generic framework.

This task is analysis/docs only. It did not add sources, change parser behavior, run monitor writes,
create candidates, create evidence-grade records, download PDFs/artifacts, touch downstream repos,
run backfills, run broad discovery, run VPS/prod DB operations, or add LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.5-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.5-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.5 snapshot after `TASK-SOURCE-PROVINCIAL-DISCOVERY-002`:

```text
docs/reports/source-coverage-v1-5-snapshot-2026-05-26.md
```

Coverage v1.5 summarizes the executable registry after `BOP_ALBACETE` and `BOP_ALICANTE` were
promoted from provincial inventory to metadata-only HTML discovery monitors:

```text
total sources: 65
estatal: 2
european: 1
autonomica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 6
inventory_only: 49
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE
BOP_ALMERIA: rejected for this task; remains inventory_only because the tested surface is ZK/JavaScript
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API/HTML writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes,
backfills, all-source runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-002
```

`TASK-SOURCE-PROVINCIAL-DISCOVERY-002` is implemented locally.

The second provincial metadata-only discovery task used the deterministic MCP recommendations as
input and evaluated:

```text
BOP_ALBACETE
BOP_ALICANTE
BOP_ALMERIA
```

Selected sources:

```text
BOP_ALBACETE
BOP_ALICANTE
```

Rejected source:

```text
BOP_ALMERIA
```

`BOP_ALBACETE` and `BOP_ALICANTE` now have source-specific HTML discovery previews. `BOP_ALMERIA`
remains `inventory_only` because the tested official surface is a ZK/JavaScript application and
needs a separate endpoint or JS-capable audit before monitoring.

Current executable registry counts:

```text
total sources: 65
estatal: 2
european: 1
autonÃ³mica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 6
inventory_only: 49
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA, BOP_ALBACETE, BOP_ALICANTE
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

The added previews are metadata-only. They do not write JSONL by default, create candidates,
create evidence-grade records, download PDFs/artifacts, run backfills, touch downstream repos, run
VPS/prod DB operations, or add LLM classification.

Report:

```text
docs/reports/provincial-html-discovery-002-2026-05-24.md
```

Previous completed source-platform task:

```text
TASK-MCP-COVERAGE-RECOMMENDATIONS-001
```

`TASK-MCP-COVERAGE-RECOMMENDATIONS-001` is implemented locally.

The MCP now exposes a deterministic next-source recommendation tool:

```text
recommend_next_sources(limit=5)
```

Current strategy:

```text
provincial_html_discovery_pilot
```

The tool recommends provincial `inventory_only` sources with official landing URLs and no validated
monitor yet. It excludes already monitored sources such as `BOP_A_CORUNA`, reads existing discovery
cache directory state when present, and returns constraints for metadata-only follow-up work.

This is not an LLM tool and it does not execute previews, fetch live sources, write JSONL, create
files, create candidates, create evidence-grade records, download PDFs/artifacts, mutate
`config/sources.yaml`, touch downstream repos, run backfills, run VPS/prod DB operations, or add LLM
classification.

Report:

```text
docs/reports/mcp-coverage-recommendations-2026-05-24.md
```

Previous completed source-platform task:

```text
TASK-MCP-DISCOVERY-PREVIEW-001
```

`TASK-MCP-DISCOVERY-PREVIEW-001` is implemented locally.

The MCP now exposes a controlled one-source discovery preview tool:

```text
preview_discovery(source_code, date, limit=1, discovery_type=None)
```

Supported preview families:

```text
rss: validated RSS/Atom discovery sources
api: BOPV API discovery
html: validated provincial HTML discovery sources
```

The tool runs preview mode only. It refuses broad/all-source requests, unknown sources,
inventory-only sources without implemented validated monitor support, and `limit > 10`.

Preview results are metadata-only:

```text
mode=preview
output_written=false
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

The tool does not write RSS/API/HTML JSONL, create files, create candidates, create evidence-grade
records, download PDFs/artifacts, mutate `config/sources.yaml`, touch downstream repos, run
backfills, run VPS/prod DB operations, or add LLM classification.

Report:

```text
docs/reports/mcp-discovery-preview-tools-2026-05-24.md
```

Previous completed source-platform task:

```text
TASK-MCP-HTML-DISCOVERY-OUTPUT-001
```

`TASK-MCP-HTML-DISCOVERY-OUTPUT-001` is implemented locally.

The MCP latest discovery reader now supports existing HTML monitor JSONL output in addition to RSS
and API output:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
data/html_monitor/<source_code>/<YYYY-MM-DD>/html_discovery.jsonl
```

Discovery entries are returned in deterministic order when multiple files exist for the same
source/date:

```text
rss -> api -> html
```

The MCP reader remains read-only. It does not fetch live RSS/API/HTML, write JSONL, create
candidates, create evidence-grade records, download PDFs/artifacts, touch downstream repos, run
backfills, run VPS/prod DB operations, or add LLM classification.

Report:

```text
docs/reports/mcp-html-discovery-output-2026-05-24.md
```

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.4-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.4-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.4 snapshot after the first provincial HTML discovery pilot:

```text
docs/reports/source-coverage-v1-4-snapshot-2026-05-25.md
```

Coverage v1.4 summarizes the executable registry after `BOP_A_CORUNA` was promoted from provincial
inventory to a single-source HTML discovery pilot:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 4
inventory_only: 51
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API/HTML writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes,
backfills, all-source runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001
```

`TASK-SOURCE-PROVINCIAL-DISCOVERY-PILOT-001` is implemented locally.

The first provincial metadata-only discovery pilot uses `BOP_A_CORUNA`:

```text
source: BOP_A_CORUNA
access: date-scoped official HTML summary page
command: official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD --limit 1
output path when explicitly written: data/html_monitor/BOP_A_CORUNA/<YYYY-MM-DD>/html_discovery.jsonl
```

The pilot validates that one provincial bulletin can be observed as metadata-only discovery without
creating candidates, evidence-grade records, PDFs, artifacts, backfills, downstream writes, broad
runs, VPS operations, production DB operations, or LLM classification. The other provincial sources
remain inventory-only.

Current executable registry counts after the pilot:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 4
inventory_only: 51
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
HTML discovery sources: BOP_A_CORUNA
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Report:

```text
docs/reports/provincial-discovery-pilot-bop-a-coruna-2026-05-25.md
```

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.3-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.3-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.3 snapshot after official directory reconciliation:

```text
docs/reports/source-coverage-v1-3-snapshot-2026-05-24.md
```

Coverage v1.3 summarizes the executable registry after provincial inventory expansion:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 52
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
all-source runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-OFFICIAL-DIRECTORY-001
```

`TASK-SOURCE-OFFICIAL-DIRECTORY-001` is implemented locally.

The executable registry has been reconciled against the official BOE/PAG bulletin directory pages.
The task added provincial bulletin entries as inventory/control-plane records only:

```text
docs/reports/official-directory-registry-reconciliation-2026-05-24.md
```

Current executable registry counts:

```text
total sources: 65
estatal: 2
european: 1
autonómica: 19
provincial: 43
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 52
paused: 1
candidate_creation_allowed=false: 65
evidence_grade_allowed=false: 65
```

Provincial bulletin entries are official directory inventory only. They are not RSS/API monitors,
not candidates, not evidence, and not validated HTML monitors. The task did not create
source_candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
RSS/API writes, broad monitor runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001
```

`TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001` is implemented locally.

The CLI module entrypoint now works for source-tree validation:

```powershell
$env:PYTHONPATH='src'; python -m official_sources.cli sources status --source BOIB
```

This is the recommended validation path when the installed global `official-sources` console script
is stale. To refresh the local console script, run an editable install from the repository root:

```bash
python -m pip install -e ".[dev]"
```

Report:

```text
docs/reports/cli-entrypoint-consistency-2026-05-24.md
```

This task did not change monitor behavior, registry values, sources, candidates, evidence-grade
records, PDFs, artifacts, downstream writes, backfills, RSS/API writes, VPS operations, production
DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.2 snapshot after RSS monitor expansion 003:

```text
docs/reports/source-coverage-v1-2-snapshot-2026-05-24.md
```

Coverage v1.2 summarizes the executable registry and current RSS/API monitor/MCP capabilities:

```text
total sources: 22
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 9
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL, BOIB, BOC_CANTABRIA, DOE
API discovery sources: BOPV
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

Snapshot caveats:

```text
BOC_CANTABRIA is category-scoped, not complete bulletin coverage.
DOE feed is valid, but RSS-003 live preview returned records=0.
DOGC and BON were not added because tested feed candidates returned 404.
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
all-source runs, VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-RSS-MONITOR-003
```

`TASK-SOURCE-RSS-MONITOR-003` is implemented locally.

The RSS/Atom discovery monitor now has six validated feed-backed sources:

```text
BOCYL          rss  https://bocyl.jcyl.es/rss.do
BOE            rss  https://www.boe.es/rss/boe.php
BOJA           atom https://www.juntadeandalucia.es/boja/distribucion/boja.xml
BOIB           rss  https://www.caib.es/eboibfront/es/rss
BOC_CANTABRIA  rss  https://www.cantabria.es/o/BOC/feed/6802081
DOE            rss  https://doe.juntaex.es/rss/rss.php?seccion=6
```

BOIB, BOC_CANTABRIA, and DOE were added as metadata-only discovery sources. Live preview smokes
were run one source at a time with `--limit 1` and without `--write`.

Notes:

```text
BOC_CANTABRIA feed is category-scoped, not complete bulletin coverage.
DOGC was not added because tested candidate RSS URLs returned 404.
BON was not added because tested candidate RSS URLs returned 404.
```

Registry coverage after this task:

```text
total sources: 22
metadata_adapter_validated: 9
monitor_validated: 3
inventory_only: 9
paused: 1
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

This task did not create source candidates, evidence-grade records, PDFs, artifacts, downstream
writes, backfills, broad/all-source runs, RSS writes, VPS operations, production DB operations,
publication, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-SCHEDULE-001
```

`TASK-SOURCE-COVERAGE-SCHEDULE-001` is implemented locally.

The controlled discovery run plan is documented at:

```text
docs/SOURCE_COVERAGE_RUN_PLAN.md
```

Report:

```text
docs/reports/source-coverage-schedule-2026-05-24.md
```

This task defines safe operation for source discovery monitors:

```text
one source per command
preview by default
--write only when explicitly approved
cache-first JSONL output
run report required for non-trivial executions
no all-source runs
```

It is documentation/control-plane only. It did not add scheduler code, cron, systemd, GitHub
Actions, VPS jobs, new sources, monitor behavior changes, candidates, evidence-grade records, PDFs,
artifacts, downstream writes, backfills, production DB operations, publication, or LLM
classification.

Previous completed source-platform task:

```text
TASK-MCP-COVERAGE-USAGE-DOCS-001
```

`TASK-MCP-COVERAGE-USAGE-DOCS-001` is implemented locally.

The coverage platform usage guide is now documented at:

```text
docs/SOURCE_COVERAGE_USAGE.md
```

It documents:

```text
official-sources sources list
official-sources sources status --source BOCYL
official-sources rss monitor --source BOE/BOJA/BOCYL --date YYYY-MM-DD --limit 1
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit 1
MCP: list_sources, get_source_status, list_monitorable_sources, list_latest_discovery_entries
```

The documentation restates the coverage safety boundary: RSS/API discovery is metadata-only, MCP is
read-only, monitor writes require explicit `--write`, and coverage commands do not create
candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS operations,
production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001
```

`TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001` is implemented locally.

The coverage platform line was validated on the integration branch:

```text
codex/task-source-coverage-integration-check-001
```

Report:

```text
docs/reports/source-coverage-integration-check-2026-05-24.md
```

Validated together:

```text
config/sources.yaml
RSS/Atom discovery: BOE, BOJA, BOCYL
API discovery: BOPV
MCP read-only coverage/discovery tools
```

Validation results:

```text
sources.yaml total sources: 22
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
RSS previews: BOE, BOJA, BOCYL ok with --limit 1 and no --write
API preview: BOPV ok with --limit 1 and no --write
MCP fixture reads: empty, RSS JSONL, API JSONL, unknown source all ok
python -m pytest -q: 488 passed, 1 warning
```

This task is reporting/control-plane only. It did not create sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-MCP-API-DISCOVERY-OUTPUT-001
```

`TASK-MCP-API-DISCOVERY-OUTPUT-001` is implemented locally.

The MCP/read-only discovery reader now reads existing metadata-only RSS and API discovery JSONL:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
data/api_monitor/<source_code>/<YYYY-MM-DD>/api_discovery.jsonl
```

The existing MCP tool remains:

```text
list_latest_discovery_entries
```

It now returns `resource_type=discovery_entries`, a `discovery_types` list, `output_paths`, and a
per-entry `discovery_type` marker such as `rss` or `api`.

This task is read-only. It did not add live RSS/API fetching through MCP, JSONL writes, source
candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS operations,
production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001
```

`TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001` is implemented locally.

The project now has a Coverage v1.1 snapshot after the BOPV API discovery adapter:

```text
docs/reports/source-coverage-v1-1-snapshot-2026-05-24.md
```

Coverage v1.1 summarizes the executable registry and current RSS/API monitor/MCP capabilities:

```text
total sources: 22
metadata_adapter_validated: 9
inventory_only: 12
paused: 1
RSS/Atom discovery sources: BOE, BOJA, BOCYL
API discovery sources: BOPV
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

It also recorded that MCP source coverage still read latest discovery entries from RSS JSONL only;
that gap is now closed by `TASK-MCP-API-DISCOVERY-OUTPUT-001`.

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior,
RSS/API writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills,
VPS operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-BOPV-API-001
```

`TASK-SOURCE-BOPV-API-001` is implemented locally.

BOPV now has a metadata-only REST/API discovery adapter:

```text
src/official_sources/api_monitor.py
official-sources api monitor --source BOPV --date YYYY-MM-DD --limit N
```

The registry declares the official Open Data Euskadi BOPV administrative acts endpoint:

```text
https://api.euskadi.eus/bopv/administrative-acts/{year}/{month}
```

Default behavior is preview-only. JSONL output is written only with explicit `--write`:

```text
data/api_monitor/BOPV/<YYYY-MM-DD>/api_discovery.jsonl
```

A live bounded preview was run one source at a time with `--limit 1` and without `--write`; it
returned `records=1`, `candidate_status=not_candidate`, and `evidence_status=not_evidence`.

This task did not create source candidates, evidence-grade records, PDFs, artifacts, downstream
writes, backfills, broad historical imports, VPS operations, production DB operations, publication,
or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-COVERAGE-V1-SNAPSHOT-001
```

The project now has a canonical Coverage v1 snapshot:

```text
docs/reports/source-coverage-v1-snapshot-2026-05-24.md
```

Coverage v1 summarizes the executable registry and current monitor/MCP capabilities:

```text
total sources: 22
metadata_adapter_validated: 9
inventory_only: 12
paused: 1
validated RSS/Atom discovery sources: BOCYL, BOE, BOJA
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

This snapshot is reporting/control-plane only. It did not add sources, ingestion behavior, RSS
writes, candidates, evidence-grade records, PDFs, artifacts, downstream writes, backfills, VPS
operations, production DB operations, or LLM classification.

Previous completed source-platform task:

```text
TASK-SOURCE-RSS-MONITOR-002
```

The RSS/Atom discovery monitor now has three validated feed-backed sources:

```text
BOCYL rss  https://bocyl.jcyl.es/rss.do
BOE   rss  https://www.boe.es/rss/boe.php
BOJA  atom https://www.juntadeandalucia.es/boja/distribucion/boja.xml
```

BOE and BOJA were added as metadata-only discovery sources. Live preview smokes were run one source
at a time with `--limit 1` and without `--write`.

No source candidates, evidence-grade records, PDFs, artifacts, downstream writes, VPS operations,
production DB operations, backfills, publication, or LLM classification were added by this task.

DOGC was not added because no stable official RSS/Atom feed was verified for this task. BOPV remains
out of RSS expansion and should stay a separate REST/API task.

Earlier completed source-platform task:

```text
TASK-MCP-SOURCE-COVERAGE-001
```

The MCP/read-only interface now exposes source coverage from the executable registry and
metadata-only RSS discovery output:

```text
list_sources
get_source_status
list_monitorable_sources
list_latest_discovery_entries
```

These MCP tools read:

```text
config/sources.yaml
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

They do not fetch live feeds, create files, create source candidates, create evidence-grade records,
download PDFs, write artifacts, write downstream repos, run VPS operations, run production DB
operations, run backfills, publish data, or add LLM classification.

Earlier completed source-platform task:

```text
TASK-SOURCE-RSS-MONITOR-001
```

The project now has a metadata-only RSS/Atom discovery monitor:

```text
src/official_sources/rss_monitor.py
official-sources rss monitor --source BOCYL --date YYYY-MM-DD
```

The pilot source is BOCYL through its validated RSS feed:

```text
https://bocyl.jcyl.es/rss.do
```

Default behavior is preview-only. JSONL output is written only with explicit `--write`:

```text
data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl
```

No source candidates, evidence-grade records, PDFs, artifacts, downstream writes, VPS operations,
production DB operations, backfills, publication, or LLM classification were added by this task.

Earlier completed source-platform task:

```text
TASK-SOURCE-REGISTRY-001
```

The executable canonical source registry remains:


```text
config/sources.yaml
```

The registry is validated by:

```text
tests/test_source_registry.py
```

It is exposed read-only through:

```text
official-sources sources list
official-sources sources status --source BOCYL
```

Previous accepted decision:

```text
TASK-SOURCE-PLATFORM-001
```

Accepted boundary:

```text
official-sources = upstream official-source ingestion and evidence platform
downstream projects = staging + review + product decisions
```

The operative map is:

```text
docs/CROSS_PROJECT_INTEGRATION_MAP.md
```

The supporting report is:

```text
docs/reports/CROSS_PROJECT_INTEGRATION_MAP_2026-05-24.md
```

## Active Boundary

`official-sources` remains the common upstream platform for official source ingestion, evidence,
citations, integrity metadata, scoped artifact availability, candidate/evidence review records,
downstream-ready evidence exports, and alert-grade dry-run/export feeds.

It must not become a downstream product backend.

Hard guardrails:

- No new `oposiciones2.0` write actions from `official-sources`.
- No alert-grade to `source_candidates` conversion.
- No product records created by `official-sources`.
- No notifications, subscriptions, ranking, publication, or product workflow ownership in
  `official-sources`.
- Next allowed platform work must be one source operation at a time.
- Product-local design or preview work must happen inside the downstream repo, not in
  `official-sources`.

## Accepted Task Log

| Task | Status | Decision artifact | Notes |
| --- | --- | --- | --- |
| `TASK-SOURCE-PLATFORM-001` | Accepted | `docs/CROSS_PROJECT_INTEGRATION_MAP.md` | Locks `official-sources` as an upstream official-source ingestion/evidence platform and keeps downstream product decisions out of the platform. |
| `TASK-SOURCE-REGISTRY-001` | Implemented locally | `config/sources.yaml`, `docs/reports/source-registry-2026-05-24.md` | Adds the canonical executable registry for source coverage and status reporting. |
| `TASK-SOURCE-RSS-MONITOR-001` | Closed in main | `src/official_sources/rss_monitor.py`, `tests/test_rss_monitor.py`, `docs/reports/rss-monitor-pilot-2026-05-24.md` | Adds metadata-only RSS/Atom discovery with BOCYL as the original pilot source; current main also validates BOE RSS through later RSS/coverage work. |
| `TASK-MCP-SOURCE-COVERAGE-001` | Implemented locally | `src/official_sources/source_coverage.py`, `docs/reports/mcp-source-coverage-2026-05-24.md` | Exposes source coverage and existing RSS discovery output through read-only MCP tools. |
| `TASK-SOURCE-RSS-MONITOR-002` | Implemented locally | `config/sources.yaml`, `docs/reports/rss-monitor-expansion-2026-05-24.md` | Adds BOE and BOJA as validated metadata-only RSS/Atom discovery sources. |
| `TASK-SOURCE-COVERAGE-V1-SNAPSHOT-001` | Implemented locally | `docs/reports/source-coverage-v1-snapshot-2026-05-24.md` | Captures the v1 source coverage baseline from the executable registry and read-only MCP/monitor capabilities. |
| `TASK-SOURCE-BOPV-API-001` | Implemented locally | `src/official_sources/api_monitor.py`, `docs/reports/bopv-api-discovery-adapter-2026-05-24.md` | Adds metadata-only BOPV REST/API discovery from the official Open Data Euskadi endpoint. |
| `TASK-SOURCE-COVERAGE-V1.1-SNAPSHOT-001` | Implemented locally | `docs/reports/source-coverage-v1-1-snapshot-2026-05-24.md` | Captures the v1.1 coverage baseline after adding BOPV API discovery. |
| `TASK-MCP-API-DISCOVERY-OUTPUT-001` | Implemented locally | `src/official_sources/source_coverage.py`, `docs/reports/mcp-api-discovery-output-2026-05-24.md` | Extends the read-only MCP discovery reader to existing RSS and API discovery JSONL. |
| `TASK-SOURCE-COVERAGE-INTEGRATION-CHECK-001` | Implemented locally | `docs/reports/source-coverage-integration-check-2026-05-24.md` | Validates the integrated registry, RSS monitor, API monitor, and MCP coverage/discovery line. |
| `TASK-MCP-COVERAGE-USAGE-DOCS-001` | Implemented locally | `docs/SOURCE_COVERAGE_USAGE.md`, `docs/MCP_TOOLS.md`, `README.md` | Documents CLI and MCP source coverage usage with safety boundaries. |
| `TASK-SOURCE-COVERAGE-SCHEDULE-001` | Implemented locally | `docs/SOURCE_COVERAGE_RUN_PLAN.md`, `docs/reports/source-coverage-schedule-2026-05-24.md` | Defines controlled one-source-at-a-time discovery run plan and report template. |
| `TASK-SOURCE-RSS-MONITOR-003` | Implemented locally | `config/sources.yaml`, `docs/reports/rss-monitor-003-verified-feeds-2026-05-24.md` | Adds BOIB, BOC_CANTABRIA, and DOE as validated metadata-only RSS discovery sources; DOGC and BON were not added. |
| `TASK-SOURCE-COVERAGE-V1.2-SNAPSHOT-001` | Implemented locally | `docs/reports/source-coverage-v1-2-snapshot-2026-05-24.md` | Captures the v1.2 coverage baseline after RSS-003, including six RSS/Atom sources and one API discovery source. |
| `TASK-DEV-CLI-ENTRYPOINT-CONSISTENCY-001` | Implemented locally | `src/official_sources/cli.py`, `docs/reports/cli-entrypoint-consistency-2026-05-24.md` | Makes `python -m official_sources.cli` usable for source-tree validation and documents stale console script handling. |
| `TASK-VPS-INTEGRITY-CHECK-RAW-METADATA-001` | Implemented locally | `src/official_sources/cli.py`, `tests/test_cli.py`, `docs/reports/vps-service-drift-diagnosis-2026-05-26.md` | Clarifies local artifact integrity so non-local raw metadata rows do not fail the check while missing real local artifacts still fail. |
| `TASK-DOCS-RSS-MONITOR-STATE-RECONCILIATION-001` | Merged | `docs/reports/rss-monitor-state-reconciliation-2026-05-26.md`, `PROJECT_STATE.md`, `TASK_QUEUE.md` | Reconciles RSS monitor documentation with current main and confirms RSS-001 should not be reopened. |
| `TASK-SOURCE-RSS-MONITOR-004` | Implemented locally | `config/sources.yaml`, `tests/test_rss_monitor.py`, `docs/reports/rss-monitor-004-2026-05-26.md` | Adds BOC_CANARIAS, DOG, and BOP_LUGO as validated metadata-only RSS discovery sources. |

## Next Allowed Work

Allowed next work:

1. `TASK-SOURCE-COVERAGE-V1.6-SNAPSHOT-001` if a fresh coverage snapshot is wanted after RSS-004.
2. `TASK-SOURCE-RSS-MONITOR-005` only after selecting another 2-3 verified official RSS/Atom feeds.
3. `TASK-SOURCE-HTML-MONITOR-PILOT-001` only for sources without RSS/API after source-specific audit.
4. `TASK-SOURCE-COVERAGE-RUN-REPORT-001` if actual metadata-only JSONL writes are run.
5. `TASK-MCP-DISCOVERY-OUTPUT-SAMPLES-001` if sample discovery outputs are needed.
6. Product-local design/preview for draft process creation in `oposiciones2.0`.
7. Evidence-grade staging work in `EduAyudas` or `la-ayuda` only after their local states are clean.
8. A source-needs audit for `renta-verificable` before any integration.

Not allowed from this repo:

- downstream writes;
- DB/VPS operations without a separate source-specific task;
- broad imports or backfills;
- alert storage implementation before product storage is approved;
- `oposiciones2.0` product record creation.
