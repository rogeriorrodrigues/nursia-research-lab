# Roadmap — NursIA Research Lab

Consolidated roadmap across the three demos and the broader NursIA project.

Roadmap consolidado das três demos e do projeto NursIA mais amplo.

---

## ✅ Concluído / Done

- [x] Local FHIR + Ollama pipeline (demo 01)
- [x] Synthea integration for automated patient generation (demo 01)
- [x] Clinical evolution notes (DocumentReference) for all patients (demo 01)
- [x] Multilingual documentation EN/PT/ES/IT for demo 01
- [x] Response Mode vs. Tutor Mode prototype (demo 02)
- [x] Multilingual documentation EN/PT/ES/IT for demo 02
- [x] `$everything` FHIR + LLM demo (demo 03)
- [x] Multilingual documentation EN/PT/ES/IT for demo 03
- [x] Monorepo unification under `nursia-research-lab` (this repo)
- [x] Shared `docker-compose.yml` at the repo root
- [x] Podman + Docker support documented for all demos

---

## 🛠️ Em andamento / In progress

- [ ] [RAGAS](https://github.com/explodinggradients/ragas) quality evaluation pipeline (faithfulness > 0.85 target)
- [ ] Validation with UFSC nursing students and professors
- [ ] Comparative evaluation: typed-call context (demo 01) vs. `$everything` context (demo 03)

---

## 🔮 Futuro / Future

- [ ] [Microsoft Presidio](https://microsoft.github.io/presidio/) integration for pre-LLM anonymization (essential when real patient data enters the pipeline)
- [ ] MCP Server for standardized AI–FHIR access
- [ ] Clinical simulation scenarios for nursing students (NursIA Protocol)
- [ ] Tutor Mode generalization beyond the JS / CHF case
- [ ] Web UI for the simulation scenarios (currently CLI-only)
- [ ] Full integration with the **E4 Nursing** platform (ESEP Porto + VirtualCare)

---

## 📅 Eventos / Events

- [ ] **MIE 2026** — presentation in Genoa, Italy, May 2026

---

## 🛡️ About Presidio / Sobre o Presidio

[Microsoft Presidio](https://microsoft.github.io/presidio/) is an open-source SDK for data protection and de-identification. It detects and anonymizes PII (names, CPFs, phone numbers, addresses) in text **before** it reaches the LLM.

Right now Presidio is **not** integrated because every patient in this repo is synthetic — curated demo patients (Maria, João, Ana, JS) are fictional, and Synthea generates fully synthetic records. Presidio becomes essential the moment real clinical data enters the pipeline (e.g., from electronic health records), at which point it becomes the pre-LLM anonymization layer that keeps the architecture LGPD/GDPR-compliant.

[Presidio](https://microsoft.github.io/presidio/) é um SDK open-source da Microsoft pra proteção e desidentificação de dados. Detecta e anonimiza PII (nomes, CPFs, telefones, endereços) em texto **antes** de chegar ao LLM.

Hoje o Presidio **não** está integrado porque todos os pacientes neste repo são sintéticos — os curados (Maria, João, Ana, JS) são fictícios, e o Synthea gera registros 100% sintéticos. O Presidio se torna essencial no momento em que dados clínicos reais entrarem no pipeline (ex: prontuários eletrônicos), virando a camada de anonimização pré-LLM que mantém a arquitetura conforme LGPD/GDPR.
