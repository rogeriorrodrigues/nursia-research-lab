"""
Validadores de dígito verificador pra documentos brasileiros.

Só aritmética. Nenhuma dependência do Presidio, pra poder testar sozinho.
"""

import re

_SO_DIGITOS = re.compile(r"\D")


def _digitos(valor: str) -> str:
    return _SO_DIGITOS.sub("", valor)


def validar_cpf(valor: str) -> bool:
    """
    Valida um CPF pelos dois dígitos verificadores (mod 11).

    Aceita com ou sem pontuação: '123.456.789-09' ou '12345678909'.
    Rejeita sequências repetidas ('111.111.111-11'), que passam na conta
    mas a Receita Federal não emite.
    """
    d = _digitos(valor)
    if len(d) != 11 or d == d[0] * 11:
        return False

    for tamanho in (9, 10):
        soma = sum(int(d[i]) * (tamanho + 1 - i) for i in range(tamanho))
        dv = (soma * 10) % 11
        if dv == 10:
            dv = 0
        if dv != int(d[tamanho]):
            return False
    return True


def validar_cns(valor: str) -> bool:
    """
    Valida um Cartão Nacional de Saúde (CNS) de 15 dígitos.

    Dois algoritmos, conforme o primeiro dígito (regra do DATASUS):
      1 ou 2  → número derivado do PIS: os 11 primeiros dígitos geram
                 os 4 finais (000 ou 001 + dígito verificador).
      7, 8, 9 → número provisório: soma ponderada (pesos 15..1) tem
                 que ser múltipla de 11.
    """
    d = _digitos(valor)
    if len(d) != 15:
        return False

    if d[0] in "12":
        return _cns_a_partir_do_pis(d[:11]) == d
    if d[0] in "789":
        soma = sum(int(d[i]) * (15 - i) for i in range(15))
        return soma % 11 == 0
    return False


def _cns_a_partir_do_pis(pis: str) -> str:
    """Reconstrói o CNS completo a partir dos 11 primeiros dígitos."""
    soma = sum(int(pis[i]) * (15 - i) for i in range(11))
    resto = soma % 11
    dv = 11 - resto
    if dv == 11:
        dv = 0
    if dv == 10:
        soma += 2
        resto = soma % 11
        dv = 11 - resto
        return f"{pis}001{dv}"
    return f"{pis}000{dv}"
