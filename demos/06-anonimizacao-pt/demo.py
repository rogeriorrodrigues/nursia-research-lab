"""
Um anonimizador, cinco textos, cinco áreas.

O mesmo Presidio + presidio-br medido nas 200 notas roda aqui em uma nota
clínica e em textos de RH, atendimento, jurídico e educação. CPF, CNS,
telefone e e-mail são os mesmos em qualquer área; o que muda é o texto
em volta. Todos os textos são sintéticos. Nada sai da máquina.

    python3 demo.py              # com pausas, pra gravar
    python3 demo.py --sem-pausa
"""

import logging
import sys
import time
import warnings

warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)

from presidio_anonymizer import AnonymizerEngine  # noqa: E402

import evaluate  # noqa: E402
from corpus import carregar  # noqa: E402
from run_presidio import criar_analyzer  # noqa: E402

B, D, G, R, Y, C, X = "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[0m"
PAUSA = 0 if "--sem-pausa" in sys.argv else 2.5

OUTRAS_AREAS = [
    ("RH · ficha de admissão",
     "Admissão de Helena Rosa Teixeira, CPF 05652777230, celular (48) 99871-2233, e-mail "
     "helena.rosa@exemplo.com.br, início em 3 de março de 2026. Matrícula 4471, centro de custo 210."),
    ("Atendimento · ticket de suporte",
     "Cliente Luiz Felipe Machado, CPF 240.565.161-03, pede segunda via da fatura. Pedido 20261509887 "
     "aberto em 12/03/2026, contato 3244-1188. Protocolo 66512004471."),
    ("Jurídico · contrato de locação",
     "Locatário Otávio Pereira Cardoso, CPF 68173808392, residente na Rua das Acácias, 123, Trindade, "
     "telefone 48 99123-4567. Vigência a partir de 15/04/2026. Valor mensal R$ 1.850,00, cláusula 7."),
    ("Educação · lista de matrícula",
     "Aluna Ana Beatriz Nogueira, cartão SUS 215515105430006 (vacinação em dia), responsável Marina "
     "Pereira, telefone (11) 98877-6655. Turma 3B, matrícula 2026-0142."),
]


def titulo(texto: str) -> None:
    print(f"\n{B}{C}{'─' * 78}\n{texto}\n{'─' * 78}{X}")
    time.sleep(PAUSA)


def anonimizar(analyzer, texto: str) -> tuple[str, list]:
    resultados = analyzer.analyze(text=texto, language="pt")
    return AnonymizerEngine().anonymize(text=texto, analyzer_results=resultados).text, resultados


def sobreviventes(texto_anonimizado: str, documentos: list[str]) -> list[str]:
    return [d for d in documentos if d in texto_anonimizado]


def mostrar(rotulo: str, anonimizado: str, documentos: list[str]) -> None:
    print(f"\n{D}{rotulo}{X}\n  {anonimizado}")
    vazou = sobreviventes(anonimizado, documentos)
    if vazou:
        print(f"  {R}{B}VAZOU:{X} {R}{', '.join(vazou)}{X}  (documento inteiro, legível, no texto 'anonimizado')")
    else:
        print(f"  {G}{B}OK:{X} {G}nenhum CPF ou CNS sobreviveu{X}")
    time.sleep(PAUSA)


def main() -> None:
    print(f"{B}Demo 06 · quanto dado pessoal cada sistema deixa passar{X}")
    print(f"{D}Presidio 2.2.364 (data-privacy-stack/presidio) + spaCy pt + presidio-br (demo 04). "
          f"Tudo sintético, tudo local.{X}")
    padrao, com_br = criar_analyzer(com_br=False), criar_analyzer(com_br=True)

    titulo("DEMO 1  Saúde: a mesma evolução de enfermagem, dois anonimizadores")
    nota = carregar()[0]
    documentos = [s["texto"] for s in nota["spans"] if s["tipo"] in ("BR_CPF", "BR_CNS")]
    print(f"\n{D}original (nota_001, sintética){X}\n  {nota['texto']}")
    time.sleep(PAUSA)
    mostrar("1. Presidio padrão", anonimizar(padrao, nota["texto"])[0], documentos)
    mostrar("2. Presidio + presidio-br", anonimizar(com_br, nota["texto"])[0], documentos)

    titulo("DEMO 2  Qualquer área: CPF é CPF em RH, suporte, contrato e escola")
    for area, texto in OUTRAS_AREAS:
        print(f"\n{Y}{B}{area}{X}\n  {texto}")
        anonimizado, resultados = anonimizar(com_br, texto)
        docs = [texto[r.start:r.end] for r in resultados if r.entity_type in ("BR_CPF", "BR_CNS")]
        tipos = sorted({r.entity_type for r in resultados})
        mostrar(f"Presidio + presidio-br  ({', '.join(tipos)})", anonimizado, [] if docs else ["(nenhum CPF/CNS achado)"])
    print(f"\n{D}Pedido, protocolo e matrícula ficaram no texto: têm 11 dígitos, mas não fecham o dígito "
          f"verificador. O regex acha o candidato; a conta decide.\nO NER do spaCy pt_core_news_sm erra nome "
          f"(deixou Otávio e Marina, marcou Valor e Turma): é o PESSOA 73,7% da tabela. CPF e CNS não vazam.{X}")
    time.sleep(PAUSA)

    titulo("DEMO 3  Medido nas 200 notas (results/tabela.md)")
    res = evaluate.avaliar_todos(carregar())
    print(evaluate.dados_resultados(res))
    print(f"\n{D}Match estrito de span por tipo. Corpus sintético: cada número aqui é teto, não piso.{X}")


if __name__ == "__main__":
    main()
