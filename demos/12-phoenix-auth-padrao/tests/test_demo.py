"""Prova a afirmação central: o padrão loopback não pede senha; 0.0.0.0 pede."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import demo  # noqa: E402


def test_loopback_abre_e_todas_interfaces_fecham(tmp_path):
    aberto = demo.rodar(demo.CENARIOS[0], None, tmp_path)
    fechado = demo.rodar(demo.CENARIOS[1], None, tmp_path)
    print(f"\nloopback: spans sem credencial = {aberto['ler_spans_sem_credencial']}, "
          f"segredo na resposta = {aberto['segredo_na_resposta_sem_credencial']}")
    print(f"0.0.0.0: spans sem credencial = {fechado['ler_spans_sem_credencial']}, "
          f"login admin/admin = {fechado['login_admin_admin']}")
    assert aberto["ler_spans_sem_credencial"] == 200
    assert aberto["segredo_na_resposta_sem_credencial"] is True
    assert fechado["ler_spans_sem_credencial"] == 401
    assert fechado["segredo_na_resposta_sem_credencial"] is False
    assert fechado["login_admin_admin"] == 403
