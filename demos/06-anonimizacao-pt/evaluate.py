"""
Avalia cada sistema com resultado em results/raw/ contra o gold de data/corpus.jsonl.

Escreve results/tabela.md e results/metricas.csv e imprime o bloco
DADOS DE RESULTADOS. Sistema sem arquivo em results/raw/ aparece como "não rodou".

    python3 evaluate.py
"""

import json
from pathlib import Path

from corpus import carregar
from metricas import TIPOS, avaliar

AQUI = Path(__file__).resolve().parent
RAW, RESULTS = AQUI / "results" / "raw", AQUI / "results"
SISTEMAS = {"presidio_padrao": "Presidio 2.2.364 padrão + spaCy pt",
            "presidio_br": "Presidio 2.2.364 + presidio-br",
            "ollama_qwen": "Ollama (Qwen)", "ollama_phi": "Ollama (Phi)"}


def carregar_sistema(sistema: str, raw: Path = RAW) -> dict | None:
    arq = raw / f"{sistema}.jsonl"
    if not arq.exists():
        return None
    linhas = [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]
    meta_arq = raw / f"{sistema}.meta.json"
    meta = json.loads(meta_arq.read_text(encoding="utf-8")) if meta_arq.exists() else {}
    llm = "parse_ok" in linhas[0] if linhas else False
    return {
        "predicoes": {l["id"]: l["spans"] for l in linhas}, "n_notas": len(linhas),
        "tempo_medio_s": sum(l["tempo_s"] for l in linhas) / len(linhas) if linhas else 0.0,
        "falha_parse": sum(not l["parse_ok"] for l in linhas) / len(linhas) if llm and linhas else None,
        "modelo": meta.get("modelo", {}), "llm": llm,
    }


def avaliar_todos(notas: list[dict], raw: Path = RAW) -> dict[str, dict]:
    saida = {}
    for sistema in SISTEMAS:
        dados = carregar_sistema(sistema, raw)
        if dados:
            saida[sistema] = {**dados, "metricas": avaliar(notas, dados["predicoes"])}
    return saida


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _rotulo(sistema: str, r: dict) -> str:
    m = r["modelo"]
    return f"{SISTEMAS[sistema]} `{m['tag']}` ({m.get('quantizacao')})" if m else SISTEMAS[sistema]


def tabela_md(res: dict[str, dict], n_notas: int) -> str:
    linhas = ["| Sistema | Notas | P | R | F1 micro | Recall CPF | Recall CNS | Vazamento CPF/CNS | FP em distratores | Pior entidade | Tempo/nota | Falha parse |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for sistema in SISTEMAS:
        r = res.get(sistema)
        if not r:
            linhas.append(f"| {SISTEMAS[sistema]} | não rodou | | | | | | | | | | |")
            continue
        m, pt = r["metricas"], r["metricas"]["por_tipo"]
        v = m["vazamento"]
        linhas.append(
            f"| {_rotulo(sistema, r)} | {r['n_notas']}/{n_notas} | {_pct(m['micro']['precisao'])} | {_pct(m['micro']['recall'])} "
            f"| {_pct(m['micro']['f1'])} | {_pct(pt['BR_CPF']['recall'])} | {_pct(pt['BR_CNS']['recall'])} "
            f"| {_pct(v['taxa'])} ({v['notas_vazadas']}/{v['notas_com_doc']}) | {m['fp_distratores']['total']} "
            f"| {m['pior_entidade']} ({_pct(pt[m['pior_entidade']]['f1'])}) | {r['tempo_medio_s']:.2f} s "
            f"| {_pct(r['falha_parse']) if r['falha_parse'] is not None else 'n/a'} |")
    cab = "| Entidade (suporte) | " + " | ".join(SISTEMAS[s] for s in res) + " |"
    por_ent = [cab, "|---|" + "---|" * len(res)]
    for t in TIPOS:
        sup = next(iter(res.values()))["metricas"]["por_tipo"][t]["suporte"] if res else 0
        celulas = [f"P {_pct(r['metricas']['por_tipo'][t]['precisao'])} R {_pct(r['metricas']['por_tipo'][t]['recall'])} "
                   f"F1 {_pct(r['metricas']['por_tipo'][t]['f1'])}" for r in res.values()]
        por_ent.append(f"| {t} ({sup}) | " + " | ".join(celulas) + " |")
    return "## Geral (match estrito de span por tipo)\n\n" + "\n".join(linhas) + \
        "\n\n## Por entidade\n\n" + "\n".join(por_ent) + "\n"


def csv(res: dict[str, dict]) -> str:
    linhas = ["sistema,tipo,suporte,tp,fp,fn,precisao,recall,f1"]
    for sistema, r in res.items():
        for t, c in list(r["metricas"]["por_tipo"].items()) + [("micro", r["metricas"]["micro"])]:
            sup = c.get("suporte", c["tp"] + c["fn"])
            linhas.append(f"{sistema},{t},{sup},{c['tp']},{c['fp']},{c['fn']},{c['precisao']:.4f},{c['recall']:.4f},{c['f1']:.4f}")
    return "\n".join(linhas) + "\n"


def dados_resultados(res: dict[str, dict]) -> str:
    out = ["=" * 60, "DADOS DE RESULTADOS", "=" * 60]
    for sistema in SISTEMAS:
        r = res.get(sistema)
        if not r:
            out.append(f"{SISTEMAS[sistema]}: não rodou (sem results/raw/{sistema}.jsonl)")
            continue
        m, pt = r["metricas"], r["metricas"]["por_tipo"]
        out.append(f"{_rotulo(sistema, r)} [{r['n_notas']} notas]")
        out.append(f"  F1 micro: {_pct(m['micro']['f1'])}  recall CPF: {_pct(pt['BR_CPF']['recall'])}  recall CNS: {_pct(pt['BR_CNS']['recall'])}")
        out.append(f"  vazamento (notas com CPF/CNS não detectado): {_pct(m['vazamento']['taxa'])} "
                   f"({m['vazamento']['notas_vazadas']}/{m['vazamento']['notas_com_doc']})")
        out.append(f"  pior entidade: {m['pior_entidade']} (F1 {_pct(pt[m['pior_entidade']]['f1'])})  "
                   f"FP em distratores: {m['fp_distratores']['total']} {m['fp_distratores']['por_tipo']}")
        if r["llm"]:
            out.append(f"  tempo médio por nota: {r['tempo_medio_s']:.1f} s  falha de parse: {_pct(r['falha_parse'])}")
    return "\n".join(out)


def main() -> None:
    notas = carregar()
    res = avaliar_todos(notas)
    (RESULTS / "tabela.md").write_text(tabela_md(res, len(notas)), encoding="utf-8")
    (RESULTS / "metricas.csv").write_text(csv(res), encoding="utf-8")
    print(tabela_md(res, len(notas)))
    print(dados_resultados(res))


if __name__ == "__main__":
    main()
