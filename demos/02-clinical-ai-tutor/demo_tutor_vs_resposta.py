"""
Clinical AI Tutor Demo — Versão LangChain
==========================================

Demonstra a diferença entre dois modos de IA em educação clínica:
  - MODO RESPOSTA: IA genérica que DÁ a resposta (conduta correta)
  - MODO TUTOR: IA educacional que NUNCA dá a resposta — faz perguntas

Ambos usam o MESMO modelo LLM, o MESMO cenário clínico, a MESMA decisão.
A única diferença é o system prompt.

Requisitos:
    pip install langchain langchain-ollama rich

Uso:
    1. Instale e inicie o Ollama: ollama serve
    2. Baixe o modelo: ollama pull llama3
    3. Execute: python demo_tutor_vs_resposta.py

Autor: Rogério Rodrigues — Mestrado UFSC / Informática em Saúde
"""

import sys

import requests
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONFIGURAÇÃO                                                   ║
# ╚══════════════════════════════════════════════════════════════════╝

OLLAMA_URL = "http://localhost:11434"
MODELO = "llama3.2"

console = Console(width=100)

# ╔══════════════════════════════════════════════════════════════════╗
# ║  SYSTEM PROMPTS — a única variável entre os dois modos          ║
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

# ╔══════════════════════════════════════════════════════════════════╗
# ║  CENÁRIO CLÍNICO — caso JS (Mestrado UFSC)                     ║
# ╚══════════════════════════════════════════════════════════════════╝

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
- pH: 7.28
- pCO2: 48 mmHg
- pO2: 62 mmHg
- HCO3: 19 mEq/L
- BE: -7

LABORATÓRIO:
- Creatinina: 2.1 mg/dL
- Ureia: 84 mg/dL
- BNP: 1860 pg/mL
- Troponina: 56 ng/L
- PCR: 14.5 mg/L
- Procalcitonina: 2.3 ng/mL
"""

# ╔══════════════════════════════════════════════════════════════════╗
# ║  DECISÃO DO ESTUDANTE — o que será avaliado pelos dois modos    ║
# ╚══════════════════════════════════════════════════════════════════╝

DECISAO_ESTUDANTE = """
DECISÃO DO ESTUDANTE:

Avaliei que a SatO2 de 94% com FiO2 de 60% é insuficiente e decidi
aumentar a PEEP de 10 para 14 cmH2O.

Justificativa: "A saturação está baixa com FiO2 alta. Aumentar PEEP
recruta alvéolos e melhora a troca gasosa."
"""

# Mensagem enviada ao modelo (cenário + decisão)
MENSAGEM_USUARIO = CENARIO_CLINICO + DECISAO_ESTUDANTE


# ╔══════════════════════════════════════════════════════════════════╗
# ║  FUNÇÕES                                                        ║
# ╚══════════════════════════════════════════════════════════════════╝

def testar_conexao_ollama():
    """Verifica se o Ollama está acessível antes de executar a demo."""
    try:
        resp = requests.get(OLLAMA_URL, timeout=5)
        resp.raise_for_status()
        console.print("[green]✓ Ollama conectado com sucesso.[/green]\n")
    except Exception:
        console.print(Panel(
            "[bold]Não foi possível conectar ao Ollama.[/bold]\n\n"
            "1. Instale: https://ollama.com\n"
            "2. Inicie: [cyan]ollama serve[/cyan]\n"
            f"3. Baixe o modelo: [cyan]ollama pull {MODELO}[/cyan]",
            title="⚠ Ollama não encontrado",
            border_style="red",
        ))
        sys.exit(1)


def consultar_llm(system_prompt: str) -> str:
    """Envia o cenário clínico ao LLM com o system prompt especificado."""
    llm = ChatOllama(
        model=MODELO,
        base_url=OLLAMA_URL,
        temperature=0.3,
    )
    mensagens = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=MENSAGEM_USUARIO),
    ]
    resposta = llm.invoke(mensagens)
    return resposta.content


def salvar_output(texto_resposta: str, texto_tutor: str):
    """Salva o resultado completo em arquivo texto para screenshot."""
    with open("output_tutor_vs_resposta.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CLINICAL AI TUTOR DEMO — Resultado\n")
        f.write("=" * 70 + "\n\n")
        f.write("❌ MODO RESPOSTA (IA genérica — dá a resposta)\n")
        f.write("-" * 50 + "\n")
        f.write(texto_resposta + "\n\n")
        f.write("✅ MODO TUTOR (IA educacional — faz perguntas)\n")
        f.write("-" * 50 + "\n")
        f.write(texto_tutor + "\n\n")
        f.write("=" * 70 + "\n")
        f.write("💡 Mesmo modelo. Mesmo paciente. Prompt diferente.\n")
        f.write("   O prompt transforma o modelo de 'respondedor' em 'educador'.\n")
        f.write("=" * 70 + "\n")
    console.print("[dim]Resultado salvo em: output_tutor_vs_resposta.txt[/dim]\n")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  EXECUÇÃO PRINCIPAL                                             ║
# ╚══════════════════════════════════════════════════════════════════╝

def main():
    console.print()
    console.print(Panel(
        "[bold]Clinical AI Tutor Demo[/bold]\n"
        "Mesmo modelo · Mesmo paciente · Prompt diferente",
        border_style="cyan",
    ))
    console.print()

    # 1. Testa conexão com Ollama
    testar_conexao_ollama()

    # 2. Executa MODO RESPOSTA
    console.print("[bold yellow]⏳ Consultando MODO RESPOSTA...[/bold yellow]")
    texto_resposta = consultar_llm(PROMPT_RESPOSTA)

    console.print(Panel(
        Markdown(texto_resposta),
        title="❌ MODO RESPOSTA — IA genérica (dá a resposta)",
        border_style="red",
        padding=(1, 2),
    ))
    console.print()

    # 3. Executa MODO TUTOR
    console.print("[bold yellow]⏳ Consultando MODO TUTOR...[/bold yellow]")
    texto_tutor = consultar_llm(PROMPT_TUTOR)

    console.print(Panel(
        Markdown(texto_tutor),
        title="✅ MODO TUTOR — IA educacional (faz perguntas)",
        border_style="green",
        padding=(1, 2),
    ))
    console.print()

    # 4. Insight final
    console.print(Panel(
        "[bold]💡 Mesmo modelo. Mesmo paciente. Prompt diferente.[/bold]\n\n"
        "O system prompt transforma o modelo de 'respondedor' em 'educador'.\n"
        "Essa é a base do AI Tutor: o prompt define o comportamento pedagógico.",
        title="INSIGHT",
        border_style="yellow",
        padding=(1, 2),
    ))

    # 5. Salva output em arquivo texto
    salvar_output(texto_resposta, texto_tutor)


if __name__ == "__main__":
    main()
