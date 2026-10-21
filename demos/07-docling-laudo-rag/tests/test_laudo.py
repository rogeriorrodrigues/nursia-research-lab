import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gerar_laudos  # noqa: E402
from laudo_rag import faixa_br, numero_br, processar  # noqa: E402

FORA = ["Glicose em jejum", "Hemoglobina", "Potássio"]


@pytest.fixture(scope="module")
def resultados(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("dados")
    gerar_laudos.PASTA = pasta
    return {c.suffix[1:]: processar(c) for c in gerar_laudos.gerar()}


@pytest.mark.parametrize("formato", ["docx", "xlsx", "md"])
def test_tres_formatos_marcam_os_mesmos_exames(resultados, formato):
    r = resultados[formato]
    assert len(r["exames"]) == 6
    assert sorted(e["exame"] for e in r["exames"] if e["fora"]) == FORA
    print(f"{formato}: {len(r['exames'])} exames, fora = "
          f"{sorted(e['exame'] for e in r['exames'] if e['fora'])}, {r['segundos']:.2f} s")


@pytest.mark.parametrize("formato", ["docx", "md"])
def test_negrito_do_laboratorio_bate_com_a_conta(resultados, formato):
    assert all(e["negrito_no_laudo"] == e["fora"] for e in resultados[formato]["exames"])


def test_celula_do_docx_chega_com_asterisco(resultados):
    doc = resultados["docx"]["doc"]
    df = doc.tables[0].export_to_dataframe(doc=doc)
    assert df["Resultado"][0] == "**11,2**"


def test_conversao_ingenua_erra_o_numero_brasileiro():
    ingenuo = float("7.850".replace(",", "."))
    assert ingenuo == 7.85
    assert numero_br("7.850") == 7850.0
    assert numero_br("**5,8**") == 5.8
    assert faixa_br("4.000 a 11.000") == (4000.0, 11000.0)
    with pytest.raises(ValueError):
        float("**11,2**".replace(",", "."))
    print(f"ingênuo: 7.850 -> {ingenuo}; numero_br: {numero_br('7.850')}")


def test_chunk_por_exame_nao_leva_o_nome_do_paciente(resultados):
    chunks = resultados["docx"]["chunks"]
    assert len(chunks) == 6
    assert all("Maria" not in c["texto"] for c in chunks)
    potassio = next(c for c in chunks if c["exame"] == "Potássio")
    assert potassio["fora"] and "FORA DA REFERÊNCIA" in potassio["texto"]


def test_pdf_e_recusado_sem_tentar_a_rede(tmp_path):
    from docling.exceptions import ConversionError

    from laudo_rag import CONVERSOR
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    with pytest.raises(ConversionError):
        CONVERSOR.convert(str(pdf))
