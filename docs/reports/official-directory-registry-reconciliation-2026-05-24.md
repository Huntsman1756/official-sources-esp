# Official directory registry reconciliation - 2026-05-24

Task: `TASK-SOURCE-OFFICIAL-DIRECTORY-001`

Run date: 2026-05-25

## Scope

This task reconciled the executable source registry against official bulletin directory pages.
It is inventory/control-plane work only.

It did not add monitors, candidates, evidence-grade records, PDFs, artifacts, backfills,
RSS/API writes, downstream writes, broad monitor runs, VPS operations, production DB operations,
publication, or LLM classification.

## Directory Pages Reviewed

- BOE "Otros diarios oficiales": `https://www.boe.es/legislacion/otros_diarios_oficiales.php`
- PAG general "Boletines Oficiales": `https://administracion.gob.es/pag_Home/espanaAdmon/boletinesYLegislacion/boletinesOficiales.html`
- PAG CCAA "Boletines oficiales de las Comunidades Autonomas": `https://administracion.gob.es/pag_Home/espanaAdmon/boletinesYLegislacion/BO_CCAA.html`
- PAG diputaciones "Boletines oficiales de las Diputaciones Provinciales": `https://administracion.gob.es/pag_Home/espanaAdmon/boletinesYLegislacion/BO_Diputaciones.html`

These pages are official directory/inventory sources. They are not ingestion APIs, not evidence
sources, and not proof that a source has a validated monitor.

## Registry Counts

Before this task:

```text
total sources: 22
provincial sources: 0
candidate_creation_allowed=false: 22
evidence_grade_allowed=false: 22
```

After this task:

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

## Autonomous Coverage

The 19 autonomous/statutory-city bulletin entries were already represented in
`config/sources.yaml`:

```text
BOJA, BOA, BOPA, BOIB, BOC_CANARIAS, BOC_CANTABRIA, DOCM, BOCYL, DOGC,
DOE, DOG, BOR, BOCM, BORM, BON, BOPV, DOGV, BOCCE, BOME
```

No autonomous source was promoted or reclassified in this task.

## Provincial Coverage

The registry lacked provincial bulletin entries before this task. The following 43 official
provincial bulletin entries were added as `inventory_only`:

```text
BOP_A_CORUNA
BOP_ALBACETE
BOP_ALICANTE
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
BOP_CIUDAD_REAL
BOP_CORDOBA
BOP_CUENCA
BOP_GIPUZKOA
BOP_GIRONA
BOP_GRANADA
BOP_GUADALAJARA
BOP_HUELVA
BOP_HUESCA
BOP_JAEN
BOP_LAS_PALMAS
BOP_LEON
BOP_LLEIDA
BOP_LUGO
BOP_MALAGA
BOP_OURENSE
BOP_PALENCIA
BOP_PONTEVEDRA
BOP_SALAMANCA
BOP_SANTA_CRUZ_TENERIFE
BOP_SEGOVIA
BOP_SEVILLA
BOP_SORIA
BOP_TARRAGONA
BOP_TERUEL
BOP_TOLEDO
BOP_VALENCIA
BOP_VALLADOLID
BOP_ZAMORA
BOP_ZARAGOZA
```

Each new entry uses:

```text
jurisdiction_level: provincial
operational_status: inventory_only
monitor_support: none
backfill_support: none
evidence_adapter: false
candidate_creation_allowed: false
evidence_grade_allowed: false
access_methods[].type: html
access_methods[].status: inventory
```

The `html` access method is a directory landing URL only. It is not a validated HTML monitor.

## Exclusions And Non-Additions

The PAG diputaciones page states that provinces belonging to uniprovincial autonomous communities,
and Ceuta/Melilla, do not have separate provincial bulletins. No extra provincial source was added
for those cases.

No parliamentary bulletin, assembly bulletin, municipal bulletin, RSS feed, REST API, search
endpoint, evidence adapter, or candidate path was added in this task.

## Naming And URL Notes

BOE and PAG are overlapping directory authorities, but they are not identical in every URL target.
The executable registry uses the BOE provincial directory URL where BOE already provided a direct
provincial entry.

Known URL-diff follow-up candidates include:

```text
BOP_CADIZ
BOP_GIRONA
BOP_GRANADA
BOP_LAS_PALMAS
BOP_LLEIDA
BOP_BIZKAIA
BOP_TERUEL
```

These were not changed beyond inventory insertion because the task boundary was reconciliation,
not source-specific landing-page validation.

## Safety Confirmation

Confirmed:

- no `source_candidates` were created;
- no evidence-grade records were created;
- no PDFs were downloaded;
- no artifacts were created;
- no downstream repositories were touched;
- no RSS/API writes were run;
- no broad monitors were run;
- no backfills were run;
- no VPS operations were run;
- no production DB operations were run;
- no LLM classification was added.

## Next Recommended Task

Recommended next task:

```text
TASK-SOURCE-PROVINCIAL-URL-DIFF-AUDIT-001
```

Purpose: compare BOE/PAG provincial URL differences source by source and correct only verified
landing URLs. This should remain documentation/registry-only unless a separate monitor pilot is
explicitly approved.
