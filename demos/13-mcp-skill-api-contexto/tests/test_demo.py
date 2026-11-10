import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI))

import ferramentas  # noqa: E402


def test_validadores():
    assert ferramentas.validar_cpf("529.982.247-25")
    assert not ferramentas.validar_cpf("111.222.333-00")
    assert not ferramentas.validar_cpf("000.000.000-00")


def test_demo_roda_e_skill_carrega_menos_que_mcp_ate_ser_usada():
    subprocess.run([sys.executable, str(AQUI / "demo.py")], check=True, capture_output=True)
    r = json.loads((AQUI / "results" / "resultado.json").read_text(encoding="utf-8"))
    t = r["tokens"]
    mcp = t["mcp_definicoes_pro_modelo"]["o200k_base"]
    meta = t["skill_nivel1_metadado"]["o200k_base"]
    corpo = t["skill_nivel2_corpo"]["o200k_base"]
    print(f"\nMCP/API por pedido: {mcp} tokens · Skill parada: {meta} · Skill depois de usada: {meta + corpo}")
    assert meta < mcp
    assert "[CPF]" in r["saida_mascarada"] and "[CNS]" in r["saida_mascarada"]
    assert "111.222.333-00" in r["saida_mascarada"]
