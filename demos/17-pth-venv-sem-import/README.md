# 17 · O `.pth` que roda sem você importar nada: o que um venv limpo executa antes do seu código

O Python lê todo arquivo `.pth` do `site-packages` quando o interpretador sobe. Linha que começa com `import` seguido de espaço ou tab é executada com `exec()`, antes da primeira linha do seu programa, mesmo que você nunca importe o pacote que trouxe o arquivo. Esta demo cria venvs novos em Python 3.11, 3.12 e 3.13, instala 5 pacotes de IA comuns, conta os `.pth` e as linhas executáveis, e grava um `.pth` próprio e inofensivo (só escreve uma marca no stderr) pra ver em quais modos de execução ele roda.

Resultado (23/11/2026, Linux, CPU): os 5 pacotes de IA (openai, anthropic, langchain-core, huggingface-hub, tiktoken, 49 pacotes no venv com as dependências) **não trouxeram nenhum `.pth`**. O único `.pth` com linha executável foi o `distutils-precedence.pth` do setuptools: no 3.11 ele já vem no venv vazio (o `ensurepip` do 3.11 instala o setuptools), no 3.12 e no 3.13 só depois de instalar o setuptools. A marca do `.pth` próprio apareceu num `python -c pass` em **5 de 6 modos**: padrão, `-I`, `-s`, `-E` e `pip --version`. Só `-S` desligou, e com `-S` o `import openai` quebrou (`ModuleNotFoundError`). A varredura levou de **0,21 a 0,49 ms**.

*English: Python runs `import` lines from `.pth` files in site-packages at startup, before your code. In fresh venvs (Python 3.11, 3.12, 3.13) with 5 common AI packages (openai, anthropic, langchain-core, huggingface-hub, tiktoken; 49 packages total) there were 0 `.pth` files from those packages; the only executable one was setuptools' `distutils-precedence.pth` (present in an empty 3.11 venv). A harmless marker `.pth` ran on `python -c pass` with no flag, with `-I`, `-s`, `-E` and on `pip --version`; only `-S` stopped it, and `-S` also breaks `import openai`. Scanning took 0.21 to 0.49 ms.*

Artigo: https://rogerio.eti.br/pth-python-venv-sem-import/

## Como rodar (3 comandos)

Precisa de Python 3.11, 3.12 e/ou 3.13 no PATH (`python3.11`, `python3.12`, `python3.13`). Versão que não existir vira "interpretador não encontrado" no resultado.

```bash
pip install -r requirements.txt                 # só o pytest; a demo usa a biblioteca padrão
python3 demo.py 3.11 3.12 3.13                  # cria os venvs em pasta temporária, instala, mede, grava results/
python3 -m pytest tests -q -s                   # prova a afirmação central num venv sem pip, em menos de 1 s
```

CPU, sem GPU, sem chave de API, sem conta. Rede só pro `pip install` dos pacotes de `requirements-ia.txt`. Os venvs ficam numa pasta temporária e somem no fim. Nada roda no seu Python global além do script.

Pra olhar o seu próprio ambiente, sem instalar nada:

```bash
/caminho/do/seu/venv/bin/python varre_pth.py
```

## O que mostra

- `varre_pth.py`: lista todo `.pth` de `site.getsitepackages()` (e do site do usuário, se estiver ligado) e separa as linhas pela mesma regra do módulo `site`: vazia ou comentário, caminho, executável.
- `demo.py`: 4 etapas por versão (E0 venv vazio, E1 + 5 pacotes de IA, E2 + setuptools 84.2.1, E3 + um pacote sintético em modo editável), depois o teste da marca em 6 modos e o `import openai` com `-S`.
- `pacote_sintetico/`: pacote de mentira (`paciente-ficticio`, um nome fictício óbvio) que só existe pra ser instalado com `pip install -e`.
- `tests/test_pth.py`: o classificador e a marca num venv novo sem pip: aparece no padrão e com `-I`, some com `-S`.

O `.pth` da marca é este, e nada mais:

