<div align="center">

# 🩺 `$everything` FHIR + LLM — Full English documentation

[← Back to demo README](../README.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>

---

## 📋 Table of contents

- [What is `$everything`?](#-what-is-everything)
- [How this demo uses it](#-how-this-demo-uses-it)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Step-by-step](#-step-by-step)
- [Walkthrough of the code](#-walkthrough-of-the-code)
- [Expected output](#-expected-output)
- [Why `$everything` matters for LLMs](#-why-everything-matters-for-llms)
- [Comparison with demo 01](#-comparison-with-demo-01)
- [Troubleshooting](#-troubleshooting)
- [Next steps](#-next-steps)

---

## 🔎 What is `$everything`?

[`Patient/{id}/$everything`](https://www.hl7.org/fhir/operation-patient-everything.html) is a standard FHIR operation defined in the FHIR R4 specification. A single GET request returns a **Bundle** containing every resource the server knows about that patient — demographics, conditions, observations, medications, procedures, encounters, diagnostic reports, allergies, and more.

It is server-defined (not all FHIR servers expose it), but HAPI FHIR — the server we use in the shared stack — supports it out of the box.

> **Why it exists:** before `$everything`, building a "patient summary" required dozens of typed REST calls (`/Condition?patient=`, `/Observation?patient=`, ...). `$everything` is the FHIR-native way to say "give me the whole picture of this person."

---

## 🎯 How this demo uses it

The demo treats `$everything` as a **context-loading primitive for an LLM**. The flow:

```
GET /Patient/{id}/$everything
       │
       ▼
   Bundle (FHIR R4)
       │
       ▼
   Parse into typed buckets
   (Patient, Condition, Observation, MedicationRequest, ...)
       │
       ▼
   Format as structured text
   (sections with labels and values)
       │
       ▼
   POST to Ollama /api/chat
   with strict system prompt:
   "answer ONLY from this data"
       │
       ▼
   Markdown answer in terminal
```

The LLM never invents data. If the answer isn't in the Bundle, the prompt instructs it to say so explicitly.

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                       YOUR MACHINE                            │
│                                                               │
│  ┌─────────────┐                                              │
│  │  HAPI FHIR  │   GET /Patient/{id}/$everything              │
│  │  port 8082  │ ◄─────────────────────────────────┐         │
│  │  (FHIR R4)  │                                    │         │
│  └─────────────┘                                    │         │
│         │                                  ┌────────┴──────┐  │
│         │ Bundle                           │  demo_        │  │
│         ▼                                  │  everything_  │  │
│   parse + format                           │  fhir.py      │  │
│         │                                  └────────┬──────┘  │
│         │ structured context                        │         │
│         │                                            │         │
│         │           POST /api/chat                   │         │
│         └──────────────────────────────────► ┌──────▼──────┐  │
│                                              │   Ollama    │  │
│                                              │ port 11435  │  │
│                                              │ llama3.2:3b │  │
│                                              └─────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| Shared stack from monorepo root | running | HAPI FHIR + Ollama via `docker-compose.yml` |
| Python | 3.10+ | With `requests` and `rich` (see `requirements.txt`) |
| Patient in HAPI FHIR | at least one | Use `criar_paciente_teste.py` if you have none |

The demo expects:

- `FHIR_URL = http://localhost:8082/fhir`
- `OLLAMA_URL = http://localhost:11435`
- Model `llama3.2:3b` already pulled into Ollama

These match the host ports defined in the root `docker-compose.yml` (FHIR `8082:8080`, Ollama `11435:11434`).

---

## 🚀 Step-by-step

### 1. Start the shared stack (from repo root)

```bash
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b
```

Or with Docker:

```bash
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

### 2. Install Python deps

```bash
cd demos/03-everything-fhir
pip install -r requirements.txt
```

### 3. Seed a test patient (optional)

If you don't already have a patient, run:

```bash
python3 criar_paciente_teste.py
```

This creates patient JS (decompensated CHF) and prints a Patient ID. Note the ID.

### 4. Run the demo

```bash
python3 demo_everything_fhir.py <patient_id>
```

The script prints the `$everything` URL it called, a summary of the resources received, the structured context sent to the LLM, and the LLM's clinical answer.

It also writes `output_everything.txt` for screenshots and documentation. The file is git-ignored.

---

## 🧠 Walkthrough of the code

### `criar_paciente_teste.py`

Creates a representative ICU patient (JS Silva — decompensated CHF) by POSTing to `/Patient`, `/Condition`, `/Observation`, and `/MedicationRequest`. Uses SNOMED CT for diagnoses and LOINC for vitals/labs. Prints the resulting Patient ID.

### `demo_everything_fhir.py`

Four functions, in order:

1. **`buscar_historico_completo(patient_id)`** — calls `GET /Patient/{id}/$everything` with `Accept: application/fhir+json`. Handles `ConnectionError` (HAPI down) and `HTTPError` (patient not found).
2. **`resumir_bundle(bundle)`** — iterates over `bundle["entry"]` and groups resources by `resourceType` into a dict with keys `patient`, `conditions`, `observations`, `medications`, `procedures`, `diagnostic_reports`.
3. **`montar_contexto_para_llm(recursos)`** — converts each bucket into labeled text sections (`PACIENTE:`, `DIAGNÓSTICOS:`, `OBSERVAÇÕES CLÍNICAS:`, `MEDICAÇÕES:`). Truncates observations at 20 to avoid overflowing the model's context window.
4. **`perguntar_para_llm(contexto, pergunta)`** — POSTs to `/api/chat` with a strict system prompt: "answer ONLY based on the provided data; if the information isn't there, say so; never invent values or diagnoses." Uses `temperature=0.2` and `num_predict=500`.

The default question is hardcoded to:

> _"Qual a situação clínica geral desse paciente? Quais são os pontos de atenção?"_

To experiment with other questions, edit the `pergunta` variable in `main()`.

---

## 📺 Expected output

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
│ [Markdown clinical reasoning here]              │
╰─────────────────────────────────────────────────╯
```

---

## 🔍 Why `$everything` matters for LLMs

Most "AI + EHR" demos build context by chaining typed FHIR calls — one for `Condition`, one for `Observation`, one for `MedicationRequest`, etc. That works, but:

- It's **server-aware**: every demo has to know the resource taxonomy.
- It's **chatty**: 7–10 round trips per patient.
- It's **fragile**: forgetting a resource type silently strips data from the LLM context.

`$everything` flips this. The server decides what counts as "the patient's record" and returns it in one shot. The client just parses the Bundle. This pushes the responsibility for "what to include" to the server — which is exactly where it belongs in a regulated environment.

For LLM context loading specifically, `$everything` aligns well with **single-prompt, no-tool** architectures. You retrieve once, format once, and send the model a self-contained snapshot.

---

## ⚖️ Comparison with demo 01

| | demo 01 (`fhir-ollama-local`) | demo 03 (`everything-fhir`) |
|---|---|---|
| **Retrieval** | 7+ typed REST calls per patient | 1 call to `$everything` |
| **Context shape** | Hand-built per resource type | Bundle → buckets → sections |
| **UX** | Interactive paginated menu | CLI: `python ... <patient_id>` |
| **Best for** | Exploratory clinical reasoning, long sessions | One-shot context loading, posts/screenshots |
| **Code size** | Larger (menu, pagination, multiple endpoints) | Smaller (one function per stage) |

Both demos use the same shared stack and the same model. They illustrate two valid patterns for "FHIR → LLM context."

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `HAPI FHIR não tá respondendo em http://localhost:8082/fhir` | Stack not running. From repo root: `podman-compose up -d` (or `docker compose up -d`). Wait ~30s for HAPI to be ready. |
| `Erro HTTP: 404` | Patient ID doesn't exist. Run `criar_paciente_teste.py` and use the printed ID. |
| `Erro no Ollama` | Model not pulled or Ollama not running. `podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b`. |
| `ModuleNotFoundError: rich` | `pip install -r requirements.txt`. |
| LLM answer is weak / generic | The Bundle may be sparse. Try a Synthea patient (demo 01 generates them) instead of the seeded test patient. |

---

## 🗺️ Next steps

- Test against Synthea-generated patients with richer histories.
- Add a CLI flag for the question (currently hardcoded).
- Add a `--save-bundle` flag to dump the raw Bundle as JSON for inspection.
- Compare response quality between `$everything` context and demo 01's typed-call context.
- Evaluate response quality with [RAGAS](https://github.com/explodinggradients/ragas) (faithfulness > 0.85 target).

---

<div align="center">

[← Back to demo README](../README.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>
