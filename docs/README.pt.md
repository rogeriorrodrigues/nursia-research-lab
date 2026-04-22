<div align="center">

# 🧪 NursIA Research Lab — Documentação completa

### 🇧🇷 Português

[← Voltar pro README principal](../README.md) · [🇬🇧 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>

---

## 📋 Índice

- [Sobre o projeto](#-sobre-o-projeto)
- [Por que isso existe](#-por-que-isso-existe)
- [As demos](#-as-demos)
- [Visão geral da stack](#-visao-geral-da-stack)
- [Início rápido](#-inicio-rapido)
- [Contexto da pesquisa](#-contexto-da-pesquisa)
- [Roadmap](#-roadmap)
- [Licença](#-licenca)

---

## 🏥 Sobre o projeto

**NursIA** é uma plataforma de simulação clínica com IA construída como parte do meu mestrado em Informática em Saúde na UFSC (Universidade Federal de Santa Catarina), dentro do programa [PPGINFOS](https://ppginfos.ufsc.br) — Florianópolis, Brasil.

A pesquisa investiga como modelos de linguagem locais, pacientes sintéticos baseados em FHIR e engenharia de prompt podem apoiar a formação de estudantes e profissionais de saúde sem nunca enviar dados de paciente pra cloud. Tudo roda offline. Nada vaza. Conformidade LGPD/GDPR é efeito colateral da arquitetura, não uma camada extra colada por cima.

Este monorepo reúne demonstrações públicas abertas dessa pesquisa. Cada demo é pequena o suficiente pra ser lida numa sentada, roda local num notebook e isola uma pergunta específica sobre IA clínica.

---

## 🎯 Por que isso existe

A maior parte das ferramentas de IA clínica assume que:
1. Você vai mandar dados de paciente pra uma API na cloud.
2. Você consegue pagar o custo por token.
3. Sua instituição assinou um DPA com o fornecedor.
4. Você confia nos dados de treino, política de retenção e disponibilidade do fornecedor.

Na saúde pública brasileira e na pesquisa acadêmica, nenhuma dessas premissas se sustenta. As demos aqui mostram que dá pra ir bastante longe sem nenhuma delas — usando padrões abertos (FHIR R4, o mesmo padrão da RNDS), modelos abertos (Ollama + Llama 3.2) e infraestrutura aberta (HAPI FHIR, Synthea).

O objetivo não é substituir IA clínica comercial. O objetivo é tornar a opção local-first uma escolha padrão crível pra educadores e pesquisadores.

---

## 📚 As demos

### `demos/01-fhir-ollama-local`

Pipeline local completo. Três containers (HAPI FHIR + Synthea + Ollama), um script Python e um menu interativo que deixa você consultar qualquer paciente e conversar com um LLM local fundamentado exclusivamente nos dados FHIR. Pacientes curados (Maria, João, Ana) vêm com evoluções clínicas e de enfermagem escritas à mão; o Synthea gera volume adicional sob demanda.

→ [README da demo](../demos/01-fhir-ollama-local/README.md) · [Documentação em PT](../demos/01-fhir-ollama-local/docs/README.pt.md)

### `demos/02-clinical-ai-tutor`

Um experimento controlado: mesmo modelo, mesmo paciente, mesma decisão do estudante. Só o system prompt muda. **Modo Resposta** entrega a resposta; o estudante copia. **Modo Tutor** faz perguntas socráticas; o estudante pensa. Construído em torno de um caso real de UTI (Paciente JS, ICC descompensada, MAP 63, lactato 3.6) onde a resposta intuitiva do estudante é potencialmente insegura.

→ [README da demo](../demos/02-clinical-ai-tutor/README.md) · [Documentação em PT](../demos/02-clinical-ai-tutor/docs/README_PT.md)

### `demos/03-everything-fhir`

Demonstra a operação `$everything` do FHIR: uma única chamada REST traz o prontuário clínico completo do paciente como um Bundle. A demo parseia esse Bundle pra contexto estruturado e alimenta um LLM local, substituindo o padrão de múltiplas chamadas da demo 01 por uma recuperação one-shot. Inclui um script auxiliar pra criar um paciente de teste (JS — ICC descompensada) caso você ainda não tenha nenhum.

→ [README da demo](../demos/03-everything-fhir/README.md) · [Documentação em PT](../demos/03-everything-fhir/docs/README.pt.md)

---

## 🛠️ Visão geral da stack

| Componente | Função | Licença | Por quê |
|------------|--------|---------|---------|
| [HAPI FHIR](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) | Servidor FHIR R4 | Apache 2.0 | Mesmo padrão da RNDS (2,8 bi de registros). Implementação de referência madura. |
| [Ollama](https://ollama.com) | Runtime local de LLM | MIT | Binário único, API REST em `:11434`, roda qualquer modelo GGUF. |
| [llama3.2:3b](https://ollama.com/library/llama3.2) | Modelo padrão | Meta License | ~3 GB de RAM. Rápido em notebook. Bom o suficiente pras demos de raciocínio clínico. |
| [Synthea](https://synthetichealth.github.io/synthea/) | Gerador de pacientes sintéticos | Apache 2.0 | Gera bundles FHIR R4 totalmente sintéticos com módulos de doenças realistas. |
| [Python](https://python.org) 3.10+ | Orquestração das demos | PSF | `requests` pra FHIR, `rich` pra UI no terminal. Sem frameworks. |
| [Podman](https://podman.io) / [Docker](https://docker.com) | Runtime de container | Apache 2.0 | Os dois funcionam com o compose; escolha o que tiver instalado. |

---

## ⚡ Início rápido

### 1. Clonar e subir a stack compartilhada

```bash
git clone https://github.com/rogeriorrodrigues/nursia-research-lab.git
cd nursia-research-lab

# Podman (recomendado em macOS / Linux)
podman-compose up -d
podman exec -it $(podman ps -q -f name=ollama) ollama pull llama3.2:3b

# OU Docker
docker compose up -d
docker exec -it $(docker ps -q -f name=ollama) ollama pull llama3.2:3b
```

A stack compartilhada expõe:
- HAPI FHIR em `http://localhost:8082/fhir`
- Ollama em `http://localhost:11435` (porta de host configurada no `docker-compose.yml`)

### 2. Rodar qualquer demo

```bash
# Demo 01 — explorador interativo paginado de pacientes
cd demos/01-fhir-ollama-local
python3 fhir_ollama_demo.py

# Demo 02 — modo Resposta vs. modo Tutor
cd demos/02-clinical-ai-tutor
pip install requests rich
python3 demo_tutor_vs_resposta_lite.py

# Demo 03 — $everything em uma chamada
cd demos/03-everything-fhir
pip install -r requirements.txt
python3 criar_paciente_teste.py        # cria um paciente de teste se você não tiver
python3 demo_everything_fhir.py <patient_id>
```

### 3. Notas pra macOS

O Podman precisa de uma VM Linux no macOS:

```bash
podman machine init     # primeira vez
podman machine start
```

Se preferir Docker Desktop, é só usar a opção Docker acima.

---

## 🔬 Contexto da pesquisa

Este repositório é um artefato público do mestrado na UFSC. Os créditos vão além do autor:

| Papel | Pessoa / Instituição |
|-------|----------------------|
| **Pesquisador** | Rogério Rodrigues — mestrando em Informática em Saúde, PPGINFOS/UFSC |
| **Orientadora** | Profa. Dra. Grace Marcon Dal Sasso — referência nacional em informática em saúde, lidera o macroprojeto FAPESC |
| **Co-pesquisadora** | Brunna Cardozo — enfermeira, responsável pela metodologia clínica e pedagógica |
| **Parceira pedagógica** | ESEP Porto + VirtualCare — criadores da plataforma **E4 Nursing**, base pedagógica do NursIA |
| **Financiamento** | Macroprojeto FAPESC (Fundação de Amparo à Pesquisa e Inovação do Estado de Santa Catarina) |
| **Programa** | [PPGINFOS — Programa de Pós-Graduação em Informática em Saúde, UFSC](https://ppginfos.ufsc.br) |

O macroprojeto mira simulação clínica pra formação de estudantes e profissionais de saúde com uma restrição forte de privacy-by-design: dados reais de estudantes e qualquer dado real de paciente no futuro precisam ficar dentro da instituição. Essa restrição é o que molda cada escolha técnica nestas demos.

---

## 🗺️ Roadmap

Veja [`../roadmap.md`](../roadmap.md) pro roadmap consolidado. Temas em alto nível:

- ✅ **Pipeline local básico** (demo 01) — feito.
- ✅ **Mudança de modo pedagógico** (demo 02) — feito.
- ✅ **Recuperação via `$everything`** (demo 03) — feito.
- 🛠️ **Avaliação de qualidade** com [RAGAS](https://github.com/explodinggradients/ragas) — em andamento.
- 🛠️ **Validação** com estudantes e professores da UFSC — em andamento.
- 🔮 **Camada de anonimização** com [Microsoft Presidio](https://microsoft.github.io/presidio/) — planejada pra quando dados reais entrarem no pipeline.
- 🔮 **MCP Server** pra acesso padronizado IA–FHIR — planejado.
- 🔮 **Cenários de simulação clínica** pra estudantes e profissionais de saúde (Protocolo NursIA) — planejado.
- 📅 **MIE 2026** — apresentação em Gênova, maio de 2026.

---

## 📜 Licença

[MIT](../LICENSE) — Rogério Rodrigues, 2026.

---

<div align="center">

[← Voltar pro README principal](../README.md) · [🇬🇧 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇮🇹 Italiano](README.it.md)

</div>