```python
import sys; sys.stderr.write("MARCA-DEMO17: .pth executado antes do seu codigo\n")
```

## Resultado real

Saída completa em [`results/resultado.txt`](results/resultado.txt) e [`results/resultado.json`](results/resultado.json); o teste em [`results/pytest.txt`](results/pytest.txt).

| Etapa | 3.11.18 | 3.12.3 | 3.13.18 |
|---|---|---|---|
| E0 venv vazio: `.pth` / com `import` | 1 / 1 | 0 / 0 | 0 / 0 |
| E1 + 5 pacotes de IA | 1 / 1 | 0 / 0 | 0 / 0 |
| E2 + setuptools 84.2.1 | 1 / 1 | 1 / 1 | 1 / 1 |
| E3 + pacote editável | 2 / 1 | 2 / 1 | 2 / 1 |
| varredura (ms, faixa nas 4 etapas) | 0,30 a 0,48 | 0,21 a 0,37 | 0,26 a 0,49 |

| Modo (`python ... -c pass`) | marca do `.pth` próprio |
|---|---|
| sem flag | apareceu (3 de 3 versões) |
| `-I` (isolado) | apareceu (3 de 3) |
| `-s` (sem site do usuário) | apareceu (3 de 3) |
| `-E` (ignora variáveis `PYTHON*`) | apareceu (3 de 3) |
| `python -m pip --version` | apareceu (3 de 3) |
| `-S` (sem módulo `site`) | não apareceu (0 de 3), e `import openai` dá `ModuleNotFoundError` |

O `.pth` executável que existia é o do setuptools, legítimo: `import os; var = 'SETUPTOOLS_USE_DISTUTILS'; enabled = os.environ.get(var, 'local') == 'local'; enabled and __import__('_distutils_hack').add_shim();`. O `.pth` do pacote editável (`__editable__.paciente_ficticio-0.0.1.pth`) tem só um caminho, sem `import`.

## Limites honestos

- **5 pacotes, uma data, um sistema.** Linux, pacotes nas versões de `requirements-ia.txt`, 23/11/2026. Outros pacotes trazem `.pth` com `import` de propósito (ferramenta de cobertura, de instrumentação, instalação editável de outros backends). Zero aqui não é zero no seu ambiente.
- **A varredura acha, não julga.** Ela conta linha executável; não diz se a linha é maliciosa. O `.pth` do setuptools é legítimo e vai aparecer em quase todo ambiente de CI.
- **Não olha `sitecustomize.py`, `usercustomize.py` nem os arquivos `.start`** (novos no Python 3.15, segundo a documentação do `site` no ramo main do CPython). São outros caminhos de código que rodam na partida.
- **`-I` não protege disso.** Ele desliga o site do usuário e as variáveis `PYTHON*`, mas o `site-packages` do venv continua sendo processado. Só `-S` desliga, e aí os pacotes instalados somem do `sys.path`.
- **Não reproduz incidente nenhum.** Nenhum pacote comprometido foi baixado. O `.pth` da marca é meu e só escreve uma linha no stderr.

## Fonte

- Documentação do módulo `site` (CPython, `Doc/library/site.rst`, ramos 3.12, 3.13 e main): linhas que começam com `import` são executadas com `exec()`; no main, a mudança da 3.15 deprecia essas linhas (ignoradas em silêncio nas 3.18 e 3.19).
- setuptools 84.2.1 (MIT), openai 3.58.0, anthropic 2.13.0, huggingface-hub 2.4.0 (Apache-2.0), langchain-core 1.8.4, tiktoken 0.14.0 (MIT), versões conferidas no PyPI em 23/11/2026.

## Licença e crédito

MIT, como o resto do repositório. Parte do nursia-research-lab (NursIA, PPGINFOS/UFSC, bolsa FAPESC). Dado 100% sintético.

Como citar: Rodrigues, R. (2026). *O .pth que roda sem você importar nada* (demo 17). nursia-research-lab. https://github.com/rogeriorrodrigues/nursia-research-lab/tree/main/demos/17-pth-venv-sem-import
