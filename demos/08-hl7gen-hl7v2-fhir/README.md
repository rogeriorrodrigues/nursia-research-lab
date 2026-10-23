# 08 · hl7gen 0.2.0: synthetic HL7 v2 to FHIR, and what the converter drops

hl7gen 0.2.0 generated 185 HL7 v2.5 message types, and all 185 passed its own validator. Only 8 convert to FHIR; the other 177 stop with `UnsupportedMessageTypeError`. In 200 ADT_A01 and ORU_R01 messages, every patient family name is an 8-character random token and every phone number keeps raw HL7 components. A hand-written message with a synthetic CPF and CNS in PID-3 produces a Patient with no `identifier`: both numbers are dropped.

[Português abaixo](#pt-br)

## Try it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python demo.py          # about 8.5 minutes on CPU (one run: 8 min 25 s, timed separately); writes results/
.venv/bin/python -m pytest -s -q  # about 5 seconds
```

CPU only, no GPU, no API key, no network after `pip install`. `--realistic` (patient data written by an Anthropic model) was not run: it uses ANTHROPIC_API_KEY. `send`, the MCP server and the playground were not run either.

## What it does

| File | Role |
|---|---|
| `demo.py` | seeds the generator (2026), walks all 185 types, runs a batch of 100 ADT_A01 and 100 ORU_R01, converts to FHIR R4B, runs a hand-written Brazilian message, writes `results/` |
| `tests/test_demo.py` | 6 tests: CPF/CNS dropped, accents kept, validator accepts an impossible date while the converter fails, unsupported type refused, seed reproduces, name token and raw phone |
| `results/` | real output: `saida.txt`, `resumo.json`, `cobertura.csv` (185 rows), `br_bundle.json`, one sample HL7 and FHIR bundle per type, `pytest.txt` |

The CPF and CNS in the hand-written message pass the check digit and belong to no one. No real patient data anywhere.

## Result (one run, Python 3.11, hl7gen 0.2.0, Linux)

| Measure | Value |
|---|---|
| HL7 v2.5 message types listed | 185 |
| Generated and passed `validate` | 185 of 185 |
| Converted to FHIR (R4B and R5) | 8 of 185; 177 `UnsupportedMessageTypeError` |
| Batch: ADT_A01 and ORU_R01 valid and converted | 200 of 200 |
| Patient family name is an 8-character token | 200 of 200 |
| Phone `value` keeps raw HL7 components (`^`) | 200 of 200 |
| Patient without `identifier` | 200 of 200 |
| Patient without `gender` | 74 of 200 |
| Encounter class set by the AMB default (PV1-2 not I, O or E) | 130 of 200 |
| Observations as `valueString` / `valueQuantity` | 300 / 0 |
| ADT_A01 → FHIR, characters of HL7 vs bytes of JSON | 3,543,160 → 69,130 |
| ADT_A01 → FHIR, non-empty HL7 fields vs FHIR leaf values | 63,300 → 2,161 |
| ORU_R01 → FHIR, characters of HL7 vs bytes of JSON | 2,632,542 → 86,846 |
| ORU_R01 → FHIR, non-empty HL7 fields vs FHIR leaf values | 45,100 → 2,765 |
| Hand-written message with CPF and CNS in PID-3 | Patient has no `identifier`; neither number is in the bundle |
| Accents ("Conceição", "Florianópolis") | kept |
| PID-7 = `20261345` | `validate` says valid; `to-fhir` raises `ValidationError` |

The full run took 8 min 25 s (timed separately, not stored in results/).

## Limits

- Synthetic data only, from the tool's own random generator. It shows how the tool behaves; it measures nothing about real HL7 feeds.
- The batch is 100 messages per type, two types. Other types and HL7 versions other than 2.5 were not measured.
- By reading the code, the mapping uses PID-5, 7, 8, 11 and 13, PV1-2 and OBX. The rest is not converted. The 8 of 185 is declared scope: the module docstring says it covers common ADT/ORU/ORM, not all ~185 types. The code accepts 10 types; ADT_A04 and ADT_A08 are not among the 185 the generator lists.
- I did not compare with a reference HL7 v2 to FHIR converter. "Drops CPF" is about hl7gen 0.2.0, not about the whole category.
- `fhir.resources` parsed every bundle it produced. That is not the HL7 FHIR validator, which was not run.
- Dates in the generated messages depend on the day you run it (Faker draws up to today). Counts of structure do not.

Article: https://rogerio.eti.br/hl7gen-hl7v2-fhir-sintetico/

<a id="pt-br"></a>

# 08 · hl7gen 0.2.0: HL7 v2 sintético para FHIR, e o que o conversor descarta

O hl7gen 0.2.0 gerou 185 tipos de mensagem HL7 v2.5, e as 185 passaram no validador da própria ferramenta. Só 8 convertem para FHIR; as outras 177 param com `UnsupportedMessageTypeError`. Em 200 mensagens ADT_A01 e ORU_R01, todo sobrenome de paciente é um token aleatório de 8 caracteres e todo telefone mantém os componentes crus do HL7. Uma mensagem escrita à mão, com CPF e CNS sintéticos no PID-3, gera um Patient sem `identifier`: os dois números somem.

## Como rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python demo.py          # cerca de 8,5 minutos em CPU (uma execução: 8 min 25 s, medidos à parte); escreve results/
.venv/bin/python -m pytest -s -q  # cerca de 5 segundos
```

Só CPU, sem GPU, sem chave de API, sem rede depois do `pip install`. O `--realistic` (dado de paciente escrito por um modelo da Anthropic) não foi rodado: usa a ANTHROPIC_API_KEY. O `send`, o servidor MCP e o playground também não foram rodados.

## O que tem aqui

| Arquivo | Papel |
|---|---|
| `demo.py` | fixa a semente do gerador (2026), percorre os 185 tipos, roda um lote de 100 ADT_A01 e 100 ORU_R01, converte para FHIR R4B, roda uma mensagem brasileira escrita à mão e grava `results/` |
| `tests/test_demo.py` | 6 testes: CPF/CNS descartados, acentos mantidos, validador aceita data impossível e o conversor falha, tipo não suportado recusado, semente reproduz, nome em token e telefone cru |
| `results/` | saída real: `saida.txt`, `resumo.json`, `cobertura.csv` (185 linhas), `br_bundle.json`, uma amostra HL7 e FHIR por tipo, `pytest.txt` |

O CPF e o CNS da mensagem escrita à mão passam no dígito verificador e não pertencem a ninguém. Nenhum dado de paciente real.

## Limites

- Só dado sintético, do gerador aleatório da própria ferramenta. Mostra como a ferramenta se comporta; não mede nada sobre feeds HL7 reais.
- O lote tem 100 mensagens por tipo, em dois tipos. Os outros tipos e versões do HL7 diferentes da 2.5 não foram medidos.
- Pela leitura do código, o mapeamento usa PID-5, 7, 8, 11 e 13, PV1-2 e OBX. O resto não é convertido. O 8 de 185 é escopo declarado: o docstring do módulo diz que cobre ADT, ORU e ORM comuns, não todos os ~185 tipos. O código aceita 10 tipos; ADT_A04 e ADT_A08 não estão entre os 185 que o gerador lista.
- Não comparei com um conversor de referência de HL7 v2 para FHIR. "Descarta o CPF" vale para o hl7gen 0.2.0, não para a categoria inteira.
- O `fhir.resources` leu todos os bundles que a ferramenta produziu. Isso não é o validador FHIR da HL7, que não foi rodado.
- As datas das mensagens geradas dependem do dia em que você roda (o Faker sorteia até hoje). As contagens de estrutura não.

Artigo: https://rogerio.eti.br/hl7gen-hl7v2-fhir-sintetico/
