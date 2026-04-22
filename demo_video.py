"""
Clinical AI Tutor Demo — Versão Interativa para Vídeo
======================================================

Versão otimizada para gravação de vídeo (LinkedIn, YouTube).
Cada etapa avança com ENTER, criando ritmo visual para narração.

Uso:
    python demo_video.py

Autor: Rogério Rodrigues — Mestrado UFSC / Informática em Saúde
"""

import sys
import time

import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.align import Align

# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONFIGURAÇÃO                                                   ║
# ╚══════════════════════════════════════════════════════════════════╝

OLLAMA_URL = "http://localhost:11434"
MODELO = "llama3.2"
TIMEOUT = 120

console = Console(width=100)


def esperar(msg=""):
    """Pausa para o apresentador narrar. ENTER avança."""
    texto = f"[dim]  ↵ ENTER para continuar{f' — {msg}' if msg else ''}[/dim]"
    console.print(texto)
    input()


def limpar():
    """Limpa o terminal para manter o vídeo limpo."""
    console.clear()


# ╔══════════════════════════════════════════════════════════════════╗
# ║  SYSTEM PROMPTS                                                 ║
# ╚══════════════════════════════════════════════════════════════════╝

PROMPT_RESPOSTA = (
    "Você é um assistente clínico de IA. Analise os dados clínicos do paciente "
    "e a decisão tomada. Forneça sua análise completa e recomende a conduta correta. "
    "Responda de forma direta e objetiva. "
    "Responda em português do Brasil. Limite sua resposta a no máximo 200 palavras."
)

PROMPT_TUTOR = (
    "Você é um tutor clínico de enfermagem em UTI. Seu papel é ENSINAR o estudante "
    "a pensar, NÃO dar a resposta.\n"
    "REGRAS ABSOLUTAS:\n"
    "1. NUNCA dê a resposta direta ou a conduta correta.\n"
    "2. NUNCA diga explicitamente se a decisão está certa ou errada.\n"
    "3. Quando a decisão do estudante for potencialmente insegura, faça 2-3 perguntas "
    "que o forcem a reconsiderar usando os dados clínicos disponíveis.\n"
    "4. Cada pergunta deve direcionar o raciocínio para um dado clínico específico "
    "que o estudante não considerou.\n"
    "5. Use linguagem de professor: 'o que acontece quando...', 'você considerou que...', "
    "'olhando para o valor de...'.\n"
    "6. Se a decisão for segura, valide brevemente e avance para o próximo desafio clínico.\n"
    "Responda em português do Brasil. Limite sua resposta a no máximo 200 palavras."
)

CENARIO_CLINICO = """
CASO CLÍNICO — Paciente JS

Paciente JS, 68 anos, masculino.
Diagnóstico: ICC descompensada, internado em UTI.

SINAIS VITAIS:
- PA: 84x52 mmHg (PAM: 63 mmHg)
- FC: 118 bpm
- SatO2: 94% (FiO2 60%)
- Temperatura: 37.7°C
- Lactato: 3.6 mmol/L
- Débito urinário: 20 ml/h

VENTILAÇÃO MECÂNICA:
- Modo: PCV
- Pinsp: 24 cmH2O
- PEEP: 10 cmH2O
- FR: 20 irpm
- FiO2: 60%

EXAME FÍSICO:
- MV reduzido bilateral com estertores
- Ritmo de galope
- Pulso filiforme
- Extremidades frias e cianóticas
- Jugulares distendidas
- Edema +++/4 em MMII

DROGAS VASOATIVAS:
- Noradrenalina: 0.3 mcg/kg/min
- Vasopressina: 0.04 U/min

GASOMETRIA ARTERIAL:
- pH: 7.28, pCO2: 48, pO2: 62, HCO3: 19, BE: -7

LABORATÓRIO:
- Creatinina: 2.1, Ureia: 84, BNP: 1860, Troponina: 56
- PCR: 14.5, Procalcitonina: 2.3
"""

DECISAO_ESTUDANTE = """
DECISÃO DO ESTUDANTE:

Avaliei que a SatO2 de 94% com FiO2 de 60% é insuficiente e decidi
aumentar a PEEP de 10 para 14 cmH2O.

Justificativa: "A saturação está baixa com FiO2 alta. Aumentar PEEP
recruta alvéolos e melhora a troca gasosa."
"""

MENSAGEM_USUARIO = CENARIO_CLINICO + DECISAO_ESTUDANTE


