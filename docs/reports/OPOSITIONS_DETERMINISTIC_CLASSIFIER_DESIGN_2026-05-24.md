# Opositions Deterministic Classifier Design - 2026-05-24

## Scope

Task: `TASK-OPOSITIONS-CLASSIFIER-001`.

This report defines a deterministic alert-type classifier for alert-grade
oposiciones notices.

Guardrails applied:

- documentation-only design;
- no database schema changes;
- no code, tests, VPS, candidates, artifacts, downstream, EduAyudas,
  la-ayuda, or oposiciones2.0 changes;
- no changes outside this report.

## Boundary

The classifier described here is for alert-grade routing only.

It must remain separate from:

- `source_candidates`: candidate discovery and publication-safety state;
- evidence-grade review: human or machine review that confirms primary text,
  legal effect, citation quality, and publication readiness;
- downstream product classification: EduAyudas, la-ayuda, oposiciones2.0, or
  any other consumer-specific taxonomy.

Alert-grade output can help decide which notice deserves attention and how to
label an alert. It must not be treated as evidence that the notice is legally
valid, complete, publication-safe, or ready for downstream rendering.

## Inputs

The deterministic classifier should operate on normalized text assembled from a
single notice record:

- title;
- summary or abstract;
- section heading;
- issuing body;
- optional document metadata fields already available locally.

The classifier should not require PDF download, external lookup, downstream
context, or cross-notice reasoning. If the available text is insufficient, it
should return `other` with low confidence instead of inferring from source or
portal context.

## Output Contract

Recommended alert-grade fields:

```text
alert_type=<one of the supported types>
confidence=<high|medium|low>
matched_rules=[<stable rule names>]
classifier_version=opositions_deterministic_v1
```

Supported `alert_type` values:

- `convocatoria`
- `bolsa`
- `bases`
- `lista_provisional`
- `lista_definitiva`
- `tribunal`
- `fecha_examen`
- `plazo`
- `subsanacion`
- `correccion`
- `nombramiento`
- `adjudicacion`
- `other`

`matched_rules` must be stable, human-readable identifiers. They should name the
alert type, term strength, and semantic shape, for example:

```text
convocatoria.strong.convoca_proceso_selectivo
lista_definitiva.strong.lista_definitiva_admitidos
fecha_examen.weak.fecha_realizacion_prueba
correccion.exclusion.errata_not_oposition
```

## Normalization

Before matching:

- lowercase text;
- remove accents for matching only;
- collapse repeated whitespace;
- normalize punctuation separators to spaces;
- preserve the original text for reporting and audit;
- match whole words or controlled phrase windows, not arbitrary substrings.

Examples:

- `subsanacion` should match `subsanacion` and `subsanación`;
- `bolsa` should not match inside unrelated words;
- `lista definitiva` should match across a punctuation separator such as
  `lista: definitiva`.

## Confidence Logic

Confidence is deterministic and rule-driven.

High confidence:

- at least one strong rule matched;
- no exclusion rule matched;
- no higher-priority conflicting strong rule matched;
- the rule is anchored to an oposiciones/provision/selective-process context.

Medium confidence:

- one strong rule matched but context is generic;
- or two or more weak rules matched in a compatible context;
- or one weak rule matched with a strong general oposiciones context.

Low confidence:

- only one weak rule matched;
- or the notice has generic public-employment vocabulary but no clear alert
  type;
- or competing weak signals exist and no strong rule resolves them.

If an exclusion rule matches the winning type, downgrade to `other` unless a
more specific high-confidence type remains after applying priority rules.

## Priority Order

When multiple alert types match, apply this priority order:

1. `correccion`
2. `subsanacion`
3. `lista_definitiva`
4. `lista_provisional`
5. `fecha_examen`
6. `tribunal`
7. `nombramiento`
8. `adjudicacion`
9. `convocatoria`
10. `bases`
11. `bolsa`
12. `plazo`
13. `other`

Rationale:

- corrections and subsanation notices often mention the original notice type but
  the actionable alert is the correction or remedy window;
