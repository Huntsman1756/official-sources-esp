# Oposiciones refined alert sample review

Date: 2026-05-24

Task: `TASK-OPOSITIONS-CLASSIFIER-003`

## Summary

This review inspected refined per-source alert-grade dry-run samples after `TASK-OPOSITIONS-CLASSIFIER-002`.

No code changes were made.
No DB rows were written.
No `source_alerts` were created.
No `source_candidates` were created.
No artifacts were downloaded.
No downstream output was touched.

The refined classifier is much better than the original prototype, but the remaining volume is not just classifier noise. It reflects a product-scope decision:

```text
strict oposiciones only
vs
public employment broad
vs
two-tier strict + broad
```

Recommended scope:

```text
two-tier: strict + broad
```

Do not implement storage yet.

## Inputs

Latest code/report context:

```text
1f71ee5 fix: refine oposiciones alert classifier
docs/reports/OPOSITIONS_CLASSIFIER_REFINEMENT_2026-05-24.md
```

Refined VPS output inspected:

```text
/opt/official-sources/data/reports_tmp/opositions_alert_classifier_refined_2026-05-24/
```

Sources reviewed:

```text
BOE
BOJA
DOGV
BOCYL
BOPV
BORM
```

Sample strategy:

- all BOE alerts because there were only 7;
- up to 10 high-confidence alerts per source;
- up to 10 medium-confidence alerts per source;
- deterministic pseudo-random sample for higher-volume sources;
- top `matched_rules` and `alert_type` distribution reviewed per source.

The sample labels below are review labels for this report. They are not persisted anywhere.

## Refined baseline

| Source | Documents | Alerts | Alert rate |
| --- | ---: | ---: | ---: |
| BOE | 3984 | 7 | 0.18% |
| BOJA | 1500 | 227 | 15.13% |
| DOGV | 1113 | 307 | 27.58% |
| BOCYL | 773 | 162 | 20.96% |
| BOPV | 489 | 48 | 9.82% |
| BORM | 549 | 130 | 23.68% |

Total:

```text
881 / 8408 = 10.48%
```

No source was truncated by `--limit 1000`.

## Per-source sample review

### BOE

Sample size:

```text
7 / 7
```

Sample distribution:

| Label | Count |
| --- | ---: |
| true_positive | 0 |
| probably_relevant | 7 |
| unclear | 0 |
| false_positive | 0 |

Scope distribution:

| Scope | Count |
| --- | ---: |
| strict_oposiciones | 0 |
| public_employment_broad | 7 |
| employment_related_but_not_oposicion | 0 |
| not_relevant | 0 |

Useful patterns:

- Banco de Espana processes for provision of places.
- Education ministry calls for auxiliary/professor places abroad.

Main issues:

- Alerts are relevant only under broad public-employment scope.
- All were classified as `other`, which is too vague for product use.

Recommendation:

```text
include in first prototype only as broad public-employment alerts
```

### BOJA

Sample size:

```text
30 / 227
```

Sample distribution:

| Label | Count |
| --- | ---: |
| true_positive | 17 |
| probably_relevant | 13 |
| unclear | 0 |
| false_positive | 0 |

Scope distribution:

| Scope | Count |
| --- | ---: |
| strict_oposiciones | 17 |
| public_employment_broad | 13 |
| employment_related_but_not_oposicion | 0 |
| not_relevant | 0 |

Useful patterns:

- SAS lists and contest-opposition results.
- Junta de Andalucia appointment notices after selection processes.
- Local police and municipal selection processes.
- University administrative process notices.

Main issues:

- High volume is mostly real public-employment volume, not only classifier noise.
- `convocatoria` is still overused as an alert type for list/result records.
- Some appointment notices are broad/public-employment, not strict new-opposition alerts.

Recommendation:

```text
include in first prototype, but split strict_oposiciones from public_employment_broad
```

### DOGV

Sample size:

```text
30 / 307
```

Sample distribution:

| Label | Count |
| --- | ---: |
| true_positive | 16 |
| probably_relevant | 4 |
| unclear | 10 |
| false_positive | 0 |

Scope distribution:

| Scope | Count |
| --- | ---: |
| strict_oposiciones | 16 |
| public_employment_broad | 7 |
| employment_related_but_not_oposicion | 7 |
| not_relevant | 0 |

Useful patterns:

- bolsas de empleo temporal;
- definitive/provisional lists;
- dates for first exercises;
- Generalitat public-employment processes.

Main issues:

- DOGV has high real employment volume.
- `other` captures public employment offers and management notices that need a separate type.
- Some research/project hiring notices may be valid public employment but not strict oposiciones.

Recommendation:

```text
include in first prototype after type refinement; keep broad tier separate
```

### BOCYL

Sample size:

```text
29 / 162
```

Sample distribution:

| Label | Count |
| --- | ---: |
| true_positive | 14 |
| probably_relevant | 10 |
| unclear | 5 |
| false_positive | 0 |

Scope distribution:

| Scope | Count |
| --- | ---: |
| strict_oposiciones | 14 |
| public_employment_broad | 12 |
| employment_related_but_not_oposicion | 3 |
| not_relevant | 0 |

Useful patterns:

- local-government processes;
- bolsa de empleo;
- process results and adjudication of destinations;
- health-service and regional administration selection processes.

Main issues:

