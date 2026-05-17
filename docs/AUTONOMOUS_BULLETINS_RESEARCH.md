# Autonomous Bulletins Research

Autonomous bulletin adapters are not implemented in MVP-001. Each bulletin needs its own source assessment, parser design, tests, integrity semantics, and citation rules.

RSS availability does not imply stable parsing. Autonomous bulletins are not technically homogeneous.

| source_code | source_name | jurisdiction | official_url | has_api | has_rss | has_html | has_pdf | stable_ids | search_available | robots_notes | adapter_complexity | recommended_priority | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOCM | Boletin Oficial de la Comunidad de Madrid | ES-MD | https://www.bocm.es | unknown | unknown | yes | yes | unknown | yes | must be reviewed | medium | high | Relevant for Madrid public employment, subsidies, and procurement. |
| DOGV | Diari Oficial de la Generalitat Valenciana | ES-VC | https://dogv.gva.es | unknown | unknown | yes | yes | unknown | yes | must be reviewed | medium | high | Relevant for regional subsidies and public calls. |
| BOJA | Boletin Oficial de la Junta de Andalucia | ES-AN | https://www.juntadeandalucia.es/boja | unknown | unknown | yes | yes | unknown | yes | must be reviewed | medium | high | Relevant for Andalusian public aid, employment, and administration. |

Before implementation, update this table with verified API/RSS availability, stable identifier strategy, robots notes, and fixture samples.