- list, exam-date, tribunal, appointment, and award notices are later-process
  actions and should override generic convocatoria/bases language;
- `plazo` is often a secondary attribute and should only win when no more
  specific type is present.

## General Oposiciones Context

Some alert types require a general public-employment context before their weak
terms can count.

Strong context terms:

- `oposicion`
- `oposiciones`
- `concurso-oposicion`
- `concurso oposicion`
- `proceso selectivo`
- `procedimiento selectivo`
- `seleccion de personal`
- `personal funcionario`
- `personal laboral`
- `funcionario de carrera`
- `funcionario interino`
- `empleo publico`
- `oferta de empleo publico`
- `OEP` after case-preserving tokenization

Weak context terms:

- `aspirantes`
- `admitidos`
- `excluidos`
- `meritos`
- `baremacion`
- `turno libre`
- `promocion interna`
- `estabilizacion`
- `provision de puestos`
- `cuerpo`
- `escala`
- `categoria profesional`

General exclusions:

- procurement-only notices;
- grants or subsidies;
- education admission processes for students;
- private-sector hiring announcements;
- purely organizational appointments unrelated to a selection process;
- judicial, electoral, or collegiate notices that use similar terms without
  public-employment context.

## Type Rules

### convocatoria

Strong terms:

- `se convoca proceso selectivo`
- `convocatoria de pruebas selectivas`
- `convocatoria para la provision`
- `convocar pruebas selectivas`
- `convoca concurso-oposicion`
- `convoca oposicion`

Weak terms:

- `convocatoria`
- `convocar`
- `proceso selectivo`
- `pruebas selectivas`
- `turno libre`
- `promocion interna`

Exclusions:

- `convocatoria de subvenciones`
- `convocatoria de ayudas`
- `convocatoria de licitacion`
- `convocatoria de sesion`
- `convocatoria de elecciones`
- `convocatoria de asamblea`

Matched rule examples:

- `convocatoria.strong.convoca_proceso_selectivo`
- `convocatoria.strong.pruebas_selectivas`
- `convocatoria.weak.convocatoria_with_opositions_context`
- `convocatoria.exclusion.non_employment_call`

False-positive risks:

- subsidy, procurement, meeting, or election calls using `convocatoria`;
- announcements of OEP approval without a concrete selection call;
- downstream content that wants separate treatment for ordinary hiring vs
  statutory public-employment selection.

### bolsa

Strong terms:

- `bolsa de trabajo`
- `bolsa de empleo`
- `bolsa de interinos`
- `bolsa de empleo temporal`
- `lista de espera para nombramientos interinos`
- `constitucion de bolsa`

Weak terms:

- `bolsa`
- `interinos`
- `empleo temporal`
- `lista de espera`
- `llamamientos`

Exclusions:

- `bolsa de estudios`
- `bolsa de viaje`
- `bolsa de valores`
- `bolsa de comercio`
- `bolsas de ayudas`

Matched rule examples:

- `bolsa.strong.bolsa_de_trabajo`
- `bolsa.strong.bolsa_interinos`
- `bolsa.weak.lista_espera_with_public_employment_context`
- `bolsa.exclusion.non_employment_bolsa`

False-positive risks:

- financial or scholarship use of `bolsa`;
- temporary-employment notices that are actually adjudication or appointment
  resolutions;
- generic references to an existing bolsa inside another notice type.

### bases

Strong terms:

- `bases reguladoras de la convocatoria`
- `bases que han de regir`
- `aprueba las bases`
- `bases especificas`
- `bases generales`
- `bases de seleccion`

Weak terms:

- `bases`
- `criterios de valoracion`
- `baremo`
- `sistema selectivo`
- `requisitos de participacion`

Exclusions:

- `bases reguladoras de subvenciones`
- `bases de ayudas`
- `base imponible`
- `base de datos`
- `bases de licitacion`

Matched rule examples:

- `bases.strong.bases_han_de_regir`
- `bases.strong.aprueba_bases_seleccion`
- `bases.weak.baremo_with_opositions_context`
- `bases.exclusion.non_employment_bases`

