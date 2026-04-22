<div align="center">

# 🧪 NursIA Research Lab

### _A collection of clinical AI + FHIR demos from ongoing research at UFSC_

<br>

[![FHIR R4](https://img.shields.io/badge/FHIR-R4-blue?style=for-the-badge)](https://hl7.org/fhir/)
[![Ollama](https://img.shields.io/badge/Ollama-Local-black?style=for-the-badge&logo=meta)](https://ollama.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![UFSC](https://img.shields.io/badge/UFSC-PPGINFOS-0047AB?style=for-the-badge)](https://ppginfos.ufsc.br)

<br>

**Open clinical AI + FHIR demonstrations from the NursIA project — clinical simulation with AI for healthcare students and professionals.**

**Demonstrações abertas de IA clínica + FHIR do projeto NursIA — simulação clínica com IA para estudantes e profissionais de saúde.**

<br>

[🇬🇧 English](docs/README.en.md) · [🇧🇷 Português](docs/README.pt.md) · [🇪🇸 Español](docs/README.es.md) · [🇮🇹 Italiano](docs/README.it.md)

</div>

---

## 🎯 What's here / O que tem aqui

| Demo | What it shows / O que mostra |
|------|------------------------------|
| [01-fhir-ollama-local](demos/01-fhir-ollama-local/) | Full local pipeline: HAPI FHIR + Synthea + Ollama · Pipeline local completo |
| [02-clinical-ai-tutor](demos/02-clinical-ai-tutor/) | Response mode vs. Tutor mode · IA que pergunta em vez de responder |
| [03-everything-fhir](demos/03-everything-fhir/) | `$everything` FHIR → LLM context · Histórico completo numa chamada |

Each demo has its own multilingual README inside `demos/<demo>/docs/`.

Cada demo tem seu próprio README multilíngue dentro de `demos/<demo>/docs/`.

---

## 🏥 The project / O projeto

**NursIA** is a clinical simulation platform with AI built as part of my master's research at UFSC (Universidade Federal de Santa Catarina), inside the [PPGINFOS](https://ppginfos.ufsc.br) program.

Supervised by **Profa. Dra. Grace Marcon Dal Sasso** (national reference in health informatics, leads the FAPESC macroproject). Co-researched with **Brunna Cardozo** (nurse, responsible for clinical and pedagogical methodology). In partnership with **ESEP Porto + VirtualCare** (creators of the E4 Nursing platform that forms the pedagogical base for NursIA).

**NursIA** é uma plataforma de simulação clínica com IA desenvolvida como parte do meu mestrado na UFSC, dentro do programa PPGINFOS. Orientação da Profa. Dra. Grace Marcon Dal Sasso, co-pesquisa com Brunna Cardozo, em parceria com ESEP Porto + VirtualCare, dentro do macroprojeto financiado pela FAPESC.

The demos in this repository are public artifacts of that research.

As demos deste repositório são artefatos públicos dessa pesquisa.

---

## 🚀 Quickstart (shared stack / stack compartilhada)

All demos share one local stack: **HAPI FHIR + Synthea + Ollama**, via root [`docker-compose.yml`](docker-compose.yml).

Todas as demos compartilham uma stack local: **HAPI FHIR + Synthea + Ollama**, via [`docker-compose.yml`](docker-compose.yml) na raiz.

```bash
git clone https://github.com/rogeriorrodrigues/nursia-research-lab.git
cd nursia-research-lab
```

### Option A — Podman (recommended / recomendado)

```bash
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b
```

> **macOS:** Podman requires a VM. Run `podman machine init` (first time) and `podman machine start` before `podman-compose up`.
>
> **macOS:** O Podman precisa de uma VM. Rode `podman machine init` (primeira vez) e `podman machine start` antes do `podman-compose up`.

### Option B — Docker

```bash
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

### Then run any demo / Depois rode qualquer demo

```bash
cd demos/01-fhir-ollama-local && python3 fhir_ollama_demo.py
# or / ou
cd demos/02-clinical-ai-tutor && python3 demo_tutor_vs_resposta_lite.py
# or / ou
cd demos/03-everything-fhir && python3 criar_paciente_teste.py && python3 demo_everything_fhir.py <patient_id>
```

**Service ports / Portas dos serviços:**

| Service | Host port | Container port |
|---------|-----------|----------------|
| HAPI FHIR | `8082` | `8080` |
| Ollama | `11435` | `11434` |

---

## 🛠️ Stack overview

| Component | Role | License |
|-----------|------|---------|
| [HAPI FHIR](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) | Clinical data server (FHIR R4) | Apache 2.0 |
| [Ollama](https://ollama.com) | Local LLM runtime | MIT |
| [llama3.2:3b](https://ollama.com/library/llama3.2) | Language model (lightweight) | Meta License |
| [Synthea](https://synthetichealth.github.io/synthea/) | Synthetic patient generator | Apache 2.0 |
| [Python](https://python.org) | Demo orchestration | PSF |
| [Podman](https://podman.io) / [Docker](https://docker.com) | Container runtime | Apache 2.0 / Apache 2.0 |

---

## 🗺️ Roadmap

See [`roadmap.md`](roadmap.md) for the consolidated research roadmap.

Veja [`roadmap.md`](roadmap.md) para o roadmap consolidado da pesquisa.

---

## 👨‍💻 Author / Autor

**Rogério Rodrigues** — Azure MVP · UFSC Health Informatics Researcher · Professor USP/FIAP

Contact via [LinkedIn](https://linkedin.com/in/rogeriorrodrigues)

---

<div align="center">

⭐ Star if useful / Dá uma estrela se for útil!

Made in Mato with ☕ from a sítio in Santa Catarina, Brazil

</div>
