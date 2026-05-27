# Provincial Read-Only Batch Audit

Date: 2026-05-27

Task: `TASK-PROVINCIAL-READONLY-BATCH-AUDIT-001`

## Scope

- read-only landing-page audit;
- one request per source;
- no login, headless browser, anti-bot bypass, monitor additions, or registry writes;
- outputs are planning evidence, not monitor validation.

## Category Counts

| Category | Count |
| --- | ---: |
| `rss_or_api_detected` | 4 |
| `open_data_detected` | 7 |
| `static_html_viable` | 5 |
| `stable_form_or_endpoint` | 14 |
| `unknown` | 8 |

## Recommended Candidates

| Source | Category | Friction | Evidence |
| --- | --- | --- | --- |
| `BOP_BARCELONA` | `open_data_detected` | `low` | Landing page exposes open-data/API vocabulary. |
| `BOP_MALAGA` | `stable_form_or_endpoint` | `medium` | Landing page exposes form/search/endpoint signals. |
| `BOP_BIZKAIA` | `stable_form_or_endpoint` | `medium` | Landing page exposes form/search/endpoint signals. |
| `BOP_VALENCIA` | `open_data_detected` | `low` | Landing page exposes open-data/API vocabulary. |
| `BOP_SEVILLA` | `stable_form_or_endpoint` | `medium` | Landing page exposes form/search/endpoint signals. |

## Defer Or Manual

| Source | Category | Friction | Action |
| --- | --- | --- | --- |
| `BOP_CADIZ` | `unknown` | `unknown` | Keep unknown/manual until a narrower source-specific check is approved. |
| `BOP_CIUDAD_REAL` | `unknown` | `unknown` | Keep unknown/manual until a narrower source-specific check is approved. |
| `BOP_CUENCA` | `unknown` | `unknown` | Keep unknown/manual until a narrower source-specific check is approved. |
| `BOP_GIRONA` | `unknown` | `unknown` | Keep unknown/manual until a narrower source-specific check is approved. |
| `BOP_GUADALAJARA` | `unknown` | `unknown` | Keep unknown/manual until a narrower source-specific check is approved. |
| `BOP_OURENSE` | `unknown` | `unknown` | Keep unknown/manual until a narrower source-specific check is approved. |
| `BOP_TARRAGONA` | `unknown` | `unknown` | Keep unknown/manual until a narrower source-specific check is approved. |
| `BOP_ZARAGOZA` | `unknown` | `high` | Keep unknown/manual until a narrower source-specific check is approved. |

`BOP_ZARAGOZA` was part of the previous second-wave planning list, but this read-only audit moves it
to defer/manual for now because the current one-request evidence returned high-friction/unknown
signals. Reconsider it only through a narrower source-specific check.

## Per-Source Results