False-positive risks:

- grant, procurement, tax, or database uses of `bases`;
- convocatoria notices that include bases as attached content but whose main
  action is the call;
- amendment notices that modify bases and should classify as `correccion` or
  `subsanacion`.

### lista_provisional

Strong terms:

- `lista provisional de admitidos`
- `lista provisional de admitidos y excluidos`
- `relacion provisional de admitidos`
- `relacion provisional de aspirantes admitidos`
- `aprobacion provisional de la lista`

Weak terms:

- `lista provisional`
- `relacion provisional`
- `admitidos y excluidos`
- `aspirantes admitidos`
- `aspirantes excluidos`

Exclusions:

- `lista provisional de beneficiarios`
- `lista provisional de subvenciones`
- `relacion provisional de adjudicatarios` when procurement or grants context
  dominates;
- `calificaciones provisionales` without admitidos/excluidos or selection-list
  context.

Matched rule examples:

- `lista_provisional.strong.lista_provisional_admitidos_excluidos`
- `lista_provisional.strong.relacion_provisional_aspirantes`
- `lista_provisional.weak.lista_provisional_with_opositions_context`
- `lista_provisional.exclusion.non_employment_beneficiaries`

False-positive risks:

- provisional grant-beneficiary lists;
- provisional procurement award lists;
- provisional exam marks that should perhaps remain `other` unless the product
  later adds a grades-specific type.

### lista_definitiva

Strong terms:

- `lista definitiva de admitidos`
- `lista definitiva de admitidos y excluidos`
- `relacion definitiva de admitidos`
- `relacion definitiva de aspirantes admitidos`
- `aprobacion definitiva de la lista`

Weak terms:

- `lista definitiva`
- `relacion definitiva`
- `definitiva de admitidos`
- `definitiva de excluidos`

Exclusions:

- `lista definitiva de beneficiarios`
- `lista definitiva de subvenciones`
- `relacion definitiva de adjudicatarios` when procurement or grants context
  dominates;
- `calificaciones definitivas` without admitidos/excluidos or selection-list
  context.

Matched rule examples:

- `lista_definitiva.strong.lista_definitiva_admitidos_excluidos`
- `lista_definitiva.strong.relacion_definitiva_aspirantes`
- `lista_definitiva.weak.lista_definitiva_with_opositions_context`
- `lista_definitiva.exclusion.non_employment_beneficiaries`

False-positive risks:

- definitive grant-beneficiary lists;
- definitive procurement awards;
- final marks or merit scores that are not admission/exclusion lists.

### tribunal

Strong terms:

- `nombramiento del tribunal calificador`
- `designacion del tribunal calificador`
- `composicion del tribunal`
- `miembros del tribunal`
- `tribunal de seleccion`
- `organo de seleccion`

Weak terms:

- `tribunal`
- `calificador`
- `vocales`
- `presidente del tribunal`
- `secretario del tribunal`

Exclusions:

- judicial courts and court rulings;
- administrative appeal bodies unrelated to selection;
- exam tribunal references inside a broader correction notice.

Matched rule examples:

- `tribunal.strong.nombramiento_tribunal_calificador`
- `tribunal.strong.composicion_tribunal`
- `tribunal.weak.tribunal_with_opositions_context`
- `tribunal.exclusion.judicial_court`

False-positive risks:

- judicial notices using `tribunal`;
- corrections that mention tribunal composition but mainly correct an error;
- internal appointment notices for committees outside public-employment
  selection.

### fecha_examen

Strong terms:

- `fecha de examen`
- `fecha del primer ejercicio`
- `lugar fecha y hora`
- `se convoca a los aspirantes`
- `realizacion del ejercicio`
- `celebracion de la prueba`
- `llamamiento para la realizacion`

Weak terms:

- `examen`
- `ejercicio`
- `prueba`
- `lugar`
- `hora`
- `llamamiento`

Exclusions:

- general exam regulations without a dated call;
- education-student exams;
- medical tests or technical inspections outside selection;
- `fecha limite` for applications, which should usually be `plazo`.

