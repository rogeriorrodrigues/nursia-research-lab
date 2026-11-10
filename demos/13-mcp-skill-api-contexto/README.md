# 13 · MCP, Skill ou chamada de API: quanto contexto a mesma ferramenta ocupa

As mesmas 4 ferramentas (validar CPF, validar CNS, mascarar e contar identificadores) servidas de três jeitos: servidor MCP, definição de função de API e Skill. A demo não chama modelo nenhum. Ela monta o que cada via põe na janela de contexto e conta os tokens.

Resultado com o tokenizador `o200k_base`: como MCP, as 4 ferramentas custam **275 tokens em todo pedido**; escritas à mão pra API, **223**; como Skill parada, **60** (só nome e descrição). Quando a Skill é usada, o corpo do `SKILL.md` entra e o custo vai pra **372**. Os 52 tokens a mais do MCP são campos `title` que o Pydantic gera no JSON Schema: tirando eles, a definição do MCP fica idêntica à escrita à mão.

*English: Same 4 tools exposed as an MCP server, as hand-written API tool definitions and as an Agent Skill. No model is called; the demo builds what each route puts in the context window and counts tokens (tiktoken o200k_base). MCP: 275 tokens per request; API: 223; idle Skill: 60; Skill after use: 372. The 52-token MCP overhead is Pydantic-generated `title` fields in the input schema.*

Artigo: https://rogerio.eti.br/mcp-skill-api-tokens-contexto/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt
python3 demo.py            # grava results/resultado.json, results/saida.txt e results/mcp_tools_list.json
python3 -m pytest tests -q -s
```

CPU, sem GPU, sem chave de API, sem conta. Roda em 2 segundos. Na primeira execução o tiktoken baixa os arquivos `o200k_base` e `cl100k_base` (3,6 MB e 1,7 MB) e confere o hash deles.

## O que mostra

- `ferramentas.py`: as 4 funções, o mesmo código pras três vias.
- **Via MCP:** `demo.py` sobe um `MCPServer` (SDK oficial `mcp` 2.3.0), registra as 4 funções com `add_tool`, conecta um `Client` em memória, chama `tools/list` e `tools/call`. Mede a resposta inteira do `tools/list` e a parte que o host traduz pro modelo (`name`, `description`, `input_schema`).
- **Via API:** as mesmas 4 definições escritas à mão no formato de tool use, com a mesma descrição.
- **Via Skill:** `skill/mascarar-identificadores/SKILL.md` com frontmatter e corpo, e `scripts/identificadores.py`, que o agente roda pelo shell. Nível 1 = a linha `nome - descrição` que vai no system prompt; nível 2 = o corpo do `SKILL.md`; o código do script não entra no contexto, só a saída.

As três vias devolvem o mesmo texto mascarado pra nota sintética (o `demo.py` confere com `assert`).

## Resultado (results/saida.txt)

| o que entra no contexto | o200k_base | cl100k_base |
|---|---:|---:|
| resposta inteira do `tools/list` (MCP) | 417 | 417 |
| definições do MCP que vão pro modelo, por pedido | 275 | 283 |
| definições escritas à mão pra API, por pedido | 223 | 231 |
| Skill, nível 1 (nome e descrição), por pedido | 60 | 66 |
| Skill, nível 2 (corpo do `SKILL.md`), depois de usada | 312 | 337 |
| código do script da Skill (não entra) | 103 | 109 |
| uma chamada MCP ou API: argumentos + resultado | 61 + 43 | 65 + 47 |
| uma chamada pela Skill: comando + saída | 17 + 44 | 18 + 47 |

Projeção pra uma conversa de 10 pedidos ao modelo (o200k_base):

| cenário | tokens de definição |
|---|---:|
| MCP | 2.750 |
| API à mão | 2.230 |
| Skill usada já no 1º pedido | 3.720 |
| Skill usada só no 10º pedido | 912 |
| Skill nunca usada | 600 |

A definição do MCP não é igual à escrita à mão (`mcp_igual_api: false`). Tirando os campos `title` do schema, fica igual (`mcp_igual_api_sem_title: true`).

## Limites honestos

- **Não é o tokenizador do Claude nem de modelo nenhum em produção.** Os números são do tiktoken (`o200k_base` e `cl100k_base`). Servem pra comparar as vias entre si; o valor absoluto muda de modelo pra modelo.
- **A Skill precisa de uma ferramenta de shell ou de execução de código no agente**, e a definição dessa ferramenta também ocupa contexto. Ela não está somada aqui porque depende do host. Se o seu agente não tem shell, a Skill nem roda.
- **O host pode reescrever a definição.** A demo mede o que o servidor MCP manda; cada cliente (Claude Code, Copilot, Cursor, o seu) decide se repassa `title`, `outputSchema` e o resto.
- **Não mede acerto, latência nem custo em dinheiro.** Saber se o modelo escolhe a ferramenta certa em cada via exige rodar modelo, e isso fica pra outra demo.
- **Cache de prompt muda a conta do dinheiro**, não a do contexto: definição que se repete em todo pedido costuma cair no cache do provedor.
- A projeção de 10 pedidos supõe que a definição vai em todo pedido e que o corpo da Skill, depois de lido, fica no histórico até o fim.
- 4 ferramentas pequenas. Com 40 ferramentas o fixo do MCP e da API cresce na mesma proporção; o nível 1 da Skill cresce só com o número de Skills, não com o de ações dentro dela.
- Todo dado é sintético: o CPF e o CNS da nota são gerados por algoritmo (`gerar_cpf`, `gerar_cns`) e o nome é "FULANO DE TAL SINTETICO".

## Fonte

- SDK Python do MCP 2.3.0, licença MIT: https://github.com/modelcontextprotocol/python-sdk
- Agent Skills, carregamento em 3 níveis (metadado sempre, `SKILL.md` quando dispara, arquivos e scripts quando precisa): https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- tiktoken 0.14.0, licença MIT: https://github.com/openai/tiktoken

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
