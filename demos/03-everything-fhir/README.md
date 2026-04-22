<div align="center">

# 🩺 `$everything` FHIR + LLM

### _One REST call. Full clinical history. Local LLM reasoning._

<br>

[![FHIR R4](https://img.shields.io/badge/FHIR-R4-blue?style=for-the-badge)](https://hl7.org/fhir/)
[![Ollama](https://img.shields.io/badge/Ollama-Local-black?style=for-the-badge&logo=meta)](https://ollama.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](../../LICENSE)

<br>

**Demonstrates the FHIR `$everything` operation: pull a patient's complete clinical record in a single call, then feed it to a local LLM for grounded clinical reasoning.**

**Demonstra a operação `$everything` do FHIR: puxar o histórico clínico completo de um paciente em uma única chamada e alimentar um LLM local pra raciocínio clínico fundamentado.**

<br>

[🇬🇧 English](docs/README.en.md) · [🇧🇷 Português](docs/README.pt.md) · [🇪🇸 Español](docs/README.es.md) · [🇮🇹 Italiano](docs/README.it.md)

</div>

---

## 🇬🇧 What it does

The FHIR specification defines an operation called [`Patient/{id}/$everything`](https://www.hl7.org/fhir/operation-patient-everything.html). One GET request returns a Bundle with **every resource related to that patient**: demographics, conditions, observations, medications, procedures, diagnostic reports, and more.

This demo:

1. Calls `GET {FHIR}/Patient/{id}/$everything` and receives a Bundle.
2. Parses the Bundle into typed buckets (Patient, Condition, Observation, MedicationRequest, ...).
3. Builds a structured text context from the buckets.
4. Sends `(system_prompt + context + question)` to a local Ollama model and prints the answer.

The system prompt forces the model to answer **only from the provided data** — no hallucinations.

A helper script (`criar_paciente_teste.py`) seeds a representative test patient (JS — decompensated CHF) so you can run the demo even without Synthea data loaded.

## 🇧🇷 O que faz

A spec FHIR define uma operação chamada [`Patient/{id}/$everything`](https://www.hl7.org/fhir/operation-patient-everything.html). Uma única requisição GET retorna um Bundle com **todos os recursos relacionados àquele paciente**: demografia, condições, observações, medicações, procedimentos, relatórios diagnósticos e mais.

Esta demo:

1. Chama `GET {FHIR}/Patient/{id}/$everything` e recebe um Bundle.
2. Parseia o Bundle em buckets tipados (Patient, Condition, Observation, MedicationRequest, ...).
3. Monta um contexto textual estruturado a partir dos buckets.
4. Envia `(system_prompt + contexto + pergunta)` pra um modelo local no Ollama e imprime a resposta.

O system prompt obriga o modelo a responder **apenas com base nos dados fornecidos** — sem alucinação.

Um script auxiliar (`criar_paciente_teste.py`) cria um paciente de teste representativo (JS — ICC descompensada) pra você poder rodar a demo mesmo sem dados do Synthea carregados.

---

## ⚡ Quickstart

### Prerequisites / Pré-requisitos

The shared stack from the monorepo root must be running. From the repository root:

A stack compartilhada da raiz do monorepo precisa estar rodando. A partir da raiz do repositório:

```bash
# Podman
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b

# OR Docker
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

### Run the demo / Rodar a demo

```bash
cd demos/03-everything-fhir
pip install -r requirements.txt

# 1. Seed a test patient if you don't have one yet
#    Cria um paciente de teste se você não tiver nenhum
python3 criar_paciente_teste.py
# → prints a Patient ID, e.g. 123 / imprime um Patient ID, ex.: 123

# 2. Run the demo with that ID
#    Roda a demo com esse ID
python3 demo_everything_fhir.py 123
```

The script prints:
- The `$everything` URL it called.
- A summary panel with resource counts.
- The structured context sent to the LLM.
- The LLM's clinical answer (Markdown-rendered).

It also writes `output_everything.txt` — useful for screenshots and posts. This file is git-ignored.

O script imprime:
- A URL `$everything` chamada.
- Um painel-resumo com contagens de recursos.
- O contexto estruturado enviado pro LLM.
- A resposta clínica do LLM (renderizada em Markdown).

Também escreve `output_everything.txt` — útil pra screenshot e posts. Esse arquivo está no `.gitignore`.

---

## 🧪 What the test patient looks like

`criar_paciente_teste.py` creates patient JS — a 68-year-old male with **decompensated congestive heart failure (CHF)** in the ICU:

`criar_paciente_teste.py` cria o paciente JS — homem de 68 anos com **insuficiência cardíaca congestiva (ICC) descompensada** na UTI:

| Resource | Detail |
|----------|--------|
| Patient | JS Silva, M, 1957-03-15 |
| Conditions | ICC descompensada (SNOMED 42343007) · HAS (SNOMED 38341003) |
| Observations | BP 84/52 · HR 118 · SpO₂ 94% · Lactate 3.6 mmol/L · BNP 1860 pg/mL |
| Medications | Norepinephrine 0.3 mcg/kg/min · Vasopressin 0.04 U/min |

The default question sent to the LLM is:

A pergunta padrão enviada pro LLM é:

> _"Qual a situação clínica geral desse paciente? Quais são os pontos de atenção?"_

---

## 🏥 Connection to the NursIA project / Conexão com o projeto NursIA

This demo is part of the **NursIA Research Lab** — a collection of clinical AI + FHIR demos from master's research at UFSC. The other demos in this monorepo:

Esta demo faz parte do **NursIA Research Lab** — uma coleção de demos de IA clínica + FHIR da minha pesquisa de mestrado na UFSC. As outras demos neste monorepo:

- [`demos/01-fhir-ollama-local`](../01-fhir-ollama-local/) — full local pipeline with curated and Synthea patients · pipeline local completo com pacientes curados e do Synthea.
- [`demos/02-clinical-ai-tutor`](../02-clinical-ai-tutor/) — Response Mode vs. Tutor Mode · Modo Resposta vs. Modo Tutor.

For the full project context, see the [main README](../../README.md) and [the multilingual docs](../../docs/).

Pro contexto completo do projeto, veja o [README principal](../../README.md) e [os docs multilíngue](../../docs/).

---

## 📜 License

[MIT](../../LICENSE) — Rogério Rodrigues, 2026.
