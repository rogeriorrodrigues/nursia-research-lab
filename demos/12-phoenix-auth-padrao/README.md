# 12 · Phoenix 21.0.0: o painel de trace pede senha por padrão?

O Phoenix 21.0.0 (30/10/2026) ligou a autenticação por padrão, mas **só quando o servidor escuta fora do loopback**. No padrão (`127.0.0.1`), as **4 de 4 chamadas sem credencial responderam 200**: gravar trace, listar projetos, ler spans e GraphQL. O segredo sintético que eu pus no prompt voltou inteiro na leitura dos spans. Com `PHOENIX_HOST=0.0.0.0`, as mesmas 4 chamadas deram **401**, e o login `admin@localhost` / `admin` deu **403** (a senha padrão precisa ser trocada antes de abrir sessão).

*English: Phoenix 21.0.0 turns auth on by default only for non-loopback hosts. On the default 127.0.0.1, 4/4 unauthenticated calls (OTLP ingest, list projects, read spans, GraphQL) returned 200 and a synthetic secret in the prompt came back in the spans response. With PHOENIX_HOST=0.0.0.0 the same 4 calls returned 401, and admin/admin login returned 403. PHOENIX_ENABLE_AUTH=false opens everything again, on any interface.*

Artigo: https://rogerio.eti.br/phoenix-21-senha-padrao-loopback/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt
python3 demo.py                 # sobe o phoenix serve 4 vezes e grava results/
python3 -m pytest tests -q -s
```

CPU, sem GPU, sem chave de API, sem conta. Cada cenário leva uns 15 s.

## O que mostra

`demo.py` sobe o `phoenix serve` em 4 configurações, cada uma com pasta de trabalho nova (SQLite vazio) e portas livres:

1. `PHOENIX_HOST=127.0.0.1`, nenhuma variável de auth (o padrão);
2. `PHOENIX_HOST=0.0.0.0`, nenhuma variável de auth (o que a imagem Docker faz, segundo o MIGRATION.md);
3. `PHOENIX_HOST=0.0.0.0` com `PHOENIX_ENABLE_AUTH=false`;
4. `PHOENIX_HOST=0.0.0.0` com `PHOENIX_DEFAULT_ADMIN_INITIAL_PASSWORD` definida.

Em cada uma, sem credencial nenhuma: manda 1 trace OTLP com um span LLM cujo prompt carrega `sk-SINTETICO-0000-nao-e-chave-real-7f3a`, lista projetos (`GET /v1/projects`), lê os spans (`GET /v1/projects/default/spans`), consulta o GraphQL e tenta o login com `admin` / `admin`. No cenário 4, faz o login com a senha inicial e repete a listagem com o cookie da sessão (controle positivo). Por fim, tenta o `/healthz` pelo IP não-loopback da máquina.

## Resultado (results/resultado.json)

| Chamada | 1 · 127.0.0.1 padrão | 2 · 0.0.0.0 padrão | 3 · 0.0.0.0 + `ENABLE_AUTH=false` | 4 · 0.0.0.0 + senha inicial |
|---|---|---|---|---|
| gravar trace (`POST /v1/traces`) | 200 | 401 | 200 | 401 |
| listar projetos | 200 | 401 | 200 | 401 |
| ler spans | 200 | 401 | 200 | 401 |
| segredo sintético na resposta | sim | não | sim | não |
| GraphQL | 200 | 401 | 200 | 401 |
| login `admin` / `admin` | 405 (rota não existe) | 403 | 405 (rota não existe) | 401 |
| login com a senha inicial | - | - | - | 204 |
| listar projetos com a sessão | - | - | - | 200 |
| `/healthz` pelo IP da máquina | sem conexão | 200 | 200 | 200 |

- No padrão, o painel não aceita conexão pelo IP da máquina: só quem está na mesma máquina chega nele. Quem está na mesma máquina lê tudo sem senha.
- O 403 do cenário 2 é a regra nova: com a senha `admin`, o Phoenix não abre sessão e manda trocar a senha (`POST /auth/password-reset`).
- O 405 nos cenários 1 e 3 é a rota `/auth/login` que nem é montada quando a auth está desligada.

## Limites honestos

- **Não testei a versão 20.x.** O que mudou da 20 pra 21 vem da release e do MIGRATION.md; a demo só mede a 21.0.0.
- **Não testei Docker, Helm nem Databricks.** O cenário 2 imita o `PHOENIX_HOST=::` da imagem Docker com `0.0.0.0`, mas não rodei a imagem.
- **Não testei proxy reverso nem port-forward.** Se você põe um nginx ou um `ssh -L` na frente de um Phoenix em loopback, o Phoenix continua achando que está em loopback e segue sem senha. Isso sai da leitura do código (`auth_enabled_for_host()` olha o host configurado, não quem conecta); não medi.
- Só testei 4 chamadas da API. Não varri todas as rotas nem a interface web.
- Não testei `PHOENIX_SECRET`. Sem ela, segundo o MIGRATION.md, quem tem cópia do banco consegue decifrar as chaves de provedor salvas.
- Todo dado é sintético: a "chave" é inválida por construção e o prompt é inventado.

## Fonte

- Phoenix 21.0.0, Elastic License 2.0: https://github.com/Arize-ai/phoenix/releases/tag/arize-phoenix-v21.0.0
- Guia de migração v20 → v21: https://github.com/Arize-ai/phoenix/blob/main/MIGRATION.md
- Código: `phoenix/config.py`, função `auth_enabled_for_host()`.

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
