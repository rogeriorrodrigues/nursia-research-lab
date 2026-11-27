"""hl7apy valida HL7 v2? 240 mensagens ADT^A01 sintéticas, 200 com defeito plantado.

Roda o mesmo lote em 2 níveis (TOLERANT, o padrão, e STRICT) e conta, por tipo de
defeito, quantas mensagens o hl7apy reprovou (exceção no parse ou no validate()).
"""
import json
import platform
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

from importlib.metadata import version

HL7APY = version("hl7apy")
from hl7apy.consts import VALIDATION_LEVEL
from hl7apy.parser import parse_message
from hl7apy import get_default_validation_level

from gera_hl7 import TIPOS_CONTEUDO, TIPOS_FORMA, cns_valida, cpf_valida, gera

ORDEM_ADT_A01 = ["MSH", "EVN", "PID", "PV1"]  # só os segmentos que este lote usa
SEXO_HL70001 = {"F", "M", "O", "U", "A", "N"}

RESULTS = Path(__file__).parent / "results"
NIVEIS = {"TOLERANT": VALIDATION_LEVEL.TOLERANT, "STRICT": VALIDATION_LEVEL.STRICT}


def avisos(m):
    """Avisos do validate() (tabela HL7, tamanho): só aparecem no report_file."""
    with tempfile.NamedTemporaryFile("r", suffix=".txt") as f:
        try:
            m.validate(report_file=f.name)
        except Exception:  # noqa: BLE001
            pass
        return [linha.strip() for linha in open(f.name, encoding="utf-8") if linha.startswith("Warning")]


def checa(er7, nivel):
    """(reprovou, etapa, erro, er7_reserializado)."""
    try:
        m = parse_message(er7, validation_level=nivel, find_groups=True)
    except Exception as e:  # noqa: BLE001 - qualquer recusa conta como reprovação
        return True, "parse", f"{type(e).__name__}: {str(e)[:100]}", None
    try:
        m.validate()
    except Exception as e:  # noqa: BLE001
        return True, "validate", f"{type(e).__name__}: {str(e)[:100]}", m.to_er7()
    return False, "", "", m.to_er7()


def regras_br(er7, hoje="20261126"):
    """Checagens que o hl7apy não faz: ordem, CPF, CNS, sexo na tabela, nascimento no futuro.
    Roda depois do parse STRICT; devolve a lista de problemas."""
    probs = []
    segs = [linha.split("|")[0] for linha in er7.split("\r")]
    vistos = [x for x in segs if x in ORDEM_ADT_A01]
    if vistos != sorted(vistos, key=ORDEM_ADT_A01.index):
        probs.append("segmentos fora de ordem")
    m = parse_message(er7, validation_level=VALIDATION_LEVEL.STRICT, find_groups=True)
    pid = m.pid
    for rep in pid.pid_3:
        num, tipo = rep.cx_1.to_er7(), rep.cx_4.to_er7()
        if tipo == "CPF" and not cpf_valida(num):
            probs.append(f"CPF {num} com dígito errado")
        if tipo == "CNS" and not cns_valida(num):
            probs.append(f"CNS {num} inválido")
    if pid.pid_8.to_er7() not in SEXO_HL70001:
        probs.append(f"sexo {pid.pid_8.to_er7()} fora da tabela 0001")
    if pid.pid_7.to_er7()[:8] > hoje:
        probs.append(f"nascimento {pid.pid_7.to_er7()} no futuro")
    return probs


def roda_regras(msgs):
    """Aplica regras_br() só no que o STRICT aceitou."""
    por_tipo = defaultdict(lambda: {"aceitas_strict": 0, "pegas_pelas_regras": 0})
    for m in msgs:
        if checa(m["er7"], VALIDATION_LEVEL.STRICT)[0]:
            continue
        t = por_tipo[m["tipo"]]
        t["aceitas_strict"] += 1
        t["pegas_pelas_regras"] += int(bool(regras_br(m["er7"])))
    return dict(por_tipo)


def roda(msgs):
    res = {}
    for nome, nivel in NIVEIS.items():
        por_tipo = defaultdict(lambda: {"total": 0, "reprovadas": 0, "etapas": Counter(), "exemplo_erro": "",
                                        "aceitas_com_aviso": 0, "exemplo_aviso": ""})
        reordenadas = 0
        for m in msgs:
            rep, etapa, erro, saida = checa(m["er7"], nivel)
            t = por_tipo[m["tipo"]]
            t["total"] += 1
            t["reprovadas"] += int(rep)
            if rep:
                t["etapas"][etapa] += 1
                t["exemplo_erro"] = t["exemplo_erro"] or erro
            if not rep:
                w = avisos(parse_message(m["er7"], validation_level=nivel, find_groups=True))
                if w:
                    t["aceitas_com_aviso"] += 1
                    t["exemplo_aviso"] = t["exemplo_aviso"] or w[0][:120]
            if m["tipo"] == "fora_de_ordem" and not rep and saida and saida != m["er7"]:
                reordenadas += 1
        res[nome] = {"por_tipo": {k: {**v, "etapas": dict(v["etapas"])} for k, v in por_tipo.items()},
                     "fora_de_ordem_aceitas_e_reordenadas": reordenadas}
    return res


