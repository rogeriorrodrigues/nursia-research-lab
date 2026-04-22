"""
Clinical AI Tutor Demo — Versão Lite (sem LangChain)
=====================================================

Versão leve que usa apenas requests + rich.
Chama a API do Ollama diretamente via HTTP, sem dependência de LangChain.

Requisitos:
    pip install requests rich

Uso:
    1. Instale e inicie o Ollama: ollama serve
    2. Baixe o modelo: ollama pull llama3
    3. Execute: python demo_tutor_vs_resposta_lite.py

Autor: Rogério Rodrigues — Mestrado UFSC / Informática em Saúde
"""

import sys

import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONFIGURAÇÃO                                                   ║
# ╚══════════════════════════════════════════════════════════════════╝

OLLAMA_URL = "http://localhost:11434"
MODELO = "llama3.2"
TIMEOUT = 120  # segundos — modelos locais podem demorar em hardware modesto

console = Console(width=100)

# ╔══════════════════════════════════════════════════════════════════╗
# ║  SYSTEM PROMPTS — a única variável entre os dois modos          ║
# ╚══════════════════════════════════════════════════════════════════╝

# Prompt do modo resposta: IA genérica que analisa e DÁ a conduta correta
PROMPT_RESPOSTA = (
    "Você é um assistente clínico de IA. Analise os dados clínicos do paciente "
    "e a decisão tomada. Forneça sua análise completa e recomende a conduta correta. "
    "Responda de forma direta e objetiva. "
    "Responda em português do Brasil. Limite sua resposta a no máximo 200 palavras."
)

# Prompt do modo tutor: IA educacional que NUNCA dá a resposta
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

# Mensagem completa enviada ao modelo (cenário + decisão)
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
    except requests.ConnectionError:
        console.print(Panel(
            "[bold]Não foi possível conectar ao Ollama.[/bold]\n\n"
            "1. Instale: https://ollama.com\n"
            "2. Inicie: [cyan]ollama serve[/cyan]\n"
            f"3. Baixe o modelo: [cyan]ollama pull {MODELO}[/cyan]",
            title="⚠ Ollama não encontrado",
            border_style="red",
        ))
        sys.exit(1)
    except requests.Timeout:
        console.print("[red]⚠ Ollama demorou para responder. Tente novamente.[/red]")
        sys.exit(1)


def consultar_llm(system_prompt: str) -> str:
    """
    Chama a API do Ollama diretamente via POST /api/chat.
    Usa stream=False para receber a resposta completa de uma vez.
    """
    # Monta o payload no formato esperado pela API do Ollama
    payload = {
        "model": MODELO,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": MENSAGEM_USUARIO},
        ],
        "stream": False,  # resposta completa (não streaming)
        "options": {
            "temperature": 0.3,  # baixa para respostas mais consistentes
        },
    }

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        dados = resp.json()
        return dados["message"]["content"]

    except requests.ConnectionError:
        console.print("[red]⚠ Conexão perdida com o Ollama durante a consulta.[/red]")
        sys.exit(1)
    except requests.Timeout:
        console.print(
            f"[red]⚠ Timeout ({TIMEOUT}s). O modelo pode ser grande demais "
            "para o hardware disponível.[/red]"
        )
        sys.exit(1)


def salvar_output(texto_resposta: str, texto_tutor: str):
    """Salva o resultado completo em arquivo texto para screenshot."""
    with open("output_demo.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CLINICAL AI TUTOR DEMO (Lite) — Resultado\n")
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
    console.print("[dim]Resultado salvo em: output_demo.txt[/dim]\n")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  EXECUÇÃO PRINCIPAL                                             ║
# ╚══════════════════════════════════════════════════════════════════╝

def main():
    console.print()
    console.print(Panel(
        "[bold]Clinical AI Tutor Demo[/bold] [dim](Lite — sem LangChain)[/dim]\n"
        "Mesmo modelo · Mesmo paciente · Prompt diferente",
        border_style="cyan",
    ))
    console.print()

    # 1. Testa conexão com Ollama
    testar_conexao_ollama()

    # 2. Executa MODO RESPOSTA — IA analisa e dá a conduta correta
    console.print("[bold yellow]⏳ Consultando MODO RESPOSTA...[/bold yellow]")
    texto_resposta = consultar_llm(PROMPT_RESPOSTA)

    console.print(Panel(
        Markdown(texto_resposta),
        title="❌ MODO RESPOSTA — IA genérica (dá a resposta)",
        border_style="red",
        padding=(1, 2),
    ))
    console.print()

    # 3. Executa MODO TUTOR — IA faz perguntas que forçam o raciocínio
    console.print("[bold yellow]⏳ Consultando MODO TUTOR...[/bold yellow]")
    texto_tutor = consultar_llm(PROMPT_TUTOR)

    console.print(Panel(
        Markdown(texto_tutor),
        title="✅ MODO TUTOR — IA educacional (faz perguntas)",
        border_style="green",
        padding=(1, 2),
    ))
    console.print()

    # 4. Insight final — destaca que a diferença é apenas o prompt
    console.print(Panel(
        "[bold]💡 Mesmo modelo. Mesmo paciente. Prompt diferente.[/bold]\n\n"
        "O system prompt transforma o modelo de 'respondedor' em 'educador'.\n"
        "Essa é a base do AI Tutor: o prompt define o comportamento pedagógico.",
        title="INSIGHT",
        border_style="yellow",
        padding=(1, 2),
    ))

    # 5. Salva output em arquivo texto para screenshot/documentação
    salvar_output(texto_resposta, texto_tutor)


if __name__ == "__main__":
    main()
