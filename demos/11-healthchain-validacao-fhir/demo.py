"""
Demo 11: healthchain 0.16.1, validate_resource() em 240 recursos FHIR sintéticos.

60 válidos e 180 com um defeito conhecido (9 categorias x 20). Pra cada categoria:
quantos o validador reprovou. Nos válidos: quantos reprovou por engano.

Uso: python3 demo.py   (grava results/)
"""

import json
import time
from collections import defaultdict
from importlib.metadata import version
from pathlib import Path

from healthchain.fhir import validate_resource

import gerar_dados

AQUI = Path(__file__).parent


def carregar(caminho: Path = AQUI / "data" / "recursos.jsonl") -> list[dict]:
    return [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines()]


def validar(itens: list[dict]) -> list[dict]:
    saida = []
    for item in itens:
        t0 = time.perf_counter()
        rel = validate_resource(item["recurso"])
        dt = time.perf_counter() - t0
        saida.append({
            "id": item["id"], "categoria": item["categoria"], "valid": rel.valid,
            "issues": [{"code": i.code, "expression": i.expression} for i in rel.issues],
            "segundos": dt,
        })
    return saida


def resumir(resultados: list[dict]) -> dict:
    por_cat: dict[str, dict] = defaultdict(lambda: {"total": 0, "reprovados": 0})
    for r in resultados:
        c = por_cat[r["categoria"]]
        c["total"] += 1
        c["reprovados"] += not r["valid"]
    defeituosos = [r for r in resultados if r["categoria"] != "valido"]
    estruturais = [r for r in defeituosos if gerar_dados.CATEGORIAS[r["categoria"]][1]]
    semanticos = [r for r in defeituosos if not gerar_dados.CATEGORIAS[r["categoria"]][1]]
    return {
        "por_categoria": dict(por_cat),
        "defeitos_total": len(defeituosos),
        "defeitos_reprovados": sum(not r["valid"] for r in defeituosos),
        "estruturais_total": len(estruturais),
        "estruturais_reprovados": sum(not r["valid"] for r in estruturais),
        "semanticos_total": len(semanticos),
        "semanticos_reprovados": sum(not r["valid"] for r in semanticos),
        "validos_total": por_cat["valido"]["total"],
        "validos_reprovados": por_cat["valido"]["reprovados"],
    }


def tabela(m: dict, tempo_medio: float, ver: str) -> str:
    linhas = [
        f"healthchain {ver}, validate_resource(), R4B, tempo médio {tempo_medio * 1000:.2f} ms por recurso",
        "",
        "| Categoria | Natureza | Reprovados |",
        "|---|---|---|",
    ]
    for cat, (desc, estrutural) in gerar_dados.CATEGORIAS.items():
        c = m["por_categoria"][cat]
        natureza = "estrutural" if estrutural else "semântico"
        linhas.append(f"| {desc} | {natureza} | {c['reprovados']}/{c['total']} |")
    v = m["por_categoria"]["valido"]
    linhas += [
        f"| (controle) recurso válido | - | {v['reprovados']}/{v['total']} |",
        "",
        f"Defeitos estruturais reprovados: {m['estruturais_reprovados']}/{m['estruturais_total']}",
        f"Defeitos semânticos reprovados: {m['semanticos_reprovados']}/{m['semanticos_total']}",
        f"Defeitos reprovados no total: {m['defeitos_reprovados']}/{m['defeitos_total']}",
    ]
    return "\n".join(linhas) + "\n"


def main() -> None:
    gerar_dados.main()
    itens = carregar()
    resultados = validar(itens)
    tempo_medio = sum(r["segundos"] for r in resultados) / len(resultados)
    ver = version("healthchain")
    m = resumir(resultados)

    res = AQUI / "results"
    res.mkdir(exist_ok=True)
    (res / "metricas.json").write_text(
        json.dumps({"healthchain": ver, "recursos": len(itens), "tempo_medio_s": round(tempo_medio, 6), **m},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (res / "raw.jsonl").open("w", encoding="utf-8") as f:
        for r in resultados:
            r = {k: v for k, v in r.items() if k != "segundos"}
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    texto = tabela(m, tempo_medio, ver)
    (res / "tabela.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
