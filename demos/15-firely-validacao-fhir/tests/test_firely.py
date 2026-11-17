"""Roda a demo do zero (dotnet run) numa pasta temporária e confere os números do artigo."""
import hashlib
import json
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent


def test_mesmos_240_recursos_da_demo_11():
    sha = hashlib.sha256((AQUI / "data" / "recursos.jsonl").read_bytes()).hexdigest()
    assert sha == "82b438f357c7be26e963d94d0ba6f153314b9a2e559e8dcfc77d15ed81bfa91d"


def test_firely_pega_forma_e_obs6_mas_nao_a_referencia(tmp_path):
    subprocess.run(
        ["dotnet", "run", "-c", "Release", "--project", str(AQUI / "src"), "--",
         str(AQUI / "data" / "recursos.jsonl"), str(tmp_path)],
        check=True, capture_output=True, text=True, timeout=600,
    )
    m = json.loads((tmp_path / "metricas.json").read_text(encoding="utf-8"))
    cat = m["por_categoria"]
    print(f"\nforma {m['forma_reprovados']}/{m['forma_total']} · conteúdo "
          f"{m['conteudo_reprovados']}/{m['conteudo_total']} · total "
          f"{m['defeitos_reprovados']}/{m['defeitos_total']} · válidos reprovados "
          f"{m['validos_reprovados']}/{m['validos_total']} · referência com UUID válido "
          f"{m['controle_referencia']['A_quebrada_reprovados']}/20")
    assert (m["forma_reprovados"], m["forma_total"]) == (80, 80)
    assert (m["conteudo_reprovados"], m["conteudo_total"]) == (40, 100)
    assert m["validos_reprovados"] == 0
    assert cat["invariante_obs6"]["pelo_validador"] == 20
    assert cat["invariante_obs6"]["pelo_parser"] == 0
    for c in ("loinc_inventado", "unidade_ucum_invalida", "cpf_digito_invalido"):
        assert cat[c]["reprovados"] == 0
    # os 20 Bundles caem pelo fullUrl "urn:uuid:pac-000" (não é UUID), não pela referência
    assert cat["referencia_quebrada"]["pelo_parser"] == 20
    assert m["controle_referencia"]["A_quebrada_reprovados"] == 0
    assert m["controle_referencia"]["B_correta_reprovados"] == 0
