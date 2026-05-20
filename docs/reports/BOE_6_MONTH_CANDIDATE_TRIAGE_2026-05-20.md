# BOE 6-Month Candidate Triage - 2026-05-20

## Scope

This report documents metadata-only triage for the 50 BOE `source_candidates` created in `TASK-005C`.

Target range:

```text
2025-11-20 to 2026-05-20
```

Profile:

```text
la-ayuda
```

Reviewed candidate batch:

```text
26-75
```

This task did not call BOE, did not run a new backfill, did not download XML/HTML/PDF artifacts, did not create more candidates, did not approve candidates, did not publish anything, and did not write to downstream projects.

Triage labels in this report are metadata-only operational planning labels. They were not written to the database.

## Deployment State

- Deployed commit: `76ac109`
- DB schema: `8/8`
- SQLite journal mode: `wal`
- SQLite synchronous: `2`
- DB validation: valid

## Candidate Batch Reviewed

| Item | Value |
|---|---:|
| Candidates reviewed | 50 |
| Candidate ID range | `26-75` |
| `source_candidates` total | 75 |
| `source_candidates.human_review_required` | 75 |
| Artifact directory size before triage | 23M |
| `artifact_download_attempts` before triage | 366 |

## Triage Distribution

| Triage label | Count |
|---|---:|
| `likely_relevant` | 10 |
| `unclear` | 7 |
| `out_of_scope` | 27 |
| `false_positive` | 6 |

Recommended evidence actions:

| Action | Count |
|---|---:|
| `download_xml_html` | 13 |
| `needs_human_title_review` | 1 |
| `defer` | 3 |
| `do_not_download` | 33 |

## Selected Evidence Candidates

Selected for future XML/HTML evidence download:

```text
32, 36, 40, 42, 44, 49, 56, 57, 58, 60, 68, 69, 72
```

Selection count:

```text
13
```

No XML/HTML/PDF was downloaded in this task.

## Triage Table

