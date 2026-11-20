# 16 · Servidor MCP em C# com o SDK oficial 2.4.0: o que vem pronto e o que fica com você

As mesmas 4 ferramentas da [demo 13](../13-mcp-skill-api-contexto/) (validar CPF, validar CNS, mascarar e contar identificadores), agora num servidor MCP em C# com o pacote `ModelContextProtocol.AspNetCore` 2.4.0, por HTTP em 127.0.0.1. Um script em Python fala JSON-RPC cru com o servidor, sem SDK de cliente, e mede o que trafega.

Resultado: o `tools/list` do C# custa **223 tokens** por pedido (tiktoken `o200k_base`), o mesmo que a definição escrita à mão, contra **275** do servidor em Python da demo 13. O C# não gera os campos `title` no JSON Schema (**0 contra 14**). O resto que a demo mede vem aberto: sem header nenhum, com token inventado e com `Origin` de outro site, o servidor respondeu **200** e devolveu o texto mascarado nos três casos; uma rajada de **500 chamadas** levou **0** respostas 429; e o log padrão registra o nome da ferramenta e o tempo, mas não quem chamou nem o argumento.

*English: The same 4 tools as demo 13, served by a C# MCP server with the official SDK (`ModelContextProtocol.AspNetCore` 2.4.0, .NET 8, streamable HTTP on 127.0.0.1), measured from the outside with raw JSON-RPC. `tools/list` costs 223 tokens per request (tiktoken o200k_base), the same as hand-written definitions, versus 275 for the Python SDK server in demo 13: the C# schema has no `title` fields (0 vs 14). Out of the box there is no auth (no header, a made-up bearer token and a foreign `Origin` all got 200), no rate limit (500/500 calls answered, 0 HTTP 429) and the default log has tool name and duration but not caller or arguments. Median tool call: 1.83 ms on localhost.*

Artigo: https://rogerio.eti.br/servidor-mcp-csharp-sdk/

## Como rodar (3 comandos)

Precisa do .NET 8 SDK e de Python 3.11+.

```bash
dotnet build -c Release src                      # restaura o ModelContextProtocol.AspNetCore 2.4.0 do NuGet na 1ª vez
pip install -r requirements.txt
python3 demo.py && python3 -m pytest tests -q -s # sobe o servidor, mede, grava results/ e confere
```

CPU, sem GPU, sem chave de API, sem conta. O `demo.py` sobe o servidor sozinho em `http://127.0.0.1:5088/mcp` e derruba no fim. Na primeira execução o tiktoken baixa os arquivos `o200k_base` e `cl100k_base` e confere o hash deles. Pra comparar com o Python, o script lê `../13-mcp-skill-api-contexto/results/mcp_tools_list.json` (precisa do repositório inteiro clonado).

## O que mostra

- `src/Identificadores.cs`: as 4 ferramentas, com o mesmo nome e a mesma descrição da demo 13.
- `src/Program.cs`: o servidor inteiro. É isto:

```csharp
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();

var app = builder.Build();
app.MapMcp("/mcp");
app.Run(args.Length > 0 ? args[0] : "http://127.0.0.1:5088");
```

- `demo.py`: abre sessão (`initialize`), pede `tools/list`, chama as ferramentas e mede:
  1. tokens das definições que o host repassa pro modelo (`name`, `description`, `inputSchema`), com o mesmo método da demo 13;
  2. tempo de 200 chamadas de `mascarar_identificadores` em sequência, servidor quente;
  3. três clientes diferentes: sem header nenhum, com `Authorization: Bearer token-inventado-123` e com `Origin: http://site-qualquer.example`;
  4. rajada de 500 chamadas (20 clientes em paralelo, 25 cada);
  5. o que o log padrão do ASP.NET Core registrou.

## Resultado (results/saida.txt)

