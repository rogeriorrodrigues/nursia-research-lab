"""
Métrica de span estrito por tipo: (inicio, fim, tipo) tem que bater exato.

Só aritmética, sem I/O, pra testar com casos pequenos à mão.
"""

TIPOS = ["PESSOA", "BR_CPF", "BR_CNS", "DATA", "TELEFONE", "EMAIL", "ENDERECO"]
DOCUMENTOS = ("BR_CPF", "BR_CNS")


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1


def _chaves(spans: list[dict]) -> set[tuple]:
    return {(s["inicio"], s["fim"], s["tipo"]) for s in spans}


def _sobrepoe(a: dict, b: dict) -> bool:
    return a["inicio"] < b["fim"] and b["inicio"] < a["fim"]


def avaliar(notas: list[dict], predicoes: dict[str, list[dict]]) -> dict:
    """
    notas: corpus gold (com 'spans' e 'distratores').
    predicoes: {id da nota: [spans preditos]}. Nota sem predição conta como zero.
    """
    cont = {t: {"tp": 0, "fp": 0, "fn": 0} for t in TIPOS}
    vazadas, com_doc = 0, 0
    fp_distr: dict[str, int] = {}
    for nota in notas:
        preditos = predicoes.get(nota["id"], [])
        gold, pred = _chaves(nota["spans"]), _chaves(preditos)
        for _, _, t in gold & pred:
            cont[t]["tp"] += 1
        for _, _, t in gold - pred:
            cont[t]["fn"] += 1
        for _, _, t in pred - gold:
            if t in cont:
                cont[t]["fp"] += 1
        docs = {k for k in gold if k[2] in DOCUMENTOS}
        if docs:
            com_doc += 1
            vazadas += bool(docs - pred)
        for d in nota["distratores"]:
            if any(_sobrepoe(d, s) for s in preditos):
                fp_distr[d["tipo"]] = fp_distr.get(d["tipo"], 0) + 1

    por_tipo = {}
    for t, c in cont.items():
        p, r, f1 = prf(**c)
        por_tipo[t] = {**c, "suporte": c["tp"] + c["fn"], "precisao": p, "recall": r, "f1": f1}
    tp, fp, fn = (sum(c[k] for c in cont.values()) for k in ("tp", "fp", "fn"))
    p, r, f1 = prf(tp, fp, fn)
    com_suporte = [t for t in TIPOS if por_tipo[t]["suporte"]]
    pior = min(com_suporte, key=lambda t: por_tipo[t]["f1"]) if com_suporte else None
    return {
        "por_tipo": por_tipo,
        "micro": {"tp": tp, "fp": fp, "fn": fn, "precisao": p, "recall": r, "f1": f1},
        "vazamento": {"notas_vazadas": vazadas, "notas_com_doc": com_doc,
                      "taxa": vazadas / com_doc if com_doc else 0.0},
        "fp_distratores": {"total": sum(fp_distr.values()), "por_tipo": fp_distr},
        "pior_entidade": pior,
    }
