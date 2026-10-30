"""
Gera 240 recursos FHIR R4B sintéticos: 60 válidos e 180 com um defeito conhecido,
20 por categoria. Semente fixa (2026). Nada aqui é dado de paciente real.

Cada item sai como {"id", "categoria", "defeito_esperado", "recurso"}.
"defeito_esperado" é o que o HL7 FHIR exigiria: serve de gabarito pra contar
quantos defeitos o validador deixou passar.
"""

import copy
import json
import random
from pathlib import Path

AQUI = Path(__file__).parent
SEMENTE = 2026
POR_CATEGORIA = 20
CPF_SYSTEM = "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf"
NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabi", "Hugo", "Inês", "João"]
SOBRENOMES = ["Silva", "Souza", "Lima", "Pereira", "Costa", "Ribeiro", "Alves", "Nunes"]

# categoria -> (descrição, estrutural?)  estrutural = a especificação FHIR em si recusa na forma
CATEGORIAS = {
    "obrigatorio_ausente": ("campo obrigatório ausente", True),
    "data_formato_br": ("data no formato dd/mm/aaaa", True),
    "campo_desconhecido": ("campo que não existe no recurso", True),
    "codigo_fora_do_conjunto": ("valor fora do conjunto obrigatório (code)", True),
    "loinc_inventado": ("código inventado sob o sistema LOINC", False),
    "unidade_ucum_invalida": ("unidade que não é UCUM válida", False),
    "referencia_quebrada": ("referência pra um Patient que não está no Bundle", False),
    "cpf_digito_invalido": ("CPF com dígito verificador errado", False),
    "invariante_obs6": ("valor e dataAbsentReason juntos (invariante obs-6)", False),
}


def digito_cpf(base: list[int]) -> int:
    soma = sum(d * p for d, p in zip(base, range(len(base) + 1, 1, -1)))
    resto = (soma * 10) % 11
    return 0 if resto == 10 else resto


def cpf_valido(rng: random.Random) -> str:
    base = [rng.randint(0, 9) for _ in range(9)]
    base.append(digito_cpf(base))
    base.append(digito_cpf(base))
    return "".join(map(str, base))


def cpf_confere(cpf: str) -> bool:
    d = [int(c) for c in cpf]
    return len(d) == 11 and digito_cpf(d[:9]) == d[9] and digito_cpf(d[:10]) == d[10]


def cpf_invalido(rng: random.Random) -> str:
    cpf = cpf_valido(rng)
    ultimo = (int(cpf[-1]) + rng.randint(1, 9)) % 10
    return cpf[:-1] + str(ultimo)


def paciente(rng: random.Random, i: int) -> dict:
    return {
        "resourceType": "Patient",
        "id": f"pac-{i:03d}",
        "identifier": [{"system": CPF_SYSTEM, "value": cpf_valido(rng)}],
        "name": [{"family": rng.choice(SOBRENOMES), "given": [rng.choice(NOMES)]}],
        "gender": rng.choice(["male", "female"]),
        "birthDate": f"{rng.randint(1940, 2005)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
    }


def observacao(rng: random.Random, i: int, pac_id: str) -> dict:
    return {
        "resourceType": "Observation",
        "id": f"obs-{i:03d}",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
        "subject": {"reference": f"Patient/{pac_id}"},
        "effectiveDateTime": f"2026-10-{rng.randint(1, 28):02d}T08:00:00-03:00",
        "valueQuantity": {"value": rng.randint(50, 120), "unit": "/min",
                          "system": "http://unitsofmeasure.org", "code": "/min"},
    }


def condicao(rng: random.Random, i: int, pac_id: str) -> dict:
    return {
        "resourceType": "Condition",
        "id": f"con-{i:03d}",
        "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                       "code": "active"}]},
        "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": rng.choice(["I10", "E11", "J45"])}]},
        "subject": {"reference": f"Patient/{pac_id}"},
    }


def bundle(pac: dict, obs: dict) -> dict:
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"fullUrl": f"urn:uuid:{pac['id']}", "resource": pac},
                  {"fullUrl": f"urn:uuid:{obs['id']}", "resource": obs}],
    }


def estragar(categoria: str, rng: random.Random, i: int) -> tuple[dict, str]:
    """Devolve (recurso com um defeito, descrição do defeito)."""
    pac = paciente(rng, i)
    obs = observacao(rng, i, pac["id"])
    con = condicao(rng, i, pac["id"])
    if categoria == "obrigatorio_ausente":
        alvo, campo = [(obs, "status"), (obs, "code"), (con, "subject")][i % 3]
        r = copy.deepcopy(alvo)
        del r[campo]
        return r, f"{r['resourceType']} sem {campo}"
    if categoria == "data_formato_br":
        if i % 2:
            pac["birthDate"] = "-".join(reversed(pac["birthDate"].split("-"))).replace("-", "/")
            return pac, "Patient.birthDate em dd/mm/aaaa"
        obs["effectiveDateTime"] = "30/10/2026"
        return obs, "Observation.effectiveDateTime em dd/mm/aaaa"
    if categoria == "campo_desconhecido":
        if i % 2:
            pac["cpf"] = pac["identifier"][0]["value"]
            return pac, "Patient.cpf (campo que não existe)"
        obs["paciente"] = "Patient/x"
        return obs, "Observation.paciente (campo que não existe)"
    if categoria == "codigo_fora_do_conjunto":
        if i % 2:
            pac["gender"] = rng.choice(["masculino", "feminino", "M", "F"])
            return pac, "Patient.gender fora do conjunto"
        obs["status"] = rng.choice(["concluido", "ok", "final "])
        return obs, "Observation.status fora do conjunto"
    if categoria == "loinc_inventado":
        obs["code"]["coding"][0]["code"] = f"FC-{i:04d}"
        return obs, "código FC-xxxx sob o sistema LOINC"
    if categoria == "unidade_ucum_invalida":
        obs["valueQuantity"].update({"unit": "batimentos por minuto", "code": "batimentos/minuto"})
        return obs, "unidade fora do UCUM"
    if categoria == "referencia_quebrada":
        obs["subject"]["reference"] = f"Patient/{'fantasma-' + str(i)}"
        return bundle(pac, obs), "Observation.subject aponta pra Patient fora do Bundle"
    if categoria == "cpf_digito_invalido":
        pac["identifier"][0]["value"] = cpf_invalido(rng)
        return pac, "CPF com dígito verificador errado"
    if categoria == "invariante_obs6":
        obs["dataAbsentReason"] = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                                               "code": "unknown"}]}
        return obs, "valueQuantity e dataAbsentReason juntos"
    raise ValueError(categoria)


def gerar() -> list[dict]:
    rng = random.Random(SEMENTE)
    itens = []
    for i in range(60):
        base = [paciente, lambda r, n: observacao(r, n, f"pac-{n:03d}"),
                lambda r, n: condicao(r, n, f"pac-{n:03d}")][i % 3](rng, i)
        itens.append({"id": f"valido-{i:03d}", "categoria": "valido", "defeito_esperado": None, "recurso": base})
    for cat in CATEGORIAS:
        for i in range(POR_CATEGORIA):
            recurso, defeito = estragar(cat, rng, i)
            itens.append({"id": f"{cat}-{i:03d}", "categoria": cat, "defeito_esperado": defeito, "recurso": recurso})
    return itens


def main() -> None:
    itens = gerar()
    caminho = AQUI / "data" / "recursos.jsonl"
    caminho.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in itens) + "\n", encoding="utf-8")
    print(f"{len(itens)} recursos em {caminho.relative_to(AQUI)}")


if __name__ == "__main__":
    main()
