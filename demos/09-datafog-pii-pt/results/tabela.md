DataFog 4.9.0, engine regex, 7 tipos do corpus, tempo médio 0.21 ms por nota

| Tipo | Suporte | Exato | Coberto | Parcial | Vazou após redact |
|---|---|---|---|---|---|
| PESSOA | 292 | 0/292 (0.0%) | 0/292 (0.0%) | 0/292 (0.0%) | 292/292 (100.0%) |
| BR_CPF | 133 | 0/133 (0.0%) | 8/133 (6.0%) | 0/133 (0.0%) | 125/133 (94.0%) |
| BR_CNS | 120 | 0/120 (0.0%) | 0/120 (0.0%) | 0/120 (0.0%) | 120/120 (100.0%) |
| DATA | 98 | 17/98 (17.3%) | 17/98 (17.3%) | 0/98 (0.0%) | 81/98 (82.7%) |
| TELEFONE | 60 | 0/60 (0.0%) | 16/60 (26.7%) | 27/60 (45.0%) | 17/60 (28.3%) |
| EMAIL | 26 | 26/26 (100.0%) | 26/26 (100.0%) | 0/26 (0.0%) | 0/26 (0.0%) |
| ENDERECO | 58 | 0/58 (0.0%) | 0/58 (0.0%) | 0/58 (0.0%) | 58/58 (100.0%) |

Notas com CPF ou CNS: 200; notas em que algum CPF/CNS ainda aparece depois do redact: 196
Entidades achadas por tipo do DataFog: {'ZIP_CODE': 43, 'EMAIL': 26, 'DATE': 17, 'PHONE': 10}
CPF coberto por formato: {'BR_CPF sem pontuação': {'suporte': 66, 'coberto': 8}, 'BR_CPF com pontuação': {'suporte': 67, 'coberto': 0}}
Rótulo que o DataFog deu ao que cobriu CPF/CNS: {'BR_CPF -> PHONE': 8}
Falsos positivos em números que não são dado pessoal: {'protocolo': 2}
