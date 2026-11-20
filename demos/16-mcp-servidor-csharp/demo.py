"""Mede um servidor MCP em C# (SDK oficial 2.4.0) de fora, pelo fio.

Sobe o servidor de src/ por HTTP em 127.0.0.1, fala JSON-RPC cru com ele
(sem SDK de cliente, pra ver exatamente o que trafega) e grava em results/:
- tokens das definições do tools/list (tiktoken, o mesmo método da demo 13);
- se o schema gerado em C# traz os campos "title" que o Python trouxe;
- tempo de uma chamada de ferramenta (200 chamadas em sequência);
- o que acontece sem autenticação, com token inventado e com Origin de fora;
- se uma rajada de 500 chamadas leva algum "não" (limite de chamadas);
- o que o log padrão do servidor registrou das chamadas.
Não chama modelo nenhum. Dado sintético.
"""
import json
import re
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import tiktoken

AQUI = Path(__file__).parent
RESULTS = AQUI / "results"
DLL = AQUI / "src" / "bin" / "Release" / "net8.0" / "ServidorMcp.dll"
DEMO13 = AQUI.parent / "13-mcp-skill-api-contexto" / "results" / "mcp_tools_list.json"
URL = "http://127.0.0.1:5088/mcp"
ENCODINGS = ["o200k_base", "cl100k_base"]
HDR = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def gerar_cpf(base9: str) -> str:
    d = base9
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        d += str((soma * 10) % 11 % 10)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


CPF_OK = gerar_cpf("529982247")  # sintético, gerado por algoritmo
CNS_OK = "700 0000 0000 0005"  # o mesmo CNS sintético da demo 13
NOTA = (
    f"Paciente FULANO DE TAL SINTETICO, CPF {CPF_OK}, CNS {CNS_OK}. "
    "Retorno em 7 dias. CPF do acompanhante 111.222.333-00 (digitado errado)."
)
ESPERADO = (
    "Paciente FULANO DE TAL SINTETICO, CPF [CPF], CNS [CNS]. "
    "Retorno em 7 dias. CPF do acompanhante 111.222.333-00 (digitado errado)."
)


def js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def contar(texto: str) -> dict:
    return {e: len(tiktoken.get_encoding(e).encode(texto)) for e in ENCODINGS}


def ler_resposta(r: httpx.Response):
    """O transporte HTTP do MCP responde em JSON ou em SSE; aceita os dois."""
    if r.headers.get("content-type", "").startswith("text/event-stream"):
        dados = [l[5:].strip() for l in r.text.splitlines() if l.startswith("data:")]
        return json.loads(dados[-1]) if dados else None
    return r.json() if r.text else None


class Sessao:
    def __init__(self, cli: httpx.Client, extra=None):
        self.cli, self.extra, self.sid, self.n = cli, dict(extra or {}), None, 0

    def post(self, metodo, params=None, notificacao=False):
        corpo = {"jsonrpc": "2.0", "method": metodo}
        if params is not None:
            corpo["params"] = params
        if not notificacao:
            self.n += 1
            corpo["id"] = self.n
        h = {**HDR, **self.extra}
        if self.sid:
            h["Mcp-Session-Id"] = self.sid
        r = self.cli.post(URL, headers=h, content=js(corpo))
        self.sid = r.headers.get("mcp-session-id", self.sid)
        return r

    def abrir(self):
        r = self.post("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "demo16", "version": "1"},
        })
        if r.status_code == 200:
            self.post("notifications/initialized", notificacao=True)
        return r


def sem_title(obj):
    if isinstance(obj, dict):
        return {k: sem_title(v) for k, v in obj.items() if k != "title"}
    if isinstance(obj, list):
        return [sem_title(v) for v in obj]
    return obj