| Candidate | Official identifier | Date | Department | Title metadata | Keywords | Score | Label | Reason | Evidence action |
|---:|---|---|---|---|---|---:|---|---|---|
| 26 | `BOE-B-2026-16141` | `2026-05-19` | MINISTERIO DE ASUNTOS EXTERIORES, U... | Extracto de la Resolución de 18 de mayo de 2026, de la Secretaría de Estado de Asuntos Exteriores y Globales, por la ... | `subvenciones, convocatoria` | 3 | `out_of_scope` | Subsidies to non-profit entities for foreign policy priorities; institutional/project grant. | `do_not_download` |
| 27 | `BOE-B-2026-16157` | `2026-05-19` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de 14 de mayo de 2026, de la Dirección Provincial del SEPE en Cádiz, por la que se anuncia ... | `subvenciones, convocatoria` | 3 | `out_of_scope` | PFEA employment subsidy to hire unemployed workers through projects; not a citizen/student aid record. | `do_not_download` |
| 28 | `BOE-B-2026-16158` | `2026-05-19` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de 14 de mayo de 2026, de la Dirección Provincial del SEPE en Cádiz, por la que se anuncia ... | `subvenciones, convocatoria` | 3 | `out_of_scope` | PFEA competitive employment project subsidy; institutional/local project focus. | `do_not_download` |
| 29 | `BOE-B-2026-16159` | `2026-05-19` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de 4 de mayo de 2026 de la Dirección Provincial del Servicio Público de Empleo Estatal en M... | `subvenciones, convocatoria` | 3 | `out_of_scope` | PFEA local corporation hiring subsidy; not direct aid for downstream pilot. | `do_not_download` |
| 30 | `BOE-B-2026-16236` | `2026-05-19` | MINISTERIO DE SANIDAD | Extracto de la Resolución de 17 de marzo de 2026 , de la Secretaría de Estado de Sanidad, por la que se convoca la co... | `ayudas` | 2 | `out_of_scope` | Aid to local corporations for addiction prevention programs; entity/program subsidy. | `do_not_download` |
| 31 | `BOE-B-2026-16237` | `2026-05-19` | MINISTERIO DE DERECHOS SOCIALES, CO... | Extracto de la Resolución de 12 de mayo de 2026, de la Secretaría de Estado de Derechos Sociales, por la que se convo... | `subvenciones` | 2 | `out_of_scope` | General-interest social activity subsidies; likely entity/project grants. | `do_not_download` |
| 32 | `BOE-B-2026-16238` | `2026-05-19` | MINISTERIO DE IGUALDAD | Extracto de la Resolución de 14 de mayo de 2026 de la Secretaría de Estado de Igualdad y para la Erradicación de la V... | `subvenciones, discapacidad` | 4 | `unclear` | Vulnerable-group support topic is potentially useful, but title suggests project subsidies and needs evidence. | `download_xml_html` |
| 33 | `BOE-B-2026-16025` | `2026-05-18` | COMUNIDAD AUTÓNOMA DE CATALUÑA | Anuncio de los Servicios Territoriales del Departamento de Territorio, Vivienda y Transición Ecològica de la Generali... | `vivienda` | 2 | `false_positive` | Infrastructure public-information notice; keyword comes from housing department/context, not an aid. | `do_not_download` |
| 34 | `BOE-B-2026-14388` | `2026-05-06` | MINISTERIO DE IGUALDAD | Extracto de la Resolución 28 de abril de 2026, de la Directora del Instituto de las Mujeres, por la que se convocan s... | `subvenciones` | 2 | `out_of_scope` | Artistic/cultural production subsidy; sectoral project grant. | `do_not_download` |
| 35 | `BOE-B-2026-14177` | `2026-05-05` | MINISTERIO DE ASUNTOS EXTERIORES, U... | Extracto de la Resolución de 30 de abril de 2026, de la Secretaría de Estado de Asuntos Exteriores y Globales, por la... | `subvenciones, convocatoria` | 3 | `out_of_scope` | Human-rights dissemination activity subsidy; institutional/project grant. | `do_not_download` |
| 36 | `BOE-B-2026-14182` | `2026-05-05` | MINISTERIO DE LA PRESIDENCIA, JUSTI... | Extracto de la Resolución de 29 de abril de 2026 del Centro de Investigaciones Sociológicas por la que se publica la ... | `subvenciones, convocatoria, convocatoria de subvenciones` | 6 | `likely_relevant` | Training/research grant wording; plausible scholarship/training aid needing evidence. | `download_xml_html` |
| 37 | `BOE-B-2026-14188` | `2026-05-05` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de la Dirección Provincial del Servicio Público de Empleo Estatal en Murcia por la que se c... | `subvenciones` | 2 | `out_of_scope` | SEPE public works/services employment subsidy; project/institutional scope. | `do_not_download` |
| 38 | `BOE-B-2026-14189` | `2026-05-05` | MINISTERIO DE AGRICULTURA, PESCA Y ... | Extracto de la Orden de 29 de abril de 2026, por la que se convoca para el año 2026 la concesión de subvenciones dire... | `subvenciones` | 2 | `out_of_scope` | Direct subsidy to professional agrarian organizations; legal-entity support. | `do_not_download` |
| 39 | `BOE-B-2026-14243` | `2026-05-05` | MINISTERIO DE CULTURA | Extracto de la Resolución de la Secretaría de Estado de Cultura por la que se convocan las ayudas, en régimen en conc... | `ayudas` | 2 | `unclear` | Culture/photography promotion aid may target creators or entities; not enough from title. | `defer` |
| 40 | `BOE-B-2026-14244` | `2026-05-05` | MINISTERIO DE IGUALDAD | Extracto de la Resolución de 27 de abril de 2026, de la Secretaría de Estado de Igualdad y para la Erradicación de la... | `becas` | 2 | `likely_relevant` | Training scholarships for a public observatory; strong candidate for evidence review. | `download_xml_html` |
| 41 | `BOE-B-2026-14058` | `2026-05-04` | UNIVERSIDADES | Anuncio de Servicio de Títulos, Becas y Ayudas al Estudiante de la Universidad Rey Juan Carlos sobre extravío de títu... | `becas, ayudas` | 4 | `false_positive` | Lost university title notice; not an aid or grant. | `do_not_download` |
| 42 | `BOE-B-2026-13661` | `2026-05-01` | MINISTERIO DE DEFENSA | Extracto de la Resolución de 29 de abril de 2026 del Mando de Adiestramiento y Doctrina por la que se convocan ayudas... | `ayudas` | 2 | `likely_relevant` | Master study aid; narrow defense scope but education/training aid wording is clear. | `download_xml_html` |
| 43 | `BOE-B-2026-13591` | `2026-04-30` | MINISTERIO DE DEFENSA | Resolución del organismo autónomo Instituto de Vivienda, Infraestructura y Equipamiento de la Defensa, por la que se ... | `vivienda` | 2 | `false_positive` | Property auction notice; not an aid. | `do_not_download` |
| 44 | `BOE-B-2026-13592` | `2026-04-30` | MINISTERIO DE DEFENSA | Extracto de la Resolución de 29 de abril de 2026 del Mando de Adiestramiento y Doctrina por la que se convocan ayudas... | `ayudas` | 2 | `likely_relevant` | Master study aid; narrow defense scope but education/training aid wording is clear. | `download_xml_html` |
| 45 | `BOE-B-2026-13595` | `2026-04-30` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de la Dirección Provincial del Servicio Público de Empleo Estatal en Cáceres, por la que se... | `subvenciones, convocatoria, convocatoria de subvenciones` | 6 | `out_of_scope` | PFEA local corporation project subsidy; not direct citizen/student aid. | `do_not_download` |
| 46 | `BOE-B-2026-13596` | `2026-04-30` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de la Dirección Provincial del Servicio Público de Empleo Estatal en Cáceres, por la que se... | `subvenciones, convocatoria, convocatoria de subvenciones` | 6 | `out_of_scope` | PFEA local corporation project subsidy; not direct citizen/student aid. | `do_not_download` |
| 47 | `BOE-B-2026-13473` | `2026-04-29` | MINISTERIO DE DEFENSA | Extracto de la Orden de 27 de abril de 2026, por la que se convocan subvenciones para promover la cultura de defensa,... | `subvenciones` | 2 | `out_of_scope` | Subsidies to promote defense culture; sectoral/institutional. | `do_not_download` |
| 48 | `BOE-B-2026-13475` | `2026-04-29` | MINISTERIO DE HACIENDA | Extracto de la resolución de la gerencia del consorcio de la ciudad de Santiago de Compostela por la que se aprueban ... | `subvenciones, bases reguladoras, convocatoria` | 6 | `unclear` | Municipal program subsidy; title lacks beneficiary/product fit detail. | `needs_human_title_review` |
| 49 | `BOE-B-2026-13482` | `2026-04-29` | MINISTERIO DE EDUCACIÓN, FORMACIÓN ... | Extracto de la Resolución de 23 de abril de 2026 de la Presidencia del Consejo Superior de Deportes, por la que se co... | `becas` | 2 | `likely_relevant` | Scholarships for athletes at a high-performance center; clear scholarship wording. | `download_xml_html` |
| 50 | `BOE-B-2026-13485` | `2026-04-29` | MINISTERIO DE POLÍTICA TERRITORIAL ... | Extracto de la Resolución de 24 de abril de 2026, de la Dirección General de Cooperación Autonómica y Local, por la q... | `ayudas, subvenciones` | 4 | `out_of_scope` | Aid to local entities for infrastructure repairs; not citizen/student aid. | `do_not_download` |
| 51 | `BOE-B-2026-13517` | `2026-04-29` | MINISTERIO PARA LA TRANSICIÓN ECOLÓ... | Extracto de la Resolución de la Secretaría de Estado de Energía por la que se aprueba la convocatoria para la concesi... | `ayudas, convocatoria` | 3 | `out_of_scope` | Mining exploration public aid; industrial sector scope. | `do_not_download` |
| 52 | `BOE-B-2026-13518` | `2026-04-29` | MINISTERIO DE CULTURA | Extracto de la Resolución de la Secretaría de Estado de Cultura, de 20 de abril de 2026, por la que se convocan ayuda... | `ayudas` | 2 | `out_of_scope` | Aid to non-profits for archive equipment; entity/equipment grant. | `do_not_download` |
| 53 | `BOE-B-2026-13519` | `2026-04-29` | MINISTERIO PARA LA TRANSFORMACIÓN D... | Extracto de Resolución de 27 de abril de 2026 de la Secretaría de Estado de Función Pública, por la que se convocan s... | `subvenciones` | 2 | `out_of_scope` | Subsidies to trade union organizations; institutional support. | `do_not_download` |
| 54 | `BOE-B-2026-13393` | `2026-04-28` | MINISTERIO DE HACIENDA | Extracto de la resolución por la que se hace público el Acuerdo de 13 de abril de 2026 del Consejo de Administración ... | `subvención, bases reguladoras` | 5 | `out_of_scope` | In-kind direct subsidy for cultural center rehabilitation; infrastructure/project support. | `do_not_download` |
| 55 | `BOE-B-2026-13407` | `2026-04-28` | MINISTERIO DE CULTURA | Extracto de la Resolución de 20 abril de 2026, del Organismo Autónomo Instituto de la Cinematografía y de las Artes A... | `ayudas` | 2 | `out_of_scope` | Cinema festival organization aid; sectoral cultural grant. | `do_not_download` |
| 56 | `BOE-B-2026-13408` | `2026-04-28` | MINISTERIO DE CULTURA | Extracto de la Resolución de 16 de abril de 2026, del Organismo Autónomo Instituto de la Cinematografía y de las Arte... | `ayudas` | 2 | `likely_relevant` | School-year Cine Escuela aid; education-adjacent and worth evidence review. | `download_xml_html` |
| 57 | `BOE-B-2026-12992` | `2026-04-25` | MINISTERIO DE DEFENSA | Extracto de la Resolución de 22 de abril de 2026 del Mando de Adiestramiento y Doctrina por la que se convocan las be... | `becas` | 2 | `likely_relevant` | Master scholarship wording; narrow defense scope but education/training aid. | `download_xml_html` |
| 58 | `BOE-B-2026-12993` | `2026-04-25` | MINISTERIO DE DEFENSA | Extracto de la Resolución de 22 de abril de 2026 del Mando de Adiestramiento y Doctrina por la que se convocan las be... | `becas` | 2 | `likely_relevant` | Master scholarship wording; narrow defense scope but education/training aid. | `download_xml_html` |
| 59 | `BOE-B-2026-13094` | `2026-04-25` | MINISTERIO DE HACIENDA | Extracto de la Resolución de 22 de abril de 2026 de la Sociedad Estatal de Promoción Industrial y Desarrollo Empresar... | `ayudas, convocatoria, convocatoria de ayudas` | 6 | `out_of_scope` | Industrial decarbonization aid; business/industry scope. | `do_not_download` |
| 60 | `BOE-B-2026-13097` | `2026-04-25` | MINISTERIO DE EDUCACIÓN, FORMACIÓN ... | Extracto de la Resolución de 22 de abril de 2026, de la Subsecretaría del Ministerio de Educación, Formación Profesio... | `ayudas` | 2 | `likely_relevant` | Education ministry aid for school theater participation; direct education-program fit. | `download_xml_html` |
| 61 | `BOE-B-2026-13098` | `2026-04-25` | MINISTERIO DE CULTURA | Extracto de la Resolución de 15 de marzo de 2026 de la Secretaría de Estado de Cultura por la que se convocan las sub... | `subvenciones` | 2 | `out_of_scope` | Digital preservation of bibliographic heritage; institutional/culture project. | `do_not_download` |
| 62 | `BOE-B-2026-13099` | `2026-04-25` | MINISTERIO DE CULTURA | Extracto de la Resolución de 16 de abril de 2026, del Organismo Autónomo Instituto de la Cinematografía y de las Arte... | `ayudas` | 2 | `out_of_scope` | International film distribution aid; sectoral business/culture grant. | `do_not_download` |
| 63 | `BOE-B-2026-13100` | `2026-04-25` | MINISTERIO DE CULTURA | Extracto de la Resolución de la Secretaría de Estado de Cultura por la que se convocan las ayudas, en régimen de conc... | `ayudas` | 2 | `out_of_scope` | Contemporary art production/research aid; sectoral culture grant. | `do_not_download` |
| 64 | `BOE-B-2026-12825` | `2026-04-24` | COMUNIDAD AUTÓNOMA DE CATALUÑA | Anuncio de los Servicios Territoriales en les Terres de l'Ebre del Departamento de Territorio, Vivienda y Transición ... | `vivienda` | 2 | `false_positive` | Gas infrastructure public-information notice; keyword from housing/territory context. | `do_not_download` |
| 65 | `BOE-B-2026-12660` | `2026-04-23` | MINISTERIO DE EDUCACIÓN, FORMACIÓN ... | Extracto de la Resolución de 21 de abril de 2026 de la Presidencia del Consejo Superior de Deportes, por la que se co... | `ayudas` | 2 | `unclear` | Sports training-center equipment aid to autonomous communities; education-adjacent but institutional. | `defer` |
| 66 | `BOE-B-2026-12661` | `2026-04-23` | MINISTERIO DE EDUCACIÓN, FORMACIÓN ... | Extracto de la Resolución de 25 de marzo de 2026, la Presidencia del Consejo Superior de Deportes, por la que se conv... | `subvenciones` | 2 | `unclear` | University championships support to federations; possible student sport context but entity-targeted. | `defer` |
| 67 | `BOE-B-2026-12723` | `2026-04-23` | UNIVERSIDADES | Anuncio del Servicio de Títulos, Becas y Ayudas al Estudiante de la Universidad Rey Juan Carlos sobre extravío de tít... | `becas, ayudas` | 4 | `false_positive` | Lost university title notice; not an aid or grant. | `do_not_download` |
| 68 | `BOE-B-2026-12557` | `2026-04-22` | MINISTERIO DE ASUNTOS EXTERIORES, U... | Extracto de la Orden de 14 abril de 2026 por la que se convocan subvenciones a instituciones asistenciales que presta... | `ayuda, subvenciones` | 4 | `unclear` | Aid to institutions helping Spaniards abroad; potentially la-ayuda relevant but entity-mediated. | `download_xml_html` |
| 69 | `BOE-B-2026-12558` | `2026-04-22` | MINISTERIO DE ASUNTOS EXTERIORES, U... | Extracto de la Orden de 14 de abril de 2026 por la que se convoca la concesión de subvenciones para la asistencia jur... | `subvenciones` | 2 | `likely_relevant` | Legal-assistance subsidy for citizens in extreme circumstances; plausible la-ayuda fit. | `download_xml_html` |
| 70 | `BOE-B-2026-12559` | `2026-04-22` | MINISTERIO DE ASUNTOS EXTERIORES, U... | Extracto de la Resolución de 15 de abril de 2026, de la Dirección de la Agencia Española de Cooperación Internacional... | `subvenciones` | 2 | `out_of_scope` | Development cooperation innovation actions; institutional/project grant. | `do_not_download` |
| 71 | `BOE-B-2026-12565` | `2026-04-22` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de 15 de abril de 2026 de la Dirección Provincial del Servicio Público de Empleo Estatal de... | `subvenciones, convocatoria, convocatoria de subvenciones` | 6 | `out_of_scope` | PFEA local corporation project subsidy; not direct citizen/student aid. | `do_not_download` |
| 72 | `BOE-B-2026-12566` | `2026-04-22` | MINISTERIO DE TRABAJO Y ECONOMÍA SO... | Extracto de la Resolución de 20 de abril de 2026, del Servicio Público de Empleo Estatal, por la que se aprueba la co... | `subvenciones, convocatoria` | 3 | `unclear` | Training-plan funding; may be institutional but topic is training and worth evidence review. | `download_xml_html` |
| 73 | `BOE-B-2026-12599` | `2026-04-22` | UNIVERSIDADES | Anuncio de Servicio de Títulos, Becas y Ayudas al Estudiante de la Universidad Rey Juan Carlos sobre extravío de títu... | `becas, ayudas` | 4 | `false_positive` | Lost university title notice; not an aid or grant. | `do_not_download` |
| 74 | `BOE-B-2026-12465` | `2026-04-21` | MINISTERIO DE INDUSTRIA Y TURISMO | Extracto de la Resolución de la Dirección de la Oficina Española de Patentes y Marcas, O.A., por la que se amplía el ... | `subvenciones` | 2 | `out_of_scope` | Patent/model subsidy; business/IP scope. | `do_not_download` |
| 75 | `BOE-B-2026-12493` | `2026-04-21` | MINISTERIO PARA LA TRANSFORMACIÓN D... | Extracto de la Resolución de la Secretaría de Estado de Telecomunicaciones e Infraestructuras Digitales por la que se... | `ayudas, convocatoria` | 3 | `out_of_scope` | Cloud infrastructure IPCEI aid to direct participants; industrial/digital sector scope. | `do_not_download` |