| o que mediu | resultado |
|---|---|
| definições pro modelo, C# 2.4.0 (o200k_base / cl100k_base) | **223** / 231 tokens |
| definições pro modelo, Python `mcp` 2.3.0 da demo 13 | 275 / 283 tokens |
| Python sem os campos `title` | 223 / 231 tokens |
| resposta inteira do `tools/list` em C# | 225 / 232 tokens |
| campos `title` no schema: C# / Python | 0 / 14 |
| `outputSchema` no C# | nenhuma ferramenta |
| saída do `mascarar_identificadores` igual à da demo 13 | sim |
| chamada de ferramenta, n = 200 | mediana 1,83 ms · p95 2,26 ms · máx 5,94 ms |
| do processo subir até a 1ª resposta | 450 ms |
| sem header nenhum | `initialize` 200 · `tools/call` 200 · devolveu o texto |
| com token inventado | 200 · 200 · devolveu o texto |
| com `Origin` de outro site | 200 · 200 · devolveu o texto |
| rajada de 500 chamadas (1,16 s) | 500 com 200 · 0 com 429 |
| log padrão (nível Information) | 10.702 linhas; 725 citam o nome da ferramenta; o CPF da nota não aparece |

O trecho do log está em `results/servidor-log-trecho.txt`. A linha da chamada diz `"mascarar_identificadores" completed. IsError = False.` e o tempo. Quem chamou só aparece no `initialize`, pelo nome que o próprio cliente declarou (`Client (demo16 1)`).

## O que o SDK não fez por mim nesta demo

- **Autenticação.** Não vem ligada. O pacote traz `McpAuthenticationHandler`, que publica os metadados de recurso protegido do OAuth e responde o desafio, e `AddAuthorizationFilters()`, que filtra ferramenta por `[Authorize]`. Emitir e validar o token é com o seu servidor de autorização e o `AddAuthentication` do ASP.NET Core.
- **Validação do `Origin`.** A spec do transporte HTTP (2025-06-18) diz que o servidor **MUST** validar o `Origin` contra DNS rebinding. Com a configuração padrão, o pedido com `Origin` de outro site passou. Não achei opção pra isso na documentação XML do pacote 2.4.0; fica com um middleware seu.
- **Limite de chamadas.** 500 de 500 atendidas. O ASP.NET Core tem `AddRateLimiter`; o SDK não liga nada.
- **Log de auditoria.** O log padrão é volumoso e diz qual ferramenta rodou, mas não quem pediu nem com o quê. Pra auditoria, você escreve um filtro (`WithRequestFilters(f => f.AddCallToolFilter(...))`) ou middleware que grave identidade, ferramenta, decisão e hash do argumento, nunca o dado em claro.

## Limites honestos

- **Não é o tokenizador de nenhum modelo em produção.** tiktoken `o200k_base` e `cl100k_base`, iguais à demo 13, servem pra comparar C# e Python entre si.
- **O host pode reescrever a definição.** A demo mede o que o servidor manda; cada cliente decide o que repassa ao modelo.
- **4 ferramentas pequenas, com parâmetro `string` e sem `[Description]` no parâmetro.** Com descrição por parâmetro ou tipos complexos o schema muda nos dois SDKs.
- **Latência medida na mesma máquina, sem rede, sem TLS, sem modelo.** É o custo do protocolo e do ASP.NET Core, não o de uma conversa com agente.
- **Não liguei o servidor ao Claude Code nem ao Copilot.** A demo fala com ele por JSON-RPC cru; o que muda com um host real fica pra outra demo.
- **Só HTTP.** Por stdio, o transporte local, não há porta aberta e a pergunta de autenticação é outra: quem pode iniciar o processo.
- **SDK em evolução.** 2.4.0 publicada em 07/11/2026. Versões novas podem mudar log, schema e padrões.
- Todo dado é sintético: o CPF e o CNS da nota são gerados por algoritmo e o nome é "FULANO DE TAL SINTETICO".

## Fonte

- SDK C# do MCP, `ModelContextProtocol` e `ModelContextProtocol.AspNetCore` 2.4.0, licença Apache-2.0: https://github.com/modelcontextprotocol/csharp-sdk · https://www.nuget.org/packages/ModelContextProtocol.AspNetCore/2.4.0
- Spec do MCP, transportes (2025-06-18), aviso de segurança sobre `Origin`: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- tiktoken 0.14.0, licença MIT: https://github.com/openai/tiktoken

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
