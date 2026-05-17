# BOE 30-day candidate prefilter dry-run - 2026-05-17

## Summary

TASK-004C-RUN2 validated a safe candidate prefilter dry-run over the cached 30-day BOE summary
range for `la-ayuda` / `EduAyudas`.

The initial VPS command help did not expose `--dry-run`, `--no-write`, or `--limit`, so the
candidate search was not run in normal write mode. Safe preview support was implemented, validated
locally, deployed, and then used for the operational dry-run.

No BOE API calls were made during the candidate prefilter. No XML, HTML, or PDF artifacts were
downloaded. No `source_candidates` rows were created. No downstream project was written to. MCP
remained private and stopped.

## Environment

- Host: private VPS, public IP redacted.
- Date/time UTC: `2026-05-17`.
- Application path: `/opt/official-sources/app`.
- Database path: `/opt/official-sources/data/official_sources.sqlite`.
- Artifact path: `/opt/official-sources/data/artifacts`.
- Cached range: `2026-04-18` through `2026-05-17`.
- Cached summary state: `success=25 no_publication=5 failed=0`.
- Deployed commit for final dry-run: `ab0c206`.

## Safety Check

Initial command:

```bash
/opt/official-sources/app/.venv/bin/official-sources find-boe-candidates --help
```

Result before implementation:

- `--dry-run`: missing.
- `--no-write`: missing.
- `--limit`: missing.

The candidate search was not run in normal mode.

Safe mode was then implemented and deployed:

- `962f1e1 feat: add safe candidate prefilter dry run`
- `ab0c206 fix: ignore unmatched BOE candidate rows`

The second fix was needed because an initial VPS dry-run exposed that documents without keyword
matches were counted as matched rows. The root cause was that the warning envelope made empty match
objects truthy. The fix prevents unmatched rows from being counted or printed.

## Commands Executed

```bash
cd /opt/official-sources/app
git rev-parse --short HEAD
/opt/official-sources/app/.venv/bin/official-sources find-boe-candidates --help
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
sqlite3 /opt/official-sources/data/official_sources.sqlite \
  "SELECT COUNT(*) FROM source_candidates;"
du -sh /opt/official-sources/data/artifacts
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-boe-candidates \
  --date-from 2026-04-18 \
  --date-to 2026-05-17 \
  --keywords "beca,becas,ayuda,ayudas,subvención,subvenciones,convocatoria,bases reguladoras,educación,estudiantes,alquiler,bono,familia numerosa,discapacidad,transporte,vivienda" \
  --dry-run \
  --limit 100
sqlite3 /opt/official-sources/data/official_sources.sqlite \
  "SELECT COUNT(*) FROM source_candidates;"
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  db validate
du -sh /opt/official-sources/data/artifacts
ss -tulpn
```

## Dry-run Result

```text
documents_scanned=3896
documents_matched=554
candidates_created=0
review_status=human_review_required
write_mode=dry_run
```

Candidate count:

```text
before=0
after=0
```

Artifact directory size:

```text
before=22M
after=22M
```

Database validation:

```text
current_version=6 latest_version=6 status=valid
```

## Matches by Keyword

```text
alquiler:7
ayuda:28
ayudas:27
bases reguladoras:2
beca:10
becas:10
bono:2
convocatoria:217
discapacidad:3
educación:28
estudiantes:1
subvenciones:35
subvención:1
transporte:246
vivienda:16
```

## Matches by Section

```text
V._Anuncios._-_A._Contratación_del_Sector_Público:173
V._Anuncios._-_B._Otros_anuncios_oficiales:381
```

## Matches by Department

Highest-volume departments:

```text
MINISTERIO_DE_TRANSPORTES_Y_MOVILIDAD_SOSTENIBLE:225
OTROS_ENTES:176
MINISTERIO_DE_CULTURA:18
MINISTERIO_DE_TRABAJO_Y_ECONOMÍA_SOCIAL:18
MINISTERIO_DE_DEFENSA:17
UNIVERSIDADES:16
MINISTERIO_PARA_LA_TRANSICIÓN_ECOLÓGICA_Y_EL_RETO_DEMOGRÁFICO:10
MINISTERIO_DE_ASUNTOS_EXTERIORES,_UNIÓN_EUROPEA_Y_COOPERACIÓN:9
MINISTERIO_DE_EDUCACIÓN,_FORMACIÓN_PROFESIONAL_Y_DEPORTES:9
MINISTERIO_DE_VIVIENDA_Y_AGENDA_URBANA:8
```

The full dry-run output also included smaller counts for other ministries and public bodies.

## Top 50 Sample Matches

The following sample rows were printed by `--limit 50`. Titles are summary metadata only; no
artifact content or raw legal text was printed.

