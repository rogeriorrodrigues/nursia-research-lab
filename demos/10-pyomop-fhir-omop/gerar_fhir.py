"""
Gera FHIR R4 sintético em NDJSON (um arquivo por tipo de recurso), seed fixa.

60 pacientes com CPF e CNS (dígito verificador válido, sorteados, de ninguém),
nome, telefone e endereço inventados; 1 a 3 consultas, 1 a 2 condições,
2 observações (FC e PA sistólica) e 1 prescrição por paciente.
Condição, observação e prescrição apontam pra 1ª consulta do paciente (campo encounter).
Uso: python3 gerar_fhir.py   (reescreve fhir_sintetico/)
"""

import json
import random
from pathlib import Path

AQUI = Path(__file__).parent
SEED = 2026
N_PACIENTES = 60

NOMES = ["Ana", "João", "Maria", "Pedro", "Lucas", "Beatriz", "Rafael", "Camila", "Tiago", "Fernanda"]
SOBRENOMES = ["Silva", "Rosa", "Pereira", "Machado", "Barbosa", "Cardoso", "Almeida", "Ribeiro"]
RUAS = ["Rua do Mirante", "Rua das Flores", "Avenida Central", "Rua Sete de Setembro"]
CONDICOES = [("I10", "Hipertensão essencial"), ("E11.9", "Diabetes mellitus tipo 2"),
             ("J45.9", "Asma"), ("N39.0", "Infecção urinária")]
SISTEMA_CPF = "http://www.saude.gov.br/fhir/r4/NamingSystem/cpf"
SISTEMA_CNS = "http://www.saude.gov.br/fhir/r4/NamingSystem/cns"


def gerar_cpf(rng: random.Random) -> str:
    while True:
        d = [rng.randint(0, 9) for _ in range(9)]
        if len(set(d)) == 1:
            continue
        for n in (9, 10):
            dv = (sum(d[i] * (n + 1 - i) for i in range(n)) * 10) % 11 % 10
            d.append(dv)
        return "".join(map(str, d))


def gerar_cns(rng: random.Random) -> str:
    """CNS provisório (começa com 7, 8 ou 9): soma ponderada dos 15 dígitos múltipla de 11."""
    while True:
        base = [rng.choice([7, 8, 9])] + [rng.randint(0, 9) for _ in range(13)]
        soma = sum(base[i] * (15 - i) for i in range(14))
        dv = (11 - soma % 11) % 11
        if dv < 10:  # dv 10 não cabe em um dígito: sorteia de novo
            return "".join(map(str, base)) + str(dv)


def cns_valido(cns: str) -> bool:
    return len(cns) == 15 and sum(int(c) * (15 - i) for i, c in enumerate(cns)) % 11 == 0


def cpf_valido(cpf: str) -> bool:
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    d = [int(c) for c in cpf]
    for n in (9, 10):
        if (sum(d[i] * (n + 1 - i) for i in range(n)) * 10) % 11 % 10 != d[n]:
            return False
    return True


def gerar(rng: random.Random) -> dict[str, list[dict]]:
    recursos: dict[str, list[dict]] = {k: [] for k in
                                       ("Patient", "Encounter", "Condition", "Observation", "MedicationRequest")}
    for i in range(1, N_PACIENTES + 1):
        pid = f"p{i:03d}"
        ref = {"reference": f"Patient/{pid}"}
        nome, sobrenome = rng.choice(NOMES), rng.choice(SOBRENOMES)
        ddd = rng.choice(["48", "11", "51"])
        recursos["Patient"].append({
            "resourceType": "Patient", "id": pid,
            "identifier": [
                {"system": SISTEMA_CPF, "value": gerar_cpf(rng)},
                {"system": SISTEMA_CNS, "value": gerar_cns(rng)},
            ],
            "name": [{"use": "official", "family": sobrenome, "given": [nome]}],
            "telecom": [{"system": "phone", "value": f"({ddd}) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"}],
            "gender": rng.choice(["female", "male"]),
            "birthDate": f"{rng.randint(1940, 2005)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            "address": [{"line": [f"{rng.choice(RUAS)}, {rng.randint(10, 999)}"], "city": "Florianópolis",
                         "state": "SC", "postalCode": f"88{rng.randint(100, 999)}-{rng.randint(100, 999)}"}],
        })
        enc = {"reference": f"Encounter/e{i:03d}0"}
        for j in range(rng.randint(1, 3)):
            dia, mes = rng.randint(1, 28), rng.randint(1, 9)
            recursos["Encounter"].append({
                "resourceType": "Encounter", "id": f"e{i:03d}{j}", "status": "finished",
                "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
                "subject": ref, "period": {"start": f"2026-0{mes}-{dia:02d}T09:00:00Z",
                                           "end": f"2026-0{mes}-{dia:02d}T09:30:00Z"},
            })
        for j, (cid, texto) in enumerate(rng.sample(CONDICOES, rng.randint(1, 2))):
            recursos["Condition"].append({
                "resourceType": "Condition", "id": f"c{i:03d}{j}", "subject": ref, "encounter": enc,
                "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": cid, "display": texto}],
                         "text": texto},
                "onsetDateTime": f"2025-0{rng.randint(1, 9)}-{rng.randint(1, 28):02d}T00:00:00Z",
            })
        for j, (loinc, nome_obs, un, lo, hi) in enumerate(
                [("8867-4", "Frequência cardíaca", "/min", 55, 110), ("8480-6", "PA sistólica", "mm[Hg]", 100, 170)]):
            recursos["Observation"].append({
                "resourceType": "Observation", "id": f"o{i:03d}{j}", "status": "final", "subject": ref, "encounter": enc,
                "code": {"coding": [{"system": "http://loinc.org", "code": loinc, "display": nome_obs}]},
                "effectiveDateTime": f"2026-0{rng.randint(1, 9)}-{rng.randint(1, 28):02d}T10:00:00Z",
                "valueQuantity": {"value": rng.randint(lo, hi), "unit": un,
                                  "system": "http://unitsofmeasure.org", "code": un},
            })
        recursos["MedicationRequest"].append({
            "resourceType": "MedicationRequest", "id": f"m{i:03d}", "status": "active", "intent": "order",
            "subject": ref, "encounter": enc,
            "medicationCodeableConcept": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                                      "code": rng.choice(["197361", "860975"]),
                                                      "display": rng.choice(["amlodipina 5 mg", "metformina 500 mg"])}]},
            "authoredOn": f"2026-0{rng.randint(1, 9)}-{rng.randint(1, 28):02d}T11:00:00Z",
        })
    return recursos


def main() -> None:
    destino = AQUI / "fhir_sintetico"
    destino.mkdir(exist_ok=True)
    for tipo, lista in gerar(random.Random(SEED)).items():
        (destino / f"{tipo}.ndjson").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in lista) + "\n", encoding="utf-8")
        print(tipo, len(lista))


if __name__ == "__main__":
    main()
