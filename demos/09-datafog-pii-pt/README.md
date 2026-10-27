# 09 · DataFog 4.9.0 em notas clínicas em português: o que a camada regex pega

DataFog 4.9.0 (engine `regex`, o padrão) rodou nas mesmas 200 notas clínicas sintéticas da [demo 06](../06-anonimizacao-pt/). Depois do `redact()`, **196 das 200 notas ainda mostram um CPF ou CNS inteiro**. Só 8 de 133 CPFs foram cobertos, todos sem pontuação e rotulados como telefone; 0 de 120 CNS. E-mail: 26 de 26.

*English: DataFog 4.9.0 regex engine on 200 synthetic Brazilian clinical notes. After `redact()`, 196 of 200 notes still contain a full CPF or CNS. It covers 26/26 emails, 17/98 dates, 8/133 CPFs (mislabeled as phone) and 0/120 CNS. No names or addresses, by design.*

Artigo: https://rogerio.eti.br/datafog-pii-portugues-cpf-cns/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt
python3 demo.py                 # grava results/
python3 -m pytest tests -q
```

CPU, sem rede depois do `pip install`, sem modelo, sem chave. Roda em menos de 1 s. `demo.py` desliga a telemetria do DataFog (`DATAFOG_NO_TELEMETRY=1`, `DO_NOT_TRACK=1`) antes de importar a biblioteca.

## O que mostra

Para cada span do corpus (gabarito da demo 06, copiado em `data/corpus.jsonl`, semente 2026), três perguntas:

- **Exato**: DataFog devolveu o mesmo `(início, fim)` com o tipo certo (`DATE`→DATA, `PHONE`→TELEFONE, `EMAIL`→EMAIL).
- **Coberto**: o span inteiro cai dentro de alguma entidade, de qualquer tipo. É o que importa pra redigir.
- **Vazou após redact**: o texto do dado ainda aparece na nota depois de `datafog.redact()`.

Há também **Parcial**: a entidade encosta no span, mas sobra parte dele (ex.: o DDD do telefone).

## Resultado (results/tabela.md)

| Tipo | Suporte | Exato | Coberto | Parcial | Vazou após redact |
|---|---|---|---|---|---|
| PESSOA | 292 | 0/292 (0.0%) | 0/292 (0.0%) | 0/292 (0.0%) | 292/292 (100.0%) |
| BR_CPF | 133 | 0/133 (0.0%) | 8/133 (6.0%) | 0/133 (0.0%) | 125/133 (94.0%) |
| BR_CNS | 120 | 0/120 (0.0%) | 0/120 (0.0%) | 0/120 (0.0%) | 120/120 (100.0%) |
| DATA | 98 | 17/98 (17.3%) | 17/98 (17.3%) | 0/98 (0.0%) | 81/98 (82.7%) |
| TELEFONE | 60 | 0/60 (0.0%) | 16/60 (26.7%) | 27/60 (45.0%) | 17/60 (28.3%) |
| EMAIL | 26 | 26/26 (100.0%) | 26/26 (100.0%) | 0/26 (0.0%) | 0/26 (0.0%) |
| ENDERECO | 58 | 0/58 (0.0%) | 0/58 (0.0%) | 0/58 (0.0%) | 58/58 (100.0%) |

- Notas com CPF ou CNS: 200. Notas em que algum CPF ou CNS ainda aparece depois do `redact()`: **196**.
- CPF coberto por formato: sem pontuação 8/66, com pontuação 0/67. Os 8 foram rotulados `PHONE`.
- Entidades achadas pelo DataFog nas 200 notas: ZIP_CODE 43, EMAIL 26, DATE 17, PHONE 10.
- Telefones no formato `99123-4567` viraram `ZIP_CODE`; com DDD, o DDD fica de fora (27 parciais).
- Falsos positivos em números que não são dado pessoal (lote, leito, dose, pressão, protocolo): 2, ambos em protocolo.
- Tempo médio: 0,21 ms por nota nesta máquina (CPU, Python 3.11, uma execução; o valor muda a cada rodada, o resto é determinístico).

Para comparar, a demo 06 mediu o Presidio 2.2.364 padrão deixando CPF ou CNS passar em 200 das 200 notas, e o Presidio + presidio-br em 0 de 200.

`results/exemplo.txt` mostra a primeira nota antes e depois: nada foi redigido. `results/raw.jsonl` guarda as entidades achadas em cada nota; `results/metricas.json` tem os números crus.

## Limites honestos

- **Só o engine `regex`.** O DataFog tem engines com NER (spaCy, GLiNER) que exigem baixar modelo. Não rodei: a demo é sobre o que vem de fábrica com `pip install datafog`. O resultado vale pra esse engine, não pra biblioteca inteira.
- O engine regex do 4.9.0 lista 7 tipos (`EMAIL`, `PHONE`, `SSN`, `CREDIT_CARD`, `IP_ADDRESS`, `DATE`, `ZIP_CODE`). Não existe CPF, CNS, nome nem endereço em português. As linhas PESSOA e ENDERECO em 0% são o esperado, não um defeito.
- 200 notas sintéticas, 4 estilos, uma semente. Notas reais têm mais ruído; o corpus foi montado com casos difíceis de propósito (CPF sem pontuação em 49,6%).
- Mede detecção e o texto depois do `redact()`. Não mede reidentificação por combinação de campos.
- Não testei a opção `locales`: o 4.9.0 só aceita `de` (alemão).
- Todo dado é sintético: CPF e CNS passam no dígito verificador mas são sorteados com semente fixa e não pertencem a ninguém. Nomes, ruas e telefones saem de listas curtas inventadas.

## Fonte

- DataFog: https://github.com/DataFog/datafog-python, versão 4.9.0 (PyPI). Licença: o `LICENSE` do repo é MIT; o classificador do PyPI diz Apache.
- Corpus e gabarito: [demo 06](../06-anonimizacao-pt/).

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
