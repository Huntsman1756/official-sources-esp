# BOE selected candidate review checklist - 2026-05-17

## Scope

This report exports the 10 BOE source candidates currently marked as operationally
`likely_relevant` with `evidence_review_status=evidence_downloaded`.

This is a human-review checklist only. It does not approve candidates, publish anything, write
to downstream projects, call BOE, download new artifacts, expose MCP, or expose SQLite.

No full legal text, raw XML, or raw HTML is included.

## VPS State

```text
deployed_commit=9e62d47
schema_current_version=7
schema_latest_version=7
pending_migrations=0
journal_mode=wal
synchronous=normal
db_status=up_to_date
db_validation=valid
```

The `sqlite3` CLI was not installed on the VPS. The requested candidate status check was run
with the project Python runtime using a read-only SQLite connection:

```text
human_review_required | 25
```

## Evidence Availability Summary

```text
selected_candidates_exported=10
evidence_label=likely_relevant
evidence_review_status=evidence_downloaded
xml_available=10
html_available=10
pdf_available=0
integrity_warnings=0
hashes_match=10
manual_fields_completed=10
accept_for_downstream_pilot=4
needs_more_evidence=4
out_of_scope=2
needs_pdf_yes=4
needs_pdf_no=6
```

The optional CSV export was created locally outside tracked docs:

```text
data/review_exports/boe_selected_candidate_review_2026-05-17.csv
```

`data/` is ignored by Git, so the CSV export is not committed.

## Human Review Outcome

The human reviewer filled the manual fields based on title and metadata review only.

```text
reviewer=Dani
reviewed_at=2026-05-17
pilot_candidate_ids=1,11,17,18
needs_more_evidence_candidate_ids=3,20,21,23
out_of_scope_candidate_ids=10,14
pdf_requested_candidate_ids=3,20,21,23
```

This manual checklist does not change `source_candidates.review_status`, does not approve
candidates, and does not publish anything.

## PDF Policy Reminder

PDF remains on-demand only.

- Do not download PDFs by default.
- Do not download PDFs for all candidates automatically.
- Do not download PDFs for a whole date range.
- Download PDF only when a human reviewer explicitly requests it for selected candidates or
  document IDs.
- PDF absence does not mean evidence is invalid.
- PDF presence does not mean the candidate is approved.

## Selected Candidates

| Candidate ID | Official identifier | Publication date | Section | Title | Official URL |
| --- | --- | --- | --- | --- | --- |
| 1 | BOE-B-2026-15543 | 2026-05-15 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la resolución de 13 de mayo de 2026 del Centro de Estudios Políticos y Constitucionales, por la que se convocan un máximo de 13 ayudas de formación para jóvenes con titulación universitaria superior en el marco del Máster Universitario Oficial en Derecho Constitucional. | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-15543 |
| 3 | BOE-B-2026-15552 | 2026-05-15 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución de la Dirección General del Instituto de la Juventud, por la que se convocan ayudas del Programa "Cuerpo Europeo de Solidaridad" correspondientes a la ronda de febrero de 2026. | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-15552 |
| 10 | BOE-B-2026-15334 | 2026-05-13 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución, de 24 de abril de 2026, de la Jefatura de Personal de la Armada, por la que se convocan las subvenciones de ayudas de acción social para organismos sin ánimo de lucro estrechamente relacionadas con la Armada para el 2026. | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-15334 |
| 11 | BOE-B-2026-15350 | 2026-05-13 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución de 6 de mayo de 2026 de la Secretaría de Estado de Educación por la que se convocan ayudas para la adquisición de libros de texto y material didáctico e informático para alumnos matriculados en centros docentes españoles en el exterior, en las ciudades de Ceuta y Melilla y en el Centro para la Innovación y Desarrollo de la Educación a Distancia en el curso académico 2026/2027 | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-15350 |
| 14 | BOE-B-2026-15228 | 2026-05-12 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución de 08 de mayo de 2026 de la Dirección Provincial en Melilla del SEPE por la que se aprueba, en régimen de concurrencia competitiva, la convocatoria de subvenciones públicas destinadas a la financiación de proyectos de programas experienciales de empleo y formación TándEM, correspondiente al ejercicio 2026 en el territorio de la Ciudad de Melilla. | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-15228 |
| 17 | BOE-B-2026-15263 | 2026-05-12 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución de 6 de mayo de 2026, de la Dirección del Instituto de las Mujeres, por la que se convocan becas de formación "María Telo" 2026 | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-15263 |
| 18 | BOE-B-2026-14562 | 2026-05-08 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución de la Secretaría de Estado de Educación, de fecha 6 de mayo de 2026, por la que se convocan ayudas para alumnos con necesidad específica de apoyo educativo para el curso académico 2026-2027. | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-14562 |
| 20 | BOE-B-2026-14487 | 2026-05-07 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución de 5 de mayo de 2026 de la Dirección de la Fundación Biodiversidad, que aprueba la publicación de la Convocatoria de la Fundación Biodiversidad, F.S.P., en régimen de concurrencia competitiva, para becas de formación en cambio climático | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-14487 |
| 21 | BOE-B-2026-14488 | 2026-05-07 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución de 5 de mayo de 2026 de la Dirección de la Fundación Biodiversidad, F.S.P., por la que se aprueba la convocatoria, en régimen de concurrencia competitiva, para becas de formación relacionadas con los fines de la Fundación Biodiversidad | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-14488 |
| 23 | BOE-B-2026-14385 | 2026-05-06 | V. Anuncios. - B. Otros anuncios oficiales | Extracto de la Resolución del 30 de abril de la Secretaría de Estado de Cultura por la que se convocan ayudas, en régimen de concurrencia competitiva, para proyectos de salvaguarda del Patrimonio Cultural Inmaterial correspondientes al año 2026. | https://www.boe.es/diario_boe/txt.php?id=BOE-B-2026-14385 |

