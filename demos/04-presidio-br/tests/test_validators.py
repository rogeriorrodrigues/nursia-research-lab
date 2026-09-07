from presidio_br.validators import validar_cns, validar_cpf


def test_cpf_valido_com_e_sem_pontuacao():
    # CPF sintético, fecha a conta do dígito verificador
    assert validar_cpf("158.813.998-03")
    assert validar_cpf("15881399803")


def test_cpf_com_digito_errado_falha():
    assert not validar_cpf("158.813.998-04")


def test_cpf_sequencia_repetida_falha():
    assert not validar_cpf("111.111.111-11")


def test_cpf_tamanho_errado_falha():
    assert not validar_cpf("1588139980")
    assert not validar_cpf("158813998031")


def test_cns_definitivo_valido():
    # começa com 1 ou 2, derivado do PIS
    assert validar_cns("204587901660008")


def test_cns_provisorio_valido():
    # começa com 7, 8 ou 9, soma ponderada múltipla de 11
    assert validar_cns("768976846978807")
    assert validar_cns("768 9768 4697 8807")


def test_cns_com_digito_errado_falha():
    assert not validar_cns("768976846978808")
    assert not validar_cns("204587901660009")


def test_cns_prefixo_invalido_falha():
    assert not validar_cns("368976846978807")
