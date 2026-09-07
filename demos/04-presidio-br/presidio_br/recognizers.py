"""
Reconhecedores BR_CPF e BR_CNS pro Presidio Analyzer.

Segue o mesmo desenho dos reconhecedores country_specific do Presidio
(ex.: ItFiscalCodeRecognizer, EsNifRecognizer): PatternRecognizer com
regex de baixa confiança e validate_result() com o dígito verificador.

Sem validate_result, todo número de 11 dígitos vira "CPF".
Com validate_result, só o que fecha a conta passa.
"""

from typing import List, Optional

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer

from .validators import validar_cns, validar_cpf


class BrCpfRecognizer(PatternRecognizer):
    """Reconhece o CPF (Cadastro de Pessoa Física), com ou sem pontuação."""

    PATTERNS = [
        Pattern(
            "CPF pontuado",
            r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
            0.5,
        ),
        Pattern(
            "CPF sem pontuação",
            r"\b\d{11}\b",
            0.1,
        ),
    ]

    CONTEXT = ["cpf", "cadastro de pessoa física", "documento", "titular"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "BR_CPF",
        validar: bool = True,
    ):
        self.validar = validar
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns or self.PATTERNS,
            context=context or self.CONTEXT,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """
        True  → score vai pra 1.0
        False → resultado descartado
        None  → fica o score do regex (modo 'só regex', usado na comparação)
        """
        if not self.validar:
            return None
        return validar_cpf(pattern_text)


class BrCnsRecognizer(PatternRecognizer):
    """Reconhece o CNS (Cartão Nacional de Saúde, o 'cartão SUS')."""

    PATTERNS = [
        Pattern(
            "CNS com espaços",
            r"\b[1-2789]\d{2} ?\d{4} ?\d{4} ?\d{4}\b",
            0.3,
        ),
        Pattern(
            "CNS sem espaços",
            r"\b[1-2789]\d{14}\b",
            0.1,
        ),
    ]

    CONTEXT = ["cns", "cartão sus", "cartao sus", "cartão nacional de saúde", "sus"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "BR_CNS",
        validar: bool = True,
    ):
        self.validar = validar
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns or self.PATTERNS,
            context=context or self.CONTEXT,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        if not self.validar:
            return None
        return validar_cns(pattern_text)


def registrar_reconhecedores_br(analyzer: AnalyzerEngine, validar: bool = True) -> None:
    """Adiciona BR_CPF e BR_CNS num AnalyzerEngine já criado."""
    analyzer.registry.add_recognizer(BrCpfRecognizer(validar=validar))
    analyzer.registry.add_recognizer(BrCnsRecognizer(validar=validar))
