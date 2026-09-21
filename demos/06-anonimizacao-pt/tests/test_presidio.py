"""Sistemas 1 e 2 rodam no CI, nas 200 notas, e imprimem a tabela."""

import evaluate
import run_presidio
from corpus import carregar


def test_presidio_padrao_e_br_nas_mesmas_notas():
    notas = carregar()
    for sistema in run_presidio.SISTEMAS:
        run_presidio.rodar(sistema, notas)
    res = evaluate.avaliar_todos(notas)
    print("\n" + evaluate.tabela_md(res, len(notas)))
    print(evaluate.dados_resultados(res))

    padrao, br = res["presidio_padrao"]["metricas"], res["presidio_br"]["metricas"]
    assert padrao["por_tipo"]["BR_CPF"]["recall"] == 0.0
    assert padrao["vazamento"]["taxa"] == 1.0
    assert br["por_tipo"]["BR_CPF"]["recall"] == 1.0
    assert br["por_tipo"]["BR_CNS"]["recall"] == 1.0
    assert br["vazamento"]["taxa"] == 0.0
    assert br["por_tipo"]["BR_CPF"]["fp"] == 0  # protocolos de 11 dígitos não viram CPF
