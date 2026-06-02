# Ayuntamiento de Zaragoza Employment API Monitor

Date: 2026-06-01

## Decision

`AYTO_ZARAGOZA_EMPLEO` is now a local metadata-only API discovery monitor for Zaragoza municipal
public-employment notices.

This is intentionally separate from `BOP_ZARAGOZA`. At the time of this task, the provincial BOPZ
parser path existed but direct VPS fetch timed out. Later `REL-001` relay probes still did not
produce a validated VPS runtime path for `BOP_ZARAGOZA`; the municipal employment source remains a
distinct city-level employment surface and is not a provincial BOP substitute.

## Official Source

- Landing page: `https://www.zaragoza.es/oferta/`
- Open-data JSON endpoint: `https://www.zaragoza.es/sede/servicio/oferta-empleo.json`

The endpoint is listed as an Ayuntamiento de Zaragoza public-employment dataset and returns dated
employment-notice groups. The monitor filters entries by the requested notice date and emits one
metadata record per matching notice.

## Boundaries

- metadata-only API discovery;
- one requested date per preview;
- no detail-page crawling;
- no PDF or attachment download;
- no candidate creation;
- no evidence-grade records;
- no broad backfill;
- no downstream writes;
- no VPS, Hermes, systemd, timer, or relay changes.

All records keep:

```text
candidate_status=not_candidate
evidence_status=not_evidence
classification_status=unclassified
```

## Validation

Local full-suite tests:

```text
rtk python -m pytest -q
```

Result:

```text
725 passed, 2 warnings
```

The warnings are existing third-party deprecation warnings from Starlette/python-multipart and
key_value/Pydantic schema generation.

Additional checks:

```text
rtk python -m ruff check src tests
git diff --check
rtk python -m official_sources.cli api monitor --source AYTO_ZARAGOZA_EMPLEO --date 2026-06-01 --limit 2
```

The live preview returned `records=2` in preview mode and did not create `data/api_monitor`,
`data/html_monitor`, or `data/rss_monitor`.
