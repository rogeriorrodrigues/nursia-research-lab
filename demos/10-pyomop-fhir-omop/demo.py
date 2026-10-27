"""
Demo 10: pyomop 6.4.0 carrega FHIR sintético em OMOP CDM 5.4 (SQLite).

Gera 60 pacientes em NDJSON, roda o comando real do pyomop
(`pyomop --create --input ...`) e confere, no banco resultante:
  1. quantas linhas de cada recurso FHIR chegaram em cada tabela OMOP;
  2. se os valores de origem batem com o FHIR (data, código, valor, sexo);
  3. se CPF, CNS, nome, telefone e endereço aparecem em alguma tabela;
  4. quantos concept_id ficaram em 0 (sem vocabulário Athena carregado);
  5. quantas linhas clínicas têm visit_occurrence_id.

Uso: python3 demo.py   (grava results/)
"""

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import gerar_fhir

AQUI = Path(__file__).parent
FHIR = AQUI / "fhir_sintetico"
RESULTADOS = AQUI / "results"

# recurso FHIR -> tabelas OMOP onde o pyomop 6.4.0 grava (mapping.default.json)
DESTINOS = {
    "Patient": ["person"],
    "Encounter": ["visit_occurrence"],
    "Condition": ["condition_occurrence"],
    "Observation": ["measurement", "observation"],
    "MedicationRequest": ["drug_exposure"],
}
CONCEPT_COLS = {
    "person": ["gender_concept_id", "race_concept_id", "ethnicity_concept_id"],
    "visit_occurrence": ["visit_concept_id"],
    "condition_occurrence": ["condition_concept_id"],
    "measurement": ["measurement_concept_id", "unit_concept_id"],
    "observation": ["observation_concept_id"],
    "drug_exposure": ["drug_concept_id"],
}
CLINICAS = ["visit_occurrence", "condition_occurrence", "measurement", "observation", "drug_exposure"]


def ler(tipo: str) -> list[dict]:
    return [json.loads(x) for x in (FHIR / f"{tipo}.ndjson").read_text(encoding="utf-8").splitlines()]


def carregar_no_omop(db: Path) -> str:
    cmd = [sys.executable, "-m", "pyomop", "--create", "--name", str(db), "--input", str(FHIR)]
    r = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "Done" in r.stdout, r.stdout
    return "pyomop --create --name cdm.sqlite --input fhir_sintetico"


def contar(con: sqlite3.Connection, tabela: str) -> int:
    return con.execute(f'select count(*) from "{tabela}"').fetchone()[0]


def texto_do_banco(con: sqlite3.Connection) -> str:
    """Todas as células de todas as tabelas, num texto só, pra procurar dado pessoal."""
    partes = []
    for (t,) in con.execute("select name from sqlite_master where type='table'").fetchall():
        for linha in con.execute(f'select * from "{t}"'):
            partes.append(" ".join(str(v) for v in linha if v is not None))
    return "\n".join(partes)


