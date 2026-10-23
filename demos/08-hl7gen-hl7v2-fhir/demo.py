"""hl7gen 0.2.0: gera HL7 v2 sintético, valida e converte pra FHIR. Mede o que sobra no caminho.

Roda sem rede, sem chave de API e sem dado de paciente. Tudo sai de results/.
"""
import csv
import json
import random
import re
import subprocess
import sys
from collections import Counter
from importlib.metadata import version
from pathlib import Path

from faker import Faker
from hl7gen.fhir_export import SUPPORTED_TYPES, message_to_fhir
from hl7gen.generator import generate_message
from hl7gen.validator import validate_message

AQUI = Path(__file__).resolve().parent
RESULTS = AQUI / "results"
SEMENTE = 2026
LOTE = 100
TOKEN = re.compile(r"^[A-Z0-9]{8}$")

# Mensagem escrita à mão, com CPF e CNS sintéticos (dígito verificador válido, sem dono).
MSG_BR = "\r".join([
    "MSH|^~\\&|SIS|HOSP|DEST|HOSP|20261022090000||ADT^A01^ADT_A01|MSG0001|P|2.5",
    "EVN|A01|20261022090000",
    "PID|1||52998224725^^^BR^CPF~898001234567891^^^BR^CNS||Conceição^João Paulo^Silva"
    "||19800315|M|||Rua das Flores 10^Florianópolis^SC||(48)99999-0000",
    "PV1|1|I",
])


def semear():
    random.seed(SEMENTE)
    Faker.seed(SEMENTE)


def tipos_hl7():
    saida = subprocess.run(
        [str(Path(sys.executable).with_name("hl7gen")), "types"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [linha.split()[0] for linha in saida.splitlines() if linha.strip()]


def folhas(obj):
    if isinstance(obj, dict):
        return sum(folhas(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(folhas(v) for v in obj)
    return 1


def converter(msg, fhir="R4B"):
    """Devolve (bundle, None) ou (None, nome da exceção)."""
    try:
        return json.loads(json.dumps(message_to_fhir(msg, fhir), default=str)), None
    except Exception as exc:  # o que a CLI faria o usuário ver
        return None, type(exc).__name__


def cobertura():
    semear()
    linhas = []
    for tipo in tipos_hl7():
        try:
            msg = generate_message(tipo)
        except Exception as exc:
            linhas.append({"tipo": tipo, "gerou": 0, "valida": 0, "r4b": "-", "r5": "-", "erro": type(exc).__name__})
            continue
        _, e4 = converter(msg, "R4B")
        _, e5 = converter(msg, "R5")
        linhas.append({
            "tipo": tipo, "gerou": 1, "valida": int(validate_message(msg).valid),
            "r4b": e4 or "ok", "r5": e5 or "ok", "erro": "",
        })
    with open(RESULTS / "cobertura.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    return linhas


def lote(tipo):
    semear()
    r = Counter()
    classes = Counter()
    tipos_obs = Counter()
    bytes_hl7 = bytes_fhir = campos_hl7 = folhas_fhir = recursos = 0
    amostra = None
    for i in range(LOTE):
        msg = generate_message(tipo)
        r["geradas"] += 1
        r["validas"] += validate_message(msg).valid
        bundle, erro = converter(msg)
        if erro:
            r["erro_conversao"] += 1
            continue
        r["convertidas"] += 1
        amostra = amostra or (msg, bundle)
        bytes_hl7 += len(msg)
        bytes_fhir += len(json.dumps(bundle, ensure_ascii=False))
        campos_hl7 += sum(1 for seg in msg.split("\r") for c in seg.split("|")[1:] if c)
        folhas_fhir += folhas(bundle)
        entradas = [e["resource"] for e in bundle["entry"]]
        recursos += len(entradas)
        pv1 = next((s.split("|") for s in msg.split("\r") if s.startswith("PV1|")), None)
        for res in entradas:
            if res["resourceType"] == "Patient":
                r["pacientes"] += 1
                r["sem_identifier"] += "identifier" not in res
                nome = res.get("name", [{}])[0]
                r["nome_token"] += bool(TOKEN.match(nome.get("family", "")))
                r["sem_genero"] += "gender" not in res
                r["telecom_cru"] += any("^" in t["value"] for t in res.get("telecom", []))
            elif res["resourceType"] == "Encounter":
                r["encontros"] += 1
                classes[res["class"]["code"]] += 1
                r["classe_por_padrao"] += bool(pv1 and pv1[2] not in ("I", "O", "E"))
            elif res["resourceType"] == "Observation":
                r["observacoes"] += 1
                tipos_obs["valueQuantity" if "valueQuantity" in res else "valueString"] += 1
                r["obs_string_vazia"] += res.get("valueString") == ""
    r.update(bytes_hl7=bytes_hl7, bytes_fhir=bytes_fhir, campos_hl7=campos_hl7,
             folhas_fhir=folhas_fhir, recursos=recursos)
    if amostra:
        (RESULTS / f"amostra_{tipo}.hl7").write_text(amostra[0].replace("\r", "\n"), encoding="utf-8")
        (RESULTS / f"amostra_{tipo}.fhir.json").write_text(
            json.dumps(amostra[1], indent=2, ensure_ascii=False), encoding="utf-8")
    return dict(r), dict(classes), dict(tipos_obs)


def caso_br():
    bundle, _ = converter(MSG_BR)
    (RESULTS / "br_bundle.json").write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    texto = json.dumps(bundle, ensure_ascii=False)
    ruim = MSG_BR.replace("19800315", "20261345")
    _, erro = converter(ruim)
    return {
        "valida": validate_message(MSG_BR).valid,
        "patient_tem_identifier": "identifier" in bundle["entry"][0]["resource"],
        "cpf_no_bundle": "52998224725" in texto,
        "cns_no_bundle": "898001234567891" in texto,
        "acentos_preservados": "Conceição" in texto and "Florianópolis" in texto,
        "data_impossivel_valida": validate_message(ruim).valid,
        "data_impossivel_conversao": erro,
    }


def main():
    RESULTS.mkdir(exist_ok=True)
    cob = cobertura()
    resumo = {
        "hl7gen": version("hl7gen"),
        "tipos_hl7_v25": len(cob),
        "geram": sum(c["gerou"] for c in cob),
        "validam": sum(c["valida"] for c in cob),
        "convertem_r4b": sum(c["r4b"] == "ok" for c in cob),
        "convertem_r5": sum(c["r5"] == "ok" for c in cob),
        "tipos_suportados_pelo_codigo": sorted(SUPPORTED_TYPES),
        "erros_r4b": dict(Counter(c["r4b"] for c in cob if c["r4b"] != "ok")),
    }
    for tipo in ("ADT_A01", "ORU_R01"):
        r, classes, obs = lote(tipo)
        resumo[f"lote_{tipo}"] = {"mensagens": LOTE, **r, "classes_encounter": classes, "tipo_valor_obs": obs}
    resumo["caso_br"] = caso_br()
    (RESULTS / "resumo.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
