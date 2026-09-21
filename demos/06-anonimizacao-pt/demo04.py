"""
Reuso fiel de demos/04-presidio-br/presidio_br, por caminho relativo.

Nada é reescrito aqui: os reconhecedores BR_CPF e BR_CNS e os validadores
de dígito verificador são os mesmos da demo 04.
"""

import sys
from pathlib import Path

DEMO04 = Path(__file__).resolve().parent.parent / "04-presidio-br"
if str(DEMO04) not in sys.path:
    sys.path.insert(0, str(DEMO04))

from presidio_br import registrar_reconhecedores_br  # noqa: E402
from presidio_br.validators import _cns_a_partir_do_pis, validar_cns, validar_cpf  # noqa: E402

__all__ = ["registrar_reconhecedores_br", "validar_cpf", "validar_cns", "_cns_a_partir_do_pis"]
