import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import demo  # noqa: E402
from hl7gen.fhir_export import UnsupportedMessageTypeError, message_to_fhir  # noqa: E402
from hl7gen.generator import generate_message  # noqa: E402
from hl7gen.validator import validate_message  # noqa: E402


def test_cpf_e_cns_do_pid3_nao_chegam_ao_bundle():
    bundle, erro = demo.converter(demo.MSG_BR)
    assert erro is None
    paciente = bundle["entry"][0]["resource"]
    assert "identifier" not in paciente
    texto = json.dumps(bundle, ensure_ascii=False)
    assert "52998224725" not in texto
    assert "898001234567891" not in texto


def test_acentos_sobrevivem():
    bundle, _ = demo.converter(demo.MSG_BR)
    nome = bundle["entry"][0]["resource"]["name"][0]
    assert nome["family"] == "Conceição"
    assert bundle["entry"][0]["resource"]["address"][0]["city"] == "Florianópolis"


def test_validador_aceita_data_impossivel_e_conversor_quebra():
    ruim = demo.MSG_BR.replace("19800315", "20261345")
    assert validate_message(ruim).valid
    _, erro = demo.converter(ruim)
    assert erro == "ValidationError"


def test_tipo_fora_da_lista_e_recusado():
    msg = generate_message("ACK")
    assert validate_message(msg).valid
    with pytest.raises(UnsupportedMessageTypeError):
        message_to_fhir(msg, "R4B")


def test_semente_reproduz_a_mensagem():
    demo.semear()
    a = generate_message("ADT_A02")
    demo.semear()
    assert generate_message("ADT_A02") == a


def test_lote_pequeno_tem_nome_token_e_telefone_cru():
    demo.semear()
    for _ in range(3):
        msg = generate_message("ADT_A01")
        bundle, erro = demo.converter(msg)
        assert erro is None
        paciente = bundle["entry"][0]["resource"]
        assert demo.TOKEN.match(paciente["name"][0]["family"])
        assert "^" in paciente["telecom"][0]["value"]