# ╔══════════════════════════════════════════════════════════════════╗
# ║  FUNÇÕES                                                        ║
# ╚══════════════════════════════════════════════════════════════════╝

def testar_conexao():
    try:
        resp = requests.get(OLLAMA_URL, timeout=5)
        resp.raise_for_status()
        return True
    except Exception:
        console.print(Panel(
            "[bold]Ollama não encontrado.[/bold]\n\n"
            f"1. [cyan]ollama serve[/cyan]\n"
            f"2. [cyan]ollama pull {MODELO}[/cyan]",
            title="⚠ Erro",
            border_style="red",
        ))
        return False


def consultar_llm(system_prompt: str) -> str:
    payload = {
        "model": MODELO,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": MENSAGEM_USUARIO},
        ],
        "stream": False,
        "options": {"temperature": 0.3},
    }
    resp = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def mostrar_spinner(label: str) -> str:
    """Mostra spinner enquanto o LLM processa — bom para vídeo."""
    with console.status(f"[bold yellow]{label}[/bold yellow]", spinner="dots"):
        if "RESPOSTA" in label:
            return consultar_llm(PROMPT_RESPOSTA)
        else:
            return consultar_llm(PROMPT_TUTOR)


# ╔══════════════════════════════════════════════════════════════════╗
# ║  TELAS DO VÍDEO — cada função é uma "cena"                     ║
# ╚══════════════════════════════════════════════════════════════════╝

def cena_titulo():
    """Cena 1: Título do projeto."""
    limpar()
    console.print()
    console.print()
    console.print(Align.center(Text("🏥  CLINICAL AI TUTOR DEMO", style="bold cyan")))
    console.print()
    console.print(Align.center(Text("Modo Resposta  vs  Modo Tutor", style="bold white")))
    console.print()
    console.print(Align.center(Text("Mesmo modelo  ·  Mesmo paciente  ·  Prompt diferente", style="dim")))
    console.print()
    console.print(Align.center(Text("Rogério Rodrigues — Mestrado UFSC / Informática em Saúde", style="dim italic")))
    console.print()
    esperar("apresentar o cenário clínico")


def cena_cenario():
    """Cena 2: Apresenta o paciente."""
    limpar()
    # Dados vitais em tabela visual
    tabela = Table(title="Paciente JS — 68 anos — ICC descompensada — UTI", border_style="cyan", show_header=True)
    tabela.add_column("Categoria", style="bold cyan", width=22)
    tabela.add_column("Dados", style="white")

    tabela.add_row("Sinais Vitais",     "PA 84×52 (PAM 63)  ·  FC 118  ·  SatO₂ 94% (FiO₂ 60%)  ·  Temp 37.7°C")
    tabela.add_row("Perfusão",          "Lactato [bold red]3.6[/bold red] mmol/L  ·  Diurese [bold red]20[/bold red] ml/h")
    tabela.add_row("Ventilação",        "PCV  ·  Pinsp 24  ·  PEEP 10  ·  FR 20  ·  FiO₂ 60%")
    tabela.add_row("Exame Físico",      "Estertores · Galope · Pulso filiforme · Jugulares distendidas")
    tabela.add_row("Vasopressores",     "Noradrenalina 0.3 mcg/kg/min + Vasopressina 0.04 U/min")
    tabela.add_row("Gasometria",        "pH 7.28 · pCO₂ 48 · pO₂ 62 · HCO₃ 19 · BE −7")
    tabela.add_row("Laboratório",       "Cr 2.1 · BNP [bold red]1860[/bold red] · Trop 56 · PCT 2.3")

    console.print()
    console.print(tabela)
    console.print()
    esperar("mostrar a decisão do estudante")


def cena_decisao():
    """Cena 3: Mostra o que o estudante decidiu."""
    console.print(Panel(
        "[bold yellow]O estudante decidiu:[/bold yellow]\n\n"
        '  "A SatO₂ de 94% com FiO₂ 60% é insuficiente.\n'
        '   Vou [bold]aumentar a PEEP de 10 → 14 cmH₂O[/bold]\n'
        '   para recrutar alvéolos e melhorar a troca gasosa."\n\n'
        "[dim]Parece razoável... mas será que é seguro neste paciente?[/dim]",
        title="⚠️  DECISÃO DO ESTUDANTE",
        border_style="yellow",
        padding=(1, 2),
    ))
    console.print()
    esperar("consultar o MODO RESPOSTA")


