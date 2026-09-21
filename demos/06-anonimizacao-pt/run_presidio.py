"""
Sistemas 1 e 2, nas mesmas 200 notas:
  presidio_padrao  Presidio 2.2.364 padrão + spaCy pt_core_news_sm
  presidio_br      o mesmo, mais os reconhecedores BR_CPF e BR_CNS da demo 04

Escreve results/raw/<sistema>.jsonl (spans por nota) e <sistema>.meta.json.

    python3 run_presidio.py
"""

import json
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from ambiente import info_maquina
from corpus import carregar
from demo04 import registrar_reconhecedores_br

RAW = Path(__file__).resolve().parent / "results" / "raw"
MODELO_SPACY = "pt_core_news_sm"
# Entidade do Presidio -> tipo do gold. O que não está aqui é descartado (URL, ORGANIZATION...).
MAPA = {"PERSON": "PESSOA", "BR_CPF": "BR_CPF", "BR_CNS": "BR_CNS", "DATE_TIME": "DATA",
        "PHONE_NUMBER": "TELEFONE", "EMAIL_ADDRESS": "EMAIL", "LOCATION": "ENDERECO"}
SISTEMAS = {"presidio_padrao": False, "presidio_br": True}


def criar_analyzer(com_br: bool) -> AnalyzerEngine:
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "pt", "model_name": MODELO_SPACY}],
    })
    analyzer = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["pt"])
    if com_br:
        registrar_reconhecedores_br(analyzer)
    return analyzer


def analisar(analyzer: AnalyzerEngine, texto: str) -> list[dict]:
    spans = []
    for r in analyzer.analyze(text=texto, language="pt"):
        tipo = MAPA.get(r.entity_type)
        if tipo:
            spans.append({"inicio": r.start, "fim": r.end, "tipo": tipo,
                          "texto": texto[r.start:r.end], "score": round(r.score, 2)})
    return spans


def rodar(sistema: str, notas: list[dict]) -> Path:
    analyzer = criar_analyzer(SISTEMAS[sistema])
    RAW.mkdir(parents=True, exist_ok=True)
    linhas = []
    for nota in notas:
        t0 = time.perf_counter()
        spans = analisar(analyzer, nota["texto"])
        linhas.append({"id": nota["id"], "spans": spans, "tempo_s": round(time.perf_counter() - t0, 4)})
    saida = RAW / f"{sistema}.jsonl"
    saida.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in linhas), encoding="utf-8")
    meta = {
        "sistema": sistema, "reconhecedores_br": SISTEMAS[sistema],
        "presidio_analyzer": version("presidio-analyzer"), "spacy": version("spacy"),
        "modelo_spacy": f"{MODELO_SPACY} {version(MODELO_SPACY)}",
        "tempo_medio_s": round(sum(l["tempo_s"] for l in linhas) / len(linhas), 4),
        "maquina": info_maquina(), "quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (RAW / f"{sistema}.meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return saida


def main() -> None:
    notas = carregar()
    for sistema in SISTEMAS:
        saida = rodar(sistema, notas)
        print(f"{sistema}: {len(notas)} notas -> {saida.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
