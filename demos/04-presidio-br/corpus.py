"""
Corpus sintético em português pra medir o Presidio antes e depois
dos reconhecedores brasileiros.

Tudo é gerado por construção, com seed fixa: nenhum CPF, CNS ou nome
aqui pertence a uma pessoa real. Os CPFs e CNSs são válidos pela conta
do dígito verificador, e os distratores são inválidos pela mesma conta.

Três fatias de 100 textos:
  cpf         → frase clínica com um CPF válido
  cns         → frase clínica com um CNS válido
  distratores → frase com um número de 11 dígitos que NÃO é CPF
                (protocolo, nota fiscal, CPF digitado errado)
"""

import random
from dataclasses import dataclass
from typing import List

from presidio_br.validators import _cns_a_partir_do_pis, validar_cns, validar_cpf

SEED = 2026

NOMES = [
    "Maria S.", "João P.", "Ana L.", "Carlos M.", "Fernanda R.", "Paulo H.",
    "Juliana C.", "Roberto A.", "Beatriz T.", "Marcos V.", "Luciana F.",
    "André G.", "Patrícia N.", "Ricardo B.", "Camila D.", "Eduardo O.",
]

TEMPLATES_CPF = [
    "Paciente {nome}, CPF {doc}, admitida na enfermaria com dispneia aos esforços.",
    "Evolução de enfermagem: {nome} (CPF {doc}) refere dor torácica há 2h, PA 150x95.",
    "Encaminhamento: {nome}, CPF {doc}, para avaliação cardiológica ambulatorial.",
    "Termo de consentimento assinado por {nome}, portador do CPF {doc}.",
    "Alta hospitalar de {nome}, CPF {doc}, com orientação de retorno em 7 dias.",
    "Prescrição para {nome} (CPF {doc}): furosemida 40 mg VO 1x/dia.",
    "{nome}, CPF {doc}, comparece à UBS para renovação de receita.",
    "Notificação: {nome}, CPF {doc}, resultado de glicemia de jejum 182 mg/dL.",
]

TEMPLATES_CNS = [
    "Paciente {nome}, cartão SUS {doc}, atendida na triagem com febre há 3 dias.",
    "Evolução: {nome} (CNS {doc}) mantém saturação 92% em ar ambiente.",
    "Agendamento de ultrassom para {nome}, CNS {doc}, na próxima quinta.",
    "Registro de vacinação de {nome}, cartão nacional de saúde {doc}.",
    "Encaminhado {nome}, CNS {doc}, para fisioterapia motora.",
    "Consulta de retorno de {nome} (cartão SUS {doc}) reagendada.",
    "Dispensação de insulina NPH para {nome}, CNS {doc}.",
    "{nome}, CNS {doc}, apresenta edema em membros inferiores 2+/4+.",
]

TEMPLATES_DISTRATOR = [
    "Protocolo de atendimento {doc} aberto para reposição de material.",
    "Nota fiscal {doc} referente à compra de luvas de procedimento.",
    "Número do pedido {doc} liberado pela farmácia central.",
    "Registro interno {doc} do equipamento de oximetria.",
    "Lote {doc} de soro fisiológico conferido no almoxarifado.",
    "Ordem de serviço {doc} da manutenção do ar-condicionado da UTI.",
    "CPF informado com erro de digitação: {doc}. Solicitar correção na recepção.",
    "Documento {doc} não confere com o cadastro. Verificar com o paciente.",
]


@dataclass
class Amostra:
    texto: str
    doc: str        # o número, do jeito que aparece no texto
    inicio: int     # posição do número no texto
    fim: int
    tipo: str       # cpf | cns | distrator


def _dv_cpf(digitos: str) -> str:
    for tamanho in (9, 10):
        soma = sum(int(digitos[i]) * (tamanho + 1 - i) for i in range(tamanho))
        dv = (soma * 10) % 11
        digitos += str(0 if dv == 10 else dv)
    return digitos


def gerar_cpf(rng: random.Random) -> str:
    while True:
        base = "".join(rng.choice("0123456789") for _ in range(9))
        cpf = _dv_cpf(base)
        if validar_cpf(cpf):
            break
    if rng.random() < 0.7:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def gerar_cns(rng: random.Random) -> str:
    while True:
        if rng.random() < 0.5:
            # definitivo: começa com 1 ou 2, derivado do PIS
            pis = rng.choice("12") + "".join(rng.choice("0123456789") for _ in range(10))
            cns = _cns_a_partir_do_pis(pis)
        else:
            # provisório: começa com 7, 8 ou 9, soma ponderada múltipla de 11
            base = rng.choice("789") + "".join(rng.choice("0123456789") for _ in range(13))
            soma = sum(int(base[i]) * (15 - i) for i in range(14))
            ultimo = (11 - soma % 11) % 11
            if ultimo == 10:
                continue
            cns = base + str(ultimo)
        if validar_cns(cns):
            break
    if rng.random() < 0.5:
        return f"{cns[:3]} {cns[3:7]} {cns[7:11]} {cns[11:]}"
    return cns


def gerar_distrator(rng: random.Random, template: str) -> str:
    """11 dígitos que NÃO fecham a conta do CPF."""
    while True:
        d = "".join(rng.choice("0123456789") for _ in range(11))
        if not validar_cpf(d):
            break
    if "CPF" in template or "Documento" in template:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return d


def gerar_corpus(n_por_tipo: int = 100, seed: int = SEED) -> List[Amostra]:
    rng = random.Random(seed)
    amostras: List[Amostra] = []

    for tipo, templates, gerador in (
        ("cpf", TEMPLATES_CPF, lambda t: gerar_cpf(rng)),
        ("cns", TEMPLATES_CNS, lambda t: gerar_cns(rng)),
        ("distrator", TEMPLATES_DISTRATOR, lambda t: gerar_distrator(rng, t)),
    ):
        for i in range(n_por_tipo):
            template = templates[i % len(templates)]
            doc = gerador(template)
            texto = template.format(nome=rng.choice(NOMES), doc=doc)
            inicio = texto.index(doc)
            amostras.append(Amostra(texto, doc, inicio, inicio + len(doc), tipo))

    return amostras


if __name__ == "__main__":
    for a in gerar_corpus(3):
        print(f"[{a.tipo}] {a.texto}")
