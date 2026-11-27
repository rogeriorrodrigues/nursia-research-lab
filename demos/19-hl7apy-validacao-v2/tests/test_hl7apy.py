import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hl7apy.consts import VALIDATION_LEVEL  # noqa: E402

from demo import checa  # noqa: E402
from gera_hl7 import cns_valida, cpf_valida, gera  # noqa: E402


def test_sinteticos_tem_documento_valido_por_algoritmo():
    msgs = [m for m in gera() if m["tipo"] == "valida"]
    assert all(cpf_valida(m["cpf"]) and cns_valida(m["cns"]) for m in msgs)


def test_strict_aceita_conteudo_errado_e_fora_de_ordem():
    msgs = gera()
    for tipo in ("cpf_digito_errado", "cns_invalido", "sexo_fora_da_tabela", "nascimento_no_futuro", "fora_de_ordem"):
        lote = [m for m in msgs if m["tipo"] == tipo][:5]
        aceitas = sum(not checa(m["er7"], VALIDATION_LEVEL.STRICT)[0] for m in lote)
        print(f"{tipo}: {aceitas}/5 aceitas no STRICT")
        assert aceitas == 5


def test_strict_reprova_data_invalida_e_tolerant_aceita():
    lote = [m for m in gera() if m["tipo"] == "data_invalida"][:5]
    strict = sum(checa(m["er7"], VALIDATION_LEVEL.STRICT)[0] for m in lote)
    tolerant = sum(checa(m["er7"], VALIDATION_LEVEL.TOLERANT)[0] for m in lote)
    print(f"data_invalida: STRICT reprovou {strict}/5, TOLERANT {tolerant}/5")
    assert strict == 5 and tolerant == 0


def test_regras_br_pegam_o_que_o_strict_deixou_e_nao_reprovam_validas():
    from demo import regras_br
    msgs = gera()
    validas = [m for m in msgs if m["tipo"] == "valida"]
    conteudo = [m for m in msgs if m["grupo"] == "conteudo"]
    falsos = sum(bool(regras_br(m["er7"])) for m in validas)
    pegas = sum(bool(regras_br(m["er7"])) for m in conteudo)
    print(f"regras_br: {pegas}/{len(conteudo)} de conteúdo, {falsos}/{len(validas)} válidas reprovadas")
    assert pegas == len(conteudo) and falsos == 0