| # | Date | Identifier | Keywords | Department | Title summary |
|---:|---|---|---|---|---|
| 1 | 2026-05-15 | BOE-B-2026-15543 | ayuda, ayudas | Presidency / Justice | Training grants for young university graduates. |
| 2 | 2026-05-15 | BOE-B-2026-15544 | transporte | Transport | Bilbao port public information notice. |
| 3 | 2026-05-15 | BOE-B-2026-15545 | convocatoria | Labour | Agricultural employment programme grants in Huelva. |
| 4 | 2026-05-15 | BOE-B-2026-15546 | convocatoria | Labour | Direct grant call for social-interest projects in Huelva. |
| 5 | 2026-05-15 | BOE-B-2026-15547 | convocatoria | Labour | Agricultural employment programme call in Córdoba. |
| 6 | 2026-05-15 | BOE-B-2026-15550 | transporte | Ecological Transition | Grid access capacity contest notice. |
| 7 | 2026-05-15 | BOE-B-2026-15551 | ayuda, ayudas | Culture | Film production project grants. |
| 8 | 2026-05-15 | BOE-B-2026-15552 | ayuda, ayudas | Youth and Children | European Solidarity Corps grants. |
| 9 | 2026-05-15 | BOE-B-2026-15553 | convocatoria | Other entities | Irrigation community meeting call. |
| 10 | 2026-05-15 | BOE-B-2026-15554 | convocatoria | Other entities | Irrigation community meeting call. |
| 11 | 2026-05-15 | BOE-B-2026-15555 | convocatoria | Other entities | Irrigation community meeting call. |
| 12 | 2026-05-15 | BOE-B-2026-15556 | convocatoria | Other entities | Irrigation community meeting call. |
| 13 | 2026-05-15 | BOE-B-2026-15557 | convocatoria | Other entities | Irrigation community meeting call. |
| 14 | 2026-05-15 | BOE-B-2026-15558 | convocatoria | Other entities | Irrigation community meeting call. |
| 15 | 2026-05-15 | BOE-B-2026-15559 | convocatoria | Other entities | Irrigation community meeting call. |
| 16 | 2026-05-15 | BOE-B-2026-15560 | convocatoria | Other entities | Irrigation community meeting call. |
| 17 | 2026-05-15 | BOE-B-2026-15561 | convocatoria | Other entities | Irrigation community meeting call. |
| 18 | 2026-05-15 | BOE-B-2026-15562 | convocatoria | Other entities | Irrigation community meeting call. |
| 19 | 2026-05-15 | BOE-B-2026-15563 | convocatoria | Other entities | Irrigation community meeting call. |
| 20 | 2026-05-15 | BOE-B-2026-15564 | convocatoria | Other entities | Irrigation community meeting call. |
| 21 | 2026-05-14 | BOE-B-2026-15465 | transporte | Transport | Salvage vessel repair contract formalization. |
| 22 | 2026-05-14 | BOE-B-2026-15466 | transporte | Transport | ADIF level-crossing works contract. |
| 23 | 2026-05-14 | BOE-B-2026-15467 | transporte | Transport | ADIF award withdrawal notice. |
| 24 | 2026-05-14 | BOE-B-2026-15468 | transporte | Transport | ADIF rolling-stock maintenance tender. |
| 25 | 2026-05-14 | BOE-B-2026-15469 | transporte | Transport | ADIF construction project services tender. |
| 26 | 2026-05-14 | BOE-B-2026-15470 | transporte | Transport | High-speed rail station works supervision tender. |
| 27 | 2026-05-14 | BOE-B-2026-15471 | transporte | Transport | Rail safety coordination services tender. |
| 28 | 2026-05-14 | BOE-B-2026-15472 | transporte | Transport | Building security services contract. |
| 29 | 2026-05-14 | BOE-B-2026-15493 | convocatoria, transporte | Transport | Port concession contest notice. |
| 30 | 2026-05-14 | BOE-B-2026-15494 | transporte | Transport | Port concession grant notice. |
| 31 | 2026-05-14 | BOE-B-2026-15495 | convocatoria, subvenciones | Labour | Grants for employment-office facility renewal. |
| 32 | 2026-05-14 | BOE-B-2026-15496 | convocatoria, subvenciones | Labour | Local corporation employment-project grants. |
| 33 | 2026-05-14 | BOE-B-2026-15498 | transporte | Territorial Policy | Electric transport line public information notice. |
| 34 | 2026-05-14 | BOE-B-2026-15525 | subvenciones | Culture | Municipal public library modernization grants. |
| 35 | 2026-05-14 | BOE-B-2026-15526 | convocatoria | Social Rights | Animal-protection awards call. |
| 36 | 2026-05-14 | BOE-B-2026-15527 | convocatoria, subvenciones | Science | Biomedical research platform grants. |
| 37 | 2026-05-14 | BOE-B-2026-15528 | subvenciones | Equality | State association and foundation support grants. |
| 38 | 2026-05-13 | BOE-B-2026-15295 | transporte | Defence | Horse transport vehicle supply tender. |
| 39 | 2026-05-13 | BOE-B-2026-15307 | transporte | Transport | Train radio equipment supply and repair tender. |
| 40 | 2026-05-13 | BOE-B-2026-15308 | transporte | Transport | Railway safety facilities contract. |
| 41 | 2026-05-13 | BOE-B-2026-15314 | educación | Ecological Transition | Environmental education service contract. |
| 42 | 2026-05-13 | BOE-B-2026-15316 | vivienda | Housing | Fiscal, accounting, and treasury support tender. |
| 43 | 2026-05-13 | BOE-B-2026-15317 | vivienda | Housing | Affordable housing building project tender. |
| 44 | 2026-05-13 | BOE-B-2026-15332 | convocatoria, subvenciones | Foreign Affairs | Development cooperation grants. |
| 45 | 2026-05-13 | BOE-B-2026-15334 | ayuda, ayudas, subvenciones | Defence | Social-action grants for Navy-related nonprofit bodies. |
| 46 | 2026-05-13 | BOE-B-2026-15336 | transporte | Transport | Port concession project competition notice. |
| 47 | 2026-05-13 | BOE-B-2026-15337 | transporte | Transport | Port concession public information notice. |
| 48 | 2026-05-13 | BOE-B-2026-15338 | transporte | Transport | Port concession modification notice. |
| 49 | 2026-05-13 | BOE-B-2026-15339 | transporte | Transport | Port concession grant notice. |
| 50 | 2026-05-13 | BOE-B-2026-15340 | transporte | Transport | Port concession grant notice. |