## Evidence Review Signals

| Candidate ID | Official identifier | Department | Matched keywords | Score | Score reasons | Evidence label | Evidence status | XML | HTML | PDF | Integrity warning | Hashes match |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | BOE-B-2026-15543 | MINISTERIO DE LA PRESIDENCIA, JUSTICIA Y RELACIONES CON LAS CORTES | ayudas | 2 | strong_keyword:ayudas | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 3 | BOE-B-2026-15552 | MINISTERIO DE JUVENTUD E INFANCIA | ayudas | 2 | strong_keyword:ayudas | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 10 | BOE-B-2026-15334 | MINISTERIO DE DEFENSA | ayudas,subvenciones | 4 | strong_keyword:ayudas,strong_keyword:subvenciones | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 11 | BOE-B-2026-15350 | MINISTERIO DE EDUCACIÓN, FORMACIÓN PROFESIONAL Y DEPORTES | ayudas | 2 | strong_keyword:ayudas | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 14 | BOE-B-2026-15228 | MINISTERIO DE TRABAJO Y ECONOMÍA SOCIAL | subvenciones,convocatoria,convocatoria de subvenciones | 6 | weak_keyword:convocatoria,strong_phrase:convocatoria_de_subvenciones,strong_keyword:subvenciones | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 17 | BOE-B-2026-15263 | MINISTERIO DE IGUALDAD | becas | 2 | strong_keyword:becas | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 18 | BOE-B-2026-14562 | MINISTERIO DE EDUCACIÓN, FORMACIÓN PROFESIONAL Y DEPORTES | ayudas | 2 | strong_keyword:ayudas | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 20 | BOE-B-2026-14487 | MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO | becas,convocatoria | 3 | strong_keyword:becas,weak_keyword:convocatoria | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 21 | BOE-B-2026-14488 | MINISTERIO PARA LA TRANSICIÓN ECOLÓGICA Y EL RETO DEMOGRÁFICO | becas,convocatoria | 3 | strong_keyword:becas,weak_keyword:convocatoria | likely_relevant | evidence_downloaded | true | true | false | false | true |
| 23 | BOE-B-2026-14385 | MINISTERIO DE CULTURA | ayudas | 2 | strong_keyword:ayudas | likely_relevant | evidence_downloaded | true | true | false | false | true |

## Hash Summary

`source_snapshot_hash` and `content_sha256` are exported as artifact-type-prefixed values.
All selected candidates have matching XML/HTML snapshot and content hashes.

