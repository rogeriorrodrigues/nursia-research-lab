"""Gera mensagens HL7 v2.5 ADT^A01 100% sintéticas, com e sem defeito plantado.

CPF e CNS são válidos por algoritmo (dígito verificador), mas gerados ao acaso:
não pertencem a pessoas conhecidas. Nomes são fictícios e óbvios (TESTE).
"""
import random

SEED = 20261127
TIPOS_FORMA = ["sem_pid", "sem_nome", "data_invalida", "campo_longo", "pid_duplicado", "fora_de_ordem"]
TIPOS_CONTEUDO = ["cpf_digito_errado", "cns_invalido", "sexo_fora_da_tabela", "nascimento_no_futuro"]
POR_TIPO = 20
VALIDAS = 40

SOBRENOMES = ["SILVA", "SOUZA", "OLIVEIRA", "PEREIRA", "COSTA", "ALMEIDA", "RIBEIRO", "CARVALHO"]
NOMES = ["ANA", "BRUNO", "CARLA", "DIEGO", "ELISA", "FABIO", "GABRIELA", "HUGO"]


def cpf_valido(rng):
    base = [rng.randint(0, 9) for _ in range(9)]
    for n in (10, 11):
        s = sum(d * (n - i) for i, d in enumerate(base))
        dv = (s * 10) % 11
        base.append(0 if dv == 10 else dv)
    return "".join(map(str, base))


def cpf_errado(rng):
    c = cpf_valido(rng)
    return c[:-1] + str((int(c[-1]) + 1) % 10)


def cns_valido(rng):
    # CNS definitivo iniciado em 1 ou 2: 11 dígitos + "00" ou "001" + DV (regra do Ministério da Saúde)
    while True:
        pis = str(rng.choice([1, 2])) + "".join(str(rng.randint(0, 9)) for _ in range(10))
        soma = sum(int(d) * (15 - i) for i, d in enumerate(pis))
        dv = 11 - soma % 11
        if dv == 11:
            dv = 0
        if dv == 10:
            soma += 2
            dv = 11 - soma % 11
            return pis + "001" + str(dv)
        return pis + "000" + str(dv)


def cns_valida(cns):
    if len(cns) != 15 or not cns.isdigit():
        return False
    if cns[0] in "12":
        if cns[11:15] not in ("0000", "0001") and cns[11:14] not in ("000", "001"):
            return False
    return sum(int(d) * (15 - i) for i, d in enumerate(cns)) % 11 == 0


def cpf_valida(cpf):
    if len(cpf) != 11 or not cpf.isdigit() or len(set(cpf)) == 1:
        return False
    d = list(map(int, cpf))
    for n in (9, 10):
        s = sum(d[i] * (n + 1 - i) for i in range(n))
        dv = (s * 10) % 11
        if (0 if dv == 10 else dv) != d[n]:
            return False
    return True


def _segmentos(rng, i, cpf, cns, nome, nasc, sexo):
    ts = "20261126%02d%02d00" % (8 + i % 10, i % 60)
    msh = f"MSH|^~\\&|SINTETICO|HOSP_TESTE|DESTINO|FAC_TESTE|{ts}||ADT^A01^ADT_A01|MSG{i:05d}|P|2.5"
    evn = f"EVN|A01|{ts}"
    pid = f"PID|1||{cpf}^^^CPF^TAX~{cns}^^^CNS^HC||{nome}||{nasc}|{sexo}"
    pv1 = "PV1|1|I|UTI^01^A"
    return msh, evn, pid, pv1


def gera(seed=SEED):
    """Lista de dicts: id, tipo, grupo (valida | forma | conteudo), er7, cpf, cns."""
    rng = random.Random(seed)
    tipos = ["valida"] * VALIDAS + [t for t in TIPOS_FORMA + TIPOS_CONTEUDO for _ in range(POR_TIPO)]
    out = []
    for i, tipo in enumerate(tipos):
        cpf, cns = cpf_valido(rng), cns_valido(rng)
        nome = f"{rng.choice(SOBRENOMES)} TESTE^{rng.choice(NOMES)}"
        nasc = "%04d%02d%02d" % (rng.randint(1940, 2015), rng.randint(1, 12), rng.randint(1, 28))
        sexo = rng.choice(["F", "M"])
        if tipo == "sem_nome":
            nome = ""
        elif tipo == "data_invalida":
            nasc = rng.choice([nasc[:4] + "13" + nasc[6:], nasc[:6] + "32", f"{nasc[6:]}/{nasc[4:6]}/{nasc[:4]}"])
        elif tipo == "campo_longo":
            nome = nome.split("^")[0] + " " + "X" * 200 + "^" + nome.split("^")[1]
        elif tipo == "cpf_digito_errado":
            cpf = cpf_errado(rng)
        elif tipo == "cns_invalido":
            cns = cns[:-1] + str((int(cns[-1]) + 1) % 10)
        elif tipo == "sexo_fora_da_tabela":
            sexo = rng.choice(["X", "H", "Masculino"])
        elif tipo == "nascimento_no_futuro":
            nasc = "%04d%02d%02d" % (rng.randint(2030, 2099), rng.randint(1, 12), rng.randint(1, 28))
        msh, evn, pid, pv1 = _segmentos(rng, i, cpf, cns, nome, nasc, sexo)
        if tipo == "sem_pid":
            segs = [msh, evn, pv1]
        elif tipo == "pid_duplicado":
            segs = [msh, evn, pid, pid, pv1]
        elif tipo == "fora_de_ordem":
            segs = [msh, evn, pv1, pid]
        else:
            segs = [msh, evn, pid, pv1]
        grupo = "valida" if tipo == "valida" else ("forma" if tipo in TIPOS_FORMA else "conteudo")
        out.append({"id": f"MSG{i:05d}", "tipo": tipo, "grupo": grupo, "er7": "\r".join(segs), "cpf": cpf, "cns": cns})
    return out
