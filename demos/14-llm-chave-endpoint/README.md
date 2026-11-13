# 14 · O llm manda a sua chave da OpenAI pra um endpoint de terceiro?

Reprodução das duas falhas corrigidas no `llm` 0.37.2 (11/11/2026): modelo extra com `api_base` próprio recebendo a chave da OpenAI. A demo roda os mesmos 5 cenários no 0.37.1 e no 0.37.2 contra um endpoint falso em `127.0.0.1` e anota qual chave chegou no cabeçalho `Authorization`.

Resultado: no **0.37.1, 3 de 5 cenários** mandaram a chave canário da OpenAI pro endpoint de terceiro, todos com código de saída 0 e resposta normal. No **0.37.2, 0 de 5**. No cenário A, o 0.37.2 nem chega a fazer o pedido: para com `No key found - add one using 'llm keys set terceiro'`.

*English: Reproduces the two key-leak fixes in `llm` 0.37.2 (GHSA-v9h7-jj4g-f862 and GHSA-r639-rr7r-x72w). Same 5 scenarios run on 0.37.1 and 0.37.2 against a fake OpenAI-compatible endpoint on 127.0.0.1 with a canary key. 0.37.1 sent the OpenAI key to the third-party endpoint in 3 of 5 scenarios, all exiting 0; 0.37.2 in 0 of 5.*

Artigo: https://rogerio.eti.br/llm-chave-openai-endpoint-terceiro/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt
python3 demo.py                # cria .venvs/llm-0.37.1 e .venvs/llm-0.37.2 na 1ª vez; grava results/
python3 -m pytest tests -q -s
```

CPU, sem GPU, sem chave de verdade, sem conta, sem internet depois de instalar. Com os dois venvs prontos, a demo inteira levou 8,9 s (`results/pytest.txt`). Python 3.11; o pip resolveu `openai` 3.50.0 nos dois venvs.

## O que mostra

- `servidor_falso.py`: um endpoint compatível com OpenAI em `127.0.0.1`, porta aleatória. Guarda o `Authorization` de cada pedido e responde um `chat.completion` mínimo.
- `demo.py`: pra cada versão, cria um `LLM_USER_PATH` temporário com `extra-openai-models.yaml` (e `keys.json` quando o cenário pede), põe `OPENAI_API_KEY=sk-CANARIO-OPENAI-FALSA-0000` no ambiente quando o cenário pede, roda `llm -m tp --no-stream --no-log oi` e confere o que chegou no endpoint.

| cenário | configuração |
|---|---|
| A | `api_base` + `api_key_name: terceiro` não guardada, `OPENAI_API_KEY` no ambiente |
| B | controle: `api_key_name: terceiro` guardada com a chave do terceiro |
| C | controle: `api_base` sem `api_key_name` |
| D | `responses: true` + `-o chat_completions 1`, `OPENAI_API_KEY` no ambiente |
| E | `responses: true` + `-o chat_completions 1`, chave `openai` guardada (como `llm keys set openai`) |

## Resultado (results/saida.txt)

| cenário | 0.37.1 recebeu | 0.37.2 recebeu |
|---|---|---|
| A | **chave da OpenAI** (rc 0) | nenhum pedido (rc 1, `No key found`) |
| B | chave do terceiro | chave do terceiro |
| C | `DUMMY_KEY` | `DUMMY_KEY` |
| D | **chave da OpenAI** (rc 0) | `DUMMY_KEY` |
| E | **chave da OpenAI** (rc 0) | `DUMMY_KEY` |
| total que vazou | **3 de 5** | **0 de 5** |

Os controles B e C deram igual nas duas versões. O 0.37.1 respondeu "ok" nos 5 cenários: quem usa não vê erro nenhum.

## Limites honestos

- **Endpoint falso, chave falsa.** Mostra o que o cliente manda; não mostra o que um terceiro faria com a chave.
- **Só o caminho da linha de comando**, com modelo definido em `extra-openai-models.yaml`. Não testei a API Python, o modo assíncrono, plugins nem `llm openai endpoint ... --responses`, que o aviso GHSA-r639-rr7r-x72w também cita.
- **5 cenários escolhidos por mim** a partir dos dois avisos. Não é varredura de todas as combinações de opção.
- Vale pra quem usa `api_base` próprio (OpenRouter, vLLM, LM Studio, gateway da empresa) e tem chave da OpenAI no ambiente ou guardada no `llm`. Quem só usa a OpenAI direto não é afetado por essas duas falhas.
- O que fazer: `pip install -U "llm>=0.37.2"` e, se usou `api_base` de terceiro com versão antiga, trocar a chave da OpenAI.

## Fonte

- Release 0.37.2 do `llm` (Simon Willison), licença Apache-2.0: https://github.com/simonw/llm/releases/tag/0.37.2
- GHSA-v9h7-jj4g-f862 (afeta >= 0.6, < 0.37.2): https://github.com/simonw/llm/security/advisories/GHSA-v9h7-jj4g-f862
- GHSA-r639-rr7r-x72w (afeta >= 0.32a2, < 0.37.2): https://github.com/simonw/llm/security/advisories/GHSA-r639-rr7r-x72w

Licença MIT, como o resto do repositório. Nenhum dado pessoal: as chaves são strings inventadas e o prompt é "oi".

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
