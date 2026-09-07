# Roadmap — NursIA Research Lab

Consolidated roadmap across the demos and the broader NursIA project.

Roadmap consolidado das demos e do projeto NursIA mais amplo.

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
- [x] Brazilian CPF + CNS recognizers for Presidio, measured on a synthetic PT corpus (demo 04)
- [x] Multilingual documentation EN/PT/ES/IT for demo 04

---

## 🛠️ Em andamento / In progress

- [ ] [RAGAS](https://github.com/explodinggradients/ragas) quality evaluation pipeline (faithfulness > 0.85 target)
- [ ] Validation with UFSC healthcare students and professors
- [ ] Comparative evaluation: typed-call context (demo 01) vs. `$everything` context (demo 03)

---

## 🔮 Futuro / Future

- [ ] Wire the Presidio layer from demo 04 into the NursIA pipeline (essential when real patient data enters it)
- [ ] Upstream PR to [`data-privacy-stack/presidio`](https://github.com/data-privacy-stack/presidio): `country_specific/brazil` (CPF + CNS)
- [ ] CRM recognizer with state suffix; measurement on dirty synthetic text (OCR, line breaks)
- [ ] MCP Server for standardized AI–FHIR access
- [ ] Clinical simulation scenarios for healthcare students and professionals (NursIA Protocol)
- [ ] Tutor Mode generalization beyond the JS / CHF case
- [ ] Web UI for the simulation scenarios (currently CLI-only)
- [ ] Full integration with the **E4 Nursing** platform (ESEP Porto + VirtualCare)

---

## 📅 Eventos / Events

- [ ] **MIE 2026** — presentation in Genoa, Italy, May 2026

---

## 🛡️ About Presidio / Sobre o Presidio

[Microsoft Presidio](https://microsoft.github.io/presidio/) is an open-source SDK for data protection and de-identification. It detects and anonymizes PII (names, CPFs, phone numbers, addresses) in text **before** it reaches the LLM.

Demo 04 ([`demos/04-presidio-br`](demos/04-presidio-br/)) adds the Brazilian recognizers Presidio does not ship (CPF and CNS, with check-digit validation) and measures them: recall 0/100 → 100/100, false positives 100 → 0 on 11-digit distractors. In June 2026 the project moved from `microsoft/presidio` to community governance under [Data Privacy Stack](https://github.com/data-privacy-stack/presidio); the recognizers are written to be upstreamed there.

Right now Presidio is **not** wired into the LLM demos because every patient in this repo is synthetic — curated demo patients (Maria, João, Ana, JS) are fictional, and Synthea generates fully synthetic records. Presidio becomes essential the moment real clinical data enters the pipeline (e.g., from electronic health records), at which point it becomes the pre-LLM anonymization layer that keeps the architecture LGPD/GDPR-compliant.

[Presidio](https://microsoft.github.io/presidio/) é um SDK open-source da Microsoft pra proteção e desidentificação de dados. Detecta e anonimiza PII (nomes, CPFs, telefones, endereços) em texto **antes** de chegar ao LLM.

A demo 04 ([`demos/04-presidio-br`](demos/04-presidio-br/)) adiciona os reconhecedores brasileiros que o Presidio não traz (CPF e CNS, com dígito verificador) e mede: recall 0/100 → 100/100, falso positivo 100 → 0 em distratores de 11 dígitos. Em junho de 2026 o projeto saiu do `microsoft/presidio` pra governança comunitária no [Data Privacy Stack](https://github.com/data-privacy-stack/presidio); os reconhecedores foram escritos pra subir pra lá.

Hoje o Presidio **não** está ligado às demos com LLM porque todos os pacientes neste repo são sintéticos — os curados (Maria, João, Ana, JS) são fictícios, e o Synthea gera registros 100% sintéticos. O Presidio se torna essencial no momento em que dados clínicos reais entrarem no pipeline (ex: prontuários eletrônicos), virando a camada de anonimização pré-LLM que mantém a arquitetura conforme LGPD/GDPR.
