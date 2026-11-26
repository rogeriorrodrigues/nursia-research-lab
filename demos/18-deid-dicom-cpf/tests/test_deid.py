import copy, logging, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deid.dicom import replace_identifiers
from gera_dicom import gera
from demo import vazamentos

logging.disable(logging.WARNING)


def _limpa(n, **kw):
    arquivos = gera(n=n)
    with tempfile.TemporaryDirectory() as tmp:
        caminhos = []
        for k, (ds, _) in enumerate(arquivos):
            p = os.path.join(tmp, f"{k}.dcm"); ds.save_as(p, enforce_file_format=True); caminhos.append(p)
        limpos = replace_identifiers(caminhos, **kw)
    return [(l, can) for l, (_, can) in zip(limpos, arquivos)]


def test_padrao_tira_campos_de_paciente_mas_deixa_cpf_no_texto_livre():
    res = _limpa(20)
    assert all("PatientName" not in l and "PatientID" not in l for l, _ in res)
    com_cpf = sum(1 for l, can in res if "CPF" in vazamentos(l, can))
    print(f"\n[padrao] arquivos com CPF depois do deid: {com_cpf} de 20")
    assert com_cpf > 0


def test_tag_privada_fica_sem_remove_private():
    res = _limpa(20)
    privadas = sum(1 for l, _ in res if any(el.tag.is_private for el in l.iterall()))
    print(f"[padrao] arquivos com tag privada: {privadas} de 20")
    assert privadas > 0
