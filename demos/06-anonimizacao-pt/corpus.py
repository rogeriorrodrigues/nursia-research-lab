"""
Corpus sintético: 200 notas clínicas em português, 3 a 6 frases cada,
com spans de entidade anotados por offset de caractere.

Seed fixa (2026). Nenhum nome, documento, telefone ou endereço aqui é
de uma pessoa real: tudo é sorteado de listas inventadas em frases.py.

    python3 corpus.py   # escreve data/corpus.jsonl e imprime as proporções
"""

import hashlib
import json
import random
import re
from pathlib import Path

import frases as F
from valores import DISTRATOR, GOLD, gerar_nome, valor_de

SEED = 2026
N_NOTAS = 200
ARQUIVO = Path(__file__).resolve().parent / "data" / "corpus.jsonl"
_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def _preencher(modelo: str, rng: random.Random, paciente: str, base: int):
    """Preenche um modelo de frase e devolve (texto, spans, distratores)."""
    texto, spans, distratores, pos = "", [], [], 0
    for m in _PLACEHOLDER.finditer(modelo):
        texto += modelo[pos:m.start()]
        chave, inicio = m.group(1), base + len(texto)
        valor = valor_de(chave, rng, paciente)
        texto += valor
        registro = {"inicio": inicio, "fim": inicio + len(valor),
                    "tipo": (GOLD | DISTRATOR)[chave], "texto": valor}
        (spans if chave in GOLD else distratores).append(registro)
        pos = m.end()
    return texto + modelo[pos:], spans, distratores


def gerar_nota(i: int, rng: random.Random) -> dict:
    estilo = F.ESTILOS[i % len(F.ESTILOS)]
    paciente = gerar_nome(rng)
    n_frases = rng.randint(3, 6)
    modelos = [rng.choice(F.ABERTURA[estilo])]
    if rng.random() < 0.25:  # segundo documento, do tipo que a abertura não tem
        modelos.append(F.SEGUNDO_DOCUMENTO[0 if "{cns}" in modelos[0] else 1])
    fechar = rng.random() < 0.6
    modelos += rng.sample(F.MEIO, n_frases - len(modelos) - int(fechar))
    if fechar:
        modelos.append(rng.choice(F.FECHAMENTO[estilo]))

    texto, spans, distratores = "", [], []
    for modelo in modelos:
        if texto:
            texto += " "
        frase, s, d = _preencher(modelo, rng, paciente, len(texto))
        texto, spans, distratores = texto + frase, spans + s, distratores + d
    return {"id": f"nota_{i + 1:03d}", "estilo": estilo, "n_frases": n_frases,
            "texto": texto, "spans": spans, "distratores": distratores}


def gerar_corpus(n: int = N_NOTAS, seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    return [gerar_nota(i, rng) for i in range(n)]


def para_jsonl(notas: list[dict]) -> str:
    return "".join(json.dumps(n, ensure_ascii=False) + "\n" for n in notas)


def hash_corpus(notas: list[dict]) -> str:
    return hashlib.sha256(para_jsonl(notas).encode("utf-8")).hexdigest()


def carregar(caminho: Path = ARQUIVO) -> list[dict]:
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def estatisticas(notas: list[dict]) -> dict:
    """Proporção de cada caso difícil, contada nos spans (k, n)."""
    def spans(tipo):
        return [s["texto"] for n in notas for s in n["spans"] if s["tipo"] == tipo]
    cpf, cns, data, tel, pessoa = (spans(t) for t in ("BR_CPF", "BR_CNS", "DATA", "TELEFONE", "PESSOA"))
    distr = [d for n in notas for d in n["distratores"]]
    compostos = tuple(F.NOMES_COMPOSTOS)
    return {
        "cpf_sem_pontuacao": (sum(t.isdigit() for t in cpf), len(cpf)),
        "cns_sem_espacos": (sum(" " not in t for t in cns), len(cns)),
        "data_por_extenso": (sum(" de " in t for t in data), len(data)),
        "telefone_sem_ddd": (sum(len(t) <= 10 for t in tel), len(tel)),
        "nome_composto": (sum(t.startswith(compostos) for t in pessoa), len(pessoa)),
        "sobrenome_palavra_comum": (sum(any(s in t.split() for s in F.SOBRENOMES_COMUNS) for t in pessoa), len(pessoa)),
        "medicamento_nome_proprio": (sum(d["tipo"] == "medicamento" for d in distr), len(notas)),
        "numeros_nao_pessoais": (sum(d["tipo"] != "medicamento" for d in distr), len(notas)),
        "notas_com_cpf_ou_cns": (sum(any(s["tipo"] in ("BR_CPF", "BR_CNS") for s in n["spans"]) for n in notas), len(notas)),
    }


if __name__ == "__main__":
    notas = gerar_corpus()
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(para_jsonl(notas), encoding="utf-8")
    print(f"{len(notas)} notas -> {ARQUIVO.relative_to(Path.cwd())}  sha256={hash_corpus(notas)}")
    for nome, (k, n) in estatisticas(notas).items():
        print(f"  {nome:<26} {k:>4}/{n:<4} ({100 * k / n:5.1f}%)")
    print("\nexemplo:", notas[0]["texto"])
