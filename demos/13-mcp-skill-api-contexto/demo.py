"""Quanto contexto a mesma ferramenta ocupa como servidor MCP, como função de API e como Skill.

Não chama modelo nenhum. Monta o que cada via põe na janela de contexto,
conta tokens com dois tokenizadores (tiktoken) e grava em results/.
"""
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

import tiktoken
from mcp.client import Client
from mcp.server.mcpserver import MCPServer

import ferramentas

AQUI = Path(__file__).parent
SKILL = AQUI / "skill" / "mascarar-identificadores"
RESULTS = AQUI / "results"
ENCODINGS = ["o200k_base", "cl100k_base"]
PEDIDOS = 10  # conversa de 10 pedidos ao modelo


def gerar_cpf(base9: str) -> str:
    d = base9
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        d += str((soma * 10) % 11 % 10)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def gerar_cns(prefixo14: str) -> str:
    for ultimo in range(10):
        cns = prefixo14 + str(ultimo)
        if ferramentas.validar_cns(cns):
            return f"{cns[:3]} {cns[3:7]} {cns[7:11]} {cns[11:]}"
    raise ValueError("prefixo sem dígito final válido")


CPF_OK = gerar_cpf("529982247")
CNS_OK = gerar_cns("70000000000000")
NOTA = (
    f"Paciente FULANO DE TAL SINTETICO, CPF {CPF_OK}, CNS {CNS_OK}. "
    "Retorno em 7 dias. CPF do acompanhante 111.222.333-00 (digitado errado)."
)


# --- via 1: servidor MCP de verdade, cliente em memória ----------------------
async def via_mcp():
    servidor = MCPServer("identificadores")
    for f in ferramentas.FERRAMENTAS:
        servidor.add_tool(f)
    async with Client(servidor) as cliente:
        lista = await cliente.list_tools()
        chamada = await cliente.call_tool("mascarar_identificadores", {"texto": NOTA})
    resposta_bruta = lista.model_dump(mode="json", by_alias=True, exclude_none=True)
    # O host traduz cada Tool do MCP pra definição de ferramenta do provedor:
    # nome, descrição e o JSON Schema de entrada. É isso que vai pro modelo.
    pro_modelo = [
        {"name": t.name, "description": t.description, "input_schema": t.input_schema}
        for t in lista.tools
    ]
    saida = [c.text for c in chamada.content if getattr(c, "text", None)]
    return resposta_bruta, pro_modelo, saida


# --- via 2: definição de função escrita à mão, formato de tool use de API -----
API = [
    {
        "name": "validar_cpf",
        "description": "Confere os dois dígitos verificadores de um CPF (11 dígitos, com ou sem pontuação).",
        "input_schema": {"type": "object", "properties": {"cpf": {"type": "string"}}, "required": ["cpf"]},
    },
    {
        "name": "validar_cns",
        "description": "Confere o Cartão Nacional de Saúde (15 dígitos) pela soma ponderada módulo 11.",
        "input_schema": {"type": "object", "properties": {"cns": {"type": "string"}}, "required": ["cns"]},
    },
    {
        "name": "mascarar_identificadores",
        "description": "Troca CPF e CNS válidos do texto por [CPF] e [CNS]. Número inválido fica como está.",
        "input_schema": {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]},
    },
    {
        "name": "contar_identificadores",
        "description": "Conta quantos CPF e CNS válidos e inválidos aparecem no texto, sem devolver os números.",
        "input_schema": {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"]},
    },
]