def soma(por_tipo, tipos):
    return sum(por_tipo[t]["reprovadas"] for t in tipos), sum(por_tipo[t]["total"] for t in tipos)


def main():
    msgs = gera()
    res = roda(msgs)
    linhas = [
        f"hl7apy {HL7APY} · Python {sys.version.split()[0]} · {platform.system()}",
        f"nível padrão do parse_message(): {'TOLERANT' if get_default_validation_level() == VALIDATION_LEVEL.TOLERANT else 'STRICT'}",
        f"mensagens: {len(msgs)} (40 válidas, {len(TIPOS_FORMA) * 20} com defeito de forma, {len(TIPOS_CONTEUDO) * 20} com defeito de conteúdo)",
        "",
        f"{'tipo':<24}{'grupo':<10}{'TOLERANT':>10}{'STRICT':>10}",
    ]
    grupo = {m["tipo"]: m["grupo"] for m in msgs}
    for tipo in ["valida"] + TIPOS_FORMA + TIPOS_CONTEUDO:
        a = res["TOLERANT"]["por_tipo"][tipo]
        b = res["STRICT"]["por_tipo"][tipo]
        linhas.append(f"{tipo:<24}{grupo[tipo]:<10}{a['reprovadas']:>5}/{a['total']:<4}{b['reprovadas']:>5}/{b['total']:<4}")
    linhas.append("")
    resumo = {}
    for nome in NIVEIS:
        pt = res[nome]["por_tipo"]
        f, ft = soma(pt, TIPOS_FORMA)
        c, ct = soma(pt, TIPOS_CONTEUDO)
        v = pt["valida"]["reprovadas"]
        resumo[nome] = {"defeituosas_reprovadas": f + c, "defeituosas": ft + ct, "forma": [f, ft],
                        "conteudo": [c, ct], "validas_reprovadas": v,
                        "fora_de_ordem_aceitas_e_reordenadas": res[nome]["fora_de_ordem_aceitas_e_reordenadas"]}
        linhas.append(f"{nome}: reprovou {f + c} de {ft + ct} com defeito (forma {f}/{ft}, conteúdo {c}/{ct}); "
                      f"válidas reprovadas: {v}/40; fora de ordem aceitas e reserializadas em outra ordem: "
                      f"{res[nome]['fora_de_ordem_aceitas_e_reordenadas']}/20")
    linhas.append("")
    linhas.append("exemplo de erro por tipo (STRICT):")
    for tipo in TIPOS_FORMA + TIPOS_CONTEUDO:
        t = res["STRICT"]["por_tipo"][tipo]
        linhas.append(f"  {tipo}: {t['exemplo_erro'] or '(aceita)'}")
    linhas.append("")
    linhas.append("aceitas pelo validate() (True), mas com aviso no report_file (STRICT):")
    for tipo in ["valida"] + TIPOS_FORMA + TIPOS_CONTEUDO:
        t = res["STRICT"]["por_tipo"][tipo]
        aceitas = t["total"] - t["reprovadas"]
        if aceitas:
            linhas.append(f"  {tipo}: {t['aceitas_com_aviso']}/{aceitas} {t['exemplo_aviso']}")
    regras = roda_regras(msgs)
    linhas.append("")
    linhas.append("regras_br() (ordem, CPF, CNS, sexo, nascimento) no que o STRICT aceitou:")
    for tipo in ["valida"] + TIPOS_FORMA + TIPOS_CONTEUDO:
        if tipo in regras:
            r = regras[tipo]
            linhas.append(f"  {tipo}: pegou {r['pegas_pelas_regras']}/{r['aceitas_strict']}")
    total_def = sum(r["pegas_pelas_regras"] for k, r in regras.items() if k != "valida")
    linhas.append(f"STRICT + regras_br(): reprovou {resumo['STRICT']['defeituosas_reprovadas'] + total_def} de 200 com defeito; "
                  f"válidas reprovadas: {regras['valida']['pegas_pelas_regras']}/40")
    texto = "\n".join(linhas)
    print(texto)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "resultado.txt").write_text(texto + "\n", encoding="utf-8")
    (RESULTS / "resultado.json").write_text(json.dumps({"hl7apy": HL7APY, "python": sys.version.split()[0],
                                                        "resumo": resumo, "regras_br": regras, "detalhe": res}, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    (RESULTS / "exemplo_fora_de_ordem.txt").write_text(
        "ENTRADA:\n" + next(m["er7"] for m in msgs if m["tipo"] == "fora_de_ordem").replace("\r", "\n")
        + "\n\nSAÍDA do to_er7() depois do parse STRICT:\n"
        + checa(next(m["er7"] for m in msgs if m["tipo"] == "fora_de_ordem"), VALIDATION_LEVEL.STRICT)[3].replace("\r", "\n") + "\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
