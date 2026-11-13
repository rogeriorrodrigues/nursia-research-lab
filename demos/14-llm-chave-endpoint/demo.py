"""O llm manda a sua chave da OpenAI pra um endpoint de terceiro?

Roda os mesmos 5 cenários no llm 0.37.1 e no 0.37.2 contra um endpoint falso
em 127.0.0.1 e conta quantos pedidos chegaram com a chave canário.
Chave falsa, endpoint local, nenhum modelo de verdade é chamado.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

from servidor_falso import subir

AQUI = pathlib.Path(__file__).parent
VERSOES = ["0.37.1", "0.37.2"]
CANARIO_OPENAI = "sk-CANARIO-OPENAI-FALSA-0000"
CHAVE_TERCEIRO = "chave-do-terceiro-falsa-1111"

# (id, descrição, yaml do modelo, opções extras, guarda 'openai' em keys.json?,
#  guarda a chave do terceiro?, OPENAI_API_KEY no ambiente?)
CENARIOS = [
    ("A", "api_base + api_key_name não guardada, OPENAI_API_KEY no ambiente",
     {"api_key_name": "terceiro"}, [], False, False, True),
    ("B", "api_base + api_key_name guardada (controle: deve ir a chave do terceiro)",
     {"api_key_name": "terceiro"}, [], False, True, True),
    ("C", "api_base sem api_key_name (controle: não deve ir chave nenhuma da OpenAI)",
     {}, [], False, False, True),
    ("D", "responses: true + -o chat_completions 1, OPENAI_API_KEY no ambiente",
     {"responses": True}, ["-o", "chat_completions", "1"], False, False, True),
    ("E", "responses: true + -o chat_completions 1, chave 'openai' guardada com llm keys set",
     {"responses": True}, ["-o", "chat_completions", "1"], True, False, False),
]


def preparar_venv(versao):
    venv = AQUI / ".venvs" / f"llm-{versao}"
    exe = venv / "bin" / "llm"
    if not exe.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        subprocess.run([str(venv / "bin" / "pip"), "install", "-q", f"llm=={versao}"], check=True)
    return exe


def rodar_cenario(exe, base_url, cen):
    cid, _desc, extra, opcoes, guarda_openai, guarda_terceiro, env_openai = cen
    with tempfile.TemporaryDirectory() as home:
        modelo = {"model_id": "tp", "model_name": "modelo-falso", "api_base": base_url}
        modelo.update(extra)
        linhas = [f"- model_id: {modelo.pop('model_id')}"]
        for k, v in modelo.items():
            v = "true" if v is True else json.dumps(v)
            linhas.append(f"  {k}: {v}")
        pathlib.Path(home, "extra-openai-models.yaml").write_text("\n".join(linhas) + "\n")
        chaves = {}
        if guarda_openai:
            chaves["openai"] = CANARIO_OPENAI
        if guarda_terceiro:
            chaves["terceiro"] = CHAVE_TERCEIRO
        if chaves:
            pathlib.Path(home, "keys.json").write_text(json.dumps(chaves))
        env = {k: v for k, v in os.environ.items() if not k.startswith("OPENAI")}
        env["LLM_USER_PATH"] = home
        env["HOME"] = home
        # o endpoint é local: nunca passar por proxy
        env["NO_PROXY"] = env["no_proxy"] = "127.0.0.1,localhost"
        if env_openai:
            env["OPENAI_API_KEY"] = CANARIO_OPENAI
        p = subprocess.run(
            [str(exe), "-m", "tp", "--no-stream", "--no-log", *opcoes, "oi"],
            env=env, capture_output=True, text=True, timeout=30,
            stdin=subprocess.DEVNULL,
        )
        return p.returncode, (p.stdout + p.stderr).strip()


def classificar(auth):
    if auth is None:
        return "sem Authorization"
    if CANARIO_OPENAI in auth:
        return "CHAVE DA OPENAI"
    if CHAVE_TERCEIRO in auth:
        return "chave do terceiro"
    return "outra (" + auth.replace("Bearer ", "")[:12] + ")"


def main():
    resultado = {"canario_openai": CANARIO_OPENAI, "versoes": {}}
    inicio = time.time()
    for versao in VERSOES:
        exe = preparar_venv(versao)
        srv = subir()
        base_url = f"http://127.0.0.1:{srv.server_address[1]}/v1"
        linhas = []
        for cen in CENARIOS:
            antes = len(srv.pedidos)
            rc, saida = rodar_cenario(exe, base_url, cen)
            pedidos = srv.pedidos[antes:]
            recebido = [classificar(p["authorization"]) for p in pedidos]
            linhas.append({
                "cenario": cen[0],
                "descricao": cen[1],
                "codigo_saida": rc,
                "pedidos_no_endpoint": len(pedidos),
                "authorization_recebido": recebido,
                "vazou_chave_openai": any(r == "CHAVE DA OPENAI" for r in recebido),
                "saida_cli": saida[-200:],
            })
        srv.shutdown()
        resultado["versoes"][versao] = linhas
    resultado["segundos"] = round(time.time() - inicio, 1)

    (AQUI / "results").mkdir(exist_ok=True)
    (AQUI / "results" / "resultado.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False) + "\n")

    out = []
    for versao, linhas in resultado["versoes"].items():
        vaz = sum(l["vazou_chave_openai"] for l in linhas)
        out.append(f"llm {versao}: {vaz} de {len(linhas)} cenários mandaram a chave da OpenAI pro endpoint de terceiro")
        for l in linhas:
            out.append(f"  {l['cenario']} | rc={l['codigo_saida']} | pedidos={l['pedidos_no_endpoint']} | "
                       f"{', '.join(l['authorization_recebido']) or '-'} | {l['descricao']}")
            if l["pedidos_no_endpoint"] == 0:
                out.append(f"      saída: {l['saida_cli'].splitlines()[-1] if l['saida_cli'] else ''}")
    out.append(f"tempo total: {resultado['segundos']} s")
    texto = "\n".join(out)
    (AQUI / "results" / "saida.txt").write_text(texto + "\n")
    print(texto)
    return resultado


if __name__ == "__main__":
    main()