# --- via 3: Skill (SKILL.md + script) -----------------------------------------
def via_skill():
    texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    meta = dict(linha.split(": ", 1) for linha in m.group(1).splitlines())
    nivel1 = f"{meta['name']} - {meta['description']}"  # linha que entra no system prompt
    nivel2 = m.group(2).strip()  # corpo, lido com cat quando a Skill dispara
    script = SKILL / "scripts" / "identificadores.py"
    comando = "echo \"<nota>\" | python scripts/identificadores.py mascarar_identificadores"
    saida = subprocess.run(
        [sys.executable, str(script), "mascarar_identificadores"],
        input=NOTA, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return nivel1, nivel2, script.read_text(encoding="utf-8"), comando, saida


def sem_title(obj):
    """Tira os campos "title" que o Pydantic gera no JSON Schema."""
    if isinstance(obj, dict):
        return {k: sem_title(v) for k, v in obj.items() if k != "title"}
    if isinstance(obj, list):
        return [sem_title(v) for v in obj]
    return obj


def contar(texto: str) -> dict:
    return {e: len(tiktoken.get_encoding(e).encode(texto)) for e in ENCODINGS}


def js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def main():
    RESULTS.mkdir(exist_ok=True)
    bruta, mcp_modelo, mcp_saida = asyncio.run(via_mcp())
    nivel1, nivel2, codigo, comando, skill_saida = via_skill()
    esperado = ferramentas.mascarar_identificadores(NOTA)
    assert mcp_saida and mcp_saida[0] == esperado, (mcp_saida, esperado)
    assert json.loads(skill_saida) == esperado, (skill_saida, esperado)

    medidas = {
        "mcp_tools_list_resposta_inteira": contar(js(bruta)),
        "mcp_definicoes_pro_modelo": contar(js(mcp_modelo)),
        "api_definicoes_pro_modelo": contar(js(API)),
        "skill_nivel1_metadado": contar(nivel1),
        "skill_nivel2_corpo": contar(nivel2),
        "skill_script_codigo_nao_entra": contar(codigo),
        "chamada_mcp_ou_api_argumentos": contar(js({"texto": NOTA})),
        "chamada_mcp_ou_api_resultado": contar(mcp_saida[0]),
        "chamada_skill_comando": contar(comando),
        "chamada_skill_saida": contar(skill_saida),
    }
    o = {k: v["o200k_base"] for k, v in medidas.items()}
    projecao = {
        "mcp_10_pedidos": PEDIDOS * o["mcp_definicoes_pro_modelo"],
        "api_10_pedidos": PEDIDOS * o["api_definicoes_pro_modelo"],
        "skill_10_pedidos_usada_no_pedido_1": PEDIDOS * (o["skill_nivel1_metadado"] + o["skill_nivel2_corpo"]),
        "skill_10_pedidos_usada_no_pedido_10": PEDIDOS * o["skill_nivel1_metadado"] + o["skill_nivel2_corpo"],
        "skill_10_pedidos_nunca_usada": PEDIDOS * o["skill_nivel1_metadado"],
    }
    resultado = {
        "versoes": {
            "python": sys.version.split()[0],
            "mcp": __import__("importlib.metadata").metadata.version("mcp"),
            "tiktoken": tiktoken.__version__,
        },
        "ferramentas": [f.__name__ for f in ferramentas.FERRAMENTAS],
        "mcp_igual_api": mcp_modelo == API,
        "mcp_igual_api_sem_title": sem_title(mcp_modelo) == API,
        "mcp_schema_exemplo": mcp_modelo[0]["input_schema"],
        "nota_sintetica": NOTA,
        "saida_mascarada": esperado,
        "tokens": medidas,
        "projecao_o200k_base": projecao,
    }
    (RESULTS / "resultado.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "mcp_tools_list.json").write_text(json.dumps(bruta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    linhas = [
        f"mcp {resultado['versoes']['mcp']} · tiktoken {resultado['versoes']['tiktoken']} · Python {resultado['versoes']['python']}",
        f"4 ferramentas: {', '.join(resultado['ferramentas'])}",
        f"saída igual nas 3 vias: {esperado}",
        "",
        f"{'o que entra no contexto':44} {'o200k':>6} {'cl100k':>7}",
    ]
    for k, v in medidas.items():
        linhas.append(f"{k:44} {v['o200k_base']:>6} {v['cl100k_base']:>7}")
    linhas += ["", f"projeção, {PEDIDOS} pedidos (o200k_base):"]
    linhas += [f"  {k:40} {v:>6}" for k, v in projecao.items()]
    linhas.append(f"\ndefinição MCP idêntica à escrita à mão pra API: {resultado['mcp_igual_api']}")
    linhas.append(f"idêntica depois de tirar os campos title do Pydantic: {resultado['mcp_igual_api_sem_title']}")
    (RESULTS / "saida.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()
