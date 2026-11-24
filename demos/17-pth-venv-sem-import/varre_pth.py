"""Lista todo .pth visível pro interpretador e separa as linhas que o Python executa.

Regra (Doc/library/site.rst do CPython): linha que começa com "import" seguido de
espaço ou tab é executada com exec() quando o módulo site carrega, antes do seu código.
Uso: python varre_pth.py  (rode com o python do venv que você quer olhar)
"""
import json
import site
import sys
import time
from pathlib import Path


def classifica(linha: str) -> str:
    if not linha.strip() or linha.startswith("#"):
        return "vazia_ou_comentario"
    if linha.startswith(("import ", "import\t")):
        return "executavel"
    return "caminho"


def varre(diretorios):
    achados = []
    for d in diretorios:
        p = Path(d)
        if not p.is_dir():
            continue
        for pth in sorted(p.glob("*.pth")):
            linhas = pth.read_text(encoding="utf-8", errors="replace").splitlines()
            tipos = [classifica(l) for l in linhas]
            achados.append({
                "arquivo": pth.name,
                "dir": str(p),
                "linhas": len(linhas),
                "executaveis": tipos.count("executavel"),
                "caminhos": tipos.count("caminho"),
                "primeira_executavel": next((l[:120] for l, t in zip(linhas, tipos) if t == "executavel"), None),
            })
    return achados


def main():
    t0 = time.perf_counter()
    dirs = list(site.getsitepackages())
    if site.ENABLE_USER_SITE:
        dirs.append(site.getusersitepackages())
    achados = varre(dirs)
    ms = (time.perf_counter() - t0) * 1000
    print(json.dumps({
        "python": sys.version.split()[0],
        "diretorios": dirs,
        "pth_total": len(achados),
        "pth_com_executavel": sum(1 for a in achados if a["executaveis"]),
        "linhas_executaveis": sum(a["executaveis"] for a in achados),
        "varredura_ms": round(ms, 2),
        "arquivos": achados,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
