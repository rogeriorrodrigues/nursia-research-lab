"""Phoenix 21.0.0: o painel de trace pede senha por padrão?

Sobe o `phoenix serve` em 4 configurações, manda 1 trace sintético com um
segredo falso no prompt e tenta ler esse trace SEM credencial. Grava a saída
em results/.

Dado 100% sintético. Nenhuma chave real, nenhum dado de pessoa.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
from opentelemetry.proto.common.v1.common_pb2 import AnyValue, KeyValue
from opentelemetry.proto.resource.v1.resource_pb2 import Resource
from opentelemetry.proto.trace.v1.trace_pb2 import ResourceSpans, ScopeSpans, Span

# Segredo falso, inválido por construção. É o que procuramos na resposta.
SEGREDO = "sk-SINTETICO-0000-nao-e-chave-real-7f3a"
PROMPT = f"Resuma o chamado. Minha chave da API é {SEGREDO}, use se precisar."

CENARIOS = [
    {"nome": "1-loopback-padrao", "host": "127.0.0.1", "env": {}},
    {"nome": "2-todas-interfaces-padrao", "host": "0.0.0.0", "env": {}},
    {"nome": "3-todas-interfaces-auth-false", "host": "0.0.0.0", "env": {"PHOENIX_ENABLE_AUTH": "false"}},
    {"nome": "4-todas-interfaces-senha-inicial", "host": "0.0.0.0",
     "env": {"PHOENIX_DEFAULT_ADMIN_INITIAL_PASSWORD": "Sintetica-Demo-2026!x"}},
]


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def ip_da_maquina() -> str | None:
    """IP não-loopback desta máquina, pra testar se o painel responde fora do 127.0.0.1."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        return None if ip.startswith("127.") else ip
    except OSError:
        return None


def http(metodo: str, url: str, corpo: bytes | None = None, tipo: str | None = None,
         cookie: str | None = None) -> tuple[int | str, str, object]:
    req = urllib.request.Request(url, data=corpo, method=metodo)
    if tipo:
        req.add_header("Content-Type", tipo)
    if cookie:
        req.add_header("Cookie", cookie)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode("utf-8", "replace"), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e.headers
    except (urllib.error.URLError, OSError) as e:
        return f"sem conexão ({type(e).__name__})", "", {}


def cookie_de(headers) -> str:
    """Junta os pares nome=valor de todos os Set-Cookie da resposta do login."""
    return "; ".join(c.split(";")[0].strip() for c in (headers.get_all("Set-Cookie") or []))


def trace_sintetico() -> bytes:
    def kv(k: str, v: str) -> KeyValue:
        return KeyValue(key=k, value=AnyValue(string_value=v))

    agora = time.time_ns()
    span = Span(
        trace_id=os.urandom(16), span_id=os.urandom(8), name="llm.chamado-sintetico",
        kind=Span.SPAN_KIND_CLIENT, start_time_unix_nano=agora - 1_000_000,
        end_time_unix_nano=agora,
        attributes=[kv("openinference.span.kind", "LLM"), kv("input.value", PROMPT),
                    kv("output.value", "Resumo sintético do chamado.")],
    )
    req = ExportTraceServiceRequest(resource_spans=[ResourceSpans(
        resource=Resource(attributes=[kv("service.name", "demo-sintetica")]),
        scope_spans=[ScopeSpans(spans=[span])],
    )])
    return req.SerializeToString()


def esperar(base: str, proc: subprocess.Popen, limite: float = 120) -> None:
    fim = time.time() + limite
    while time.time() < fim:
        if proc.poll() is not None:
            raise RuntimeError("phoenix serve saiu antes de ficar pronto")
        st, _, _ = http("GET", base + "/healthz")
        if st == 200:
            return
        time.sleep(1)
    raise TimeoutError("phoenix serve não respondeu /healthz")


def rodar(c: dict, ip_externo: str | None, logdir: Path) -> dict:
    trabalho = tempfile.mkdtemp(prefix="phx-")
    porta, grpc = porta_livre(), porta_livre()
    env = {k: v for k, v in os.environ.items() if not k.startswith("PHOENIX_")}
    env.update({"PHOENIX_WORKING_DIR": trabalho, "PHOENIX_PORT": str(porta),
                "PHOENIX_GRPC_PORT": str(grpc), "PHOENIX_HOST": c["host"],
                "PHOENIX_TELEMETRY_ENABLED": "false"})
    env.update(c["env"])
    log = open(logdir / f"{c['nome']}.log", "w")
    exe = Path(sys.executable).with_name("phoenix")
    proc = subprocess.Popen([str(exe), "serve"], env=env, stdout=log, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{porta}"
    r: dict = {"cenario": c["nome"], "PHOENIX_HOST": c["host"],
               "env_extra": {k: ("<definida>" if "PASSWORD" in k else v) for k, v in c["env"].items()}}
    try:
        esperar(base, proc)
        st, _, _ = http("POST", base + "/v1/traces", trace_sintetico(), "application/x-protobuf")
        r["enviar_trace_sem_credencial"] = st
        time.sleep(3)  # o Phoenix grava em lote
        st, corpo, _ = http("GET", base + "/v1/projects")
        r["listar_projetos_sem_credencial"] = st
        st, corpo, _ = http("GET", base + "/v1/projects/default/spans?limit=50")
        r["ler_spans_sem_credencial"] = st
        r["segredo_na_resposta_sem_credencial"] = SEGREDO in corpo
        gql = json.dumps({"query": "{ projects { edges { node { name traceCount } } } }"}).encode()
        st, _, _ = http("POST", base + "/graphql", gql, "application/json")
        r["graphql_sem_credencial"] = st
        st, _, _ = http("POST", base + "/auth/login",
                        json.dumps({"email": "admin@localhost", "password": "admin"}).encode(),
                        "application/json")
        r["login_admin_admin"] = st
        if "PHOENIX_DEFAULT_ADMIN_INITIAL_PASSWORD" in c["env"]:
            st, _, h = http("POST", base + "/auth/login", json.dumps({
                "email": "admin@localhost",
                "password": c["env"]["PHOENIX_DEFAULT_ADMIN_INITIAL_PASSWORD"]}).encode(),
                "application/json")
            r["login_senha_inicial"] = st
            # Controle positivo: com a sessão do login, a mesma API responde.
            cookie = cookie_de(h)
            st, _, _ = http("GET", base + "/v1/projects", cookie=cookie)
            r["listar_projetos_com_login"] = st
        if ip_externo:
            st, _, _ = http("GET", f"http://{ip_externo}:{porta}/healthz")
            r["responde_no_ip_da_maquina"] = st
    finally:
        proc.terminate()
        try:
            proc.wait(15)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
        shutil.rmtree(trabalho, ignore_errors=True)
    return r


def main() -> None:
    import importlib.metadata as md
    saida = Path(__file__).parent / "results"
    saida.mkdir(exist_ok=True)
    logdir = Path(tempfile.mkdtemp(prefix="phx-logs-"))
    ip = ip_da_maquina()
    resultados = {"arize-phoenix": md.version("arize-phoenix"), "python": sys.version.split()[0],
                  "ip_da_maquina_testado": "sim" if ip else "não encontrado", "cenarios": []}
    for c in CENARIOS:
        t0 = time.time()
        r = rodar(c, ip, logdir)
        r["segundos"] = round(time.time() - t0, 1)
        resultados["cenarios"].append(r)
        print(json.dumps(r, ensure_ascii=False))
    (saida / "resultado.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2) + "\n")
    print(f"\nlogs do servidor em {logdir}")


if __name__ == "__main__":
    main()
