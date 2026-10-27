pyomop 6.4.0, CDM 5.4, SQLite. Comando: pyomop --create --name cdm.sqlite --input fhir_sintetico

## Linhas por recurso

| Recurso FHIR | no FHIR | tabela OMOP (linhas) |
|---|---|---|
| Patient | 60 | person (60) |
| Encounter | 109 | visit_occurrence (109) |
| Condition | 90 | condition_occurrence (90) |
| Observation | 120 | measurement (120), observation (120) |
| MedicationRequest | 60 | drug_exposure (60) |

## Valores de origem que chegaram iguais

| Conferência | iguais |
|---|---|
| person: sexo de origem | 60/60 |
| person: data de nascimento | 60/60 |
| measurement: código, valor e data | 120/120 |
| condition_occurrence: código e data | 90/90 |
| visit_occurrence: início, fim e classe | 109/109 |
| drug_exposure: código e data | 60/60 |

## Dado pessoal em alguma tabela (60 pacientes)

| Dado | pacientes achados |
|---|---|
| CPF | 0/60 |
| CNS | 0/60 |
| nome completo | 0/60 |
| sobrenome | 0/60 |
| telefone | 0/60 |
| rua | 0/60 |
| CEP | 0/60 |

## concept_id em 0 ou nulo (sem vocabulário Athena)

| Coluna | em 0 ou nulo |
|---|---|
| person.gender_concept_id | 0/60 |
| person.race_concept_id | 60/60 |
| person.ethnicity_concept_id | 60/60 |
| visit_occurrence.visit_concept_id | 109/109 |
| condition_occurrence.condition_concept_id | 90/90 |
| measurement.measurement_concept_id | 120/120 |
| measurement.unit_concept_id | 120/120 |
| observation.observation_concept_id | 120/120 |
| drug_exposure.drug_concept_id | 60/60 |

Linhas na tabela concept: 0

## Linhas com visit_occurrence_id

| Tabela | com vínculo |
|---|---|
| condition_occurrence | 0/90 |
| measurement | 0/120 |
| observation | 0/120 |
| drug_exposure | 0/60 |

person_source_value (3 primeiros): [('p001',), ('p002',), ('p003',)]
