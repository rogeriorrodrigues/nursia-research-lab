"""Gerador conferido à mão e carga real no pyomop (SQLite em pasta temporária)."""

import random
import sqlite3
import tempfile
from pathlib import Path

import demo
import gerar_fhir as g


def test_cpf_e_cns_gerados_sao_validos():
    rng = random.Random(1)
    assert all(g.cpf_valido(g.gerar_cpf(rng)) for _ in range(200))
    assert all(g.cns_valido(g.gerar_cns(rng)) for _ in range(200))
    assert not g.cpf_valido("11111111111")
    assert not g.cns_valido("123")


def test_gerador_e_deterministico():
    a = g.gerar(random.Random(g.SEED))
    b = g.gerar(random.Random(g.SEED))
    assert a == b
    assert len(a["Patient"]) == g.N_PACIENTES


def test_carga_real_no_pyomop():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "cdm.sqlite"
        demo.carregar_no_omop(db)
        con = sqlite3.connect(db)
        m = demo.auditar(con)
        con.close()
    assert m["contagem"]["Patient"]["person"] == g.N_PACIENTES
    assert m["contagem"]["Observation"]["measurement"] == m["contagem"]["Observation"]["observation"]
    assert all(a == b for a, b in m["fidelidade"].values())
    assert sum(m["dado_pessoal_em_alguma_tabela"]["achados"].values()) == 0
