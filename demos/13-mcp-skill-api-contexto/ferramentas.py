"""As 4 ferramentas da demo. O mesmo código atende as três vias (MCP, API e Skill).

Dado sintético: os CPFs e CNS de exemplo são gerados por algoritmo e não
pertencem a ninguém.
"""
import re

_CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
_CNS = re.compile(r"\b[1-9]\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b")


def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor)


def validar_cpf(cpf: str) -> bool:
    """Confere os dois dígitos verificadores de um CPF (11 dígitos, com ou sem pontuação)."""
    d = _so_digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        dv = (soma * 10) % 11 % 10
        if dv != int(d[n]):
            return False
    return True


def validar_cns(cns: str) -> bool:
    """Confere o Cartão Nacional de Saúde (15 dígitos) pela soma ponderada módulo 11."""
    d = _so_digitos(cns)
    if len(d) != 15 or d[0] not in "126789":
        return False
    return sum(int(d[i]) * (15 - i) for i in range(15)) % 11 == 0


def mascarar_identificadores(texto: str) -> str:
    """Troca CPF e CNS válidos do texto por [CPF] e [CNS]. Número inválido fica como está."""
    texto = _CNS.sub(lambda m: "[CNS]" if validar_cns(m.group()) else m.group(), texto)
    return _CPF.sub(lambda m: "[CPF]" if validar_cpf(m.group()) else m.group(), texto)


def contar_identificadores(texto: str) -> dict:
    """Conta quantos CPF e CNS válidos e inválidos aparecem no texto, sem devolver os números."""
    cpfs = _CPF.findall(texto)
    cnss = _CNS.findall(texto)
    return {
        "cpf_validos": sum(validar_cpf(c) for c in cpfs),
        "cpf_invalidos": sum(not validar_cpf(c) for c in cpfs),
        "cns_validos": sum(validar_cns(c) for c in cnss),
        "cns_invalidos": sum(not validar_cns(c) for c in cnss),
    }


FERRAMENTAS = [validar_cpf, validar_cns, mascarar_identificadores, contar_identificadores]
