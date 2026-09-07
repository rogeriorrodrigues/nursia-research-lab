from presidio_br import BrCnsRecognizer, BrCpfRecognizer


def _entidades(reconhecedor, texto):
    return [(r.entity_type, texto[r.start:r.end], r.score)
            for r in reconhecedor.analyze(texto, entities=reconhecedor.supported_entities)]


def test_cpf_valido_recebe_score_maximo():
    r = BrCpfRecognizer()
    saida = _entidades(r, "Paciente Ana L., CPF 158.813.998-03, admitida hoje.")
    assert saida == [("BR_CPF", "158.813.998-03", 1.0)]


def test_cpf_invalido_e_descartado_com_digito_verificador():
    r = BrCpfRecognizer()
    assert _entidades(r, "Protocolo 158.813.998-04 aberto.") == []


def test_cpf_invalido_passa_no_modo_so_regex():
    r = BrCpfRecognizer(validar=False)
    saida = _entidades(r, "Protocolo 158.813.998-04 aberto.")
    assert [s[0] for s in saida] == ["BR_CPF"]


def test_cns_valido_com_espacos():
    r = BrCnsRecognizer()
    saida = _entidades(r, "Cartão SUS 768 9768 4697 8807 conferido.")
    assert saida == [("BR_CNS", "768 9768 4697 8807", 1.0)]


def test_cns_invalido_e_descartado():
    r = BrCnsRecognizer()
    assert _entidades(r, "Cartão SUS 768976846978808 conferido.") == []