def cena_modo_resposta():
    """Cena 4: Executa e exibe o Modo Resposta."""
    limpar()
    console.print()
    console.print(Align.center(Text("TESTE 1:  MODO RESPOSTA", style="bold red")))
    console.print(Align.center(Text("System prompt: 'Analise e recomende a conduta correta'", style="dim")))
    console.print()

    texto = mostrar_spinner("🔴 Consultando MODO RESPOSTA...")

    console.print(Panel(
        Markdown(texto),
        title="❌ MODO RESPOSTA — IA genérica (dá a resposta)",
        border_style="red",
        padding=(1, 2),
    ))
    console.print()
    esperar("agora consultar o MODO TUTOR")
    return texto


def cena_modo_tutor():
    """Cena 5: Executa e exibe o Modo Tutor."""
    limpar()
    console.print()
    console.print(Align.center(Text("TESTE 2:  MODO TUTOR", style="bold green")))
    console.print(Align.center(Text("System prompt: 'NUNCA dê a resposta — faça perguntas'", style="dim")))
    console.print()

    texto = mostrar_spinner("🟢 Consultando MODO TUTOR...")

    console.print(Panel(
        Markdown(texto),
        title="✅ MODO TUTOR — IA educacional (faz perguntas)",
        border_style="green",
        padding=(1, 2),
    ))
    console.print()
    esperar("ver a comparação final")
    return texto


def cena_comparacao():
    """Cena 6: Comparação lado a lado + insight final."""
    limpar()
    console.print()

    tabela = Table(border_style="white", show_header=True, title="Comparação: Mesmo Modelo, Prompt Diferente")
    tabela.add_column("", width=20, style="bold")
    tabela.add_column("❌ Modo Resposta", style="red", width=35)
    tabela.add_column("✅ Modo Tutor", style="green", width=35)

    tabela.add_row("Instrução",       "Analise e recomende",          "NUNCA dê a resposta")
    tabela.add_row("Comportamento",   "Dá a conduta correta",         "Faz perguntas direcionadas")
    tabela.add_row("O estudante...",  "Copia a resposta",             "Constrói o raciocínio")
    tabela.add_row("Segurança",       "Nenhuma",                      "Força reavaliação")
    tabela.add_row("Modelo LLM",      MODELO,                         MODELO)
    tabela.add_row("Temperatura",     "0.3",                          "0.3")

    console.print(tabela)
    console.print()
    esperar("ver o insight final")


def cena_insight():
    """Cena 7: O insight central — fechamento do vídeo."""
    console.print()
    console.print(Panel(
        "[bold]💡 Mesmo modelo. Mesmo paciente. Prompt diferente.[/bold]\n\n"
        "A IA que [bold red]DÁ[/bold red] a resposta → o estudante [bold red]copia[/bold red].\n"
        "A IA que [bold green]PERGUNTA[/bold green] → o estudante [bold green]pensa[/bold green].\n\n"
        "[dim]O system prompt transforma o modelo de 'respondedor' em 'educador'.\n"
        "Essa é a base do AI Tutor: o prompt define o comportamento pedagógico.[/dim]",
        title="✦  O INSIGHT CENTRAL",
        border_style="yellow",
        padding=(1, 2),
    ))
    console.print()
    console.print(Align.center(Text(
        "Rogério Rodrigues · Mestrado UFSC · Informática em Saúde",
        style="dim italic",
    )))
    console.print(Align.center(Text(
        "linkedin.com/in/introrfrr  ·  @rrodrigues.tech",
        style="dim",
    )))
    console.print()


# ╔══════════════════════════════════════════════════════════════════╗
# ║  EXECUÇÃO                                                       ║
# ╚══════════════════════════════════════════════════════════════════╝

def main():
    if not testar_conexao():
        sys.exit(1)

    # Sequência de cenas — cada ENTER avança
    cena_titulo()
    cena_cenario()
    cena_decisao()
    texto_resposta = cena_modo_resposta()
    texto_tutor = cena_modo_tutor()
    cena_comparacao()
    cena_insight()

    # Salva output
    with open("output_video.txt", "w", encoding="utf-8") as f:
        f.write("MODO RESPOSTA:\n" + texto_resposta + "\n\n")
        f.write("MODO TUTOR:\n" + texto_tutor + "\n")
    console.print("[dim]Salvo em: output_video.txt[/dim]\n")


if __name__ == "__main__":
    main()