| Candidate ID | Source snapshot hash | Content SHA256 |
| --- | --- | --- |
| 1 | `html:077cb871d8e55dbdeffee6aaa85ffd41f3225aa9437ea4e442257f033d1e578f;xml:655413bf3f7c4b0622148396028463da1a722b09a7a23b1fe634aecb2d0b0a25` | `html:077cb871d8e55dbdeffee6aaa85ffd41f3225aa9437ea4e442257f033d1e578f;xml:655413bf3f7c4b0622148396028463da1a722b09a7a23b1fe634aecb2d0b0a25` |
| 3 | `html:b71a806fe8a60ea36a0b8ae53bb8aac7433e444cba27a2d4a79fd17fab470923;xml:eca45ac95af076f9b96b5d9788f0f6df8b8b561260ce143afd87fecb4bb2d7f9` | `html:b71a806fe8a60ea36a0b8ae53bb8aac7433e444cba27a2d4a79fd17fab470923;xml:eca45ac95af076f9b96b5d9788f0f6df8b8b561260ce143afd87fecb4bb2d7f9` |
| 10 | `html:432d43afdd202874673cfc2ed7745a8f80249928f3eb238ad546ab388f3dec61;xml:b6a940c090ef9573ed434ce73cf03024113820a2b77fb2f97ac19d1b53a6212d` | `html:432d43afdd202874673cfc2ed7745a8f80249928f3eb238ad546ab388f3dec61;xml:b6a940c090ef9573ed434ce73cf03024113820a2b77fb2f97ac19d1b53a6212d` |
| 11 | `html:f54c659706da7efa636b98923ef09c62d92517e4b30e430bb11608198d58f4d7;xml:e1893b2da10be073c232472dfb7ce0217947eac82389cbf9661a7a538de7e13e` | `html:f54c659706da7efa636b98923ef09c62d92517e4b30e430bb11608198d58f4d7;xml:e1893b2da10be073c232472dfb7ce0217947eac82389cbf9661a7a538de7e13e` |
| 14 | `html:cff79291b423d65647d991b36f9f4712aa394aadb012dda1db137aad5ac32c1f;xml:03f8217af2fdc10e89e937b235f111a59c7f6b217ad7d949b6f32f1dce9b3641` | `html:cff79291b423d65647d991b36f9f4712aa394aadb012dda1db137aad5ac32c1f;xml:03f8217af2fdc10e89e937b235f111a59c7f6b217ad7d949b6f32f1dce9b3641` |
| 17 | `html:dd2c58bd2c6e7d1b790eaf8e32c3c47da8c09507f753f8328fa3f3b7ecbfaf05;xml:6eccc192dad51d76806daa36bb0eeaac74a43c97108b4eca52c3f920306ce28e` | `html:dd2c58bd2c6e7d1b790eaf8e32c3c47da8c09507f753f8328fa3f3b7ecbfaf05;xml:6eccc192dad51d76806daa36bb0eeaac74a43c97108b4eca52c3f920306ce28e` |
| 18 | `html:ff826eeef35c156d8f1f5a475782ce5e02fe7b9f8832062b4ac5ee371829010c;xml:829427a63de2c2454f0d5a4e2bb929928e9fd6af8cc72e4a5f08f4ae8b807940` | `html:ff826eeef35c156d8f1f5a475782ce5e02fe7b9f8832062b4ac5ee371829010c;xml:829427a63de2c2454f0d5a4e2bb929928e9fd6af8cc72e4a5f08f4ae8b807940` |
| 20 | `html:d7856b87b7c96811c45814b2a25888a216a507142ef673682c4af7c970eeea81;xml:3c4f0eb6c2228cafd3d8b528ae29975d4bc5ba6263155d66ea4328147afa130a` | `html:d7856b87b7c96811c45814b2a25888a216a507142ef673682c4af7c970eeea81;xml:3c4f0eb6c2228cafd3d8b528ae29975d4bc5ba6263155d66ea4328147afa130a` |
| 21 | `html:6f2196cb6537de83b2c902ef73c281320b197319c15913054bc9a4e98181c822;xml:f47ea5008cb4a4a199dbcb6a562dc6ab11fca3dd72f1f49dc1551e2bd93ac821` | `html:6f2196cb6537de83b2c902ef73c281320b197319c15913054bc9a4e98181c822;xml:f47ea5008cb4a4a199dbcb6a562dc6ab11fca3dd72f1f49dc1551e2bd93ac821` |
| 23 | `html:25fe8de14e1cee2a35f1859b3c37b781d394bab83ea6ed54a31186e6e2061693;xml:55c7d2ff8744c48eeb106f8bc980135b59e825d09e414f961018baeb914e2eb0` | `html:25fe8de14e1cee2a35f1859b3c37b781d394bab83ea6ed54a31186e6e2061693;xml:55c7d2ff8744c48eeb106f8bc980135b59e825d09e414f961018baeb914e2eb0` |

