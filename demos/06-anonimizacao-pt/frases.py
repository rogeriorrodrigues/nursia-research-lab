"""
Listas e modelos de frase do corpus sintético.

Placeholders: {p} paciente, {prof} profissional, {cpf}, {cns}, {data},
{tel}, {email}, {end} são entidades (gold). {lote}, {prot}, {pa}, {dose},
{leito}, {med} são distratores: números e nomes que NÃO são dado pessoal.
Todos os nomes, ruas e números são inventados.
"""

NOMES_SIMPLES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Helena", "Igor",
                 "Júlia", "Leandro", "Marina", "Otávio", "Paula", "Rafael", "Sofia", "Tiago"]
NOMES_COMPOSTOS = ["Maria Clara", "João Pedro", "Ana Luísa", "José Carlos", "Luiz Felipe",
                   "Maria Eduarda", "Pedro Henrique", "Ana Beatriz"]
SOBRENOMES_COMUNS = ["Rosa", "Pereira", "Machado"]  # também são palavras comuns
SOBRENOMES = ["Ferreira", "Almeida", "Ribeiro", "Cardoso", "Teixeira", "Nogueira",
              "Barbosa", "Moreira"]

MEDICAMENTOS_NOME_PROPRIO = ["Yasmin", "Diane 35", "Selene", "Elani"]
RUAS = ["Rua das Acácias", "Avenida dos Ipês", "Travessa das Gaivotas", "Rua do Mirante",
        "Rua Lagoa Azul", "Rua dos Jasmins"]
BAIRROS = ["Trindade", "Centro", "Estreito", "Campeche", "Saco Grande"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
DDDS = ["48", "47", "49", "11", "21"]
DOMINIOS = ["exemplo.com.br", "exemplo.org"]

ESTILOS = ["evolucao", "alta", "encaminhamento", "prescricao"]

ABERTURA = {
    "evolucao": [
        "Evolução de enfermagem: paciente {p}, CPF {cpf}, no leito {leito}, segue em observação.",
        "Paciente {p}, cartão SUS {cns}, evolui estável no leito {leito}.",
        "{p}, CPF {cpf}, refere melhora da dor após medicação.",
        "Evolução: {p} (CNS {cns}) mantém saturação 92% em ar ambiente.",
    ],
    "alta": [
        "Alta hospitalar de {p}, CPF {cpf}, após 4 dias de internação.",
        "Sumário de alta: {p}, CNS {cns}, internação por pneumonia comunitária.",
        "Paciente {p}, cartão SUS {cns}, recebe alta com receita e orientações.",
        "Alta do leito {leito}: {p}, CPF {cpf}, quadro compensado.",
    ],
    "encaminhamento": [
        "Encaminhamento de {p}, CPF {cpf}, para avaliação cardiológica ambulatorial.",
        "Solicito avaliação de {p}, CNS {cns}, pela equipe de fisioterapia.",
        "Paciente {p}, cartão SUS {cns}, encaminhado para retorno em atenção primária.",
        "Referência: {p}, CPF {cpf}, com dor torácica atípica em investigação.",
    ],
    "prescricao": [
        "Prescrição para {p}, CPF {cpf}: furosemida {dose} VO 1x/dia.",
        "Prescrição de enfermagem para {p}, CNS {cns}: curativo diário em MID.",
        "Paciente {p}, cartão SUS {cns}: manter dieta hipossódica e controle de PA.",
        "{p}, CPF {cpf}: insulina NPH {dose} SC antes do café.",
    ],
}

SEGUNDO_DOCUMENTO = [
    "Documento complementar: CPF {cpf}.",
    "Cartão SUS informado na recepção: {cns}.",
]

MEIO = [
    "Contato do responsável: {tel}.",
    "Telefone para retorno: {tel}.",
    "E-mail para envio do laudo: {email}.",
    "Reside na {end}, conforme cadastro.",
    "Endereço atualizado: {end}.",
    "Internação em {data} pela emergência.",
    "Última consulta em {data}.",
    "PA {pa} mmHg, FC 88 bpm, afebril.",
    "Administrado {dose} de furosemida VO conforme prescrição.",
    "Curativo trocado com soro fisiológico lote {lote}.",
    "Solicitação de exame registrada no protocolo {prot}.",
    "Transferência para o leito {leito} da clínica médica.",
    "Em uso de {med} há 2 anos, sem intercorrências.",
    "Avaliação feita pela enfermeira {prof} no período da tarde.",
    "Caso discutido com {prof}, médico assistente.",
    "Nega alergias medicamentosas conhecidas.",
    "Diurese presente, evacuações ausentes há 2 dias.",
    "Orientação sobre sinais de alerta e retorno.",
    "Acompanhante presente durante todo o plantão.",
    "Glicemia capilar 182 mg/dL antes do almoço.",
    "Deambula com auxílio, risco de queda moderado.",
]

FECHAMENTO = {
    "evolucao": ["Segue em observação, {p} sem queixas no momento.",
                 "Plantão passado às 19h sem intercorrências."],
    "alta": ["Retorno ambulatorial marcado para {data}.",
             "Alta com receita e orientações entregues a {p}."],
    "encaminhamento": ["Avaliação agendada para {data}.",
                       "Contato do serviço de referência: {tel}."],
    "prescricao": ["Prescrição válida até {data}.",
                   "Dúvidas pelo e-mail {email}."],
}
