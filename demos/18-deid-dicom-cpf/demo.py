"""Demo 18: o deid limpa um DICOM brasileiro? Conta o que sobra depois da receita padrão."""
import copy, json, os, sys, tempfile, time, logging
from importlib.metadata import version
import pydicom
from deid.dicom import replace_identifiers
from deid.config import DeidRecipe
from gera_dicom import gera

AQUI = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(AQUI, "results")


def textos(ds):
    """Todo valor do arquivo como texto, inclusive sequências e tags privadas."""
    out = []
    for el in ds.iterall():
        if el.VR in ("SQ", "OB", "OW", "OF", "UN") and el.tag != 0x7FE00010:
            continue
        if el.tag == 0x7FE00010:
            continue
        out.append((str(el.tag), el.keyword or "privada", str(el.value)))
    return out


def vazamentos(ds, canarios):
    achados = {}
    vals = textos(ds)
    for tipo, lista in canarios.items():
        for tag, kw, v in vals:
            if any(c and c in v for c in lista):
                achados.setdefault(tipo, []).append(kw)
    return achados


def roda(cenario, arquivos, pasta, **kw):
    t0 = time.perf_counter()
    caminhos = []
    for k, (ds, _) in enumerate(arquivos):
        p = os.path.join(pasta, f"{k:03d}.dcm")
        ds.save_as(p, enforce_file_format=True)
        caminhos.append(p)
    limpos = replace_identifiers(caminhos, **kw)
    ms = (time.perf_counter() - t0) * 1000
    por_tipo, por_campo, arquivos_com = {}, {}, 0
    uids_ausentes = 0
    com_cpf_cns = com_pessoal = 0
    for ds_limpo, (_, can) in zip(limpos, arquivos):
        v = vazamentos(ds_limpo, can)
        if v:
            arquivos_com += 1
        if "CPF" in v or "CNS" in v:
            com_cpf_cns += 1
        if any(t != "instituicao" for t in v):
            com_pessoal += 1
        campos_do_arquivo = set()
        for tipo, campos in v.items():
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
            campos_do_arquivo.update(campos)
        for c in campos_do_arquivo:
            por_campo[c] = por_campo.get(c, 0) + 1
        if not any(k in ds_limpo for k in ("SOPInstanceUID", "StudyInstanceUID", "SeriesInstanceUID")):
            uids_ausentes += 1
    return {"cenario": cenario, "arquivos": len(arquivos), "arquivos_com_vazamento": arquivos_com, "arquivos_com_cpf_ou_cns": com_cpf_cns, "arquivos_com_dado_pessoal": com_pessoal,
            "por_tipo": dict(sorted(por_tipo.items())), "por_campo": dict(sorted(por_campo.items(), key=lambda x: -x[1])),
            "sem_os_3_UIDs": uids_ausentes, "ms_total": round(ms, 1)}


def main():
    logging.disable(logging.WARNING)
    arquivos = gera()
    plantados = {}
    for ds, can in arquivos:
        for tipo in vazamentos(ds, can):
            plantados[tipo] = plantados.get(tipo, 0) + 1
    resultados = {"versoes": {"python": sys.version.split()[0], "pydicom": version("pydicom"), "deid": version("deid")},
                  "plantado_antes": dict(sorted(plantados.items())), "cenarios": []}
    receita_extra = os.path.join(AQUI, "receita_br.dicom")
    with tempfile.TemporaryDirectory() as tmp:
        for nome, kw in [
            ("A receita padrao do deid", {}),
            ("B padrao + remove_private=True", {"remove_private": True}),
            ("C receita_br.dicom + remove_private=True", {"remove_private": True, "deid": DeidRecipe(receita_extra, base=True)}),
        ]:
            pasta = os.path.join(tmp, nome[0]); os.makedirs(pasta)
            resultados["cenarios"].append(roda(nome, copy.deepcopy(arquivos), pasta, **kw))
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    linhas = [f"versoes: {resultados['versoes']}", f"plantado (arquivos com cada tipo, de {len(arquivos)}): {resultados['plantado_antes']}", ""]
    for c in resultados["cenarios"]:
        linhas += [f"[{c['cenario']}] arquivos com algum identificador: {c['arquivos_com_vazamento']} de {c['arquivos']}",
                   f"  com CPF ou CNS inteiro: {c['arquivos_com_cpf_ou_cns']} · com dado pessoal (sem contar instituicao): {c['arquivos_com_dado_pessoal']}",
                   f"  por tipo: {c['por_tipo']}", f"  por campo: {c['por_campo']}",
                   f"  sem SOP, Study e Series Instance UID: {c['sem_os_3_UIDs']} de {c['arquivos']} · tempo total: {c['ms_total']} ms", ""]
    txt = "\n".join(linhas)
    print(txt)
    with open(os.path.join(RES, "resultado.txt"), "w", encoding="utf-8") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
