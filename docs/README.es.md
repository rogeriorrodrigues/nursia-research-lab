<div align="center">

# 🧪 NursIA Research Lab — Documentación completa

### 🇪🇸 Español

[← Volver al README principal](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇮🇹 Italiano](README.it.md)

</div>

---

## 📋 Índice

- [Sobre el proyecto](#-sobre-el-proyecto)
- [Por qué existe](#-por-que-existe)
- [Las tres demos](#-las-tres-demos)
- [Visión general del stack](#-vision-general-del-stack)
- [Inicio rápido](#-inicio-rapido)
- [Contexto de investigación](#-contexto-de-investigacion)
- [Hoja de ruta](#-hoja-de-ruta)
- [Licencia](#-licencia)

---

## 🏥 Sobre el proyecto

**NursIA** es una plataforma de simulación clínica con IA construida como parte de mi maestría en Informática de la Salud en la UFSC (Universidade Federal de Santa Catarina), dentro del programa [PPGINFOS](https://ppginfos.ufsc.br) — Florianópolis, Brasil.

La investigación examina cómo los modelos de lenguaje locales, los pacientes sintéticos basados en FHIR y la ingeniería de prompts pueden apoyar la formación en enfermería sin enviar nunca datos de pacientes a la nube. Todo se ejecuta sin conexión. Nada se filtra. El cumplimiento de LGPD/GDPR es un efecto secundario de la arquitectura, no una capa adicional añadida después.

Este monorepo reúne tres demostraciones públicas de esa investigación. Cada demo es lo suficientemente pequeña como para leerse de una sentada, se ejecuta localmente en un portátil y aísla una pregunta específica sobre IA clínica.

---

## 🎯 Por qué existe

La mayoría de las herramientas de IA clínica asumen que:
1. Vas a enviar datos de pacientes a una API en la nube.
2. Puedes pagar el coste por token.
3. Tu institución ha firmado un DPA con el proveedor.
4. Confías en los datos de entrenamiento, la política de retención y la disponibilidad del proveedor.

En la sanidad pública brasileña y en la investigación académica, ninguna de esas premisas se sostiene. Las demos aquí muestran que se puede llegar bastante lejos sin ninguna de ellas — usando estándares abiertos (FHIR R4, el mismo estándar de la red nacional de salud RNDS), modelos abiertos (Ollama + Llama 3.2) e infraestructura abierta (HAPI FHIR, Synthea).

El objetivo no es reemplazar la IA clínica comercial. El objetivo es convertir la opción local-first en una elección por defecto creíble para educadores e investigadores.

---

## 📚 Las tres demos

### `demos/01-fhir-ollama-local`

Pipeline local completo. Tres contenedores (HAPI FHIR + Synthea + Ollama), un script Python y un menú interactivo que te permite consultar a cualquier paciente y conversar con un LLM local fundamentado exclusivamente en sus datos FHIR. Los pacientes curados (Maria, João, Ana) vienen con notas clínicas y de enfermería escritas a mano; Synthea genera volumen adicional bajo demanda.

→ [README de la demo](../demos/01-fhir-ollama-local/README.md) · [Documentación en ES](../demos/01-fhir-ollama-local/docs/README.es.md)

### `demos/02-clinical-ai-tutor`

Un experimento controlado: el mismo modelo, el mismo paciente, la misma decisión del estudiante. Solo cambia el system prompt. **Modo Respuesta** entrega la respuesta; el estudiante copia. **Modo Tutor** hace preguntas socráticas; el estudiante piensa. Construido en torno a un caso real de UCI (Paciente JS, ICC descompensada, MAP 63, lactato 3.6) donde la respuesta intuitiva del estudiante es potencialmente insegura.

→ [README de la demo](../demos/02-clinical-ai-tutor/README.md) · [Documentación en ES](../demos/02-clinical-ai-tutor/docs/README_ES.md)

### `demos/03-everything-fhir`

Demuestra la operación `$everything` de FHIR: una sola llamada REST devuelve el historial clínico completo del paciente como un Bundle. La demo analiza ese Bundle en contexto estructurado y lo alimenta a un LLM local, reemplazando el patrón de múltiples llamadas de la demo 01 por una recuperación one-shot. Incluye un script auxiliar para crear un paciente de prueba (JS — ICC descompensada) en caso de que aún no tengas ninguno.

→ [README de la demo](../demos/03-everything-fhir/README.md) · [Documentación en ES](../demos/03-everything-fhir/docs/README.es.md)

---

## 🛠️ Visión general del stack

| Componente | Función | Licencia | Por qué |
|------------|---------|----------|---------|
| [HAPI FHIR](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) | Servidor FHIR R4 | Apache 2.0 | Mismo estándar que la RNDS de Brasil (2,8 mil millones de registros). Implementación de referencia madura. |
| [Ollama](https://ollama.com) | Runtime local de LLM | MIT | Binario único, API REST en `:11434`, ejecuta cualquier modelo GGUF. |
| [llama3.2:3b](https://ollama.com/library/llama3.2) | Modelo por defecto | Meta License | ~3 GB de RAM. Rápido en un portátil. Suficientemente bueno para las demos de razonamiento clínico. |
| [Synthea](https://synthetichealth.github.io/synthea/) | Generador de pacientes sintéticos | Apache 2.0 | Genera bundles FHIR R4 totalmente sintéticos con módulos de enfermedades realistas. |
| [Python](https://python.org) 3.10+ | Orquestación de las demos | PSF | `requests` para FHIR, `rich` para UI en terminal. Sin frameworks. |
| [Podman](https://podman.io) / [Docker](https://docker.com) | Runtime de contenedor | Apache 2.0 | Ambos funcionan con el compose; elige el que tengas instalado. |

---

## ⚡ Inicio rápido

### 1. Clonar y arrancar el stack compartido

```bash
git clone https://github.com/rogeriorrodrigues/nursia-research-lab.git
cd nursia-research-lab

# Podman (recomendado en macOS / Linux)
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b

# O Docker
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

El stack compartido expone:
- HAPI FHIR en `http://localhost:8082/fhir`
- Ollama en `http://localhost:11435` (puerto del host configurado en `docker-compose.yml`)

### 2. Ejecutar cualquier demo

```bash
# Demo 01 — explorador interactivo paginado de pacientes
cd demos/01-fhir-ollama-local
python3 fhir_ollama_demo.py

# Demo 02 — modo Respuesta vs. modo Tutor
cd demos/02-clinical-ai-tutor
pip install requests rich
python3 demo_tutor_vs_resposta_lite.py

# Demo 03 — $everything en una sola llamada
cd demos/03-everything-fhir
pip install -r requirements.txt
python3 criar_paciente_teste.py        # crea un paciente de prueba si no tienes ninguno
python3 demo_everything_fhir.py <patient_id>
```

### 3. Notas para macOS

Podman necesita una VM Linux en macOS:

```bash
podman machine init     # solo la primera vez
podman machine start
```

Si prefieres Docker Desktop, simplemente usa la opción Docker de arriba.

---

## 🔬 Contexto de investigación

Este repositorio es un artefacto público de la investigación de maestría en la UFSC. Los créditos van más allá del autor:

| Rol | Persona / Institución |
|-----|------------------------|
| **Investigador** | Rogério Rodrigues — estudiante de maestría en Informática de la Salud, PPGINFOS/UFSC |
| **Directora** | Profa. Dra. Grace Marcon Dal Sasso — referencia nacional en informática de la salud, lidera el macroproyecto FAPESC |
| **Co-investigadora** | Brunna Cardozo — enfermera, responsable de la metodología clínica y pedagógica |
| **Socio pedagógico** | ESEP Porto + VirtualCare — creadores de la plataforma **E4 Nursing**, base pedagógica de NursIA |
| **Financiación** | Macroproyecto FAPESC (Fundación de Apoyo a la Investigación e Innovación del Estado de Santa Catarina) |
| **Programa** | [PPGINFOS — Programa de Postgrado en Informática de la Salud, UFSC](https://ppginfos.ufsc.br) |

El macroproyecto se centra en la simulación clínica para la formación en enfermería con una fuerte restricción de privacy-by-design: los datos reales de los estudiantes y cualquier dato real de pacientes en el futuro deben permanecer dentro de la institución. Esa restricción es la que da forma a cada elección técnica en estas demos.

---

## 🗺️ Hoja de ruta

Consulta [`../roadmap.md`](../roadmap.md) para la hoja de ruta consolidada. Temas de alto nivel:

- ✅ **Pipeline local básico** (demo 01) — hecho.
- ✅ **Cambio de modo pedagógico** (demo 02) — hecho.
- ✅ **Recuperación vía `$everything`** (demo 03) — hecho.
- 🛠️ **Evaluación de calidad** con [RAGAS](https://github.com/explodinggradients/ragas) — en curso.
- 🛠️ **Validación** con estudiantes y profesores de la UFSC — en curso.
- 🔮 **Capa de anonimización** con [Microsoft Presidio](https://microsoft.github.io/presidio/) — prevista para cuando entren datos reales en el pipeline.
- 🔮 **Servidor MCP** para acceso estandarizado IA–FHIR — previsto.
- 🔮 **Escenarios de simulación clínica** para estudiantes de enfermería (Protocolo NursIA) — previsto.
- 📅 **MIE 2026** — presentación en Génova, mayo de 2026.

---

## 📜 Licencia

[MIT](../LICENSE) — Rogério Rodrigues, 2026.

---

<div align="center">

[← Volver al README principal](../README.md) · [🇬🇧 English](README.en.md) · [🇧🇷 Português](README.pt.md) · [🇮🇹 Italiano](README.it.md)

</div>