Matched rule examples:

- `fecha_examen.strong.fecha_primer_ejercicio`
- `fecha_examen.strong.lugar_fecha_hora`
- `fecha_examen.weak.llamamiento_with_aspirantes_context`
- `fecha_examen.exclusion.deadline_not_exam_date`

False-positive risks:

- application deadline dates;
- notices publishing syllabi or bases that mention exams generically;
- education-sector student examination calendars.

### plazo

Strong terms:

- `plazo de presentacion de solicitudes`
- `abre plazo de presentacion`
- `amplia el plazo`
- `nuevo plazo de solicitudes`
- `plazo para presentar instancias`
- `plazo de alegaciones`

Weak terms:

- `plazo`
- `solicitudes`
- `instancias`
- `alegaciones`
- `dias habiles`
- `reclamaciones`

Exclusions:

- deadlines for procurement, grants, or tax procedures;
- remedy windows that should be `subsanacion`;
- appeal periods after final administrative decisions when no selection-process
  action is being announced.

Matched rule examples:

- `plazo.strong.presentacion_solicitudes`
- `plazo.strong.amplia_plazo`
- `plazo.weak.plazo_with_opositions_context`
- `plazo.exclusion.subsanation_window`

False-positive risks:

- almost every administrative notice has a deadline;
- `plazo` is often secondary to convocatoria, bases, list, or correction;
- product users may expect deadline extraction separately from alert-type
  classification.

### subsanacion

Strong terms:

- `subsanacion de solicitudes`
- `requerimiento de subsanacion`
- `plazo de subsanacion`
- `subsanar defectos`
- `subsanar errores`
- `lista de aspirantes que deben subsanar`

Weak terms:

- `subsanacion`
- `subsanar`
- `defectos`
- `documentacion requerida`
- `requerimiento`

Exclusions:

- correction of the bulletin text itself, which should be `correccion`;
- generic defect correction outside a public-employment process;
- procurement or grant-documentation remedy windows unless an oposiciones context
  is explicit.

Matched rule examples:

- `subsanacion.strong.requerimiento_subsanacion`
- `subsanacion.strong.plazo_subsanacion_solicitudes`
- `subsanacion.weak.subsanar_with_aspirantes_context`
- `subsanacion.exclusion.bulletin_errata`

False-positive risks:

- public-procurement remedy windows;
- grant-application remedy windows;
- corrections that use `subsanar` colloquially but legally operate as errata.

### correccion

Strong terms:

- `correccion de errores`
- `corrige errores`
- `rectificacion de errores`
- `se rectifica`
- `modificacion de la convocatoria`
- `modificacion de las bases`
- `anuncio de correccion`

Weak terms:

- `correccion`
- `rectificacion`
- `modificacion`
- `error material`
- `errores advertidos`

Exclusions:

- applicant correction or remedy windows, which should be `subsanacion`;
- routine amendments unrelated to a selection process;
- legal text corrections outside public employment.

Matched rule examples:

- `correccion.strong.correccion_errores`
- `correccion.strong.modificacion_bases`
- `correccion.weak.rectificacion_with_opositions_context`
- `correccion.exclusion.applicant_subsanation`

False-positive risks:

- grant or procurement corrections;
- notices that modify employment structures but not a selection process;
- `correccion` used in the sense of exam grading, not bulletin errata.

### nombramiento

Strong terms:

- `nombramiento como funcionario de carrera`
- `nombramiento de funcionarios de carrera`
- `nombramiento de personal laboral fijo`
- `nombramiento de funcionarios interinos`
- `se nombran funcionarios`
- `toma de posesion`

Weak terms:

- `nombramiento`
- `nombrar`
- `funcionario de carrera`
- `personal laboral fijo`
- `toma de posesion`
- `interino`

Exclusions:

- appointment of tribunal members, which should be `tribunal`;
- appointment of political, advisory, or managerial posts outside a selection
  process;
- generic personnel appointments without a process reference.

Matched rule examples:

