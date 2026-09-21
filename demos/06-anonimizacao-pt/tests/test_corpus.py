"""O corpus é determinístico e cada span aponta pro texto certo."""

import corpus
from demo04 import validar_cns, validar_cpf
from metricas import TIPOS

HASH_ESPERADO = "55fb607fce5fba8b6796be23985c90e0f88af3e36bb310e6d43b943c07ae333f"


def test_corpus_deterministico_mesma_seed_mesmo_hash():
    notas = corpus.gerar_corpus()
    assert len(notas) == 200
    assert corpus.hash_corpus(notas) == HASH_ESPERADO
    assert corpus.hash_corpus(corpus.gerar_corpus()) == HASH_ESPERADO


def test_arquivo_exportado_bate_com_o_gerador():
    assert corpus.carregar() == corpus.gerar_corpus()


def test_todo_span_aponta_pro_texto_certo():
    for nota in corpus.gerar_corpus():
        for s in nota["spans"] + nota["distratores"]:
            assert nota["texto"][s["inicio"]:s["fim"]] == s["texto"], nota["id"]
        assert all(s["tipo"] in TIPOS for s in nota["spans"])


def test_spans_nao_se_sobrepoem():
    for nota in corpus.gerar_corpus():
        todos = sorted(nota["spans"] + nota["distratores"], key=lambda s: s["inicio"])
        for a, b in zip(todos, todos[1:]):
            assert a["fim"] <= b["inicio"], nota["id"]


def test_cpf_e_cns_validos_pelo_digito_verificador():
    for nota in corpus.gerar_corpus():
        for s in nota["spans"]:
            if s["tipo"] == "BR_CPF":
                assert validar_cpf(s["texto"]), s["texto"]
            if s["tipo"] == "BR_CNS":
                assert validar_cns(s["texto"]), s["texto"]
        for d in nota["distratores"]:
            if d["tipo"] == "protocolo":
                assert not validar_cpf(d["texto"]), d["texto"]


def test_toda_nota_tem_3_a_6_frases_e_um_documento():
    for nota in corpus.gerar_corpus():
        assert 3 <= nota["n_frases"] <= 6
        assert nota["texto"].count(". ") + 1 == nota["n_frases"]
        assert any(s["tipo"] in ("BR_CPF", "BR_CNS") for s in nota["spans"])


def test_casos_dificeis_presentes():
    est = corpus.estatisticas(corpus.gerar_corpus())
    for nome, (k, n) in est.items():
        assert k > 0, nome
    assert 0.3 <= est["cpf_sem_pontuacao"][0] / est["cpf_sem_pontuacao"][1] <= 0.7
    assert 0.3 <= est["data_por_extenso"][0] / est["data_por_extenso"][1] <= 0.7
    assert 0.3 <= est["telefone_sem_ddd"][0] / est["telefone_sem_ddd"][1] <= 0.7
