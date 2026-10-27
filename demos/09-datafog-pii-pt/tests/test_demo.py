"""Métrica conferida em casos pequenos e no corpus gravado."""

import json
from pathlib import Path

import demo

NOTA = {"id": "n1", "texto": "Ana, CPF 12345678909, tel 99123-4567, protocolo 2026.",
        "spans": [{"inicio": 9, "fim": 20, "tipo": "BR_CPF", "texto": "12345678909"},
                  {"inicio": 26, "fim": 36, "tipo": "TELEFONE", "texto": "99123-4567"}],
        "distratores": [{"inicio": 48, "fim": 52, "tipo": "protocolo", "texto": "2026"}]}


def test_coberto_uniao_de_intervalos():
    assert demo.coberto(0, 10, [(0, 5), (5, 10)])
    assert not demo.coberto(0, 10, [(0, 5), (6, 10)])
    assert not demo.coberto(0, 10, [])


def test_avaliar_caso_pequeno():
    prev = {"n1": {"entidades": [{"tipo": "PHONE", "inicio": 9, "fim": 20, "texto": "12345678909"}],
                   "redigido": "Ana, CPF [PHONE_1], tel 99123-4567, protocolo 2026."}}
    m = demo.avaliar([NOTA], prev)
    assert m["por_tipo"]["BR_CPF"]["coberto"] == 1
    assert m["por_tipo"]["BR_CPF"].get("exato", 0) == 0  # tipo errado
    assert m["por_tipo"]["TELEFONE"]["vazou"] == 1
    assert m["notas_vazadas"] == 0


def test_corpus_tem_200_notas():
    assert len(demo.carregar()) == 200


def test_resultado_gravado_bate_com_o_corpus():
    notas = demo.carregar()
    m = json.loads((Path(demo.AQUI) / "results" / "metricas.json").read_text(encoding="utf-8"))
    assert m["notas"] == len(notas)
    for tipo in demo.TIPOS:
        esperado = sum(s["tipo"] == tipo for n in notas for s in n["spans"])
        assert m["por_tipo"][tipo]["suporte"] == esperado