## Manual Review Checklist

Manual fields were filled by the human reviewer. These are review notes for a downstream pilot
decision, not approval or publication status inside `official-sources`.

| Candidate ID | Official identifier | Manual decision | Manual notes | Needs PDF | Downstream project fit | Reviewer | Reviewed at |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | BOE-B-2026-15543 | `accept_for_downstream_pilot` | Fits as a training grant for young university graduates in an official master program. | `no` | `EduAyudas` | Dani | 2026-05-17 |
| 3 | BOE-B-2026-15552 | `needs_more_evidence` | European Solidarity Corps may fit, but beneficiaries, age, country, management, and product fit need review. | `yes` | `unclear` | Dani | 2026-05-17 |
| 10 | BOE-B-2026-15334 | `out_of_scope` | Social action grants tied to organizations related to the Navy; not a general citizen or student aid. | `no` | `neither` | Dani | 2026-05-17 |
| 11 | BOE-B-2026-15350 | `accept_for_downstream_pilot` | Strong candidate for textbook and teaching or IT materials aid for students. | `no` | `both` | Dani | 2026-05-17 |
| 14 | BOE-B-2026-15228 | `out_of_scope` | Experiential employment and training programs in Melilla; likely institutional rather than general education aid. | `no` | `neither` | Dani | 2026-05-17 |
| 17 | BOE-B-2026-15263 | `accept_for_downstream_pilot` | Clear training scholarship candidate. | `no` | `EduAyudas` | Dani | 2026-05-17 |
| 18 | BOE-B-2026-14562 | `accept_for_downstream_pilot` | Very strong candidate for students with specific educational support needs. | `no` | `both` | Dani | 2026-05-17 |
| 20 | BOE-B-2026-14487 | `needs_more_evidence` | Climate change training scholarships may fit; requirements and target recipients need review. | `yes` | `unclear` | Dani | 2026-05-17 |
| 21 | BOE-B-2026-14488 | `needs_more_evidence` | Fundacion Biodiversidad training scholarships may fit; rules and target recipients need review. | `yes` | `unclear` | Dani | 2026-05-17 |
| 23 | BOE-B-2026-14385 | `needs_more_evidence` | Likely aimed at entities or projects for intangible cultural heritage; needs evidence before product fit decision. | `yes` | `unclear` | Dani | 2026-05-17 |

## Allowed Manual Values

`manual_decision`:

- `accept_for_downstream_pilot`
- `needs_more_evidence`
- `reject_false_positive`
- `out_of_scope`
- `defer`

`needs_pdf`:

- `yes`
- `no`

`downstream_project_fit`:

- `la-ayuda`
- `EduAyudas`
- `both`
- `neither`
- `unclear`

## Verification

Candidate review status remained unchanged:

```text
review_status=human_review_required count=25
```

Artifact size remained stable:

```text
artifact_size=23M
```

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
result=no_matching_public_listener
```

## Next Recommended Review Action

Prepare downstream pilot intake for candidate IDs `1,11,17,18`, keeping downstream approval
separate from `official-sources`.

For candidate IDs `3,20,21,23`, request explicit PDF downloads only if the next review step
requires official PDF validation. Candidate IDs `10,14` should stay available as evidence but
should not be passed to the downstream pilot at this stage.

`official-sources` must keep `source_candidates.review_status` as `human_review_required`.

## Limitations

- This checklist does not approve or publish any candidate.
- `likely_relevant` is an operational evidence label, not approval.
- The export uses cached XML/HTML metadata only and does not include raw legal text.
- PDF is absent for all selected candidates because PDF is on-demand.
- The export does not perform legal interpretation or project eligibility classification.
- Downstream projects must still maintain their own review workflow.
