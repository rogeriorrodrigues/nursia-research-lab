# 11 · HealthChain 0.16.1: o que o `validate_resource()` pega em FHIR sintético

`validate_resource()` do HealthChain 0.16.1 reprovou **80 de 180 recursos FHIR defeituosos**: os 80 com defeito de forma (campo obrigatório ausente, data em `dd/mm/aaaa`, campo que não existe, `gender` fora do conjunto) e **0 dos 100 com defeito de conteúdo** (código LOINC inventado, unidade que não é UCUM, referência quebrada, CPF com dígito verificador errado, invariante `obs-6`). Nos 60 recursos válidos: 0 falsos positivos.

*English: HealthChain 0.16.1 `validate_resource()` on 240 synthetic FHIR R4B resources (60 valid, 180 with one known defect). It rejected 80/80 structural defects and 0/100 content defects (invented LOINC code, non-UCUM unit, broken reference, CPF with a bad check digit, invariant obs-6). 0/60 false positives. The module docstring says as much; this measures it.*

Artigo: https://rogerio.eti.br/healthchain-validate-resource-fhir/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt
python3 demo.py                 # gera data/ e grava results/
python3 -m pytest tests -q
```

CPU, sem rede depois do `pip install`, sem chave, sem modelo.

## O que mostra

`gerar_dados.py` monta, com semente 2026, 240 recursos FHIR R4B sintéticos:

- 60 válidos (Patient, Observation de frequência cardíaca, Condition), usados como controle;
- 180 com **um** defeito conhecido, 20 por categoria, em 9 categorias.

`demo.py` passa cada um por `healthchain.fhir.validate_resource()` e conta quantos foram reprovados (`valid == False`).

## Resultado (results/tabela.md)

| Categoria | Natureza | Reprovados |
|---|---|---|
| campo obrigatório ausente | forma | 20/20 |
| data no formato dd/mm/aaaa | forma | 20/20 |
| campo que não existe no recurso | forma | 20/20 |
| valor fora do conjunto obrigatório (`code`) | forma | 20/20 |
| código inventado sob o sistema LOINC | conteúdo | 0/20 |
| unidade que não é UCUM válida | conteúdo | 0/20 |
| referência pra um Patient que não está no Bundle | conteúdo | 0/20 |
| CPF com dígito verificador errado | conteúdo | 0/20 |
| valor e `dataAbsentReason` juntos (invariante `obs-6`) | conteúdo | 0/20 |
| (controle) recurso válido | - | 0/60 |

- Forma: 80 de 80 reprovados. Conteúdo: 0 de 100. Total: 80 de 180.
- Tempo médio: cerca de 0,2 ms por recurso nesta máquina (CPU, Python 3.11; 0,19 a 0,25 ms nas rodadas que fiz; o tempo muda a cada rodada, o resto é determinístico).
- `results/raw.jsonl` guarda, por recurso, se foi reprovado e quais problemas o validador apontou; `results/metricas.json` tem os números crus.

## Limites honestos

- **Isso confirma o que a documentação do módulo já diz.** O docstring de `healthchain/fhir/validation.py` lista o que não é checado: bindings de `CodeableConcept`/`Coding`, invariantes FHIRPath, conformidade com perfil e integridade de referência. A demo mede esse recorte; não é um defeito escondido. Pra validação completa, o próprio módulo manda usar o `$validate` de um servidor FHIR.
- **O gabarito é meu.** Escolhi as 9 categorias e fiz o defeito de cada uma. Outras categorias dariam outra proporção. O 80/180 descreve este conjunto, não a taxa de erro de FHIR real.
- **Não comparei com o validador oficial da HL7.** A demo não roda o validador Java; só diz o que o `validate_resource()` deixa passar.
- **Perfil brasileiro não entra.** Usei o sistema de identificador de CPF do Ministério da Saúde só pra montar o dado; a demo não valida contra perfil BR.
- Só `validate_resource()` em recurso solto ou Bundle montado à mão. Não testei `load_bundle()` nem as demais partes do SDK (gateway, MCP, sandbox).
- Todo dado é sintético: CPF passa no dígito verificador mas é sorteado com semente fixa e não pertence a ninguém. Nomes saem de lista curta inventada.

## Fonte

- HealthChain 0.16.1 (PyPI), Apache-2.0: https://github.com/healthchainai/HealthChain
- `fhir.resources` 8.1.0 (modelos Pydantic que o HealthChain usa por baixo).

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