def tem_title(obj) -> int:
    if isinstance(obj, dict):
        return ("title" in obj) + sum(tem_title(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(tem_title(v) for v in obj)
    return 0


def pro_modelo(tools):
    # O que o host repassa pro modelo: nome, descrição e o JSON Schema de entrada.
    return [{"name": t["name"], "description": t["description"], "input_schema": t["inputSchema"]} for t in tools]


def subir_servidor(log):
    t0 = time.perf_counter()
    proc = subprocess.Popen(["dotnet", str(DLL)], stdout=log, stderr=subprocess.STDOUT)
    with httpx.Client(trust_env=False, timeout=2) as c:
        for _ in range(300):
            try:
                c.get(URL)
                return proc, (time.perf_counter() - t0) * 1000
            except httpx.TransportError:
                time.sleep(0.05)
    proc.kill()
    raise RuntimeError("servidor não subiu")


def main():
    RESULTS.mkdir(exist_ok=True)
    caminho_log = RESULTS / "servidor.log"
    with open(caminho_log, "w") as log:
        proc, partida_ms = subir_servidor(log)
        try:
            out = medir()
        finally:
            proc.terminate()
            proc.wait(timeout=10)
    texto_log = caminho_log.read_text(encoding="utf-8", errors="replace")
    out["partida_ms"] = round(partida_ms)
    out["log_padrao"] = {
        "linhas": len(texto_log.splitlines()),
        "linhas_que_citam_tools_call": sum("tools/call" in l for l in texto_log.splitlines()),
        "linhas_que_citam_nome_de_ferramenta": sum(
            any(n in l for n in out["ferramentas"]) for l in texto_log.splitlines()
        ),
        "cpf_da_nota_aparece_no_log": CPF_OK in texto_log,
    }
    # O log inteiro passa de 600 KB; fica só o começo, que já mostra o padrão.
    (RESULTS / "servidor-log-trecho.txt").write_text("\n".join(texto_log.splitlines()[:80]) + "\n", encoding="utf-8")
    caminho_log.unlink()
    (RESULTS / "resultado.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    imprimir(out)


def medir():
    out = {}
    with httpx.Client(trust_env=False, timeout=10) as cli:
        s = Sessao(cli)
        r = s.abrir()
        out["initialize_status"] = r.status_code
        out["server_info"] = ler_resposta(r)["result"]["serverInfo"]
        lista = ler_resposta(s.post("tools/list", {}))["result"]
        (RESULTS / "tools_list.json").write_text(json.dumps(lista, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tools = lista["tools"]
        out["ferramentas"] = [t["name"] for t in tools]
        out["output_schema_presente"] = [t["name"] for t in tools if "outputSchema" in t]
        out["schema_exemplo"] = tools[0]["inputSchema"]
        out["campos_title_no_tools_list"] = tem_title(lista)

        # Mesma conta da demo 13 (Python, mcp 2.3.0), pras mesmas 4 ferramentas.
        py = json.loads(DEMO13.read_text(encoding="utf-8"))["tools"]
        out["tokens"] = {
            "csharp_tools_list_resposta_inteira": contar(js(lista)),
            "csharp_definicoes_pro_modelo": contar(js(pro_modelo(tools))),
            "python_definicoes_pro_modelo_demo13": contar(js(pro_modelo(py))),
            "python_sem_title_demo13": contar(js(sem_title(pro_modelo(py)))),
        }
        out["python_campos_title_demo13"] = tem_title(py)

        # Chamada de ferramenta: resultado igual ao da demo 13?
        r = ler_resposta(s.post("tools/call", {"name": "mascarar_identificadores", "arguments": {"texto": NOTA}}))
        saida = r["result"]["content"][0]["text"]
        out["mascarar_saida"] = saida
        out["mascarar_igual_demo13"] = saida == ESPERADO
        r = ler_resposta(s.post("tools/call", {"name": "contar_identificadores", "arguments": {"texto": NOTA}}))
        out["contar_saida"] = r["result"]["content"][0]["text"]

        # Tempo de uma chamada, servidor quente, cliente na mesma máquina.
        for _ in range(20):
            s.post("tools/call", {"name": "validar_cpf", "arguments": {"cpf": CPF_OK}})
        tempos = []
        for _ in range(200):
            t0 = time.perf_counter()
            s.post("tools/call", {"name": "mascarar_identificadores", "arguments": {"texto": NOTA}})
            tempos.append((time.perf_counter() - t0) * 1000)
        tempos.sort()
        out["chamada_ms"] = {
            "n": len(tempos),
            "mediana": round(statistics.median(tempos), 2),
            "p95": round(tempos[int(0.95 * len(tempos)) - 1], 2),
            "max": round(tempos[-1], 2),
        }

        # Autenticação: o servidor não pede nada. Três clientes diferentes.
        casos = {
            "sem_header_nenhum": {},
            "token_inventado": {"Authorization": "Bearer token-inventado-123"},
            "origin_de_fora": {"Origin": "http://site-qualquer.example"},
        }
        auth = {}
        for nome, extra in casos.items():
            c = Sessao(cli, extra)
            ri = c.abrir()
            rc = c.post("tools/call", {"name": "mascarar_identificadores", "arguments": {"texto": NOTA}})
            corpo = ler_resposta(rc) if rc.status_code == 200 else None
            auth[nome] = {
                "initialize": ri.status_code,
                "tools_call": rc.status_code,
                "devolveu_texto_mascarado": bool(corpo and corpo["result"]["content"][0]["text"] == ESPERADO),
            }
        out["autenticacao"] = auth

    # Rajada: 500 chamadas, 20 em paralelo. Algum 429?
    def uma(_):
        with httpx.Client(trust_env=False, timeout=30) as c:
            ss = Sessao(c)
            ss.abrir()
            return [ss.post("tools/call", {"name": "validar_cpf", "arguments": {"cpf": CPF_OK}}).status_code for _ in range(25)]

    t0 = time.perf_counter()
    with ThreadPoolExecutor(20) as ex:
        codigos = [c for lote in ex.map(uma, range(20)) for c in lote]
    out["rajada"] = {
        "chamadas": len(codigos),
        "status_200": codigos.count(200),
        "status_429": codigos.count(429),
        "outros": len(codigos) - codigos.count(200) - codigos.count(429),
        "segundos": round(time.perf_counter() - t0, 2),
    }
    return out


def imprimir(o):
    t = o["tokens"]
    linhas = [
        f"servidor: {o['server_info']}  partida até responder: {o['partida_ms']} ms",
        f"ferramentas: {', '.join(o['ferramentas'])}",
        f"campos title no tools/list: C# {o['campos_title_no_tools_list']} · Python (demo 13) {o['python_campos_title_demo13']}",
        f"outputSchema presente em: {o['output_schema_presente'] or 'nenhuma'}",
        "",
        "tokens (o200k_base / cl100k_base)",
        f"  C#  tools/list inteiro          {t['csharp_tools_list_resposta_inteira']['o200k_base']:>4} / {t['csharp_tools_list_resposta_inteira']['cl100k_base']}",
        f"  C#  definições pro modelo       {t['csharp_definicoes_pro_modelo']['o200k_base']:>4} / {t['csharp_definicoes_pro_modelo']['cl100k_base']}",
        f"  Py  definições (demo 13)        {t['python_definicoes_pro_modelo_demo13']['o200k_base']:>4} / {t['python_definicoes_pro_modelo_demo13']['cl100k_base']}",
        f"  Py  sem title (demo 13)         {t['python_sem_title_demo13']['o200k_base']:>4} / {t['python_sem_title_demo13']['cl100k_base']}",
        "",
        f"mascarar igual à demo 13: {o['mascarar_igual_demo13']}",
        f"contar: {o['contar_saida']}",
        f"chamada (n={o['chamada_ms']['n']}): mediana {o['chamada_ms']['mediana']} ms · p95 {o['chamada_ms']['p95']} ms · máx {o['chamada_ms']['max']} ms",
        "",
        "autenticação:",
    ] + [f"  {k}: initialize {v['initialize']} · tools/call {v['tools_call']} · devolveu o texto {v['devolveu_texto_mascarado']}" for k, v in o["autenticacao"].items()] + [
        "",
        f"rajada: {o['rajada']['chamadas']} chamadas em {o['rajada']['segundos']} s · 200: {o['rajada']['status_200']} · 429: {o['rajada']['status_429']} · outros: {o['rajada']['outros']}",
        f"log padrão: {o['log_padrao']['linhas']} linhas · citam tools/call: {o['log_padrao']['linhas_que_citam_tools_call']} · citam nome de ferramenta: {o['log_padrao']['linhas_que_citam_nome_de_ferramenta']} · CPF no log: {o['log_padrao']['cpf_da_nota_aparece_no_log']}",
    ]
    texto = "\n".join(linhas)
    print(texto)
    (RESULTS / "saida.txt").write_text(texto + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