- `plazas` remains ambiguous. It can mean public-employment vacancies, but also non-employment physical capacity in environmental records.
- University professor access notices need product-scope treatment.
- Several true employment records are typed as generic `convocatoria` when they are result/list/adjudication notices.

Recommendation:

```text
include in first prototype after handling ambiguous plazas and type refinement
```

### BOPV

Sample size:

```text
24 / 48
```

Sample distribution:

| Label | Count |
| --- | ---: |
| true_positive | 1 |
| probably_relevant | 13 |
| unclear | 10 |
| false_positive | 0 |

Scope distribution:

| Scope | Count |
| --- | ---: |
| strict_oposiciones | 1 |
| public_employment_broad | 16 |
| employment_related_but_not_oposicion | 7 |
| not_relevant | 0 |

Useful patterns:

- Lanbide and public-employment provision processes.
- Some direct process-selection notices.
- University appointment notices linked to previous competitions.

Main issues:

- BOPV is mainly broad employment/provision/appointment signal in this range.
- A high-confidence `subsanacion` sample was a generic administrative claim, not an oposiciones notice.
- University appointment notices may be useful, but not for strict-oposiciones users.

Recommendation:

```text
do not include BOPV in strict-first prototype unless broad tier is implemented
```

### BORM

Sample size:

```text
28 / 130
```

Sample distribution:

| Label | Count |
| --- | ---: |
| true_positive | 19 |
| probably_relevant | 8 |
| unclear | 1 |
| false_positive | 0 |

Scope distribution:

| Scope | Count |
| --- | ---: |
| strict_oposiciones | 19 |
| public_employment_broad | 8 |
| employment_related_but_not_oposicion | 1 |
| not_relevant | 0 |

Useful patterns:

- tribunal appointment plus admitted/excluded lists;
- provisional lists;
- Servicio Murciano de Salud selection processes;
- university technical-scale processes;
- bolsa de trabajo.

Main issues:

- The high volume is mostly real process volume.
- University professor/cuerpo docente notices need scope policy.
- `other` is too broad and should not be user-facing as-is.

Recommendation:

```text
include in first prototype; BORM is one of the strongest sources for strict alerts
```

## Product scope decision

Recommended scope:

```text
two-tier: strict + broad
```

Reasoning:

- `strict_oposiciones_only` would be cleaner, but would discard useful employment-public notices users may expect, such as OPE, appointments after processes, university/public-body processes and broad provision notices.
- `public_employment_broad` alone would keep too much volume and make the product feel noisy.
- A two-tier model allows safe product behavior:

```text
strict = user-facing default
broad = review queue / optional advanced filter
```

Proposed tiers:

### Strict

```text
proceso selectivo
pruebas selectivas
concurso-oposicion
bolsa de trabajo
bolsa de empleo
lista provisional
lista definitiva
admitidos/excluidos
tribunal calificador
fecha examen
subsanacion tied to process
nombramiento tied to process completion
```

### Broad

```text
oferta publica de empleo
libre designacion
provision de puestos
university access/professor appointments
appointments in execution of judgments
public employment management notices
```

## Source inclusion recommendation

First prototype recommendation:

| Source | Include? | Tier |
| --- | --- | --- |
| BORM | yes | strict + broad |
| BOJA | yes | strict + broad |
| BOCYL | yes | strict + broad |
| DOGV | yes | strict + broad after type refinement |
| BOE | limited | broad only or review-only |
| BOPV | defer strict; include broad only if product wants provision/appointments |

Recommended first measurement/export set:

```text
BORM
BOJA
BOCYL
DOGV
```

Keep BOE and BOPV in review-only until tiering and type labels are better.

## Classifier changes needed

No classifier changes were made in this task.

Recommended next classifier changes:

1. Add `alert_scope` to dry-run output:

```text
strict_oposiciones
public_employment_broad
employment_related_but_not_oposicion
unclear
```

2. Split `other` into more useful types:

```text
oferta_publica_empleo
provision_puestos
nombramiento_post_proceso
empleo_universitario
resultado_proceso
```

3. Reduce ambiguous `plazas` false positives:

```text
plazas should require employment context unless paired with cuerpo/escala/proceso/selectivo/funcionario/laboral.
```

4. Make `subsanacion` require process context.

5. Add source-specific confidence tuning:

- BOE: strict gating by process context.
- BOPV: downgrade provision/appointment notices unless strict process terms exist.
- BORM: keep tribunal/lista provisional strong.
- BOJA/DOGV/BOCYL: preserve employment-process volume but improve type assignment.

## Storage/import decision

Storage remains blocked.

Do not create:

```text
source_alerts
opposition_alerts
DB migrations
product imports
```

Reason:

- alert rate is still high;
- `other` is too broad;
- scope tier is not encoded;
- product behavior depends on strict vs broad distinction.

## Safety verification

This task only inspected existing refined dry-run JSON files and validated DB state.

DB validation:

```text
database_path=/opt/official-sources/data/official_sources.sqlite
current_version=8
latest_version=8
status=valid
```

No artifacts were downloaded.
No DB rows were written.
No candidates were created.

## Next recommended task

Recommended:

```text
TASK-OPOSITIONS-CLASSIFIER-004 — Add alert_scope and refined alert types to dry-run output
```

This should still be dry-run only.

After that:

```text
TASK-OPOSITIONS-ALERT-GRADE-005 — Export scoped dry-run alerts for oposiciones2.0 review
```

Still without DB migration and without persistent `source_alerts`.
