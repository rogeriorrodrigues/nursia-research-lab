<div align="center">

# 🩺 `$everything` FHIR + LLM — Documentazione completa in IT

[← Torna al README della demo](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md)

</div>

---

## 📋 Indice

- [Cos'è `$everything`?](#-cose-everything)
- [Come la demo lo usa](#-come-la-demo-lo-usa)
- [Architettura](#-architettura)
- [Prerequisiti](#-prerequisiti)
- [Passo per passo](#-passo-per-passo)
- [Walkthrough del codice](#-walkthrough-del-codice)
- [Output atteso](#-output-atteso)
- [Perché `$everything` è importante per gli LLM](#-perche-everything-e-importante-per-gli-llm)
- [Confronto con la demo 01](#-confronto-con-la-demo-01)
- [Risoluzione dei problemi](#-risoluzione-dei-problemi)
- [Prossimi passi](#-prossimi-passi)

---

## 🔎 Cos'è `$everything`?

[`Patient/{id}/$everything`](https://www.hl7.org/fhir/operation-patient-everything.html) è un'operazione standard definita nella specifica FHIR R4. Una singola richiesta GET restituisce un **Bundle** che contiene tutte le risorse che il server conosce su quel paziente — dati demografici, condizioni, osservazioni, farmaci, procedure, incontri, referti diagnostici, allergie e altro.

È un'operazione definita dal server (non tutti i server FHIR la espongono), ma HAPI FHIR — il server che usiamo nello stack condiviso — la supporta nativamente.

> **Perché esiste:** prima di `$everything`, costruire un "riepilogo del paziente" richiedeva decine di chiamate REST tipizzate (`/Condition?patient=`, `/Observation?patient=`, ...). `$everything` è il modo FHIR-nativo di dire "dammi il quadro completo di questa persona".

---

## 🎯 Come la demo lo usa

La demo tratta `$everything` come una **primitiva di caricamento del contesto per LLM**. Il flusso:

```
GET /Patient/{id}/$everything
       │
       ▼
   Bundle (FHIR R4)
       │
       ▼
   Parse in bucket tipizzati
   (Patient, Condition, Observation, MedicationRequest, ...)
       │
       ▼
   Formatta come testo strutturato
   (sezioni con etichette e valori)
       │
       ▼
   POST a Ollama /api/chat
   con system prompt rigoroso:
   "rispondi SOLO sulla base di questi dati"
       │
       ▼
   Risposta in Markdown nel terminale
```

L'LLM non inventa mai dati. Se la risposta non è nel Bundle, il prompt gli dice di dichiararlo esplicitamente.

---

## 🏗️ Architettura

```
┌───────────────────────────────────────────────────────────────┐
│                       LA TUA MACCHINA                         │
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
│         │ contesto strutturato                      │         │
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

## 📦 Prerequisiti

| Requisito | Minimo | Note |
|-----------|--------|------|
| Stack condiviso dalla radice del monorepo | in esecuzione | HAPI FHIR + Ollama via `docker-compose.yml` |
| Python | 3.10+ | Con `requests` e `rich` (vedi `requirements.txt`) |
| Paziente in HAPI FHIR | almeno uno | Usa `criar_paciente_teste.py` se non ne hai |

La demo si aspetta:

- `FHIR_URL = http://localhost:8082/fhir`
- `OLLAMA_URL = http://localhost:11435`
- Modello `llama3.2:3b` già scaricato in Ollama

Queste porte corrispondono a quelle che il `docker-compose.yml` della radice espone (FHIR `8082:8080`, Ollama `11435:11434`).

---

## 🚀 Passo per passo

### 1. Avviare lo stack condiviso (radice del repo)

```bash
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b
```

Oppure con Docker:

```bash
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

### 2. Installare le dipendenze Python

```bash
cd demos/03-everything-fhir
pip install -r requirements.txt
```

### 3. Creare un paziente di test (opzionale)

Se non hai ancora un paziente, esegui:

```bash
python3 criar_paciente_teste.py
```

Questo crea il paziente JS (ICC scompensata) e stampa un Patient ID. Annota l'ID.

### 4. Eseguire la demo

```bash
python3 demo_everything_fhir.py <patient_id>
```

Lo script stampa l'URL `$everything` chiamato, un riepilogo delle risorse ricevute, il contesto strutturato inviato all'LLM e la risposta clinica dell'LLM.

Scrive anche `output_everything.txt` per screenshot e documentazione. Il file è in `.gitignore`.

---

## 🧠 Walkthrough del codice

### `criar_paciente_teste.py`

Crea un paziente di terapia intensiva rappresentativo (JS Silva — ICC scompensata) facendo POST su `/Patient`, `/Condition`, `/Observation` e `/MedicationRequest`. Usa SNOMED CT per le diagnosi e LOINC per i parametri vitali/laboratorio. Alla fine stampa il Patient ID generato.

### `demo_everything_fhir.py`

Quattro funzioni, in ordine:

1. **`buscar_historico_completo(patient_id)`** — chiama `GET /Patient/{id}/$everything` con `Accept: application/fhir+json`. Gestisce `ConnectionError` (HAPI giù) e `HTTPError` (paziente non esistente).
2. **`resumir_bundle(bundle)`** — itera su `bundle["entry"]` e raggruppa le risorse per `resourceType` in un dict con chiavi `patient`, `conditions`, `observations`, `medications`, `procedures`, `diagnostic_reports`.
3. **`montar_contexto_para_llm(recursos)`** — converte ogni bucket in sezioni di testo etichettate (`PACIENTE:`, `DIAGNÓSTICOS:`, `OBSERVAÇÕES CLÍNICAS:`, `MEDICAÇÕES:`). Tronca le osservazioni a 20 per non far overflow della finestra di contesto del modello.
4. **`perguntar_para_llm(contexto, pergunta)`** — POST su `/api/chat` con system prompt rigoroso: "rispondi SOLO sulla base dei dati forniti; se l'informazione non c'è, dillo; non inventare mai valori o diagnosi". Usa `temperature=0.2` e `num_predict=500`.

La domanda predefinita è hardcoded:

> _"Qual a situação clínica geral desse paciente? Quais são os pontos de atenção?"_

Per provare altre domande, modifica la variabile `pergunta` in `main()`.

---

## 📺 Output atteso

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
│ [Ragionamento clinico in Markdown qui]          │
╰─────────────────────────────────────────────────╯
```

---

## 🔍 Perché `$everything` è importante per gli LLM

La maggior parte delle demo "IA + cartella clinica" costruisce il contesto concatenando chiamate FHIR tipizzate — una per `Condition`, una per `Observation`, una per `MedicationRequest`, ecc. Funziona, ma:

- È **server-aware**: ogni demo deve conoscere la tassonomia delle risorse.
- È **prolisso**: 7-10 round-trip per paziente.
- È **fragile**: dimenticare un resourceType rimuove silenziosamente dati dal contesto dell'LLM.

`$everything` ribalta tutto. Il server decide cosa conta come "cartella del paziente" e lo restituisce in una volta. Il client deve solo fare il parse del Bundle. Questo sposta la responsabilità di "cosa includere" sul server — che è esattamente dove deve stare in un ambiente regolato.

Specificamente per il caricamento del contesto LLM, `$everything` si allinea bene con architetture **single-prompt, senza tool calling**. Recuperi una volta, formatti una volta e invii al modello uno snapshot autocontenuto.

---

## ⚖️ Confronto con la demo 01

| | demo 01 (`fhir-ollama-local`) | demo 03 (`everything-fhir`) |
|---|---|---|
| **Recupero** | 7+ chiamate REST tipizzate per paziente | 1 chiamata a `$everything` |
| **Forma del contesto** | Costruito a mano per tipo di risorsa | Bundle → bucket → sezioni |
| **UX** | Menu interattivo paginato | CLI: `python ... <patient_id>` |
| **Migliore per** | Ragionamento clinico esplorativo, sessioni lunghe | Caricamento one-shot, post/screenshot |
| **Dimensione del codice** | Maggiore (menu, paginazione, endpoint multipli) | Minore (una funzione per fase) |

Entrambe usano lo stesso stack condiviso e lo stesso modello. Illustrano due pattern validi di "FHIR → contesto LLM".

---

## 🔧 Risoluzione dei problemi

| Problema | Soluzione |
|----------|-----------|
| `HAPI FHIR não tá respondendo em http://localhost:8082/fhir` | Stack non in esecuzione. Dalla radice del repo: `podman-compose up -d` (o `docker compose up -d`). Aspetta ~30s perché HAPI sia pronto. |
| `Erro HTTP: 404` | Il Patient ID non esiste. Esegui `criar_paciente_teste.py` e usa l'ID stampato. |
| `Erro no Ollama` | Modello non scaricato o Ollama non in esecuzione. `podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b`. |
| `ModuleNotFoundError: rich` | `pip install -r requirements.txt`. |
| Risposta dell'LLM debole / generica | Il Bundle potrebbe essere scarno. Prova con un paziente generato da Synthea (la demo 01 li genera) invece del paziente di test. |

---

## 🗺️ Prossimi passi

- Testare con pazienti generati da Synthea con storia clinica più ricca.
- Aggiungere un flag CLI per la domanda (oggi è hardcoded).
- Flag `--save-bundle` per esportare il Bundle grezzo come JSON per ispezione.
- Confrontare la qualità della risposta tra contesto `$everything` e contesto per chiamate tipizzate (demo 01).
- Valutare la qualità della risposta con [RAGAS](https://github.com/explodinggradients/ragas) (obiettivo: faithfulness > 0.85).

---

<div align="center">

[← Torna al README della demo](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md)

</div>
