<div align="center">

# 🩺 `$everything` FHIR + LLM — Documentación completa en ES

[← Volver al README de la demo](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇮🇹 Italiano](README.it.md)

</div>

---

## 📋 Índice

- [¿Qué es `$everything`?](#-que-es-everything)
- [Cómo lo usa esta demo](#-como-lo-usa-esta-demo)
- [Arquitectura](#-arquitectura)
- [Requisitos previos](#-requisitos-previos)
- [Paso a paso](#-paso-a-paso)
- [Recorrido por el código](#-recorrido-por-el-codigo)
- [Salida esperada](#-salida-esperada)
- [Por qué `$everything` importa para LLMs](#-por-que-everything-importa-para-llms)
- [Comparación con la demo 01](#-comparacion-con-la-demo-01)
- [Solución de problemas](#-solucion-de-problemas)
- [Próximos pasos](#-proximos-pasos)

---

## 🔎 ¿Qué es `$everything`?

[`Patient/{id}/$everything`](https://www.hl7.org/fhir/operation-patient-everything.html) es una operación estándar definida en la especificación FHIR R4. Una sola petición GET devuelve un **Bundle** que contiene todos los recursos que el servidor conoce sobre ese paciente — demografía, condiciones, observaciones, medicaciones, procedimientos, encuentros, informes diagnósticos, alergias y más.

Es una operación definida por el servidor (no todos los servidores FHIR la exponen), pero HAPI FHIR — el servidor que usamos en la stack compartida — la soporta de fábrica.

> **Por qué existe:** antes de `$everything`, construir un "resumen del paciente" requería docenas de llamadas REST tipadas (`/Condition?patient=`, `/Observation?patient=`, ...). `$everything` es la forma FHIR-nativa de decir "dame el panorama completo de esta persona".

---

## 🎯 Cómo lo usa esta demo

La demo trata `$everything` como una **primitiva de carga de contexto para LLM**. El flujo:

```
GET /Patient/{id}/$everything
       │
       ▼
   Bundle (FHIR R4)
       │
       ▼
   Parse en buckets tipados
   (Patient, Condition, Observation, MedicationRequest, ...)
       │
       ▼
   Formatea como texto estructurado
   (secciones con etiquetas y valores)
       │
       ▼
   POST a Ollama /api/chat
   con system prompt estricto:
   "responde SÓLO en base a estos datos"
       │
       ▼
   Respuesta en Markdown en la terminal
```

El LLM nunca inventa datos. Si la respuesta no está en el Bundle, el prompt le indica que lo diga explícitamente.

---

## 🏗️ Arquitectura

```
┌───────────────────────────────────────────────────────────────┐
│                       TU MÁQUINA                              │
│                                                               │
│  ┌─────────────┐                                              │
│  │  HAPI FHIR  │   GET /Patient/{id}/$everything              │
│  │  puerto 8082│ ◄─────────────────────────────────┐         │
│  │  (FHIR R4)  │                                    │         │
│  └─────────────┘                                    │         │
│         │                                  ┌────────┴──────┐  │
│         │ Bundle                           │  demo_        │  │
│         ▼                                  │  everything_  │  │
│   parse + format                           │  fhir.py      │  │
│         │                                  └────────┬──────┘  │
│         │ contexto estructurado                     │         │
│         │                                            │         │
│         │           POST /api/chat                   │         │
│         └──────────────────────────────────► ┌──────▼──────┐  │
│                                              │   Ollama    │  │
│                                              │ puerto 11435│  │
│                                              │ llama3.2:3b │  │
│                                              └─────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 📦 Requisitos previos

| Requisito | Mínimo | Notas |
|-----------|--------|-------|
| Stack compartida desde la raíz | en ejecución | HAPI FHIR + Ollama vía `docker-compose.yml` |
| Python | 3.10+ | Con `requests` y `rich` (ver `requirements.txt`) |
| Paciente en HAPI FHIR | al menos uno | Usa `criar_paciente_teste.py` si no tienes |

La demo espera:

- `FHIR_URL = http://localhost:8082/fhir`
- `OLLAMA_URL = http://localhost:11435`
- Modelo `llama3.2:3b` ya descargado en Ollama

Estos puertos coinciden con los que el `docker-compose.yml` raíz expone (FHIR `8082:8080`, Ollama `11435:11434`).

---

## 🚀 Paso a paso

### 1. Arrancar la stack compartida (raíz del repo)

```bash
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b
```

O con Docker:

```bash
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

### 2. Instalar dependencias Python

```bash
cd demos/03-everything-fhir
pip install -r requirements.txt
```

### 3. Crear un paciente de prueba (opcional)

Si aún no tienes un paciente, ejecuta:

```bash
python3 criar_paciente_teste.py
```

Esto crea el paciente JS (ICC descompensada) e imprime un Patient ID. Anota el ID.

### 4. Ejecutar la demo

```bash
python3 demo_everything_fhir.py <patient_id>
```

El script imprime la URL `$everything` llamada, un resumen de los recursos recibidos, el contexto estructurado enviado al LLM y la respuesta clínica del LLM.

También escribe `output_everything.txt` para capturas y documentación. El archivo está en `.gitignore`.

---

## 🧠 Recorrido por el código

### `criar_paciente_teste.py`

Crea un paciente de UCI representativo (JS Silva — ICC descompensada) haciendo POST en `/Patient`, `/Condition`, `/Observation` y `/MedicationRequest`. Usa SNOMED CT para los diagnósticos y LOINC para signos vitales/laboratorio. Al final imprime el Patient ID generado.

### `demo_everything_fhir.py`

Cuatro funciones, en orden:

1. **`buscar_historico_completo(patient_id)`** — llama `GET /Patient/{id}/$everything` con `Accept: application/fhir+json`. Maneja `ConnectionError` (HAPI caído) y `HTTPError` (paciente no existe).
2. **`resumir_bundle(bundle)`** — itera sobre `bundle["entry"]` y agrupa los recursos por `resourceType` en un dict con claves `patient`, `conditions`, `observations`, `medications`, `procedures`, `diagnostic_reports`.
3. **`montar_contexto_para_llm(recursos)`** — convierte cada bucket en secciones de texto con etiquetas (`PACIENTE:`, `DIAGNÓSTICOS:`, `OBSERVAÇÕES CLÍNICAS:`, `MEDICAÇÕES:`). Trunca observaciones en 20 para no desbordar la ventana de contexto del modelo.
4. **`perguntar_para_llm(contexto, pergunta)`** — POST a `/api/chat` con system prompt estricto: "responde SÓLO en base a los datos proporcionados; si la información no está, dilo; nunca inventes valores ni diagnósticos". Usa `temperature=0.2` y `num_predict=500`.

La pregunta por defecto está hardcoded:

> _"Qual a situação clínica geral desse paciente? Quais são os pontos de atenção?"_

Para probar otras preguntas, edita la variable `pergunta` en `main()`.

---

## 📺 Salida esperada

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
│ [Razonamiento clínico en Markdown aquí]         │
╰─────────────────────────────────────────────────╯
```

---

## 🔍 Por qué `$everything` importa para LLMs

La mayoría de las demos de "IA + historia clínica" construyen contexto encadenando llamadas FHIR tipadas — una para `Condition`, una para `Observation`, una para `MedicationRequest`, etc. Funciona, pero:

- Es **server-aware**: cada demo necesita conocer la taxonomía de recursos.
- Es **verboso**: 7-10 round-trips por paciente.
- Es **frágil**: olvidar un resourceType elimina silenciosamente datos del contexto del LLM.

`$everything` invierte esto. El servidor decide qué cuenta como "el historial del paciente" y lo devuelve de una vez. El cliente sólo parsea el Bundle. Eso empuja la responsabilidad de "qué incluir" hacia el servidor — que es exactamente donde debe estar en un entorno regulado.

Específicamente para carga de contexto en LLM, `$everything` se alinea bien con arquitecturas **single-prompt, sin tool calling**. Recuperas una vez, formateas una vez y envías al modelo un snapshot autocontenido.

---

## ⚖️ Comparación con la demo 01

| | demo 01 (`fhir-ollama-local`) | demo 03 (`everything-fhir`) |
|---|---|---|
| **Recuperación** | 7+ llamadas REST tipadas por paciente | 1 llamada a `$everything` |
| **Forma del contexto** | Construido a mano por tipo de recurso | Bundle → buckets → secciones |
| **UX** | Menú interactivo paginado | CLI: `python ... <patient_id>` |
| **Mejor para** | Razonamiento clínico exploratorio, sesiones largas | Carga one-shot, posts/screenshots |
| **Tamaño del código** | Mayor (menú, paginación, múltiples endpoints) | Menor (una función por etapa) |

Ambas usan la misma stack compartida y el mismo modelo. Ilustran dos patrones válidos de "FHIR → contexto LLM".

---

## 🔧 Solución de problemas

| Problema | Solución |
|----------|----------|
| `HAPI FHIR não tá respondendo em http://localhost:8082/fhir` | Stack no está corriendo. Desde la raíz del repo: `podman-compose up -d` (o `docker compose up -d`). Espera ~30s para que HAPI esté listo. |
| `Erro HTTP: 404` | El Patient ID no existe. Ejecuta `criar_paciente_teste.py` y usa el ID impreso. |
| `Erro no Ollama` | Modelo no descargado o Ollama no en ejecución. `podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b`. |
| `ModuleNotFoundError: rich` | `pip install -r requirements.txt`. |
| Respuesta del LLM débil / genérica | El Bundle puede estar escaso. Prueba con un paciente generado por Synthea (la demo 01 los genera) en vez del paciente de prueba. |

---

## 🗺️ Próximos pasos

- Probar contra pacientes generados por Synthea con historiales más ricos.
- Añadir un flag CLI para la pregunta (hoy está hardcoded).
- Flag `--save-bundle` para volcar el Bundle crudo como JSON para inspección.
- Comparar calidad de respuesta entre contexto `$everything` y contexto por llamadas tipadas (demo 01).
- Evaluar calidad de respuesta con [RAGAS](https://github.com/explodinggradients/ragas) (objetivo: faithfulness > 0.85).

---

<div align="center">

[← Volver al README de la demo](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇮🇹 Italiano](README.it.md)

</div>