## Sample Likely Relevant Candidates

- `36` / `BOE-B-2026-14182`: training/research grant wording; plausible scholarship or training-aid fit.
- `40` / `BOE-B-2026-14244`: training scholarships in a public observatory.
- `49` / `BOE-B-2026-13482`: scholarships for athletes at a high-performance center.
- `60` / `BOE-B-2026-13097`: education ministry aid for school theater participation.
- `69` / `BOE-B-2026-12558`: citizen-facing legal-assistance topic, potentially useful for `la-ayuda`.

## Sample Unclear Candidates

- `32` / `BOE-B-2026-16238`: vulnerable-group support topic, but likely project subsidy until evidence confirms beneficiaries.
- `39` / `BOE-B-2026-14243`: culture/photography promotion aid; beneficiary type unclear from metadata.
- `68` / `BOE-B-2026-12557`: aid for Spaniards abroad, but title suggests institutional intermediaries.
- `72` / `BOE-B-2026-12566`: training-plan funding; topic is relevant, target may be institutional.

## Sample False Positives

- `33` / `BOE-B-2026-16025`: infrastructure public-information notice; not an aid.
- `41` / `BOE-B-2026-14058`: lost university title notice.
- `43` / `BOE-B-2026-13591`: property auction notice.
- `64` / `BOE-B-2026-12825`: gas infrastructure public-information notice.
- `67` / `BOE-B-2026-12723`: lost university title notice.
- `73` / `BOE-B-2026-12599`: lost university title notice.

