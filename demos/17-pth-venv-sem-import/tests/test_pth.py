"""Prova a afirmação central: um .pth com linha import roda em `python -c pass`, inclusive com -I; só -S desliga."""
import subprocess
import sys
import venv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from varre_pth import classifica, varre  # noqa: E402


def test_classifica():
    assert classifica("import os; os.getcwd()") == "executavel"
    assert classifica("import\tsys") == "executavel"
    assert classifica("importante/caminho") == "caminho"
    assert classifica("# import os") == "vazia_ou_comentario"
    assert classifica("/opt/projeto/src") == "caminho"


def test_marca_roda_sem_import(tmp_path):
    venv.EnvBuilder(with_pip=False).create(tmp_path / "v")
    py = tmp_path / "v" / "bin" / "python"
    sp = subprocess.run([py, "-c", "import site;print(site.getsitepackages()[0])"],
                        capture_output=True, text=True).stdout.strip()
    Path(sp, "zz_teste.pth").write_text('import sys; sys.stderr.write("MARCA-TESTE\\n")\n')
    achou = {f: "MARCA-TESTE" in subprocess.run([py, *f.split(), "-c", "pass"], capture_output=True, text=True).stderr
             for f in ("", "-I", "-S")}
    print("marca apareceu:", achou)
    assert achou == {"": True, "-I": True, "-S": False}
    v = varre([sp])
    assert any(a["arquivo"] == "zz_teste.pth" and a["executaveis"] == 1 for a in v)
