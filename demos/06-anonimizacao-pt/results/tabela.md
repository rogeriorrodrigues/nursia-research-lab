## Geral (match estrito de span por tipo)

| Sistema | Notas | P | R | F1 micro | Recall CPF | Recall CNS | Vazamento CPF/CNS | FP em distratores | Pior entidade | Tempo/nota | Falha parse |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Presidio 2.2.364 padrão + spaCy pt | 200/200 | 43.3% | 43.3% | 43.3% | 0.0% | 0.0% | 100.0% (200/200) | 49 | BR_CPF (0.0%) | 0.01 s | n/a |
| Presidio 2.2.364 + presidio-br | 200/200 | 57.1% | 75.5% | 65.0% | 100.0% | 100.0% | 0.0% (0/200) | 49 | ENDERECO (0.0%) | 0.01 s | n/a |
| Ollama (Qwen) `qwen3.8:27b` (Q4_K_M) | 200/200 | 99.9% | 100.0% | 99.9% | 100.0% | 100.0% | 0.0% (0/200) | 1 | PESSOA (99.8%) | 12.38 s | 0.0% |
| Ollama (Phi) `phi4:14b` (Q4_K_M) | 200/200 | 100.0% | 97.8% | 98.9% | 97.7% | 99.2% | 2.0% (4/200) | 0 | ENDERECO (90.6%) | 5.08 s | 0.0% |

## Por entidade

| Entidade (suporte) | Presidio 2.2.364 padrão + spaCy pt | Presidio 2.2.364 + presidio-br | Ollama (Qwen) | Ollama (Phi) |
|---|---|---|---|---|
| PESSOA (292) | P 66.9% R 82.2% F1 73.7% | P 66.9% R 82.2% F1 73.7% | P 99.7% R 100.0% F1 99.8% | P 100.0% R 100.0% F1 100.0% |
| BR_CPF (133) | P 0.0% R 0.0% F1 0.0% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 97.7% F1 98.9% |
| BR_CNS (120) | P 0.0% R 0.0% F1 0.0% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 99.2% F1 99.6% |
| DATA (98) | P 100.0% R 49.0% F1 65.8% | P 100.0% R 49.0% F1 65.8% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 96.9% F1 98.4% |
| TELEFONE (60) | P 45.8% R 45.0% F1 45.4% | P 45.8% R 45.0% F1 45.4% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 100.0% F1 100.0% |
| EMAIL (26) | P 100.0% R 100.0% F1 100.0% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 100.0% F1 100.0% |
| ENDERECO (58) | P 0.0% R 0.0% F1 0.0% | P 0.0% R 0.0% F1 0.0% | P 100.0% R 100.0% F1 100.0% | P 100.0% R 82.8% F1 90.6% |
