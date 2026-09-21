"""
Geradores de valor pra cada placeholder do corpus.

CPF e CNS são válidos pelo dígito verificador (mesma conta da demo 04) e,
por construção, não pertencem a ninguém: são sorteados com seed fixa.
Os distratores são números que NÃO são dado pessoal.
"""

import random
import unicodedata

import frases as F
from demo04 import _cns_a_partir_do_pis, validar_cns, validar_cpf

GOLD = {"p": "PESSOA", "prof": "PESSOA", "cpf": "BR_CPF", "cns": "BR_CNS", "data": "DATA",
        "tel": "TELEFONE", "email": "EMAIL", "end": "ENDERECO"}
DISTRATOR = {"lote": "lote", "prot": "protocolo", "pa": "pressao_arterial", "dose": "dose",
             "leito": "leito", "med": "medicamento"}


def _digitos(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(n))


def gerar_cpf(rng: random.Random) -> str:
    """11 dígitos, dois verificadores mod 11. Rejeita sequências repetidas."""
    while True:
        d = _digitos(rng, 9)
        for tamanho in (9, 10):
            soma = sum(int(d[i]) * (tamanho + 1 - i) for i in range(tamanho))
            dv = (soma * 10) % 11
            d += str(0 if dv == 10 else dv)
        if validar_cpf(d):
            return d


def gerar_cns(rng: random.Random) -> str:
    """15 dígitos: definitivo (1/2, derivado do PIS) ou provisório (7/8/9)."""
    while True:
        if rng.random() < 0.5:
            cns = _cns_a_partir_do_pis(rng.choice("12") + _digitos(rng, 10))
        else:
            base = rng.choice("789") + _digitos(rng, 13)
            soma = sum(int(base[i]) * (15 - i) for i in range(14))
            cns = base + str((11 - soma % 11) % 11)
        if validar_cns(cns):
            return cns


def gerar_nome(rng: random.Random) -> str:
    primeiro = rng.choice(F.NOMES_COMPOSTOS if rng.random() < 0.5 else F.NOMES_SIMPLES)
    ultimo = rng.choice(F.SOBRENOMES_COMUNS if rng.random() < 0.5 else F.SOBRENOMES)
    meio = rng.choice(F.SOBRENOMES) + " " if rng.random() < 0.4 else ""
    return f"{primeiro} {meio}{ultimo}"


def _sem_acento(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def _data(rng: random.Random) -> str:
    dia, mes = rng.randint(1, 28), rng.randint(0, 11)
    if rng.random() < 0.5:
        ano = f" de {rng.choice([2025, 2026])}" if rng.random() < 0.5 else ""
        return f"{dia} de {F.MESES[mes]}{ano}"
    return f"{dia:02d}/{mes + 1:02d}/{rng.choice(['2025', '2026', '25', '26'])}"


def _telefone(rng: random.Random) -> str:
    celular = f"9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"
    forma = rng.choice(["parenteses", "espaco", "sem_ddd", "fixo_sem_ddd"])
    if forma == "parenteses":
        return f"({rng.choice(F.DDDS)}) {celular}"
    if forma == "espaco":
        return f"{rng.choice(F.DDDS)} {celular}"
    if forma == "sem_ddd":
        return celular
    return f"3{rng.randint(100, 999)}-{rng.randint(1000, 9999)}"


def _protocolo(rng: random.Random) -> str:
    """11 dígitos que NÃO fecham a conta do CPF."""
    while True:
        d = _digitos(rng, 11)
        if not validar_cpf(d):
            return d


def valor_de(chave: str, rng: random.Random, paciente: str) -> str:
    if chave == "p":
        return paciente
    if chave == "prof":
        return gerar_nome(rng)
    if chave == "cpf":
        c = gerar_cpf(rng)
        return c if rng.random() < 0.5 else f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"
    if chave == "cns":
        c = gerar_cns(rng)
        return c if rng.random() < 0.5 else f"{c[:3]} {c[3:7]} {c[7:11]} {c[11:]}"
    if chave == "data":
        return _data(rng)
    if chave == "tel":
        return _telefone(rng)
    if chave == "email":
        return f"{_sem_acento(paciente).lower().replace(' ', '.')}@{rng.choice(F.DOMINIOS)}"
    if chave == "end":
        return f"{rng.choice(F.RUAS)}, {rng.randint(10, 999)}, {rng.choice(F.BAIRROS)}"
    if chave == "lote":
        return _digitos(rng, 6)
    if chave == "prot":
        return _protocolo(rng)
    if chave == "pa":
        return f"{rng.choice([120, 130, 140, 150, 160])}x{rng.choice([80, 85, 90, 95, 100])}"
    if chave == "dose":
        return f"{rng.choice([12, 20, 25, 40])} {rng.choice(['mg', 'UI'])}"
    if chave == "leito":
        return f"{rng.randint(1, 40):02d}"
    if chave == "med":
        return rng.choice(F.MEDICAMENTOS_NOME_PROPRIO)
    raise KeyError(chave)