def auditar(con: sqlite3.Connection) -> dict:
    pacientes = ler("Patient")
    pid = {p["id"]: i + 1 for i, p in enumerate(pacientes)}  # person_id vem da ordem de carga
    ref = lambda r: pid[r["subject"]["reference"].split("/")[1]]  # noqa: E731

    contagem = {}
    for tipo, tabelas in DESTINOS.items():
        n = len(ler(tipo))
        contagem[tipo] = {"fhir": n, **{t: contar(con, t) for t in tabelas}}

    # fidelidade dos valores de origem
    pessoas = {r[0]: r for r in con.execute(
        "select person_source_value, person_id, gender_source_value, year_of_birth, month_of_birth, day_of_birth "
        "from person")}
    sexo_ok = nasc_ok = 0
    for p in pacientes:
        r = pessoas.get(p["id"])
        ano, mes, dia = map(int, p["birthDate"].split("-"))
        sexo_ok += bool(r) and r[2] == p["gender"]
        nasc_ok += bool(r) and (r[3], r[4], r[5]) == (ano, mes, dia)
    medidas = set(con.execute("select person_id, measurement_source_value, value_as_number, measurement_date from measurement"))
    conds = set(con.execute("select person_id, condition_source_value, condition_start_date from condition_occurrence"))
    visitas = set(con.execute("select person_id, visit_start_date, visit_end_date, visit_source_value from visit_occurrence"))
    drogas = set(con.execute("select person_id, drug_source_value, drug_exposure_start_date from drug_exposure"))
    obs = ler("Observation")
    fid = {
        "person: sexo de origem": [sexo_ok, len(pacientes)],
        "person: data de nascimento": [nasc_ok, len(pacientes)],
        "measurement: código, valor e data": [sum(
            (ref(o), o["code"]["coding"][0]["code"], float(o["valueQuantity"]["value"]), o["effectiveDateTime"][:10]) in medidas
            for o in obs), len(obs)],
        "condition_occurrence: código e data": [sum(
            (ref(c), c["code"]["coding"][0]["code"], c["onsetDateTime"][:10]) in conds for c in ler("Condition")),
            len(ler("Condition"))],
        "visit_occurrence: início, fim e classe": [sum(
            (ref(e), e["period"]["start"][:10], e["period"]["end"][:10], e["class"]["code"]) in visitas
            for e in ler("Encounter")), len(ler("Encounter"))],
        "drug_exposure: código e data": [sum(
            (ref(m), m["medicationCodeableConcept"]["coding"][0]["code"], m["authoredOn"][:10]) in drogas
            for m in ler("MedicationRequest")), len(ler("MedicationRequest"))],
    }

    # dado pessoal em qualquer tabela
    banco = texto_do_banco(con)
    busca = {
        "CPF": lambda p: p["identifier"][0]["value"],
        "CNS": lambda p: p["identifier"][1]["value"],
        "nome completo": lambda p: f'{p["name"][0]["given"][0]} {p["name"][0]["family"]}',
        "sobrenome": lambda p: p["name"][0]["family"],
        "telefone": lambda p: p["telecom"][0]["value"],
        "rua": lambda p: p["address"][0]["line"][0].split(",")[0],
        "CEP": lambda p: p["address"][0]["postalCode"],
    }
    achados = {k: sum(f(p) in banco for p in pacientes) for k, f in busca.items()}

    # concept_id zerado e vínculo com a consulta
    concept = {}
    for t, cols in CONCEPT_COLS.items():
        n = contar(con, t)
        for c in cols:
            concept[f"{t}.{c}"] = [con.execute(f'select count(*) from "{t}" where "{c}" = 0 or "{c}" is null').fetchone()[0], n]
    vinculo = {t: [con.execute(f'select count(*) from "{t}" where visit_occurrence_id is not null').fetchone()[0], contar(con, t)]
               for t in CLINICAS[1:]}
    return {
        "contagem": contagem,
        "fidelidade": fid,
        "dado_pessoal_em_alguma_tabela": {"pacientes": len(pacientes), "achados": achados},
        "concept_id_zero_ou_nulo": concept,
        "com_visit_occurrence_id": vinculo,
        "linhas_na_tabela_concept": contar(con, "concept"),
        "person_source_value_exemplo": con.execute("select person_source_value from person order by person_id limit 3").fetchall(),
    }


def tabela(m: dict, comando: str, versao: str) -> str:
    L = [f"pyomop {versao}, CDM 5.4, SQLite. Comando: {comando}", "",
         "## Linhas por recurso", "", "| Recurso FHIR | no FHIR | tabela OMOP (linhas) |", "|---|---|---|"]
    for tipo, d in m["contagem"].items():
        L.append(f"| {tipo} | {d['fhir']} | " + ", ".join(f"{t} ({d[t]})" for t in DESTINOS[tipo]) + " |")
    L += ["", "## Valores de origem que chegaram iguais", "", "| Conferência | iguais |", "|---|---|"]
    L += [f"| {k} | {a}/{b} |" for k, (a, b) in m["fidelidade"].items()]
    d = m["dado_pessoal_em_alguma_tabela"]
    L += ["", f"## Dado pessoal em alguma tabela ({d['pacientes']} pacientes)", "", "| Dado | pacientes achados |", "|---|---|"]
    L += [f"| {k} | {v}/{d['pacientes']} |" for k, v in d["achados"].items()]
    L += ["", "## concept_id em 0 ou nulo (sem vocabulário Athena)", "", "| Coluna | em 0 ou nulo |", "|---|---|"]
    L += [f"| {k} | {a}/{b} |" for k, (a, b) in m["concept_id_zero_ou_nulo"].items()]
    L += ["", f"Linhas na tabela concept: {m['linhas_na_tabela_concept']}", "",
          "## Linhas com visit_occurrence_id", "", "| Tabela | com vínculo |", "|---|---|"]
    L += [f"| {k} | {a}/{b} |" for k, (a, b) in m["com_visit_occurrence_id"].items()]
    L += ["", f"person_source_value (3 primeiros): {m['person_source_value_exemplo']}"]
    return "\n".join(L) + "\n"


def main() -> None:
    import importlib.metadata as md

    gerar_fhir.main()
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "cdm.sqlite"
        comando = carregar_no_omop(db)
        con = sqlite3.connect(db)
        m = auditar(con)
        con.close()
    versao = md.version("pyomop")
    RESULTADOS.mkdir(exist_ok=True)
    (RESULTADOS / "metricas.json").write_text(
        json.dumps({"pyomop": versao, **m}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    texto = tabela(m, comando, versao)
    (RESULTADOS / "tabela.md").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
