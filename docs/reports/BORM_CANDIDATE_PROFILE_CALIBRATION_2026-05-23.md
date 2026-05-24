# BORM Candidate Profile Calibration

Date: 2026-05-24

Task: `TASK-AUTO-BORM-005B`

Scope: calibrate the metadata-only `borm-ayudas` candidate profile after the first BORM 30-day candidate dry-run.

No candidates were created. No artifacts were downloaded. No downstream project was touched.

## Context

BORM metadata window:

```text
source=BORM
range=2026-04-21 -> 2026-05-20
official_documents=549
document_files=raw_api_response only
```

Previous dry-run report:

```text
docs/reports/BORM_30_DAY_CANDIDATE_DRY_RUN_2026-05-23.md
```

Previous dry-run result:

```text
documents_scanned=549
matches_total=255
matches_after_filters=16
match_rate=2.91%
candidates_created=0
source_candidates=150 -> 150
artifact_download_attempts=482 -> 482
```

## Noise Reviewed

The previous dry-run showed a reasonable overall rate, but several visible noise families:

| Noise family | Examples observed | Calibration outcome |
| --- | --- | --- |
| University hiring | `Profesorado Ayudante Doctor`, university hiring competitions, competition modifications | Excluded |
| Youth procedural records | youth contests, job pools | Excluded |
| Entity/project-only grants | third-sector or project funding without clear direct/person-facing benefit | Downranked unless direct aid signal exists |
| Procedural grant records | collaboration agreements, direct/complementary concession records, order modifications | Excluded |

The calibration intentionally did not make generic `ayudas`, `subvenciones`, `universidad`, `joven`, `empleo`, or `formación` sufficient by themselves.

## Useful Signals Preserved

The profile still preserves direct or likely direct aid signals:

```text
becas
ayudas al estudio
libros de texto
material escolar
comedor escolar
transporte escolar
estudiantes
alumnado
movilidad internacional
ayudas económicas directas
discapacidad
familias
```

The tests explicitly preserve examples for:

```text
school material / textbooks
study grants for university students
youth international mobility aid
person-facing disability/employment aid
```

## Rules Changed

Code commit:

```text
43bb43b fix: calibrate BORM candidate profile
```

Changes:

- Added a BORM-specific candidate profile exclusion path instead of using only the generic autonomous bulletin filter.
- Kept strong direct-aid title signals for education, student, family, youth mobility, disability, and person-facing aid.
- Excluded BORM-specific public employment and contest noise:

```text
Profesorado Ayudante Doctor
concurso público / concursos de profesorado
bolsa de trabajo / bolsa de empleo
procesos selectivos
certámenes / premios
listas / nombramientos / tribunales
```

- Excluded BORM-specific procedural noise:

```text
autorización del convenio
convenio de colaboración
concesión directa
concesión complementaria
orden de concesión
autoriza la concesión
modifica la orden
```

- Downranked entity/project-only subsidy records unless the title has a direct aid/person-facing signal.

## Tests Added

Added deterministic coverage in `tests/test_cli.py` for:

- `borm-ayudas` profile preserving school material, study grant, youth mobility, and disability/person-facing aid examples.
- Excluding `Profesorado Ayudante Doctor` contests.
- Excluding job pools.
- Excluding youth contests.
- Excluding entity/project-only grants.
- Excluding collaboration agreements and concession-result style records.
- Confirming dry-run creates no `source_candidates`.

Local validation:

```text
git diff --check: OK
rtk python -m pytest -q: 423 passed, 1 warning
rtk python -m ruff check .: OK
rtk python -m ruff format --check .: OK
```

## Calibrated VPS Dry-Run

Deployed commit:

```text
43bb43b
```

Command:

```bash
/opt/official-sources/app/.venv/bin/official-sources \
  --db-path /opt/official-sources/data/official_sources.sqlite \
  find-source-candidates \
  --source BORM \
  --date-from 2026-04-21 \
  --date-to 2026-05-20 \
  --profile borm-ayudas \
  --dry-run \
  --limit 200
```

Result:

```text
documents_scanned=549
matches_total=255
matches_after_filters=13
documents_matched=13
candidates_created=0
match_rate=2.37%
```

Reduction versus previous dry-run:

```text
previous_matches_after_filters=16
calibrated_matches_after_filters=13
reduction=3
reduction_percentage=18.75%
```

The result is within the expected good range:

```text
8-16 matches after filters
```

## Safety Checks

Pre-run counts:

```text
source_candidates=150
artifact_download_attempts=482
BORM official_documents in window=549
BORM raw_api_response document_files=549
artifact_bytes=28857411
```

Post-run counts:

```text
source_candidates=150
artifact_download_attempts=482
BORM official_documents in window=549
BORM raw_api_response document_files=549
artifact_bytes=28857411
```

DB validation:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

MCP privacy check:

```text
ss -tulpn | grep -E 'official|mcp|python|uvicorn|fastmcp' || true
```

Result:

```text
no matching exposed official/MCP/python/uvicorn/fastmcp listener observed
```

## Remaining Risks

- BORM metadata titles are sometimes abbreviated/truncated in the official API response, so evidence review may still be needed before downstream routing.
- Entity/project grants can still be ambiguous from metadata alone.
- The profile is deterministic and conservative; it is not a semantic classifier.
- No artifacts were downloaded, so the dry-run cannot verify full legal text.

## Recommendation

Limited BORM candidate creation is now reasonable.

Recommended next task:

```text
TASK-AUTO-BORM-006 — Create limited BORM candidates
```

Suggested limit:

```text
--limit 13
```

Operational constraints for the next task:

```text
one VPS/DB operation only
create candidates only
review_status=human_review_required
no PDF/XML/HTML artifact downloads
no downstream writes
pre/post backup and DB validation required
```