## Sample Out-Of-Scope Candidates

- `27`, `28`, `29`, `37`, `45`, `46`, `71`: PFEA or SEPE project subsidies to local corporations or institutions.
- `30`: aid to local corporations for prevention programs.
- `38`: direct subsidies to professional agrarian organizations.
- `50`: aid to local entities for infrastructure repair.
- `59`: industrial decarbonization aid.
- `75`: digital/cloud industrial project aid.

## Noise Observations

- Generic `subvenciones` and `convocatoria` matches continue to produce institutional/project grants.
- `vivienda` creates false positives when it appears in department or infrastructure context rather than benefit context.
- University `becas/ayudas` service names produce lost-title notices that should be filtered later.
- Several training or scholarship notices are promising but narrow, especially defense, sports and institutional training programs.
- The metadata-only batch is useful for triage, but not enough for downstream operational acceptance.

## No-Write Verification

This was report-only triage. No operational DB triage fields were updated.

Post-triage verification:

| Item | Value |
|---|---:|
| `source_candidates` | 75 |
| `source_candidates.human_review_required` | 75 |
| Artifact directory size | 23M |
| `artifact_download_attempts` | 366 |

DB validation:

```text
valid
```

## MCP Privacy

Listener checks found no public MCP listener, no public Python/Uvicorn/FastMCP service, and no SQLite exposure.

## Known Issues

- This triage uses BOE metadata only; it is not a legal or eligibility review.
- No XML/HTML/PDF evidence was inspected.
- Triage labels were not written to `candidate_evidence_reviews`; this report is the operational review artifact.
- Some `likely_relevant` candidates may become out of scope after evidence review because the beneficiary type may be institutional.
- Some `unclear` candidates may be useful for `la-ayuda` but not for EduAyudas.

## Recommendation

Recommended next task:

```text
TASK-005E - Download XML/HTML for selected 6-month candidates
```

Use only the selected candidate IDs:

```text
32, 36, 40, 42, 44, 49, 56, 57, 58, 60, 68, 69, 72
```

Do not download PDFs in the next task. PDF should remain on-demand after XML/HTML review.