- `nombramiento.strong.funcionario_carrera`
- `nombramiento.strong.personal_laboral_fijo`
- `nombramiento.weak.toma_posesion_with_selection_context`
- `nombramiento.exclusion.tribunal_members`

False-positive risks:

- tribunal appointments;
- freely appointed roles or political appointments;
- personnel movements unrelated to oposiciones.

### adjudicacion

Strong terms:

- `adjudicacion de destinos`
- `adjudica destinos`
- `destinos adjudicados`
- `resolucion de adjudicacion`
- `adjudicacion provisional de destinos`
- `adjudicacion definitiva de destinos`

Weak terms:

- `adjudicacion`
- `adjudicar`
- `destinos`
- `puestos adjudicados`
- `concurso de traslados`
- `provision de puestos`

Exclusions:

- procurement awards;
- grant awards;
- contract lots;
- property or public-domain concessions;
- destination lists that are actually appointment resolutions and match
  `nombramiento` more strongly.

Matched rule examples:

- `adjudicacion.strong.adjudicacion_destinos`
- `adjudicacion.strong.destinos_adjudicados`
- `adjudicacion.weak.provision_puestos_with_public_employment_context`
- `adjudicacion.exclusion.procurement_award`

False-positive risks:

- procurement notices are the dominant source of `adjudicacion` false positives;
- grants and subsidy awards;
- mobility or destination notices that consumers may want separated from
  selection-process alerts.

### other

Use `other` when:

- no alert type reaches medium confidence;
- only generic public-employment terms are present;
- exclusions remove all specific matches;
- the notice is about OEP approval without a concrete actionable process step;
- the notice is evidence-relevant but not alert-type-specific.

Matched rule examples:

- `other.no_specific_alert_type`
- `other.exclusions_removed_specific_matches`
- `other.low_confidence_generic_public_employment`

False-positive risks:

- under-classifying terse bulletin titles that omit details available only in
  full text;
- losing useful alerts where the source uses uncommon terminology;
- masking a new class that should later become a supported type.

## Example Classifications

```text
title="Resolucion por la que se convoca proceso selectivo para ingreso..."
alert_type=convocatoria
confidence=high
matched_rules=[
  "convocatoria.strong.convoca_proceso_selectivo"
]
```

```text
title="Lista provisional de aspirantes admitidos y excluidos..."
alert_type=lista_provisional
confidence=high
matched_rules=[
  "lista_provisional.strong.lista_provisional_admitidos_excluidos"
]
```

```text
title="Correccion de errores de la convocatoria del proceso selectivo..."
alert_type=correccion
confidence=high
matched_rules=[
  "correccion.strong.correccion_errores",
  "convocatoria.weak.convocatoria_with_opositions_context"
]
```

```text
title="Se convoca a los aspirantes para la realizacion del primer ejercicio..."
alert_type=fecha_examen
confidence=high
matched_rules=[
  "fecha_examen.strong.fecha_primer_ejercicio",
  "fecha_examen.weak.llamamiento_with_aspirantes_context"
]
```

```text
title="Convocatoria de subvenciones destinadas a entidades locales..."
alert_type=other
confidence=low
matched_rules=[
  "convocatoria.exclusion.non_employment_call",
  "other.exclusions_removed_specific_matches"
]
```

## Review And Audit Notes

The classifier should record enough detail for later audit:

- normalized input fields used;
- winning type;
- confidence;
- matched rules;
- exclusions applied;
- losing strong matches, if any;
- classifier version.

This audit data is operational metadata for alert routing. It should not be
written into `source_candidates.review_status`, should not imply evidence-grade
approval, and should not be exposed as publication-safe text unless a downstream
contract explicitly accepts alert-grade labels.

## Open Implementation Questions

Future implementation work should decide, with tests, whether to:

- emit secondary attributes such as application deadline or exam date separately
  from `alert_type`;
- add later alert types for grades, merit scores, OEP approvals, or syllabi;
- tune source-specific synonym lists without changing the global contract;
- expose low-confidence matches to internal operators or suppress them by
  default.

These are implementation questions only. They do not change the docs-only scope
of this design task.
