"""Laudo (DOCX, XLSX ou MD) -> Docling -> tabela -> exames -> um chunk por exame.

PDF fica de fora de propósito: o pipeline de PDF baixa modelos na 1ª conversão.
"""
import json
import re
import sys
import time
from pathlib import Path

from docling.chunking import HierarchicalChunker
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter

AQUI = Path(__file__).parent
FORMATOS = [InputFormat.DOCX, InputFormat.XLSX, InputFormat.MD]
CONVERSOR = DocumentConverter(allowed_formats=FORMATOS)


def numero_br(texto: str) -> float:
    """'7.850' -> 7850.0 · '11,2' -> 11.2 · '**5,8**' -> 5.8"""
    limpo = re.sub(r"[*`\s]", "", texto)
    return float(limpo.replace(".", "").replace(",", "."))


def faixa_br(texto: str) -> tuple[float, float]:
    """'4.000 a 11.000' -> (4000.0, 11000.0)"""
    minimo, maximo = texto.split(" a ")
    return numero_br(minimo), numero_br(maximo)


def ler_exames(doc) -> list[dict]:
    tabela = next(t for t in doc.tables
                  if "Resultado" in t.export_to_dataframe(doc=doc).columns)
    df = tabela.export_to_dataframe(doc=doc)
    exames = []
    for _, linha in df.iterrows():
        valor = numero_br(linha["Resultado"])
        minimo, maximo = faixa_br(linha["Referência"])
        exames.append({
            "exame": linha["Exame"],
            "resultado": valor,
            "resultado_texto": re.sub(r"[*`]", "", linha["Resultado"]),
            "unidade": linha["Unidade"],
            "referencia": linha["Referência"],
            "negrito_no_laudo": linha["Resultado"].startswith("**"),
            "fora": not (minimo <= valor <= maximo),
        })
    return exames


def chunks_por_exame(doc, exames, origem):
    titulo = next((t.text for t in doc.texts if t.label == "section_header"), origem)
    saida = []
    for e in exames:
        alerta = " FORA DA REFERÊNCIA." if e["fora"] else ""
        texto = (f"{titulo}. {e['exame']}: {e['resultado_texto']} {e['unidade']} "
                 f"(referência {e['referencia']}).{alerta}")
        saida.append({"origem": origem, "exame": e["exame"],
                      "fora": e["fora"], "texto": texto})
    return saida


def processar(caminho: Path) -> dict:
    inicio = time.perf_counter()
    doc = CONVERSOR.convert(str(caminho)).document
    exames = ler_exames(doc)
    segundos = time.perf_counter() - inicio
    padrao = list(HierarchicalChunker().chunk(doc))
    return {"origem": caminho.name, "doc": doc, "exames": exames, "segundos": segundos,
            "chunks_padrao": [c.text for c in padrao],
            "chunks": chunks_por_exame(doc, exames, caminho.name)}


def main() -> None:
    resumo, jsonl = [], []
    for nome in ("laudo_sintetico.docx", "laudo_sintetico.xlsx", "laudo_sintetico.md"):
        r = processar(AQUI / "dados" / nome)
        print(f"{nome}: {len(r['exames'])} exames em {r['segundos']:.2f} s")
        for e in r["exames"]:
            marca = "FORA" if e["fora"] else "ok  "
            nota = " (negrito no laudo)" if e["negrito_no_laudo"] else ""
            print(f"  {marca} {e['exame']:<18} {e['resultado_texto']:>6} {e['unidade']}{nota}")
        print(f"  HierarchicalChunker: {len(r['chunks_padrao'])} chunks; "
              f"por exame: {len(r['chunks'])} chunks")
        resumo.append({
            "formato": nome.rsplit(".", 1)[1],
            "segundos": round(r["segundos"], 2),
            "exames": len(r["exames"]),
            "fora": [e["exame"] for e in r["exames"] if e["fora"]],
            "negrito_bate": (None if not any(e["negrito_no_laudo"] for e in r["exames"])
                             else all(e["negrito_no_laudo"] == e["fora"] for e in r["exames"])),
            "chunks_padrao": len(r["chunks_padrao"]),
            "chunks_por_exame": len(r["chunks"]),
        })
        jsonl += r["chunks"]
    saida = AQUI / "results"
    saida.mkdir(exist_ok=True)
    amostras = []
    for nome in ("laudo_sintetico.docx", "laudo_sintetico.xlsx"):
        doc = CONVERSOR.convert(str(AQUI / "dados" / nome)).document
        amostras.append(f"== {nome}: tabela do Docling (export_to_dataframe)\n"
                        f"{doc.tables[0].export_to_dataframe(doc=doc)}\n")
    r = processar(AQUI / "dados" / "laudo_sintetico.docx")
    amostras.append("== laudo_sintetico.docx: HierarchicalChunker")
    amostras += [f"{i}  {t}" for i, t in enumerate(r["chunks_padrao"])]
    (saida / "amostras.txt").write_text("\n".join(amostras) + "\n", encoding="utf-8")
    (saida / "resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (saida / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in jsonl:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print("gravado: results/resumo.json, results/chunks.jsonl, results/amostras.txt")


if __name__ == "__main__":
    sys.exit(main())
