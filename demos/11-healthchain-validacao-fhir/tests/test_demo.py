"""Gerador e métrica conferidos em casos pequenos e no resultado gravado."""

import json
from pathlib import Path

import demo
import gerar_dados


def test_cpf_gerado_confere():
    import random
    rng = random.Random(1)
    assert all(gerar_dados.cpf_confere(gerar_dados.cpf_valido(rng)) for _ in range(50))
    assert not any(gerar_dados.cpf_confere(gerar_dados.cpf_invalido(rng)) for _ in range(50))


def test_gerador_e_deterministico():
    assert gerar_dados.gerar() == gerar_dados.gerar()
    assert len(gerar_dados.gerar()) == 60 + 9 * gerar_dados.POR_CATEGORIA


def test_valido_passa_e_campo_obrigatorio_ausente_reprova():
    itens = {i["id"]: i for i in gerar_dados.gerar()}
    ok = demo.validar([itens["valido-000"], itens["valido-001"], itens["valido-002"]])
    assert all(r["valid"] for r in ok)
    ruim = demo.validar([itens["obrigatorio_ausente-000"]])
    assert not ruim[0]["valid"]


def test_resultado_gravado_bate_com_o_gerador():
    m = json.loads((Path(demo.AQUI) / "results" / "metricas.json").read_text(encoding="utf-8"))
    assert m["recursos"] == len(gerar_dados.gerar())
    assert m["validos_reprovados"] == 0
