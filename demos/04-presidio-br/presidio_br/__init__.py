"""
presidio_br — reconhecedores brasileiros pro Microsoft Presidio.

Entidades:
  BR_CPF  Cadastro de Pessoa Física (11 dígitos, 2 dígitos verificadores mod 11)
  BR_CNS  Cartão Nacional de Saúde / cartão SUS (15 dígitos, checagem mod 11)

O regex acha o candidato. O dígito verificador decide se é PII.
"""

from .recognizers import BrCnsRecognizer, BrCpfRecognizer, registrar_reconhecedores_br
from .validators import validar_cns, validar_cpf

__all__ = [
    "BrCpfRecognizer",
    "BrCnsRecognizer",
    "registrar_reconhecedores_br",
    "validar_cpf",
    "validar_cns",
]

__version__ = "0.1.0"
