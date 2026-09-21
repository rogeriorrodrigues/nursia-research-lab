"""Se results/raw/ dos LLMs estiver commitado, recalcula a métrica; se não, pula."""

import pytest

import evaluate
from corpus import carregar
from run_llms import interpretar, para_spans


def test_parse_json_invalido_conta_como_zero():
    assert interpretar("isso não é json") is None
    assert interpretar('{"entidades": "x"}') is None
    assert interpretar('{"entidades": []}') == []
    assert interpretar('[{"tipo": "PESSOA", "texto": "Ana"}]') == [{"tipo": "PESSOA", "texto": "Ana"}]


def test_texto_vira_todas_as_ocorrencias():
    texto = "Ana Rosa, CPF 123. Alta entregue a Ana Rosa."
    spans, nao = para_spans(texto, [{"tipo": "PESSOA", "texto": "Ana Rosa"},
                                    {"tipo": "BR_CPF", "texto": "999"},
                                    {"tipo": "INVENTADO", "texto": "Ana"}])
    assert [(s["inicio"], s["fim"]) for s in spans] == [(0, 8), (35, 43)]
    assert nao == 2


@pytest.mark.parametrize("sistema", ["ollama_qwen", "ollama_phi"])
def test_metrica_dos_llms_a_partir_do_raw(sistema):
    dados = evaluate.carregar_sistema(sistema)
    if dados is None:
        pytest.skip(f"AVISO: results/raw/{sistema}.jsonl não existe; rode python3 run_llms.py {sistema}")
    notas = carregar()
    res = evaluate.avaliar_todos(notas)
    print("\n" + evaluate.dados_resultados({sistema: res[sistema]}))
    assert dados["n_notas"] == len(notas), "resultado parcial: run_llms.py não terminou"
