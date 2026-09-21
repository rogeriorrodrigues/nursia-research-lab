"""
Sistemas 3 e 4: dois modelos locais via Ollama (/api/chat), mesmo prompt
congelado em prompts/extracao_v1.txt, temperature 0, seed 2026, format json.

Resumível: cada nota vai pro results/raw/<sistema>.jsonl assim que termina;
ao reiniciar, pula as que já estão lá. Pode levar horas.

    python3 run_llms.py                # os dois sistemas
    python3 run_llms.py ollama_qwen    # só um
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from ambiente import carregar_env, info_maquina
from corpus import carregar
from metricas import TIPOS

carregar_env()
AQUI = Path(__file__).resolve().parent
HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
SISTEMAS = {"ollama_qwen": os.environ.get("TAG_OLLAMA_QWEN", "qwen3.8:27b"),
            "ollama_phi": os.environ.get("TAG_OLLAMA_PHI", "phi4:14b")}
PROMPT_ARQ = AQUI / "prompts" / "extracao_v1.txt"
RAW = AQUI / "results" / "raw"
OPCOES = {"temperature": 0, "seed": 2026}
TIMEOUT_S = 900


def interpretar(conteudo: str) -> list[dict] | None:
    """Lista de {tipo, texto} ou None se o JSON for inválido (conta como zero)."""
    try:
        dados = json.loads(conteudo)
    except (json.JSONDecodeError, TypeError):
        return None
    if isinstance(dados, dict):
        dados = dados.get("entidades")
    if not isinstance(dados, list) or not all(isinstance(e, dict) for e in dados):
        return None
    return dados


def para_spans(texto: str, entidades: list[dict]) -> tuple[list[dict], int]:
    """Cada {tipo, texto} vira todas as ocorrências exatas do trecho na nota."""
    achados, nao_encontradas = {}, 0
    for e in entidades:
        tipo, trecho = e.get("tipo"), e.get("texto")
        if tipo not in TIPOS or not isinstance(trecho, str) or not trecho:
            nao_encontradas += 1
            continue
        pos, achou = texto.find(trecho), False
        while pos != -1:
            achados[(pos, pos + len(trecho), tipo)] = trecho
            achou, pos = True, texto.find(trecho, pos + len(trecho))
        nao_encontradas += not achou
    spans = [{"inicio": i, "fim": f, "tipo": t, "texto": tx} for (i, f, t), tx in sorted(achados.items())]
    return spans, nao_encontradas


def chamar(tag: str, prompt: str, texto: str) -> str:
    corpo = {"model": tag, "stream": False, "format": "json", "think": False, "options": OPCOES,
             "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": texto}]}
    r = requests.post(f"{HOST}/api/chat", json=corpo, timeout=TIMEOUT_S)
    r.raise_for_status()
    return r.json()["message"]["content"]


def verificar_modelo(tag: str, maquina: dict) -> dict:
    """Para se o modelo não está no `ollama list` ou é maior que a RAM. Não troca de modelo."""
    modelos = requests.get(f"{HOST}/api/tags", timeout=10).json().get("models", [])
    m = next((m for m in modelos if tag in (m.get("name"), m.get("model"))), None)
    if m is None:
        sys.exit(f"PARE: {tag} não está no `ollama list` em {HOST}. Puxe com `ollama pull {tag}` "
                 "ou ajuste a tag no .env. Trocar o modelo muda o post, então não troco sozinho.")
    if maquina["ram_gb"] and m["size"] / 2**30 > maquina["ram_gb"]:
        sys.exit(f"PARE: {tag} tem {m['size'] / 2**30:.0f} GB e a máquina tem {maquina['ram_gb']} GB de RAM.")
    detalhes = requests.post(f"{HOST}/api/show", json={"model": tag}, timeout=30).json().get("details", {})
    return {"tag": tag, "digest": m.get("digest"), "tamanho_gb": round(m["size"] / 2**30, 1),
            "quantizacao": detalhes.get("quantization_level"), "parametros": detalhes.get("parameter_size"),
            "familia": detalhes.get("family")}


def rodar(sistema: str, notas: list[dict]) -> None:
    maquina = info_maquina()
    modelo = verificar_modelo(SISTEMAS[sistema], maquina)
    prompt = PROMPT_ARQ.read_text(encoding="utf-8")
    RAW.mkdir(parents=True, exist_ok=True)
    saida, meta_arq = RAW / f"{sistema}.jsonl", RAW / f"{sistema}.meta.json"
    feitas = {json.loads(l)["id"] for l in saida.read_text(encoding="utf-8").splitlines() if l.strip()} \
        if saida.exists() else set()
    meta = json.loads(meta_arq.read_text(encoding="utf-8")) if meta_arq.exists() else {
        "sistema": sistema, "modelo": modelo, "prompt": PROMPT_ARQ.name, "opcoes": OPCOES, "think": False,
        "ollama": requests.get(f"{HOST}/api/version", timeout=10).json().get("version"),
        "maquina": maquina, "inicio": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    meta_arq.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{sistema}: {modelo['tag']} ({modelo['quantizacao']}, {modelo['tamanho_gb']} GB), "
          f"{len(feitas)} de {len(notas)} notas já feitas", flush=True)

    with open(saida, "a", encoding="utf-8") as f:
        for nota in notas:
            if nota["id"] in feitas:
                continue
            t0, erro = time.perf_counter(), None
            try:
                conteudo = chamar(modelo["tag"], prompt, nota["texto"])
            except (requests.RequestException, KeyError, ValueError) as e:
                conteudo, erro = "", f"{type(e).__name__}: {e}"[:200]
            tempo = round(time.perf_counter() - t0, 2)
            entidades = interpretar(conteudo)
            spans, nao = para_spans(nota["texto"], entidades or [])
            f.write(json.dumps({"id": nota["id"], "spans": spans, "parse_ok": entidades is not None,
                                "n_brutas": len(entidades or []), "nao_encontradas": nao, "tempo_s": tempo,
                                "resposta_bruta": conteudo, "erro": erro}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {nota['id']} {tempo:7.1f}s parse={'ok' if entidades is not None else 'FALHA'} "
                  f"spans={len(spans)}", flush=True)
    meta["fim"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta_arq.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    escolhidos = sys.argv[1:] or list(SISTEMAS)
    for s in escolhidos:
        if s not in SISTEMAS:
            sys.exit(f"sistema desconhecido: {s} (use {', '.join(SISTEMAS)})")
        rodar(s, carregar())
