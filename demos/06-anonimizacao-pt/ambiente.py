"""Máquina e .env, pra registrar junto com cada resultado."""

import os
import platform
import subprocess
from pathlib import Path


def carregar_env(caminho: Path = Path(__file__).resolve().parent / ".env") -> None:
    """Lê KEY=VALUE do .env sem sobrescrever variáveis já definidas."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip())


def _sysctl(chave: str) -> str | None:
    try:
        return subprocess.check_output(["sysctl", "-n", chave], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def info_maquina() -> dict:
    chip, ram = platform.processor() or platform.machine(), None
    if platform.system() == "Darwin":
        chip = _sysctl("machdep.cpu.brand_string") or chip
        ram = int(_sysctl("hw.memsize") or 0) or None
    elif Path("/proc/meminfo").exists():
        kb = next((l.split()[1] for l in open("/proc/meminfo") if l.startswith("MemTotal")), "0")
        ram = int(kb) * 1024
    return {"sistema": f"{platform.system()} {platform.release()}", "chip": chip,
            "ram_gb": round(ram / 2**30, 1) if ram else None, "python": platform.python_version()}
