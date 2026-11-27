# 19 · O hl7apy valida HL7 v2? Pegou 100 de 200 defeitos, nenhum de conteúdo

O [hl7apy](https://github.com/crs4/hl7apy) (MIT, CRS4) é a biblioteca Python pra ler, montar e validar mensagens HL7 v2.x contra as estruturas oficiais. Esta demo gera 240 mensagens ADT^A01 v2.5 100% sintéticas (40 válidas e 200 com um defeito plantado cada, 20 por tipo), roda o `parse_message()` seguido de `validate()` nos dois níveis da biblioteca e conta o que foi reprovado.

Resultado (26/11/2026, Linux, CPU, Python 3.11.18, hl7apy 1.3.5): no nível padrão (`TOLERANT`) o hl7apy reprovou **60 de 200** mensagens com defeito; no `STRICT`, **100 de 200**: 100 dos 120 defeitos de forma e **0 dos 80** de conteúdo (CPF com dígito errado, CNS inválido, sexo fora da tabela 0001, nascimento no futuro). As 20 mensagens com PV1 antes do PID passaram nos dois níveis, e no `STRICT` o `to_er7()` devolveu as 20 já na ordem certa. Sexo fora da tabela vira só aviso, gravado no `report_file`, e o `validate()` devolve `True`. Uma função de 21 linhas (`regras_br()`) pegou os 100 que sobraram, sem reprovar nenhuma das 40 válidas.

*English: hl7apy 1.3.5 on 240 synthetic HL7 v2.5 ADT^A01 messages (40 valid, 200 with one planted defect each). The default TOLERANT level rejected 60 of 200; STRICT rejected 100 of 200: 100 of 120 structural defects and 0 of 80 content defects (CPF tax ID with a wrong check digit, invalid CNS health card number, sex code outside HL7 table 0001, birth date in the future). Messages with PV1 before PID passed both levels, and STRICT re-serialized them in the right order. An out-of-table sex code only shows up as a warning in the report file; `validate()` returns True. A 21-line `regras_br()` function caught the remaining 100 with 0 of 40 valid messages rejected.*

Artigo: https://rogerio.eti.br/hl7apy-validacao-hl7-v2/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt        # hl7apy e pytest com versão fixa
python demo.py                         # gera as 240 mensagens em memória, roda TOLERANT e STRICT, grava results/
python -m pytest tests -q -s           # prova a afirmação central em menos de 2 s
```

CPU, sem GPU, sem chave de API, sem conta, sem rede depois do `pip install`. Nenhuma mensagem é gravada em disco além dos exemplos em `results/`.

## O que mostra

- `gera_hl7.py`: 240 mensagens ADT^A01 v2.5 (seed fixa 20261127) com MSH, EVN, PID e PV1. CPF e CNS válidos por algoritmo, nome fictício com "TESTE". Defeitos de forma: sem PID, sem nome (PID-5), data inválida no PID-7, nome com mais de 200 caracteres, PID duplicado, PV1 antes do PID. Defeitos de conteúdo: CPF com dígito errado, CNS inválido, sexo `X`, `H` ou `Masculino` no PID-8, nascimento entre 2030 e 2099.
- `demo.py`: `parse_message(er7, validation_level=..., find_groups=True)` e `validate()`. Qualquer exceção no parse ou no validate conta como reprovação. Também lê o `report_file` do `validate()` atrás de avisos e aplica `regras_br()` no que o `STRICT` aceitou.
- `tests/test_hl7apy.py`: o `STRICT` aceita os 4 tipos de conteúdo e a ordem trocada; reprova data inválida que o `TOLERANT` aceita; `regras_br()` pega 80 de 80 de conteúdo sem reprovar válida.

## Resultado real

Saída completa em [`results/resultado.txt`](results/resultado.txt) e [`results/resultado.json`](results/resultado.json); a mensagem fora de ordem antes e depois em [`results/exemplo_fora_de_ordem.txt`](results/exemplo_fora_de_ordem.txt); o teste em [`results/pytest.txt`](results/pytest.txt); versões em [`results/pip-freeze.txt`](results/pip-freeze.txt).

| Defeito (20 mensagens cada) | grupo | TOLERANT | STRICT |
|---|---|---|---|
| sem PID | forma | 20 | 20 |
| sem nome (PID-5) | forma | 20 | 20 |
| data inválida no PID-7 | forma | 0 | 20 |
| nome com mais de 200 caracteres | forma | 0 | 20 |
| PID duplicado | forma | 20 | 20 |
| PV1 antes do PID | forma | 0 | 0 |
| CPF com dígito errado | conteúdo | 0 | 0 |
| CNS inválido | conteúdo | 0 | 0 |
| sexo fora da tabela 0001 | conteúdo | 0 | 0 |
| nascimento no futuro | conteúdo | 0 | 0 |
| **total reprovado (de 200)** | | **60** | **100** |
| válidas reprovadas (de 40) | | 0 | 0 |

Com `regras_br()` depois do `STRICT`: 200 de 200 reprovadas, 0 de 40 válidas reprovadas.

## Limites honestos

- **Dado sintético e defeitos escolhidos por mim.** Os 10 tipos são os que eu vejo como prováveis numa integração brasileira; não é amostra de tráfego real.
- **Só ADT^A01, só v2.5, só 4 segmentos.** Mensagem com mais segmentos, grupos opcionais e Z-segments pode se comportar diferente.
- **Sem perfil de mensagem.** O hl7apy aceita um *message profile* (`message_profile=`) que pode apertar cardinalidade e tamanho; esta demo usa só a estrutura oficial que vem com a biblioteca. Perfil não checa dígito verificador de CPF.
- **A regra de ordem em `regras_br()` só conhece MSH, EVN, PID e PV1.** Não serve como validador de ordem geral.
- **A data de "hoje" está fixa** (20261126) pra o resultado ser reprodutível.
- **Versão.** A 1.3.5 é de 13/03/2024 no PyPI; existe uma 1.4.0b1 (beta) que não testei.

## Fonte

- hl7apy 1.3.5 (MIT, PyPI, repositório https://github.com/crs4/hl7apy, docs http://crs4.github.io/hl7apy/), conferido no PyPI em 26/11/2026.
- Código lido: `hl7apy/parser.py` (`parse_message`, nível padrão `TOLERANT` em `hl7apy/__init__.py`) e `hl7apy/validation.py` (`_check_table_compliance` e `_check_length` geram `ValidationWarning`, que só vai pro `report_file`).
- CNS: regra de validação do Cartão Nacional de Saúde (soma ponderada módulo 11) usada pelo Ministério da Saúde.

## Licença e crédito

MIT, como o resto do repositório. Parte do nursia-research-lab (NursIA, PPGINFOS/UFSC, bolsa FAPESC). Dado 100% sintético: nenhuma mensagem real, nenhum dado de paciente.

Como citar: Rodrigues, R. (2026). *O hl7apy valida HL7 v2?* (demo 19). nursia-research-lab. https://github.com/rogeriorrodrigues/nursia-research-lab/tree/main/demos/19-hl7apy-validacao-v2
