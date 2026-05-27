# Official Bulletin Registry

This registry is a static coverage inventory for `official-sources`.

Executable registry:

```text
config/sources.yaml
```

`config/sources.yaml` is now the canonical machine-readable source registry. This Markdown file
remains the narrative coverage inventory seeded from the BOE index.

The 2026-05-25 official-directory reconciliation mirrored provincial bulletin directory entries
from BOE/PAG into `config/sources.yaml` as `inventory_only` records. These entries are official
directory inventory only: they are not RSS/API monitors, candidates, evidence, or validated HTML
monitors.

`BOP_A_CORUNA` was later promoted from provincial inventory to a single-source metadata-only HTML
discovery pilot. `BOP_ALBACETE` and `BOP_ALICANTE` were then added as the next two provincial
HTML discovery monitors after technical preview validation. This does not change the rest of the
provincial inventory entries.

`BOC_CANARIAS`, `DOG`, and `BOP_LUGO` were later promoted to metadata-only RSS discovery monitors.
`BOC_CANARIAS` is section-scoped, and `BOP_LUGO` may expose PDF URLs as RSS metadata only.

The executable registry separates:

```text
official_landing_url = public canonical landing page
access_methods[].url = technical endpoint/feed/page for adapters or monitors
```

Validated registry commands:

```bash
official-sources sources list
official-sources sources status --source BOCYL
```

Metadata-only RSS/Atom discovery command:

```bash
official-sources rss monitor --source BOCYL --date YYYY-MM-DD
official-sources rss monitor --source BOE --date YYYY-MM-DD
official-sources rss monitor --source BOJA --date YYYY-MM-DD
official-sources rss monitor --source BOIB --date YYYY-MM-DD
official-sources rss monitor --source BOC_CANTABRIA --date YYYY-MM-DD
official-sources rss monitor --source DOE --date YYYY-MM-DD
official-sources rss monitor --source BOC_CANARIAS --date YYYY-MM-DD
official-sources rss monitor --source DOG --date YYYY-MM-DD
official-sources rss monitor --source BOP_LUGO --date YYYY-MM-DD
```

Metadata-only HTML discovery command:

```bash
official-sources html monitor --source BOP_A_CORUNA --date YYYY-MM-DD
official-sources html monitor --source BOP_ALBACETE --date YYYY-MM-DD
official-sources html monitor --source BOP_ALICANTE --date YYYY-MM-DD
```

RSS/Atom discovery records are not candidates and are not evidence. The command defaults to
preview mode; JSONL output under `data/rss_monitor/<source_code>/<YYYY-MM-DD>/rss_discovery.jsonl`
requires explicit `--write`.

Registry validation rejects ambiguous operational states and keeps `candidate_creation_allowed`
and `evidence_grade_allowed` explicit. Both are `false` by default in the current source data.

It uses the BOE "Otros diarios oficiales" page as the initial official index for European,
autonomous/statutory territory, and provincial bulletin coverage. It is not an ingestion API and
does not imply that a source has a validated adapter.

Source index:

- <https://www.boe.es/legislacion/otros_diarios_oficiales.php>

Last checked: 2026-05-25.

## Status Values

| status | Meaning |
| --- | --- |
| `implemented` | Adapter/source support is already implemented and validated in this project. |
| `pilot_validated` | Metadata/source pilot has been validated, but the source is not a fully generalized coverage surface. |
| `mvp_implemented_backfill_validated` | Metadata MVP exists and controlled metadata backfill has been validated. |
| `mvp_implemented_paused` | MVP exists, but further backfill/source work is paused on a known operational issue. |
| `mvp_implemented` | Metadata MVP exists for the official source. |
| `not_audited` | Source is listed in the official registry but has not been assessed for adapter feasibility. |

## Coverage Matrix

