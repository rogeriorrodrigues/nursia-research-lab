"""Demo 17: o que um venv limpo executa antes do seu código, via arquivos .pth.

Para cada versão de Python pedida, cria um venv novo e mede em 4 etapas:
  E0 venv vazio · E1 + 5 pacotes de IA · E2 + setuptools · E3 + pacote sintético em modo editável
Depois grava um .pth próprio e inofensivo (só escreve uma marca no stderr) e roda
`python -c pass` com e sem as flags -I, -s, -E e -S pra ver quando a marca aparece.
Sem malware, sem rede além do pip install, sem dado real.

Uso: python demo.py [3.11 3.12 3.13]
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RESULTS = AQUI / "results"
MARCA = "MARCA-DEMO17"
CONTEUDO_MARCA = f'import sys; sys.stderr.write("{MARCA}: .pth executado antes do seu codigo\\n")\n'
MODOS = {
    "padrao": [],
    "-I (isolado)": ["-I"],
    "-s (sem site do usuario)": ["-s"],
    "-E (ignora PYTHON*)": ["-E"],
    "-S (sem modulo site)": ["-S"],
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def varre(py):
    r = run([str(py), str(AQUI / "varre_pth.py")])
    r.check_returncode()
    return json.loads(r.stdout)


def resumo(v):
    return {k: v[k] for k in ("pth_total", "pth_com_executavel", "linhas_executaveis", "varredura_ms")} | {
        "arquivos": [f'{a["arquivo"]} ({a["executaveis"]} exec)' for a in v["arquivos"]]
    }


def pip(py, *args):
    r = run([str(py), "-m", "pip", "install", "-q", "--disable-pip-version-check", *args])
    if r.returncode:
        print(r.stdout, r.stderr)
    r.check_returncode()


def mede_versao(versao, base):
    exe = shutil.which(f"python{versao}")
    if not exe:
        return {"versao": versao, "erro": "interpretador não encontrado"}
    venv = base / f"venv-{versao}"
    run([exe, "-m", "venv", str(venv)]).check_returncode()
    py = venv / "bin" / "python"
    out = {"versao": run([str(py), "-c", "import sys;print(sys.version.split()[0])"]).stdout.strip()}
    out["E0_venv_vazio"] = resumo(varre(py))
    pip(py, "-r", str(AQUI / "requirements-ia.txt"))
    out["E1_mais_5_pacotes_ia"] = resumo(varre(py))
    pip(py, "setuptools==84.2.1")
    out["E2_mais_setuptools"] = resumo(varre(py))
    pip(py, "-e", str(AQUI / "pacote_sintetico"))
    out["E3_mais_editavel"] = resumo(varre(py))
    out["pacotes_no_venv"] = len(run([str(py), "-m", "pip", "list", "--format=freeze"]).stdout.split())

    sp = Path(varre(py)["diretorios"][0])
    (sp / "zz_marca_demo17.pth").write_text(CONTEUDO_MARCA, encoding="utf-8")
    marca = {}
    for nome, flags in MODOS.items():
        r = run([str(py), *flags, "-c", "pass"])
        marca[nome] = MARCA in r.stderr
    marca["pip --version (padrao)"] = MARCA in run([str(py), "-m", "pip", "--version"]).stderr
    out["marca_apareceu"] = marca
    r = run([str(py), "-S", "-c", "import openai"])
    out["import_openai_com_-S"] = "ok" if r.returncode == 0 else r.stderr.strip().splitlines()[-1]
    return out


def main():
    versoes = sys.argv[1:] or ["3.11", "3.12", "3.13"]
    RESULTS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        dados = [mede_versao(v, Path(tmp)) for v in versoes]
    (RESULTS / "resultado.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    linhas = []
    for d in dados:
        if "erro" in d:
            linhas.append(f'Python {d["versao"]}: {d["erro"]}')
            continue
        linhas.append(f'== Python {d["versao"]} ({d["pacotes_no_venv"]} pacotes no venv ao fim) ==')
        for et in ("E0_venv_vazio", "E1_mais_5_pacotes_ia", "E2_mais_setuptools", "E3_mais_editavel"):
            e = d[et]
            linhas.append(f'{et:24} .pth={e["pth_total"]:2}  com import={e["pth_com_executavel"]:2}  '
                          f'linhas exec={e["linhas_executaveis"]:2}  varredura={e["varredura_ms"]} ms')
            for a in e["arquivos"]:
                linhas.append(f'    {a}')
        linhas.append("marca do .pth próprio com `python -c pass`:")
        for k, v in d["marca_apareceu"].items():
            linhas.append(f'    {k:28} {"APARECEU" if v else "não apareceu"}')
        linhas.append(f'import openai com -S: {d["import_openai_com_-S"]}')
        linhas.append("")
    txt = "\n".join(linhas)
    (RESULTS / "resultado.txt").write_text(txt + "\n", encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
