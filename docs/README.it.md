<div align="center">

# 🧪 NursIA Research Lab — Documentazione completa

### 🇮🇹 Italiano

[← Torna al README principale](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md)

</div>

---

## 📋 Indice

- [Sul progetto](#-sul-progetto)
- [Perché esiste](#-perche-esiste)
- [Le demo](#-le-demo)
- [Panoramica dello stack](#-panoramica-dello-stack)
- [Avvio rapido](#-avvio-rapido)
- [Contesto della ricerca](#-contesto-della-ricerca)
- [Roadmap](#-roadmap)
- [Licenza](#-licenza)

---

## 🏥 Sul progetto

**NursIA** è una piattaforma di simulazione clinica con IA costruita come parte della mia ricerca di master in Informatica Sanitaria all'UFSC (Universidade Federal de Santa Catarina), all'interno del programma [PPGINFOS](https://ppginfos.ufsc.br) — Florianópolis, Brasile.

La ricerca esamina come i modelli linguistici locali, i pazienti sintetici basati su FHIR e l'ingegneria dei prompt possano supportare la formazione di studenti e professionisti sanitari senza inviare mai dati dei pazienti al cloud. Tutto gira offline. Niente trapela. La conformità LGPD/GDPR è un effetto collaterale dell'architettura, non uno strato aggiuntivo applicato successivamente.

Questo monorepo raccoglie dimostrazioni pubbliche aperte di quella ricerca. Ogni demo è abbastanza piccola da essere letta in una sola seduta, gira localmente su un laptop e isola una domanda specifica sull'IA clinica.

---

## 🎯 Perché esiste

La maggior parte degli strumenti di IA clinica presume che:
1. Invierai dati dei pazienti a un'API cloud.
2. Puoi permetterti il costo per token.
3. La tua istituzione ha firmato un DPA con il fornitore.
4. Ti fidi dei dati di addestramento, della politica di conservazione e della disponibilità del fornitore.

Nella sanità pubblica brasiliana e nella ricerca accademica, nessuna di queste premesse regge. Le demo qui mostrano che si può andare piuttosto lontano senza nessuna di esse — usando standard aperti (FHIR R4, lo stesso standard della rete sanitaria nazionale RNDS), modelli aperti (Ollama + Llama 3.2) e infrastruttura aperta (HAPI FHIR, Synthea).

L'obiettivo non è sostituire l'IA clinica commerciale. L'obiettivo è rendere l'opzione local-first una scelta predefinita credibile per educatori e ricercatori.

---

## 📚 Le demo

### `demos/01-fhir-ollama-local`

Pipeline locale completa. Tre container (HAPI FHIR + Synthea + Ollama), uno script Python e un menu interattivo che ti permette di interrogare qualsiasi paziente e conversare con un LLM locale fondato esclusivamente sui suoi dati FHIR. I pazienti curati (Maria, João, Ana) arrivano con note cliniche e infermieristiche scritte a mano; Synthea genera volume aggiuntivo su richiesta.

→ [README della demo](../demos/01-fhir-ollama-local/README.md) · [Documentazione in IT](../demos/01-fhir-ollama-local/docs/README.it.md)

### `demos/02-clinical-ai-tutor`

Un esperimento controllato: stesso modello, stesso paziente, stessa decisione dello studente. Cambia solo il system prompt. **Modalità Risposta** consegna la risposta; lo studente copia. **Modalità Tutor** pone domande socratiche; lo studente pensa. Costruito attorno a un caso reale di terapia intensiva (Paziente JS, ICC scompensata, MAP 63, lattato 3.6) dove la risposta intuitiva dello studente è potenzialmente non sicura.

→ [README della demo](../demos/02-clinical-ai-tutor/README.md) · [Documentazione in IT](../demos/02-clinical-ai-tutor/docs/README_IT.md)

### `demos/03-everything-fhir`

Dimostra l'operazione `$everything` di FHIR: una singola chiamata REST restituisce l'intera cartella clinica del paziente come Bundle. La demo analizza quel Bundle in contesto strutturato e lo passa a un LLM locale, sostituendo il pattern multi-chiamata della demo 01 con un recupero one-shot. Include uno script ausiliario per creare un paziente di test (JS — ICC scompensata) nel caso non ne abbia ancora uno.

→ [README della demo](../demos/03-everything-fhir/README.md) · [Documentazione in IT](../demos/03-everything-fhir/docs/README.it.md)

---

## 🛠️ Panoramica dello stack

| Componente | Ruolo | Licenza | Perché |
|------------|-------|---------|--------|
| [HAPI FHIR](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) | Server FHIR R4 | Apache 2.0 | Stesso standard della RNDS brasiliana (2,8 miliardi di record). Implementazione di riferimento matura. |
| [Ollama](https://ollama.com) | Runtime locale per LLM | MIT | Binario singolo, API REST su `:11434`, esegue qualsiasi modello GGUF. |
| [llama3.2:3b](https://ollama.com/library/llama3.2) | Modello predefinito | Meta License | ~3 GB di RAM. Veloce su un laptop. Abbastanza buono per le demo di ragionamento clinico. |
| [Synthea](https://synthetichealth.github.io/synthea/) | Generatore di pazienti sintetici | Apache 2.0 | Genera bundle FHIR R4 totalmente sintetici con moduli di malattie realistiche. |
| [Python](https://python.org) 3.10+ | Orchestrazione delle demo | PSF | `requests` per FHIR, `rich` per UI nel terminale. Senza framework. |
| [Podman](https://podman.io) / [Docker](https://docker.com) | Runtime container | Apache 2.0 | Entrambi funzionano con il compose; scegli quello che hai installato. |

---

## ⚡ Avvio rapido

### 1. Clonare e avviare lo stack condiviso

```bash
git clone https://github.com/rogeriorrodrigues/nursia-research-lab.git
cd nursia-research-lab

# Podman (consigliato su macOS / Linux)
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b

# OPPURE Docker
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

Lo stack condiviso espone:
- HAPI FHIR su `http://localhost:8082/fhir`
- Ollama su `http://localhost:11435` (porta host configurata in `docker-compose.yml`)

### 2. Eseguire qualsiasi demo

```bash
# Demo 01 — esploratore interattivo paginato dei pazienti
cd demos/01-fhir-ollama-local
python3 fhir_ollama_demo.py

# Demo 02 — modalità Risposta vs. modalità Tutor
cd demos/02-clinical-ai-tutor
pip install requests rich
python3 demo_tutor_vs_resposta_lite.py

# Demo 03 — $everything in un'unica chiamata
cd demos/03-everything-fhir
pip install -r requirements.txt
python3 criar_paciente_teste.py        # crea un paziente di test se non ne hai
python3 demo_everything_fhir.py <patient_id>
```

### 3. Note per macOS

Podman richiede una VM Linux su macOS:

```bash
podman machine init     # solo la prima volta
podman machine start
```

Se preferisci Docker Desktop, usa semplicemente l'opzione Docker sopra.

---

## 🔬 Contesto della ricerca

Questo repository è un artefatto pubblico della ricerca di master all'UFSC. I crediti vanno oltre l'autore:

| Ruolo | Persona / Istituzione |
|-------|------------------------|
| **Ricercatore** | Rogério Rodrigues — studente di master in Informatica Sanitaria, PPGINFOS/UFSC |
| **Relatrice** | Profa. Dra. Grace Marcon Dal Sasso — riferimento nazionale in informatica sanitaria, dirige il macroprogetto FAPESC |
| **Co-ricercatrice** | Brunna Cardozo — infermiera, responsabile della metodologia clinica e pedagogica |
| **Partner pedagogico** | ESEP Porto + VirtualCare — creatori della piattaforma **E4 Nursing**, base pedagogica di NursIA |
| **Finanziamento** | Macroprogetto FAPESC (Fondazione di Sostegno alla Ricerca e Innovazione dello Stato di Santa Catarina) |
| **Programma** | [PPGINFOS — Programma di Specializzazione in Informatica Sanitaria, UFSC](https://ppginfos.ufsc.br) |

Il macroprogetto si concentra sulla simulazione clinica per la formazione di studenti e professionisti sanitari con un forte vincolo di privacy-by-design: i dati reali degli studenti e qualsiasi dato reale dei pazienti in futuro devono rimanere all'interno dell'istituzione. Quel vincolo è ciò che modella ogni scelta tecnica in queste demo.

---

## 🗺️ Roadmap

Vedi [`../roadmap.md`](../roadmap.md) per la roadmap consolidata. Temi di alto livello:

- ✅ **Pipeline locale di base** (demo 01) — fatto.
- ✅ **Cambio di modalità pedagogica** (demo 02) — fatto.
- ✅ **Recupero tramite `$everything`** (demo 03) — fatto.
- 🛠️ **Valutazione della qualità** con [RAGAS](https://github.com/explodinggradients/ragas) — in corso.
- 🛠️ **Validazione** con studenti e professori dell'UFSC — in corso.
- 🔮 **Strato di anonimizzazione** con [Microsoft Presidio](https://microsoft.github.io/presidio/) — pianificato per quando entreranno dati reali nella pipeline.
- 🔮 **Server MCP** per accesso standardizzato IA–FHIR — pianificato.
- 🔮 **Scenari di simulazione clinica** per studenti e professionisti sanitari (Protocollo NursIA) — pianificato.
- 📅 **MIE 2026** — presentazione a Genova, maggio 2026.

---

## 📜 Licenza

[MIT](../LICENSE) — Rogério Rodrigues, 2026.

---

<div align="center">

[← Torna al README principale](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇪🇸 Español](README.es.md)

</div>