## False-positive Observations

The dry-run confirms the warning already documented for candidate prefiltering: this is a metadata
keyword filter, not a classifier.

Obvious or likely false-positive patterns:

- `convocatoria` matches many irrigation-community meeting calls.
- `transporte` matches many procurement, port, railway, road, and infrastructure notices.
- `vivienda` can match operational tenders from housing entities, not necessarily citizen-facing aid.
- `bono` can match substrings such as `carbono`; this should be improved before creating real
  candidates from broad keyword sets.
- Contract notices in Section V-A are frequent matches and may need separate weighting or exclusion
  depending on the downstream workflow.

Potentially relevant examples:

- Education textbook acquisition aid notice.
- Film, culture, research, cooperation, employment, youth, and social-action grant notices.
- Housing and accessibility-related notices may need human review because title-only matching cannot
  determine programme eligibility or downstream relevance.

## MCP Privacy Check

`ss -tulpn` showed:

- No MCP/FastMCP/Python/Uvicorn/official-sources public listener.
- No SQLite exposure.
- Public SSH listener present, expected for the VPS.
- Loopback DNS/systemd-resolved listener present, expected.

MCP remained stopped/private.

## Validation

Local validation for the safe-mode implementation:

```text
rtk python -m pytest -q -> 189 passed
rtk python -m ruff check . -> All checks passed!
rtk python -m ruff format --check . -> 56 files already formatted
```

VPS validation for the final dry-run:

```text
deployed_commit=ab0c206
candidate_count_before=0
candidate_count_after=0
artifact_size_before=22M
artifact_size_after=22M
database_status=valid
```

## Known Limitations

- Candidate prefiltering is still a simple local metadata/title keyword match.
- It does not parse document content.
- It does not download artifacts.
- It does not classify legal, fiscal, eligibility, or product relevance.
- It does not approve or publish candidates.
- It currently uses substring matching, which causes avoidable false positives such as `bono`
  matching inside `carbono`.
- The VPS virtual environment still emits a non-blocking pip warning about a leftover temporary
  distribution directory.

## Next Recommended Task

Before creating real candidates, add a small matching-quality hardening pass:

```text
TASK-004C-FIX4 - Improve BOE candidate keyword matching
```

Recommended scope:

- accent-insensitive matching;
- word-boundary matching for short terms such as `bono`;
- optional section/department filters;
- a curated dry-run keyword set for `la-ayuda` / `EduAyudas`;
- keep `--dry-run` as the default operational rehearsal path before any write-mode run.

## Follow-up Correction

TASK-004C-FIX4 implements this matching-quality hardening:

- case, accent, and whitespace normalization;
- word-boundary matching for short terms, fixing the `bono` / `carbono` false positive;
- phrase matching for terms such as `bases reguladoras`;
- optional section and department filters;
- a documented `la-ayuda` profile;
- deterministic score and score reasons in dry-run sample output.

The original baseline remains useful as the noisy pre-refinement reference: `554` matches from
`3896` scanned documents.
