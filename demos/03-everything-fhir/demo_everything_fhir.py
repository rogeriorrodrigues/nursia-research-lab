"""
Demo: $everything FHIR + LLM
=============================
Mostra como usar o endpoint $everything do FHIR pra puxar
o histórico clínico completo de um paciente numa chamada só,
e passar esse contexto pra um LLM raciocinar.

Requisitos:
  - Ollama rodando no Podman (llama3 ou outro modelo)
  - HAPI FHIR rodando em http://localhost:8082
  - Pelo menos um paciente criado (via Synthea ou manualmente)
  - pip install rich requests

Uso:
  python demo_everything_fhir.py <patient_id>

Exemplo:
  python demo_everything_fhir.py 123
"""

import sys
import json
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

# ============================================================
# CONFIGURAÇÃO
# ============================================================

FHIR_URL = "http://localhost:8082/fhir"
OLLAMA_URL = "http://localhost:11435"
MODELO = "llama3.2:3b"

console = Console(width=100)


# ============================================================
# 1. BUSCAR HISTÓRICO COMPLETO COM $everything
# ============================================================

def buscar_historico_completo(patient_id: str) -> dict:
    """
    Chama o endpoint $everything do FHIR.
    Retorna um Bundle com todos os recursos do paciente:
    Patient, Condition, Observation, MedicationRequest, etc.
    """
    url = f"{FHIR_URL}/Patient/{patient_id}/$everything"

    console.print(f"\n[dim]GET {url}[/dim]")

    try:
        resp = requests.get(
            url,
            headers={"Accept": "application/fhir+json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        console.print(f"[red]HAPI FHIR não tá respondendo em {FHIR_URL}[/red]")
        console.print("[yellow]podman ps | grep hapi[/yellow]")
        sys.exit(1)
    except requests.HTTPError as e:
        console.print(f"[red]Erro HTTP: {e}[/red]")
        console.print(f"[yellow]Paciente {patient_id} existe?[/yellow]")
        sys.exit(1)


# ============================================================
# 2. EXTRAIR INFORMAÇÃO ÚTIL DO BUNDLE
# ============================================================

def resumir_bundle(bundle: dict) -> dict:
    """
    Pega o Bundle FHIR e separa os recursos por tipo.
    Retorna um dict mais fácil de usar no prompt do LLM.
    """
    recursos = {
        "patient": None,
        "conditions": [],
        "observations": [],
        "medications": [],
        "procedures": [],
        "diagnostic_reports": [],
    }

    entries = bundle.get("entry", [])

    for entry in entries:
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if resource_type == "Patient":
            recursos["patient"] = resource
        elif resource_type == "Condition":
            recursos["conditions"].append(resource)
        elif resource_type == "Observation":
            recursos["observations"].append(resource)
        elif resource_type == "MedicationRequest":
            recursos["medications"].append(resource)
        elif resource_type == "Procedure":
            recursos["procedures"].append(resource)
        elif resource_type == "DiagnosticReport":
            recursos["diagnostic_reports"].append(resource)

    return recursos


# ============================================================
# 3. MONTAR CONTEXTO TEXTUAL PRO LLM
# ============================================================

def montar_contexto_para_llm(recursos: dict) -> str:
    """
    Transforma os recursos FHIR em texto estruturado
    que o LLM consegue entender.
    Formato simples: seções com label e conteúdo.
    """
    linhas = []

    # Paciente
    p = recursos.get("patient")
    if p:
        nome = _extrair_nome(p)
        idade = p.get("birthDate", "não informado")
        genero = p.get("gender", "não informado")
        linhas.append(f"PACIENTE: {nome}")
        linhas.append(f"Data de nascimento: {idade}")
        linhas.append(f"Gênero: {genero}")
        linhas.append("")

    # Condições (diagnósticos)
    if recursos["conditions"]:
        linhas.append("DIAGNÓSTICOS:")
        for c in recursos["conditions"]:
            texto = _extrair_texto_codigo(c.get("code", {}))
            linhas.append(f"- {texto}")
        linhas.append("")

    # Observações (exames, sinais vitais)
    if recursos["observations"]:
        linhas.append("OBSERVAÇÕES CLÍNICAS:")
        for o in recursos["observations"][:20]:  # limitar pra não estourar contexto
            texto = _extrair_texto_codigo(o.get("code", {}))
            valor = _extrair_valor(o)
            linhas.append(f"- {texto}: {valor}")
        linhas.append("")

    # Medicações
    if recursos["medications"]:
        linhas.append("MEDICAÇÕES:")
        for m in recursos["medications"]:
            med = m.get("medicationCodeableConcept", {})
            texto = _extrair_texto_codigo(med)
            linhas.append(f"- {texto}")
        linhas.append("")

    return "\n".join(linhas)


def _extrair_nome(patient: dict) -> str:
    nomes = patient.get("name", [])
    if not nomes:
        return "sem nome"
    n = nomes[0]
    given = " ".join(n.get("given", []))
    family = n.get("family", "")
    return f"{given} {family}".strip()


def _extrair_texto_codigo(code: dict) -> str:
    # tenta pegar o texto legível primeiro
    if code.get("text"):
        return code["text"]
    # senão pega o display do primeiro coding
    codings = code.get("coding", [])
    if codings:
        return codings[0].get("display", codings[0].get("code", "sem código"))
    return "desconhecido"


def _extrair_valor(obs: dict) -> str:
    if "valueQuantity" in obs:
        v = obs["valueQuantity"]
        return f"{v.get('value', '?')} {v.get('unit', '')}"
    if "valueString" in obs:
        return obs["valueString"]
    if "valueCodeableConcept" in obs:
        return _extrair_texto_codigo(obs["valueCodeableConcept"])
    return "sem valor"


# ============================================================
# 4. PERGUNTAR PRO LLM COM O CONTEXTO
# ============================================================

def perguntar_para_llm(contexto: str, pergunta: str) -> str:
    """
    Envia o contexto clínico + pergunta pro Ollama.
    O system prompt força a IA a responder APENAS com base
    nos dados fornecidos, evitando alucinação.
    """
    system = (
        "Você é um assistente clínico. Responda APENAS com base "
        "nos dados clínicos fornecidos. Se a informação não estiver "
        "nos dados, diga que não tem essa informação. "
        "Nunca invente valores ou diagnósticos. "
        "Responda em português do Brasil, máximo 250 palavras."
    )

    user = f"""
DADOS CLÍNICOS DO PACIENTE:

{contexto}

PERGUNTA:
{pergunta}
"""

    payload = {
        "model": MODELO,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 500},
    }

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat", json=payload, timeout=120
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
    except Exception as e:
        console.print(f"[red]Erro no Ollama: {e}[/red]")
        sys.exit(1)


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) < 2:
        console.print("[yellow]Uso: python demo_everything_fhir.py <patient_id>[/yellow]")
        console.print("[dim]Exemplo: python demo_everything_fhir.py 123[/dim]")
        sys.exit(1)

    patient_id = sys.argv[1]

    console.print("\n[bold cyan]Demo: $everything FHIR + LLM[/bold cyan]\n")

    # 1. Buscar histórico completo
    console.print("[dim]Chamando $everything...[/dim]")
    bundle = buscar_historico_completo(patient_id)

    total_entries = len(bundle.get("entry", []))
    console.print(f"[green]Bundle recebido: {total_entries} recursos[/green]\n")

    # 2. Resumir o Bundle
    recursos = resumir_bundle(bundle)

    console.print(Panel(
        f"[bold]Paciente:[/bold] {'✓' if recursos['patient'] else '✗'}\n"
        f"[bold]Diagnósticos:[/bold] {len(recursos['conditions'])}\n"
        f"[bold]Observações:[/bold] {len(recursos['observations'])}\n"
        f"[bold]Medicações:[/bold] {len(recursos['medications'])}\n"
        f"[bold]Procedimentos:[/bold] {len(recursos['procedures'])}\n"
        f"[bold]Relatórios:[/bold] {len(recursos['diagnostic_reports'])}",
        title="📦 Bundle FHIR — O que veio no $everything",
        border_style="cyan",
    ))

    # 3. Montar contexto
    contexto = montar_contexto_para_llm(recursos)

    console.print()
    console.print(Panel(
        contexto[:1500] + ("..." if len(contexto) > 1500 else ""),
        title="📝 Contexto estruturado pro LLM",
        border_style="blue",
    ))

    # 4. Perguntar pro LLM
    pergunta = "Qual a situação clínica geral desse paciente? Quais são os pontos de atenção?"

    console.print(f"\n[bold]Pergunta pro LLM:[/bold] {pergunta}")
    console.print("[dim]Gerando resposta...[/dim]\n")

    resposta = perguntar_para_llm(contexto, pergunta)

    console.print(Panel(
        Markdown(resposta),
        title="🤖 Resposta do LLM (baseada APENAS no Bundle)",
        border_style="green",
        padding=(1, 2),
    ))

    # Salvar pra screenshot
    with open("output_everything.txt", "w", encoding="utf-8") as f:
        f.write(f"=== BUNDLE RECEBIDO: {total_entries} recursos ===\n\n")
        f.write(f"=== CONTEXTO ESTRUTURADO ===\n\n{contexto}\n\n")
        f.write(f"=== PERGUNTA ===\n{pergunta}\n\n")
        f.write(f"=== RESPOSTA DO LLM ===\n{resposta}\n")

    console.print("\n[green]Output salvo em output_everything.txt[/green]")
    console.print("[dim]Use esse arquivo pro screenshot do post.[/dim]\n")


if __name__ == "__main__":
    main()
