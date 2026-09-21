"""Métrica conferida em casos pequenos, à mão."""

import pytest

from metricas import avaliar, prf

NOTA = {"id": "n1", "texto": "Ana Rosa, CPF 12345678909, leito 12.",
        "spans": [{"inicio": 0, "fim": 8, "tipo": "PESSOA", "texto": "Ana Rosa"},
                  {"inicio": 14, "fim": 25, "tipo": "BR_CPF", "texto": "12345678909"}],
        "distratores": [{"inicio": 33, "fim": 35, "tipo": "leito", "texto": "12"}]}


def test_prf_basico():
    assert prf(1, 0, 0) == (1.0, 1.0, 1.0)
    assert prf(0, 0, 0) == (0.0, 0.0, 0.0)
    assert prf(2, 2, 6) == pytest.approx((0.5, 0.25, 1 / 3))


def test_match_perfeito():
    r = avaliar([NOTA], {"n1": NOTA["spans"]})
    assert r["micro"] == {"tp": 2, "fp": 0, "fn": 0, "precisao": 1.0, "recall": 1.0, "f1": 1.0}
    assert r["vazamento"] == {"notas_vazadas": 0, "notas_com_doc": 1, "taxa": 0.0}
    assert r["fp_distratores"]["total"] == 0


def test_span_parcial_conta_como_erro_duplo():
    pred = [{"inicio": 0, "fim": 3, "tipo": "PESSOA", "texto": "Ana"}]  # só o primeiro nome
    r = avaliar([NOTA], {"n1": pred})
    assert r["por_tipo"]["PESSOA"] == {"tp": 0, "fp": 1, "fn": 1, "suporte": 1, "precisao": 0.0, "recall": 0.0, "f1": 0.0}
    assert r["vazamento"]["taxa"] == 1.0  # CPF não detectado
    assert r["pior_entidade"] in ("PESSOA", "BR_CPF")


def test_tipo_errado_no_span_certo_e_fp_e_fn():
    pred = [{"inicio": 14, "fim": 25, "tipo": "TELEFONE", "texto": "12345678909"}]
    r = avaliar([NOTA], {"n1": pred})
    assert r["por_tipo"]["BR_CPF"]["fn"] == 1
    assert r["por_tipo"]["TELEFONE"]["fp"] == 1
    assert r["vazamento"]["notas_vazadas"] == 1


def test_fp_em_distrator_conta_separado():
    pred = NOTA["spans"] + [{"inicio": 33, "fim": 35, "tipo": "BR_CPF", "texto": "12"}]
    r = avaliar([NOTA], {"n1": pred})
    assert r["fp_distratores"] == {"total": 1, "por_tipo": {"leito": 1}}
    assert r["por_tipo"]["BR_CPF"]["fp"] == 1


def test_nota_sem_predicao_conta_como_zero():
    r = avaliar([NOTA], {})
    assert r["micro"]["recall"] == 0.0
    assert r["vazamento"]["taxa"] == 1.0