| Source | Province | Category | Friction | Candidate | URL |
| --- | --- | --- | --- | --- | --- |
| `BOP_ARABA_ALAVA` | Boletin Oficial del Territorio Historico de Araba/Alava | `stable_form_or_endpoint` | `medium` | yes | http://www.araba.eus/botha/Inicio/SGBO5001.aspx |
| `BOP_AVILA` | la Provincia de Avila | `rss_or_api_detected` | `low` | yes | https://www.diputacionavila.es/boletin-oficial/ |
| `BOP_BADAJOZ` | la Provincia de Badajoz | `rss_or_api_detected` | `low` | yes | http://www.dip-badajoz.es/bop/ |
| `BOP_BARCELONA` | la Provincia de Barcelona | `open_data_detected` | `low` | yes | http://bop.diba.cat |
| `BOP_BIZKAIA` | Bizkaia | `stable_form_or_endpoint` | `medium` | yes | http://apps.bizkaia.eus/BT00/ |
| `BOP_BURGOS` | la Provincia de Burgos | `stable_form_or_endpoint` | `medium` | yes | http://bopbur.diputaciondeburgos.es/ |
| `BOP_CACERES` | la Provincia de Caceres | `stable_form_or_endpoint` | `medium` | yes | https://bop.dip-caceres.es/bop/index.html |
| `BOP_CADIZ` | la Provincia de Cadiz | `unknown` | `unknown` | no | http://www.bopcadiz.org |
| `BOP_CASTELLON` | la Provincia de Castellon | `stable_form_or_endpoint` | `medium` | yes | http://bop.dipcas.es/PortalBOP/boletin.do |
| `BOP_CIUDAD_REAL` | la Provincia de Ciudad Real | `unknown` | `unknown` | no | https://bop.dipucr.es/ |
| `BOP_CORDOBA` | la Provincia de Cordoba | `open_data_detected` | `low` | yes | https://bop.dipucordoba.es/ |
| `BOP_CUENCA` | la Provincia de Cuenca | `unknown` | `unknown` | no | https://www.dipucuenca.es/boletin-oficial-de-la-provincia |
| `BOP_GIPUZKOA` | Gipuzkoa | `stable_form_or_endpoint` | `medium` | yes | https://egoitza.gipuzkoa.eus/es/bog |
| `BOP_GIRONA` | la Provincia de Girona | `unknown` | `unknown` | no | http://www.ddgi.cat/ |
| `BOP_GRANADA` | la Provincia de Granada | `open_data_detected` | `low` | yes | https://www.dipgra.es/bop/ |
| `BOP_GUADALAJARA` | la Provincia de Guadalajara | `unknown` | `unknown` | no | http://boletin.dguadalajara.es/ |
| `BOP_HUELVA` | la Provincia de Huelva | `static_html_viable` | `low` | yes | https://sede.diphuelva.es/servicios/bop |
| `BOP_HUESCA` | la Provincia de Huesca | `stable_form_or_endpoint` | `medium` | yes | http://bop.dphuesca.es/ |
| `BOP_JAEN` | la Provincia de Jaen | `stable_form_or_endpoint` | `medium` | yes | http://bop.dipujaen.es/ |
| `BOP_LAS_PALMAS` | la Provincia de Las Palmas | `static_html_viable` | `low` | yes | http://www.boplaspalmas.com |
| `BOP_LEON` | la Provincia de Leon | `open_data_detected` | `low` | yes | https://bop.dipuleon.es/ |
| `BOP_LLEIDA` | la Provincia de Lleida | `stable_form_or_endpoint` | `medium` | yes | https://ebop.diputaciolleida.cat/bop/ |
| `BOP_MALAGA` | la Provincia de Malaga | `stable_form_or_endpoint` | `medium` | yes | http://www.bopmalaga.es/ |
| `BOP_OURENSE` | Boletin Oficial da Provincia de Ourense | `unknown` | `unknown` | no | https://bop.depourense.es/portal/ |
| `BOP_PALENCIA` | la Provincia de Palencia | `open_data_detected` | `low` | yes | https://www.diputaciondepalencia.es/servicios/boletin-oficial-provincia |
| `BOP_PONTEVEDRA` | la Provincia de Pontevedra | `rss_or_api_detected` | `low` | yes | https://boppo.depo.gal/es |
| `BOP_SALAMANCA` | la Provincia de Salamanca | `open_data_detected` | `low` | yes | https://sede.diputaciondesalamanca.gob.es/BOP/ |
| `BOP_SANTA_CRUZ_TENERIFE` | la Provincia de Santa Cruz de Tenerife | `static_html_viable` | `low` | yes | http://www.bopsantacruzdetenerife.es/ |
| `BOP_SEGOVIA` | la Provincia de Segovia | `stable_form_or_endpoint` | `medium` | yes | http://www.dipsegovia.es/bop |
| `BOP_SEVILLA` | la Provincia de Sevilla | `stable_form_or_endpoint` | `medium` | yes | http://www.dipusevilla.es/bop/ |
| `BOP_SORIA` | la Provincia de Soria | `rss_or_api_detected` | `low` | yes | http://bop.dipsoria.es/ |
| `BOP_TARRAGONA` | Butlleti Oficial de la Provincia de Tarragona | `unknown` | `unknown` | no | http://www.diputaciodetarragona.cat/ebop/ |
| `BOP_TERUEL` | la Provincia de Teruel | `static_html_viable` | `low` | yes | http://www.dpteruel.es/boletines.htm |
| `BOP_TOLEDO` | la Provincia de Toledo | `static_html_viable` | `low` | yes | http://bop.diputoledo.es/webEbop/inicio.jsp |
| `BOP_VALENCIA` | la Provincia de Valencia | `open_data_detected` | `low` | yes | https://bop.dival.es/bop/drvisapi.dll |
| `BOP_VALLADOLID` | la Provincia de Valladolid | `stable_form_or_endpoint` | `medium` | yes | https://bop.sede.diputaciondevalladolid.es/ |
| `BOP_ZAMORA` | la Provincia de Zamora | `stable_form_or_endpoint` | `medium` | yes | https://www.diputaciondezamora.es/opencms/servicios/BOP/bop/index.html |
| `BOP_ZARAGOZA` | la Provincia de Zaragoza | `unknown` | `high` | no | http://bop.dpz.es/BOPZ/ |

## Validation Notes

This audit classifies first-pass access-path evidence only. A recommended candidate still requires a separate metadata-only monitor PR with fixtures and preview validation.
