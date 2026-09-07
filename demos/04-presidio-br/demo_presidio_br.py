"""
Demo: Presidio + reconhecedores brasileiros (CPF e CNS)
=======================================================
Mede o que o Presidio faz com CPF e CNS em texto clínico em português
antes e depois dos reconhecedores BR_CPF e BR_CNS, e mostra por que o
dígito verificador precisa morar dentro do reconhecedor.

Requisitos:
  - pip install -r requirements.txt
  - python -m spacy download pt_core_news_sm

Uso:
  python demo_presidio_br.py
"""

import io
import sys
from collections import Counter
from contextlib import redirect_stdout

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from corpus import SEED, Amostra, gerar_corpus
from presidio_br import BrCnsRecognizer, BrCpfRecognizer, registrar_reconhecedores_br

# ============================================================
# CONFIGURAÇÃO
# ============================================================

MODELO_SPACY = "pt_core_news_sm"
IDIOMA = "pt"
ARQUIVO_SAIDA = "output_presidio_br.txt"

console = Console(width=100, record=True)


# ============================================================
# 1. MONTAR O ANALYZER EM PORTUGUÊS
# ============================================================

def criar_analyzer() -> AnalyzerEngine:
    """
    AnalyzerEngine padrão do Presidio, só que em português.
    Sem isso o Presidio nem carrega o modelo de NER em pt.
    """
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": IDIOMA, "model_name": MODELO_SPACY}],
    })
    return AnalyzerEngine(
        nlp_engine=provider.create_engine(),
        supported_languages=[IDIOMA],
    )


# ============================================================
# 2. MEDIR: O QUE O PRESIDIO DIZ SOBRE O NÚMERO
# ============================================================

def rotulos_no_span(analyzer: AnalyzerEngine, amostra: Amostra) -> set:
    """Entidades que o analyzer colocou em cima do número da amostra."""
    resultados = analyzer.analyze(text=amostra.texto, language=IDIOMA)
    return {
        r.entity_type
        for r in resultados
        if r.start < amostra.fim and r.end > amostra.inicio
    }


def medir(analyzer: AnalyzerEngine, amostras: list, tipo: str, entidade: str) -> dict:
    """Recall da entidade certa + o que o Presidio chamou o número quando errou."""
    fatia = [a for a in amostras if a.tipo == tipo]
    acertos = 0
    outros = Counter()
    for a in fatia:
        rotulos = rotulos_no_span(analyzer, a)
        if entidade in rotulos:
            acertos += 1
        for r in rotulos - {entidade}:
            outros[r] += 1
    return {"total": len(fatia), "acertos": acertos, "outros": outros}


def contar_falsos_positivos(analyzer: AnalyzerEngine, amostras: list, entidade: str) -> int:
    """Quantos distratores (que NÃO são CPF) foram marcados como CPF."""
    return sum(
        1 for a in amostras
        if a.tipo == "distrator" and entidade in rotulos_no_span(analyzer, a)
    )


# ============================================================
# 3. A CENA: O CPF PASSANDO INTEIRO PELO ANONIMIZADOR
# ============================================================

def anonimizar(analyzer: AnalyzerEngine, texto: str) -> str:
    resultados = analyzer.analyze(text=texto, language=IDIOMA)
    return AnonymizerEngine().anonymize(text=texto, analyzer_results=resultados).text


# ============================================================
# MAIN
# ============================================================

def main():
    amostras = gerar_corpus(n_por_tipo=100, seed=SEED)
    exemplo = next(a for a in amostras if a.tipo == "cpf")

    console.print(Panel.fit(
        f"[bold]Presidio + reconhecedores BR[/bold]\n"
        f"corpus sintético · {len(amostras)} textos · seed {SEED} · spaCy {MODELO_SPACY}",
        border_style="blue",
    ))

    # --- Presidio padrão -------------------------------------------------
    console.rule("[bold]1. Presidio padrão (sem reconhecedor brasileiro)")
    padrao = criar_analyzer()

    console.print("\n[dim]texto de entrada[/dim]")
    console.print(f"  {exemplo.texto}")
    console.print("[dim]depois do anonimizador[/dim]")
    console.print(f"  {anonimizar(padrao, exemplo.texto)}\n")

    cpf_padrao = medir(padrao, amostras, "cpf", "BR_CPF")
    cns_padrao = medir(padrao, amostras, "cns", "BR_CNS")

    # --- Com os reconhecedores -----------------------------------------
    console.rule("[bold]2. Presidio + BR_CPF + BR_CNS (com dígito verificador)")
    com_br = criar_analyzer()
    registrar_reconhecedores_br(com_br, validar=True)

    console.print("\n[dim]mesmo texto, depois do anonimizador[/dim]")
    console.print(f"  {anonimizar(com_br, exemplo.texto)}\n")

    cpf_br = medir(com_br, amostras, "cpf", "BR_CPF")
    cns_br = medir(com_br, amostras, "cns", "BR_CNS")

    # --- Só regex, sem dígito verificador -------------------------------
    console.rule("[bold]3. Falso positivo: 100 números de 11 dígitos que NÃO são CPF")
    so_regex = criar_analyzer()
    registrar_reconhecedores_br(so_regex, validar=False)

    fp_regex = contar_falsos_positivos(so_regex, amostras, "BR_CPF")
    fp_dv = contar_falsos_positivos(com_br, amostras, "BR_CPF")

    # --- Tabela ----------------------------------------------------------
    tabela = Table(title="Resultado", show_lines=True)
    tabela.add_column("Medida")
    tabela.add_column("Presidio padrão", justify="right")
    tabela.add_column("+ BR só regex", justify="right")
    tabela.add_column("+ BR com dígito verificador", justify="right")

    tabela.add_row(
        "Recall BR_CPF (100 CPFs válidos)",
        f"{cpf_padrao['acertos']}/{cpf_padrao['total']}",
        "—",
        f"{cpf_br['acertos']}/{cpf_br['total']}",
    )
    tabela.add_row(
        "Recall BR_CNS (100 CNSs válidos)",
        f"{cns_padrao['acertos']}/{cns_padrao['total']}",
        "—",
        f"{cns_br['acertos']}/{cns_br['total']}",
    )
    tabela.add_row(
        "Falso positivo BR_CPF (100 distratores)",
        "—",
        f"{fp_regex}/100",
        f"{fp_dv}/100",
    )
    console.print(tabela)

    # --- O que o Presidio padrão achou que o número era ------------------
    console.print("\n[bold]O que o Presidio padrão chamou o CPF/CNS quando não achou:[/bold]")
    todos = cpf_padrao["outros"] + cns_padrao["outros"]
    if not todos:
        console.print("  nada: o número passou em branco")
    for rotulo, n in todos.most_common():
        console.print(f"  {rotulo}: {n} de {cpf_padrao['total'] + cns_padrao['total']}")

    console.print("\n[bold]O que o Presidio + BR chamou o CPF/CNS além da entidade certa:[/bold]")
    todos_br = cpf_br["outros"] + cns_br["outros"]
    if not todos_br:
        console.print("  nada")
    for rotulo, n in todos_br.most_common():
        console.print(f"  {rotulo}: {n}")

    console.print(
        "\n[dim]Limite: corpus sintético e limpo. CPF por extenso, CRM e texto com "
        "erro de OCR ficam de fora desta medição.[/dim]"
    )

    console.save_text(ARQUIVO_SAIDA)
    console.print(f"\n[dim]saída salva em {ARQUIVO_SAIDA}[/dim]")


if __name__ == "__main__":
    main()
