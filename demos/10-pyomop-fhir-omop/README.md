# 10 · pyomop 6.4.0: FHIR sintético vira OMOP, e o que fica pelo caminho

O pyomop 6.4.0 carregou 60 pacientes FHIR sintéticos num OMOP CDM 5.4 (SQLite) em cerca de 4 s. Todo valor de origem chegou igual (sexo, nascimento, código, valor, data), nenhum CPF, CNS, nome, telefone ou endereço foi parar em tabela alguma, e **todos os `concept_id` clínicos ficaram em 0**: sem vocabulário Athena, a carga não serve pra consulta padronizada. Cada Observation foi gravada em duas tabelas (`measurement` e `observation`) e nenhuma linha clínica ficou ligada à consulta (`visit_occurrence_id` nulo).

*English: pyomop 6.4.0 loaded 60 synthetic FHIR patients into OMOP CDM 5.4 (SQLite) in about 4 s. Source values arrive intact, no CPF/CNS/name/phone/address lands in any table, but every clinical `concept_id` is 0 without an Athena vocabulary, each Observation is written to two tables, and no clinical row links to its visit.*

Artigo: https://rogerio.eti.br/pyomop-fhir-omop-concept-id-zero/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt
python3 demo.py                 # gera o FHIR, roda o pyomop, grava results/
python3 -m pytest tests -q
```

CPU, sem modelo, sem chave. Testado com Python 3.11. `demo.py` roda o comando real do pyomop (`pyomop --create --name cdm.sqlite --input fhir_sintetico`) num SQLite temporário e audita o banco.

## O que faz

1. `gerar_fhir.py` escreve `fhir_sintetico/*.ndjson` (seed 2026): 60 Patient, 109 Encounter, 90 Condition (CID-10), 120 Observation (LOINC 8867-4 e 8480-6), 60 MedicationRequest (RxNorm). Cada Patient tem CPF e CNS no `identifier` (dígito verificador válido, sorteados, de ninguém), nome, telefone e endereço inventados. Condition, Observation e MedicationRequest apontam pra uma consulta no campo `encounter`.
2. `demo.py` carrega com o pyomop e confere cinco coisas: linhas por tabela, valores de origem, dado pessoal em qualquer célula do banco, `concept_id` zerado e vínculo com a consulta.

## Resultado (results/tabela.md)

| Recurso FHIR | no FHIR | tabela OMOP (linhas) |
|---|---|---|
| Patient | 60 | person (60) |
| Encounter | 109 | visit_occurrence (109) |
| Condition | 90 | condition_occurrence (90) |
| Observation | 120 | measurement (120), observation (120) |
| MedicationRequest | 60 | drug_exposure (60) |

- **Valores de origem**: sexo 60/60, nascimento 60/60, medidas (código, valor, data) 120/120, condições 90/90, consultas (início, fim, classe) 109/109, medicamentos 60/60.
- **Dado pessoal em alguma tabela**: CPF 0/60, CNS 0/60, nome completo 0/60, sobrenome 0/60, telefone 0/60, rua 0/60, CEP 0/60. O `person_source_value` guarda só o `id` do Patient (`p001`...).
- **`concept_id` em 0 ou nulo**: condição 90/90, medida 120/120, unidade 120/120, observação 120/120, medicamento 60/60, consulta 109/109, raça e etnia 60/60. Só `gender_concept_id` vem preenchido (8507 e 8532). A tabela `concept` tem 0 linhas.
- **Vínculo com a consulta**: `visit_occurrence_id` preenchido em 0 de 390 linhas clínicas (90 + 120 + 120 + 60), mesmo com `encounter` no FHIR de entrada. O `mapping.default.json` do pyomop 6.4.0 não tem `visit_occurrence_id` nem `encounter` (conferi no arquivo).
- Observation duplicada: as 120 Observation viraram 120 linhas em `measurement` e 120 em `observation`, o que o `mapping.default.json` define.

## Limites honestos

- **Sem vocabulário Athena.** O download exige conta no OHDSI Athena e não fiz. É por isso que `concept_id` ficou em 0. O pyomop tem um passo que preenche `concept_id` por busca de `concept_code` na tabela `concept`; não rodei esse passo com vocabulário, então não sei o quanto ele acerta.
- 60 pacientes sintéticos, uma semente, só os cinco tipos de recurso acima, CDM 5.4, SQLite. Não testei PostgreSQL, CDM 6, Bundle em JSON nem os utilitários de LLM e MCP do pacote.
- Não testei o mapeamento por arquivo próprio (`mapping.example.json`); a demo usa o mapeamento padrão.
- Dado pessoal ausente do banco é o comportamento do mapeamento padrão com estes campos, não uma garantia de privacidade do pacote.
- Todo dado é sintético: CPF e CNS passam no dígito verificador mas são sorteados com seed fixa e não pertencem a ninguém. Nomes, ruas e telefones saem de listas curtas inventadas.

## Fonte

- pyomop: https://github.com/dermatologist/pyomop, versão 6.4.0 (PyPI). O LICENSE do repositório é GPL v3 (o pacote no PyPI não declara licença nos metadados). Dependências fixadas em `requirements.txt`.
- OMOP CDM 5.4: https://ohdsi.github.io/CommonDataModel/

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
