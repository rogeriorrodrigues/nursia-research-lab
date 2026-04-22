<div align="center">

# 🩺 `$everything` FHIR + LLM — Documentação completa em PT

[← Voltar pro README da demo](../README.md) · [🇬🇧 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>

---

## 📋 Índice

- [O que é `$everything`?](#-o-que-e-everything)
- [Como essa demo usa](#-como-essa-demo-usa)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pre-requisitos)
- [Passo a passo](#-passo-a-passo)
- [Walkthrough do código](#-walkthrough-do-codigo)
- [Saída esperada](#-saida-esperada)
- [Por que `$everything` importa pra LLM](#-por-que-everything-importa-pra-llm)
- [Comparação com a demo 01](#-comparacao-com-a-demo-01)
- [Troubleshooting](#-troubleshooting)
- [Próximos passos](#-proximos-passos)

---

## 🔎 O que é `$everything`?

[`Patient/{id}/$everything`](https://www.hl7.org/fhir/operation-patient-everything.html) é uma operação padrão definida na spec FHIR R4. Uma única requisição GET retorna um **Bundle** contendo todos os recursos que o servidor conhece daquele paciente — demografia, condições, observações, medicações, procedimentos, encontros, relatórios diagnósticos, alergias, e por aí vai.

É uma operação definida pelo servidor (nem todo servidor FHIR expõe), mas o HAPI FHIR — o servidor da nossa stack compartilhada — suporta de fábrica.

> **Por que existe:** antes do `$everything`, montar um "resumo do paciente" exigia dezenas de chamadas REST tipadas (`/Condition?patient=`, `/Observation?patient=`, ...). `$everything` é o jeito FHIR-nativo de dizer "me dá o retrato inteiro dessa pessoa".

---

## 🎯 Como essa demo usa

A demo trata `$everything` como uma **primitiva de carregamento de contexto pro LLM**. O fluxo:

```
GET /Patient/{id}/$everything
       │
       ▼
   Bundle (FHIR R4)
       │
       ▼
   Parse em buckets tipados
   (Patient, Condition, Observation, MedicationRequest, ...)
       │
       ▼
   Formata como texto estruturado
   (seções com labels e valores)
       │
       ▼
   POST pro Ollama /api/chat
   com system prompt estrito:
   "responda APENAS com base nesses dados"
       │
       ▼
   Resposta em Markdown no terminal
```

O LLM não inventa dado. Se a resposta não está no Bundle, o prompt manda ele dizer isso explicitamente.

---

## 🏗️ Arquitetura

```
┌───────────────────────────────────────────────────────────────┐
│                       SUA MÁQUINA                             │
│                                                               │
│  ┌─────────────┐                                              │
│  │  HAPI FHIR  │   GET /Patient/{id}/$everything              │
│  │  porta 8082 │ ◄─────────────────────────────────┐         │
│  │  (FHIR R4)  │                                    │         │
│  └─────────────┘                                    │         │
│         │                                  ┌────────┴──────┐  │
│         │ Bundle                           │  demo_        │  │
│         ▼                                  │  everything_  │  │
│   parse + format                           │  fhir.py      │  │
│         │                                  └────────┬──────┘  │
│         │ contexto estruturado                      │         │
│         │                                            │         │
│         │           POST /api/chat                   │         │
│         └──────────────────────────────────► ┌──────▼──────┐  │
│                                              │   Ollama    │  │
│                                              │ porta 11435 │  │
│                                              │ llama3.2:3b │  │
│                                              └─────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 📦 Pré-requisitos

| Requisito | Mínimo | Notas |
|-----------|--------|-------|
| Stack compartilhada da raiz | rodando | HAPI FHIR + Ollama via `docker-compose.yml` |
| Python | 3.10+ | Com `requests` e `rich` (veja `requirements.txt`) |
| Paciente no HAPI FHIR | pelo menos um | Use `criar_paciente_teste.py` se não tiver |

A demo espera:

- `FHIR_URL = http://localhost:8082/fhir`
- `OLLAMA_URL = http://localhost:11435`
- Modelo `llama3.2:3b` já baixado no Ollama

Essas portas batem com o que o `docker-compose.yml` da raiz expõe (FHIR `8082:8080`, Ollama `11435:11434`).

---

## 🚀 Passo a passo

### 1. Subir a stack compartilhada (raiz do repo)

```bash
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b
```

Ou com Docker:

```bash
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

### 2. Instalar dependências Python

```bash
cd demos/03-everything-fhir
pip install -r requirements.txt
```

### 3. Criar um paciente de teste (opcional)

Se você ainda não tem paciente, rode:

```bash
python3 criar_paciente_teste.py
```

Isso cria o paciente JS (ICC descompensada) e imprime um Patient ID. Anota o ID.

### 4. Rodar a demo

```bash
python3 demo_everything_fhir.py <patient_id>
```

O script imprime a URL `$everything` chamada, um resumo dos recursos recebidos, o contexto estruturado enviado pro LLM e a resposta clínica do LLM.

Também escreve `output_everything.txt` pra screenshot e documentação. O arquivo está no `.gitignore`.

---

## 🧠 Walkthrough do código

### `criar_paciente_teste.py`

Cria um paciente de UTI representativo (JS Silva — ICC descompensada) fazendo POST em `/Patient`, `/Condition`, `/Observation` e `/MedicationRequest`. Usa SNOMED CT pros diagnósticos e LOINC pros sinais vitais/labs. No final imprime o Patient ID gerado.

### `demo_everything_fhir.py`

Quatro funções, em ordem:

1. **`buscar_historico_completo(patient_id)`** — chama `GET /Patient/{id}/$everything` com `Accept: application/fhir+json`. Trata `ConnectionError` (HAPI caído) e `HTTPError` (paciente não existe).
2. **`resumir_bundle(bundle)`** — itera sobre `bundle["entry"]` e agrupa os recursos por `resourceType` num dict com chaves `patient`, `conditions`, `observations`, `medications`, `procedures`, `diagnostic_reports`.
3. **`montar_contexto_para_llm(recursos)`** — transforma cada bucket em seções de texto com label (`PACIENTE:`, `DIAGNÓSTICOS:`, `OBSERVAÇÕES CLÍNICAS:`, `MEDICAÇÕES:`). Trunca observações em 20 pra não estourar janela de contexto do modelo.
4. **`perguntar_para_llm(contexto, pergunta)`** — POST em `/api/chat` com system prompt estrito: "responda APENAS com base nos dados fornecidos; se a informação não está aí, diz que não tem; nunca invente valores ou diagnósticos". Usa `temperature=0.2` e `num_predict=500`.

A pergunta padrão está hardcoded:

> _"Qual a situação clínica geral desse paciente? Quais são os pontos de atenção?"_

Pra testar outras perguntas, edita a variável `pergunta` em `main()`.

---

## 📺 Saída esperada

```
Demo: $everything FHIR + LLM

Chamando $everything...
GET http://localhost:8082/fhir/Patient/123/$everything
Bundle recebido: 11 recursos

╭─ 📦 Bundle FHIR — O que veio no $everything ──╮
│ Paciente: ✓                                    │
│ Diagnósticos: 2                                │
│ Observações: 6                                 │
│ Medicações: 2                                  │
│ Procedimentos: 0                               │
│ Relatórios: 0                                  │
╰────────────────────────────────────────────────╯

╭─ 📝 Contexto estruturado pro LLM ─────────────╮
│ PACIENTE: JS Silva                             │
│ Data de nascimento: 1957-03-15                 │
│ Gênero: male                                   │
│                                                │
│ DIAGNÓSTICOS:                                  │
│ - ICC descompensada                            │
│ - HAS                                          │
│                                                │
│ OBSERVAÇÕES CLÍNICAS:                          │
│ - Pressão arterial sistólica: 84 mmHg          │
│ - Pressão arterial diastólica: 52 mmHg         │
│ - Frequência cardíaca: 118 bpm                 │
│ - Saturação de oxigênio: 94 %                  │
│ - Lactato: 3.6 mmol/L                          │
│ - BNP: 1860 pg/mL                              │
│                                                │
│ MEDICAÇÕES:                                    │
│ - Noradrenalina 0.3 mcg/kg/min                 │
│ - Vasopressina 0.04 U/min                      │
╰────────────────────────────────────────────────╯

Pergunta pro LLM: Qual a situação clínica geral desse paciente?
                  Quais são os pontos de atenção?
Gerando resposta...

╭─ 🤖 Resposta do LLM (baseada APENAS no Bundle) ─╮
│ [Raciocínio clínico em Markdown aqui]           │
╰─────────────────────────────────────────────────╯
```

---

## 🔍 Por que `$everything` importa pra LLM

A maioria das demos de "IA + prontuário" monta contexto encadeando chamadas FHIR tipadas — uma pra `Condition`, uma pra `Observation`, uma pra `MedicationRequest`, etc. Funciona, mas:

- É **server-aware**: toda demo precisa saber a taxonomia de recursos.
- É **verboso**: 7-10 round-trips por paciente.
- É **frágil**: esquecer um resourceType remove silenciosamente dados do contexto do LLM.

`$everything` inverte. O servidor decide o que conta como "prontuário do paciente" e retorna de uma vez. O cliente só parseia o Bundle. Isso empurra a responsabilidade de "o que incluir" pro servidor — que é exatamente onde ela deve estar num ambiente regulado.

Especificamente pra carregamento de contexto pra LLM, `$everything` se alinha bem com arquiteturas **single-prompt, sem tool calling**. Você recupera uma vez, formata uma vez, e manda pro modelo um snapshot autocontido.

---

## ⚖️ Comparação com a demo 01

| | demo 01 (`fhir-ollama-local`) | demo 03 (`everything-fhir`) |
|---|---|---|
| **Recuperação** | 7+ chamadas REST tipadas por paciente | 1 chamada ao `$everything` |
| **Formato do contexto** | Montado à mão por tipo de recurso | Bundle → buckets → seções |
| **UX** | Menu interativo paginado | CLI: `python ... <patient_id>` |
| **Melhor pra** | Raciocínio clínico exploratório, sessões longas | Carregamento one-shot, posts/screenshots |
| **Tamanho do código** | Maior (menu, paginação, múltiplos endpoints) | Menor (uma função por etapa) |

As duas usam a mesma stack compartilhada e o mesmo modelo. Ilustram dois padrões válidos de "FHIR → contexto LLM".

---

## 🔧 Troubleshooting

| Problema | Solução |
|----------|---------|
| `HAPI FHIR não tá respondendo em http://localhost:8082/fhir` | Stack não tá rodando. Na raiz do repo: `podman-compose up -d` (ou `docker compose up -d`). Espera uns 30s pra o HAPI subir. |
| `Erro HTTP: 404` | Patient ID não existe. Roda `criar_paciente_teste.py` e usa o ID impresso. |
| `Erro no Ollama` | Modelo não baixado ou Ollama não rodando. `podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b`. |
| `ModuleNotFoundError: rich` | `pip install -r requirements.txt`. |
| Resposta do LLM fraca / genérica | O Bundle pode estar esparso. Testa com um paciente do Synthea (demo 01 gera) em vez do paciente de teste. |

---

## 🗺️ Próximos passos

- Testar contra pacientes gerados pelo Synthea com histórico mais rico.
- Adicionar flag de CLI pra pergunta (hoje está hardcoded).
- Flag `--save-bundle` pra dumpar o Bundle cru como JSON pra inspeção.
- Comparar qualidade de resposta entre contexto `$everything` e contexto por chamadas tipadas (demo 01).
- Avaliar qualidade de resposta com [RAGAS](https://github.com/explodinggradients/ragas) (alvo: faithfulness > 0.85).

---

<div align="center">

[← Voltar pro README da demo](../README.md) · [🇬🇧 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>
