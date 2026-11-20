"""Confere as afirmações do artigo contra o que a demo gravou em results/.

Rode antes: python3 demo.py (precisa do .NET 8 SDK pra subir o servidor).
"""
import json
from pathlib import Path

import tiktoken

R = Path(__file__).resolve().parent.parent / "results"
O = json.loads((R / "resultado.json").read_text(encoding="utf-8"))


def test_csharp_sem_title_e_igual_a_definicao_a_mao():
    t = O["tokens"]
    print("\nC#:", t["csharp_definicoes_pro_modelo"]["o200k_base"],
          "| Python demo 13:", t["python_definicoes_pro_modelo_demo13"]["o200k_base"],
          "| Python sem title:", t["python_sem_title_demo13"]["o200k_base"])
    assert O["campos_title_no_tools_list"] == 0
    assert O["python_campos_title_demo13"] > 0
    assert t["csharp_definicoes_pro_modelo"] == t["python_sem_title_demo13"]
    assert t["csharp_definicoes_pro_modelo"]["o200k_base"] < t["python_definicoes_pro_modelo_demo13"]["o200k_base"]


def test_contagem_bate_com_tools_list_gravado():
    lista = json.loads((R / "tools_list.json").read_text(encoding="utf-8"))
    defs = [{"name": t["name"], "description": t["description"], "input_schema": t["inputSchema"]} for t in lista["tools"]]
    n = len(tiktoken.get_encoding("o200k_base").encode(json.dumps(defs, ensure_ascii=False, separators=(",", ":"))))
    assert n == O["tokens"]["csharp_definicoes_pro_modelo"]["o200k_base"]


def test_mesma_saida_da_demo_13():
    assert O["mascarar_igual_demo13"] is True


def test_servidor_aceita_qualquer_um():
    for caso, v in O["autenticacao"].items():
        print(caso, v)
        assert v["initialize"] == 200 and v["tools_call"] == 200 and v["devolveu_texto_mascarado"]


def test_rajada_sem_limite():
    r = O["rajada"]
    print("rajada:", r)
    assert r["status_200"] == r["chamadas"] == 500 and r["status_429"] == 0


def test_log_padrao_sem_argumento():
    assert O["log_padrao"]["cpf_da_nota_aparece_no_log"] is False
    assert O["log_padrao"]["linhas_que_citam_nome_de_ferramenta"] > 0