| source_code | official_name | level | jurisdiction | territory | official_url | boe_index_label | current_status | adapter_priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOE | Boletin Oficial del Estado | state | ES | Spain | https://www.boe.es/diario_boe/ | Project Tier 1 source, not part of BOE "Otros diarios oficiales" page | implemented | P0 | Mature project source for state publications, artifacts, and consolidated legislation. RSS discovery uses the official complete BOE feed. |
| BDNS | Base de Datos Nacional de Subvenciones / Sistema Nacional de Publicidad de Subvenciones y Ayudas Publicas | state | ES | Spain | https://www.infosubvenciones.es/bdnstrans/GE/es/index | Not listed on BOE "Otros diarios oficiales"; tracked here as an official high-value grants registry | mvp_implemented | P0 | Metadata-only MVP is implemented for public grant calls (`convocatorias`). BDNS ingestion is high value for subsidy-focused products, but BDNS is not a bulletin source. |
| DOUE | Diario Oficial de la Union Europea | eu | EU | European Union | http://eur-lex.europa.eu/JOIndex.do?ihmlang=es | Diario Oficial de la Union Europea (DOUE) | not_audited | not_prioritized | Listed by BOE under Union Europea. Treat as registry coverage only until a EUR-Lex/DOUE audit exists. |
| BOJA | Boletin Oficial de la Junta de Andalucia | autonomous | ES-AN | Andalucia | https://www.juntadeandalucia.es/eboja | Boletin Oficial de la Junta de Andalucia (BOJA) y base de datos de legislacion | pilot_validated | done | Metadata adapter and controlled pilot have been validated; Atom discovery uses the official complete BOJA web feed. Candidate/downstream work remains controlled. |
| BOA | Boletin Oficial de Aragon | autonomous | ES-AR | Aragon | https://www.boa.aragon.es/ | Boletin Oficial de Aragon (BOA) y base de datos de legislacion | not_audited | not_prioritized | Registry entry only. Audit endpoint model, identifiers, robots, and fixture strategy before implementation. |
| BOPA | Boletin Oficial del Principado de Asturias | autonomous | ES-AS | Principado de Asturias | https://sede.asturias.es/servicios-del-bopa | Boletin Oficial del Principado de Asturias (BOPA) y base de datos de legislacion | not_audited | not_prioritized | Registry entry only. Audit endpoint model, identifiers, robots, and fixture strategy before implementation. |
| BOIB | Boletin Oficial de las Illes Balears | autonomous | ES-IB | Illes Balears | http://www.caib.es/eboibfront/?lang=es | Boletin Oficial de las Illes Balears (BOIB) | metadata_monitor_validated | done | RSS discovery uses the official BOIB feed linked from the BOIB landing page and service RSS section. BOE also links a separate legislation database for this territory. |
| BOC_CANARIAS | Boletin Oficial de Canarias | autonomous | ES-CN | Canarias | http://www.gobiernodecanarias.org/boc/ | Boletin Oficial de Canarias (BOC) | metadata_monitor_validated | done | RSS discovery uses an official BOC section feed for "I. Disposiciones generales"; it is section-scoped, not complete bulletin coverage. BOE also links a separate legislation database for this territory. |
| BOC_CANTABRIA | Boletin Oficial de Cantabria | autonomous | ES-CB | Cantabria | https://boc.cantabria.es/boces/ | Boletin Oficial de Cantabria (BOC) y base de datos de legislacion | metadata_monitor_validated | done | RSS discovery uses an official BOC category feed for "1 Disposiciones Generales"; it is category-scoped, not complete bulletin coverage. |
| DOCM | Diario Oficial de Castilla-La Mancha | autonomous | ES-CM | Castilla-La Mancha | http://docm.castillalamancha.es/portaldocm/sumario.do | Diario Oficial de Castilla-La Mancha (DOCM) y base de datos de legislacion | not_audited | not_prioritized | Registry entry only. Audit endpoint model, identifiers, robots, and fixture strategy before implementation. |
| BOCYL | Boletin Oficial de Castilla y Leon | autonomous | ES-CL | Castilla y Leon | https://bocyl.jcyl.es/portada.do | Boletin Oficial de Castilla y Leon (BOCYL) | metadata_monitor_validated | done | Metadata adapter and RSS discovery pilot have been validated. BOE also links a separate legislation database for this territory. |
| DOGC | Diari Oficial de la Generalitat de Catalunya | autonomous | ES-CT | Catalunya | https://dogc.gencat.cat/es/index.html?newLang=es_ES&language=es_ES | Diari Oficial de la Generalitat de Catalunya (DOGC) | not_audited | not_prioritized | Registry entry only. BOE also links a separate legislation database for this territory. |
| DOE | Diario Oficial de Extremadura | autonomous | ES-EX | Extremadura | http://doe.juntaex.es/ | Diario Oficial de Extremadura (DOE) y base de datos de legislacion | metadata_monitor_validated | done | RSS discovery uses the official DOE "SUMARIO COMPLETO" RSS endpoint linked from the DOE RSS page. |
| DOG | Diario Oficial de Galicia | autonomous | ES-GA | Galicia | https://www.xunta.gal/diario-oficial-galicia/portalPublicoHome.do?lang=es | Diario Oficial de Galicia (DOG) | metadata_monitor_validated | done | RSS discovery uses the official DOG complete summary feed linked from the DOG RSS subscriptions page. BOE also links a separate legislation database for this territory. |
| BOR | Boletin Oficial de La Rioja | autonomous | ES-RI | La Rioja | http://www.larioja.org/bor/es | Boletin Oficial de la Rioja (BOR) | not_audited | not_prioritized | Registry entry only. BOE also links a separate legislation database for this territory. |
| BOCM | Boletin Oficial de la Comunidad de Madrid | autonomous | ES-MD | Comunidad de Madrid | http://www.bocm.es/ | Boletin Oficial de la Comunidad de Madrid (BOCM) | mvp_implemented_paused | paused | Metadata MVP exists, but broader work is paused on endpoint/connectivity instability observed during backfill. |
| BORM | Boletin Oficial de la Region de Murcia | autonomous | ES-MC | Region de Murcia | https://www.borm.es/#/home/ | Boletin Oficial de la Region de Murcia (BORM) | not_audited | not_prioritized | Registry entry only. BOE also links a separate legislation database for this territory. |
| BON | Boletin Oficial de Navarra | autonomous | ES-NC | Comunidad Foral de Navarra | http://www.navarra.es/home_es/Actualidad/BON/ | Boletin Oficial de Navarra (BON) | not_audited | not_prioritized | Registry entry only. BOE also links a separate legislation database for this territory. |
| BOPV | Boletin Oficial del Pais Vasco | autonomous | ES-PV | Pais Vasco | https://www.euskadi.eus/y22-bopv/es/bopv2/datos/Ultimo.shtml | Boletin Oficial del Pais Vasco (BOPV) | metadata_api_discovery_validated | done | Metadata adapter exists and metadata-only REST/API discovery now uses the official Open Data Euskadi administrative acts endpoint. |
| DOGV | Diari Oficial de la Generalitat Valenciana | autonomous | ES-VC | Comunitat Valenciana | https://dogv.gva.es/es/inici | Diari Oficial de la Generalitat Valenciana (DOGV) y base de datos de legislacion | mvp_implemented_backfill_validated | P1 | Metadata MVP and controlled 30-day metadata backfill are validated. Recommended next step: candidate dry-run, not more adapter discovery. |
| BOCCE | Boletin Oficial de la Ciudad Autonoma de Ceuta | statutory_city | ES-CE | Ceuta | http://www.ceuta.es/ceuta/documentos/ | Boletin Oficial de la Ciudad Autonoma de Ceuta (BOCCE) | not_audited | not_prioritized | Registry entry only. Prior audit notes suggest deferring implementation until another cleaner autonomous adapter is stable. |
| BOME | Boletin Oficial de la Ciudad Autonoma de Melilla | statutory_city | ES-ML | Melilla | https://bomemelilla.es/ | Boletin Oficial de la Ciudad Autonoma de Melilla (BOME) | not_audited | not_prioritized | Registry entry only. Prior audit notes suggest deferring implementation until another cleaner autonomous adapter is stable. |
| BOP_A_CORUNA | Boletin Oficial de la Provincia de A Coruna | provincial | A Coruna | A Coruna | https://bop.dacoruna.gal/bopportal/ | A Coruna | pilot_validated | after_autonomous_p1 | Metadata-only HTML discovery pilot; no PDFs/artifacts/candidates/evidence. |
| BOP_ALBACETE | Boletin Oficial de la Provincia de Albacete | provincial | Albacete | Albacete | https://bop.dipualba.es | Albacete | pilot_validated | after_autonomous_p1 | Metadata-only current-bulletin HTML discovery; PDF page URLs are recorded but never downloaded. |
| BOP_ALICANTE | Boletin Oficial de la Provincia de Alicante | provincial | Alicante | Alicante | https://sede.diputacionalicante.es/consultas-bop/ | Alicante | pilot_validated | after_autonomous_p1 | Metadata-only discovery uses the official consultation-page backing endpoint one date at a time. |
| BOP_ALMERIA | Boletin Oficial de la Provincia de Almeria | provincial | Almeria | Almeria | http://www.dipalme.org/Servicios/cmsdipro/index.nsf/bop_view.xsp?p=dipalme | Almeria | not_audited | after_autonomous_p1 | Evaluated for provincial discovery 002 but not added; official surface is a ZK/JavaScript app and needs a separate endpoint/JS-capable audit. |
| BOP_ARABA_ALAVA | Boletin Oficial del Territorio Historico de Araba/Alava | provincial | Araba/Alava | Araba/Alava | http://www.araba.eus/botha/Inicio/SGBO5001.aspx | Araba/Alava | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_AVILA | Boletin Oficial de la Provincia de Avila | provincial | Avila | Avila | https://www.diputacionavila.es/boletin-oficial/ | Avila | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_BADAJOZ | Boletin Oficial de la Provincia de Badajoz | provincial | Badajoz | Badajoz | http://www.dip-badajoz.es/bop/ | Badajoz | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_BARCELONA | Boletin Oficial de la Provincia de Barcelona | provincial | Barcelona | Barcelona | http://bop.diba.cat | Barcelona | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_BIZKAIA | Boletin Oficial de Bizkaia | provincial | Bizkaia | Bizkaia | http://apps.bizkaia.eus/BT00/ | Bizkaia | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_BURGOS | Boletin Oficial de la Provincia de Burgos | provincial | Burgos | Burgos | http://bopbur.diputaciondeburgos.es/ | Burgos | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_CACERES | Boletin Oficial de la Provincia de Caceres | provincial | Caceres | Caceres | https://bop.dip-caceres.es/bop/index.html | Caceres | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_CADIZ | Boletin Oficial de la Provincia de Cadiz | provincial | Cadiz | Cadiz | http://www.bopcadiz.org | Cadiz | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_CASTELLON | Boletin Oficial de la Provincia de Castellon | provincial | Castellon | Castellon | http://bop.dipcas.es/PortalBOP/boletin.do | Castellon | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_CIUDAD_REAL | Boletin Oficial de la Provincia de Ciudad Real | provincial | Ciudad Real | Ciudad Real | https://bop.dipucr.es/ | Ciudad Real | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_CORDOBA | Boletin Oficial de la Provincia de Cordoba | provincial | Cordoba | Cordoba | https://bop.dipucordoba.es/ | Cordoba | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_CUENCA | Boletin Oficial de la Provincia de Cuenca | provincial | Cuenca | Cuenca | https://www.dipucuenca.es/boletin-oficial-de-la-provincia | Cuenca | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_GIPUZKOA | Boletin Oficial de Gipuzkoa | provincial | Gipuzkoa | Gipuzkoa | https://egoitza.gipuzkoa.eus/es/bog | Gipuzkoa | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_GIRONA | Boletin Oficial de la Provincia de Girona | provincial | Girona | Girona | http://www.ddgi.cat/ | Girona | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_GRANADA | Boletin Oficial de la Provincia de Granada | provincial | Granada | Granada | https://www.dipgra.es/bop/ | Granada | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_GUADALAJARA | Boletin Oficial de la Provincia de Guadalajara | provincial | Guadalajara | Guadalajara | http://boletin.dguadalajara.es/ | Guadalajara | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_HUELVA | Boletin Oficial de la Provincia de Huelva | provincial | Huelva | Huelva | https://sede.diphuelva.es/servicios/bop | Huelva | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_HUESCA | Boletin Oficial de la Provincia de Huesca | provincial | Huesca | Huesca | http://bop.dphuesca.es/ | Huesca | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_JAEN | Boletin Oficial de la Provincia de Jaen | provincial | Jaen | Jaen | http://bop.dipujaen.es/ | Jaen | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_LAS_PALMAS | Boletin Oficial de la Provincia de Las Palmas | provincial | Las Palmas | Las Palmas | http://www.boplaspalmas.com | Las Palmas | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_LEON | Boletin Oficial de la Provincia de Leon | provincial | Leon | Leon | https://bop.dipuleon.es/ | Leon | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_LLEIDA | Boletin Oficial de la Provincia de Lleida | provincial | Lleida | Lleida | https://ebop.diputaciolleida.cat/bop/ | Lleida | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_LUGO | Boletin Oficial da Provincia de Lugo | provincial | Lugo | Lugo | http://www.deputacionlugo.gal/boletin-oficial-da-provincia-de-lugo | Lugo | metadata_monitor_validated | done | RSS discovery uses the official BOP Lugo feed linked from the bulletin landing page; PDF links in summaries remain metadata only. |
| BOP_MALAGA | Boletin Oficial de la Provincia de Malaga | provincial | Malaga | Malaga | http://www.bopmalaga.es/ | Malaga | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_OURENSE | Boletin Oficial da Provincia de Ourense | provincial | Ourense | Ourense | https://bop.depourense.es/portal/ | Ourense | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_PALENCIA | Boletin Oficial de la Provincia de Palencia | provincial | Palencia | Palencia | https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia | Palencia | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_PONTEVEDRA | Boletin Oficial de la Provincia de Pontevedra | provincial | Pontevedra | Pontevedra | https://boppo.depo.gal/es | Pontevedra | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_SALAMANCA | Boletin Oficial de la Provincia de Salamanca | provincial | Salamanca | Salamanca | https://sede.diputaciondesalamanca.gob.es/BOP/ | Salamanca | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_SANTA_CRUZ_TENERIFE | Boletin Oficial de la Provincia de Santa Cruz de Tenerife | provincial | Santa Cruz de Tenerife | Santa Cruz de Tenerife | http://www.bopsantacruzdetenerife.es/ | Santa Cruz de Tenerife | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_SEGOVIA | Boletin Oficial de la Provincia de Segovia | provincial | Segovia | Segovia | http://www.dipsegovia.es/bop | Segovia | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_SEVILLA | Boletin Oficial de la Provincia de Sevilla | provincial | Sevilla | Sevilla | https://bopsevilla.dipusevilla.es/publica/consulta-de-bops/ | Sevilla | pilot_validated | after_autonomous_p1 | Metadata-only current-bulletin HTML discovery uses the public date-scoped BOP listing; no PDFs/artifacts/candidates/evidence. |
| BOP_SORIA | Boletin Oficial de la Provincia de Soria | provincial | Soria | Soria | http://bop.dipsoria.es/ | Soria | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_TARRAGONA | Butlleti Oficial de la Provincia de Tarragona | provincial | Tarragona | Tarragona | http://www.diputaciodetarragona.cat/ebop/ | Tarragona | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_TERUEL | Boletin Oficial de la Provincia de Teruel | provincial | Teruel | Teruel | http://www.dpteruel.es/boletines.htm | Teruel | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_TOLEDO | Boletin Oficial de la Provincia de Toledo | provincial | Toledo | Toledo | http://bop.diputoledo.es/webEbop/inicio.jsp | Toledo | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_VALENCIA | Boletin Oficial de la Provincia de Valencia | provincial | Valencia | Valencia | https://bop.dival.es/bop/drvisapi.dll | Valencia | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_VALLADOLID | Boletin Oficial de la Provincia de Valladolid | provincial | Valladolid | Valladolid | https://bop.sede.diputaciondevalladolid.es/ | Valladolid | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_ZAMORA | Boletin Oficial de la Provincia de Zamora | provincial | Zamora | Zamora | https://www.diputaciondezamora.es/opencms/servicios/BOP/bop/index.html | Zamora | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |
| BOP_ZARAGOZA | Boletin Oficial de la Provincia de Zaragoza | provincial | Zaragoza | Zaragoza | http://bop.dpz.es/BOPZ/ | Zaragoza | not_audited | after_autonomous_p1 | BOE provincial registry entry only; audit before adapter work. |

## Prioritization

Recommended next audits and implementation work:

1. DOGV candidate dry-run next: DOGV already has a validated metadata MVP and controlled metadata
   backfill, so the next useful step is a constrained candidate dry-run.
2. BOCM retry later: keep BOCM paused until the connectivity/endpoint instability observed during
   the metadata backfill can be retried cleanly and the endpoint issue is resolved.
3. BDNS ingestion: keep BDNS high priority because public grant calls are high-value source data
   for subsidy-focused downstream products.
4. Provincial bulletins: defer BOP sources until a provincial strategy is defined. The BOE page is
   useful as coverage inventory, but each provincial source needs its own endpoint, identifier,
   robots, fixture, and citation assessment.

## Counts

- State sources listed: 2, including BDNS as a non-bulletin official grants registry.
- European sources listed from BOE index: 1.
- Autonomous/statutory territory sources listed from BOE index: 19.
- Provincial sources listed from BOE index: 43.
