<div align="center">

# 🧪 NursIA Research Lab — Full Documentation

### 🇬🇧 English

[← Back to main README](../README.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>

---

## 📋 Table of contents

- [About the project](#-about-the-project)
- [Why this exists](#-why-this-exists)
- [The three demos](#-the-three-demos)
- [Stack overview](#-stack-overview)
- [Quickstart](#-quickstart)
- [Research context](#-research-context)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🏥 About the project

**NursIA** is a clinical simulation platform with AI built as part of master's research in Health Informatics at UFSC (Universidade Federal de Santa Catarina), inside the [PPGINFOS](https://ppginfos.ufsc.br) program — Florianópolis, Brazil.

The project investigates how local large language models, FHIR-based synthetic patients, and prompt engineering can support nursing education without ever sending patient data to the cloud. Everything runs offline. Nothing leaks. LGPD/GDPR compliance is a side effect of the architecture, not an extra layer bolted on top.

This monorepo collects three public demonstrations from that research. Each demo is small enough to read in a single sitting, runs locally on a laptop, and isolates one specific question about clinical AI.

---

## 🎯 Why this exists

Most clinical AI tooling assumes:
1. You will send patient data to a cloud API.
2. You can afford the per-token cost.
3. Your institution has signed a DPA with the vendor.
4. You trust the vendor's training data, retention policies, and uptime.

In Brazilian public health and academic research, none of those assumptions hold. The demos here show that you can go quite far without any of them — using open standards (FHIR R4, the same standard the national health network RNDS is built on), open models (Ollama + Llama 3.2), and open infrastructure (HAPI FHIR, Synthea).

The goal is not to replace commercial clinical AI. The goal is to make the local-first option a credible default for educators and researchers.

---

## 📚 The three demos

### `demos/01-fhir-ollama-local`

A complete local pipeline. Three containers (HAPI FHIR + Synthea + Ollama), one Python script, and an interactive menu that lets you query any patient and chat with a local LLM grounded exclusively in their FHIR data. Curated patients (Maria, João, Ana) ship with handwritten clinical and nursing evolution notes; Synthea generates additional volume on demand.

→ [demo README](../demos/01-fhir-ollama-local/README.md) · [English docs](../demos/01-fhir-ollama-local/docs/README.en.md)

### `demos/02-clinical-ai-tutor`

A controlled experiment: same model, same patient, same student decision. Only the system prompt changes. **Response Mode** delivers the answer; the student copies. **Tutor Mode** asks Socratic questions; the student thinks. Built around a real ICU scenario (Patient JS, decompensated CHF, MAP 63, lactate 3.6) where the student's intuitive answer is potentially unsafe.

→ [demo README](../demos/02-clinical-ai-tutor/README.md) · [English docs are the demo README itself; PT/ES/IT in `demos/02-clinical-ai-tutor/docs/`](../demos/02-clinical-ai-tutor/)

### `demos/03-everything-fhir`

Demonstrates the FHIR `$everything` operation: a single REST call returns the entire clinical record of a patient as a Bundle. The demo parses that Bundle into structured context and feeds it to a local LLM, replacing the multi-call pattern of demo 01 with a one-shot retrieval. Includes a helper script to seed a test patient (JS — decompensated CHF) when you don't have one yet.

→ [demo README](../demos/03-everything-fhir/README.md) · [English docs](../demos/03-everything-fhir/docs/README.en.md)

---

## 🛠️ Stack overview

| Component | Role | License | Why this choice |
|-----------|------|---------|------------------|
| [HAPI FHIR](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) | FHIR R4 server | Apache 2.0 | Same standard as Brazil's RNDS (2.8B records). Mature reference implementation. |
| [Ollama](https://ollama.com) | Local LLM runtime | MIT | Single binary, REST API on `:11434`, runs any GGUF model. |
| [llama3.2:3b](https://ollama.com/library/llama3.2) | Default language model | Meta License | ~3 GB RAM. Fast on a laptop. Good enough for clinical reasoning demos. |
| [Synthea](https://synthetichealth.github.io/synthea/) | Synthetic patient generator | Apache 2.0 | Generates fully synthetic FHIR R4 bundles with realistic disease modules. |
| [Python](https://python.org) 3.10+ | Demo orchestration | PSF | `requests` for FHIR, `rich` for terminal UI. No frameworks. |
| [Podman](https://podman.io) / [Docker](https://docker.com) | Container runtime | Apache 2.0 | Both compose files work; choose what you have installed. |

---

## ⚡ Quickstart

### 1. Clone and start the shared stack

```bash
git clone https://github.com/rogeriorrodrigues/nursia-research-lab.git
cd nursia-research-lab

# Podman (recommended on macOS / Linux)
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b

# OR Docker
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

The shared stack exposes:
- HAPI FHIR on `http://localhost:8082/fhir`
- Ollama on `http://localhost:11434` (Podman) or as configured in `docker-compose.yml` (`11435` host-side)

### 2. Run any demo

```bash
# Demo 01 — interactive paginated patient explorer
cd demos/01-fhir-ollama-local
python3 fhir_ollama_demo.py

# Demo 02 — Response vs. Tutor mode
cd demos/02-clinical-ai-tutor
pip install requests rich
python3 demo_tutor_vs_resposta_lite.py

# Demo 03 — $everything in one shot
cd demos/03-everything-fhir
pip install -r requirements.txt
python3 criar_paciente_teste.py        # seeds a test patient if you have none
python3 demo_everything_fhir.py <patient_id>
```

### 3. macOS notes

Podman requires a Linux VM on macOS:

```bash
podman machine init     # first time only
podman machine start
```

If you prefer Docker Desktop, just use the Docker option above.

---

## 🔬 Research context

This repository is a public artifact of master's research at UFSC. Credits go beyond the author:

| Role | Person / Institution |
|------|----------------------|
| **Researcher** | Rogério Rodrigues — MSc student, Health Informatics, PPGINFOS/UFSC |
| **Supervisor** | Profa. Dra. Grace Marcon Dal Sasso — national reference in health informatics, leads the FAPESC macroproject |
| **Co-researcher** | Brunna Cardozo — nurse, responsible for clinical and pedagogical methodology |
| **Pedagogical partner** | ESEP Porto + VirtualCare — creators of the **E4 Nursing** platform that forms the pedagogical base for NursIA |
| **Funding** | FAPESC (Fundação de Amparo à Pesquisa e Inovação do Estado de Santa Catarina) macroproject |
| **Program** | [PPGINFOS — Postgraduate Program in Health Informatics, UFSC](https://ppginfos.ufsc.br) |

The macroproject targets clinical simulation for nursing education with a strong privacy-by-design constraint: real student data and any future real patient data must stay inside the institution. That constraint is what shapes every technical choice in these demos.

---

## 🗺️ Roadmap

See [`../roadmap.md`](../roadmap.md) for the consolidated roadmap. High-level themes:

- ✅ **Core local pipeline** (demo 01) — done.
- ✅ **Pedagogical mode shift** (demo 02) — done.
- ✅ **`$everything` retrieval** (demo 03) — done.
- 🛠️ **Quality evaluation** with [RAGAS](https://github.com/explodinggradients/ragas) — in progress.
- 🛠️ **Validation** with UFSC students and professors — in progress.
- 🔮 **Anonymization layer** with [Microsoft Presidio](https://microsoft.github.io/presidio/) — planned for when real patient data enters the pipeline.
- 🔮 **MCP Server** for standardized AI–FHIR access — planned.
- 🔮 **Clinical simulation scenarios** for nursing students (NursIA Protocol) — planned.
- 📅 **MIE 2026** — presentation in Genoa, May 2026.

---

## 📜 License

[MIT](../LICENSE) — Rogério Rodrigues, 2026.

---

<div align="center">

[← Back to main README](../README.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>
