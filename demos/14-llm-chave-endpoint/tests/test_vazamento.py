"""Prova a afirmação central: 0.37.1 manda a chave da OpenAI pro endpoint de
terceiro em 3 de 5 cenários; 0.37.2 em 0. Os controles B e C não mudam."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import demo  # noqa: E402


def test_vazamento_por_versao():
    r = demo.main()
    v1, v2 = r["versoes"]["0.37.1"], r["versoes"]["0.37.2"]
    vaz1 = [l["cenario"] for l in v1 if l["vazou_chave_openai"]]
    vaz2 = [l["cenario"] for l in v2 if l["vazou_chave_openai"]]
    print(f"\n0.37.1 vazou em {len(vaz1)} de 5 ({vaz1}); 0.37.2 em {len(vaz2)} de 5")
    assert vaz1 == ["A", "D", "E"]
    assert vaz2 == []
    # A no 0.37.2 falha antes de mandar qualquer pedido
    a2 = v2[0]
    assert a2["pedidos_no_endpoint"] == 0 and "No key found" in a2["saida_cli"]
    # controles iguais nas duas versões
    for i in (1, 2):
        assert v1[i]["authorization_recebido"] == v2[i]["authorization_recebido"]
