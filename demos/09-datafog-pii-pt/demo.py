"""
Demo 09: DataFog 4.9.0 (engine regex) nas 200 notas sintéticas da demo 06.

Mede, por tipo de dado pessoal:
  exato   o span bate (inicio, fim) com o tipo certo
  coberto o span inteiro cai dentro de alguma entidade, de qualquer tipo
  parcial o span encosta numa entidade, mas sobra parte dele fora
  vazou   o texto do dado ainda aparece na nota depois de datafog.redact()

Uso: python3 demo.py   (grava results/)
"""

import json
import os
import time
from collections import Counter
from pathlib import Path

# antes do import: a telemetria do DataFog fica desligada nesta demo
os.environ["DATAFOG_NO_TELEMETRY"] = "1"
os.environ["DO_NOT_TRACK"] = "1"

import datafog  # noqa: E402

AQUI = Path(__file__).parent
TIPOS = ["PESSOA", "BR_CPF", "BR_CNS", "DATA", "TELEFONE", "EMAIL", "ENDERECO"]
DOCUMENTOS = ("BR_CPF", "BR_CNS")
# tipo do DataFog que conta como acerto de tipo para cada tipo do corpus
MAPA = {"DATE": "DATA", "PHONE": "TELEFONE", "EMAIL": "EMAIL"}


def carregar(caminho: Path = AQUI / "data" / "corpus.jsonl") -> list[dict]:
    return [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines()]


def coberto(inicio: int, fim: int, intervalos: list[tuple[int, int]]) -> bool:
    """True se [inicio, fim) está inteiro dentro da união dos intervalos."""
    pos = inicio
    for a, b in sorted(intervalos):
        if b <= pos:
            continue
        if a > pos:
            return False
        pos = b
        if pos >= fim:
            return True
    return pos >= fim


def sobrepoe(a0: int, a1: int, b0: int, b1: int) -> bool:
    return a0 < b1 and b0 < a1


def rodar_nota(texto: str) -> dict:
    t0 = time.perf_counter()
    entidades = datafog.scan(texto).entities
    red = datafog.redact(texto, entities=entidades)
    dt = time.perf_counter() - t0
    return {
        "entidades": [{"tipo": e.type, "inicio": e.start, "fim": e.end, "texto": e.text} for e in entidades],
        "redigido": red.redacted_text,
        "segundos": dt,
    }


def avaliar(notas: list[dict], previsoes: dict[str, dict]) -> dict:
    por_tipo = {t: Counter() for t in TIPOS}
    notas_com_doc = notas_vazadas = 0
    rotulos_em_documento: Counter = Counter()
    distratores = Counter()
    cpf_formato = {k: Counter() for k in ("BR_CPF sem pontuação", "BR_CPF com pontuação")}
    for nota in notas:
        prev = previsoes[nota["id"]]
        ents = prev["entidades"]
        intervalos = [(e["inicio"], e["fim"]) for e in ents]
        exatos = {(e["inicio"], e["fim"], MAPA.get(e["tipo"])) for e in ents}
        vazou_doc = False
        tem_doc = False
        for s in nota["spans"]:
            c = por_tipo[s["tipo"]]
            c["suporte"] += 1
            c["exato"] += (s["inicio"], s["fim"], s["tipo"]) in exatos
            cob = coberto(s["inicio"], s["fim"], intervalos)
            c["coberto"] += cob
            c["parcial"] += (not cob) and any(sobrepoe(a, b, s["inicio"], s["fim"]) for a, b in intervalos)
            vazou = s["texto"] in prev["redigido"]
            c["vazou"] += vazou
            if s["tipo"] == "BR_CPF":
                chave = "BR_CPF sem pontuação" if s["texto"].isdigit() else "BR_CPF com pontuação"
                cpf_formato[chave]["suporte"] += 1
                cpf_formato[chave]["coberto"] += cob
            if s["tipo"] in DOCUMENTOS:
                tem_doc = True
                vazou_doc |= vazou
                for e in ents:
                    if sobrepoe(e["inicio"], e["fim"], s["inicio"], s["fim"]):
                        rotulos_em_documento[f'{s["tipo"]} -> {e["tipo"]}'] += 1
        notas_com_doc += tem_doc
        notas_vazadas += vazou_doc
        for d in nota["distratores"]:
            if any(sobrepoe(e["inicio"], e["fim"], d["inicio"], d["fim"]) for e in ents):
                distratores[d["tipo"]] += 1
    return {
        "por_tipo": {t: dict(c) for t, c in por_tipo.items()},
        "notas_com_doc": notas_com_doc,
        "notas_vazadas": notas_vazadas,
        "cpf_por_formato": {k: dict(c) for k, c in cpf_formato.items()},
        "rotulos_em_documento": dict(rotulos_em_documento),
        "falso_positivo_distratores": dict(distratores),
        "entidades_por_tipo": dict(Counter(e["tipo"] for p in previsoes.values() for e in p["entidades"])),
    }


def tabela(m: dict, tempo_medio: float, versao: str) -> str:
    linhas = [
        f"DataFog {versao}, engine regex, {len(m['por_tipo'])} tipos do corpus, tempo médio {tempo_medio * 1000:.2f} ms por nota",
        "",
        "| Tipo | Suporte | Exato | Coberto | Parcial | Vazou após redact |",
        "|---|---|---|---|---|---|",
    ]
    for t in TIPOS:
        c = m["por_tipo"][t]
        n = c["suporte"]
        f = lambda k: f"{c.get(k, 0)}/{n} ({100 * c.get(k, 0) / n:.1f}%)"  # noqa: E731
        linhas.append(f"| {t} | {n} | {f('exato')} | {f('coberto')} | {f('parcial')} | {f('vazou')} |")
    linhas += [
        "",
        f"Notas com CPF ou CNS: {m['notas_com_doc']}; notas em que algum CPF/CNS ainda aparece depois do redact: {m['notas_vazadas']}",
        f"Entidades achadas por tipo do DataFog: {m['entidades_por_tipo']}",
        f"CPF coberto por formato: {m['cpf_por_formato']}",
        f"Rótulo que o DataFog deu ao que cobriu CPF/CNS: {m['rotulos_em_documento']}",
        f"Falsos positivos em números que não são dado pessoal: {m['falso_positivo_distratores']}",
    ]
    return "\n".join(linhas) + "\n"


def main() -> None:
    notas = carregar()
    previsoes = {n["id"]: rodar_nota(n["texto"]) for n in notas}
    tempo_medio = sum(p["segundos"] for p in previsoes.values()) / len(notas)
    versao = datafog.__version__
    m = avaliar(notas, previsoes)

    res = AQUI / "results"
    res.mkdir(exist_ok=True)
    with (res / "raw.jsonl").open("w", encoding="utf-8") as f:
        for n in notas:
            p = previsoes[n["id"]]
            f.write(json.dumps({"id": n["id"], "entidades": p["entidades"]}, ensure_ascii=False) + "\n")
    (res / "metricas.json").write_text(
        json.dumps({"datafog": versao, "notas": len(notas), "tempo_medio_s": round(tempo_medio, 6), **m},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    texto_tab = tabela(m, tempo_medio, versao)
    (res / "tabela.md").write_text(texto_tab, encoding="utf-8")
    n0 = notas[0]
    (res / "exemplo.txt").write_text(
        f"ORIGINAL\n{n0['texto']}\n\nREDIGIDO\n{previsoes[n0['id']]['redigido']}\n", encoding="utf-8")
    print(texto_tab)


if __name__ == "__main__":
    main()
