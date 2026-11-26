# 18 · O deid limpa um DICOM brasileiro? A receita padrão deixou CPF ou CNS em 47 de 60

O [deid](https://github.com/pydicom/deid) (MIT) é a biblioteca Python do ecossistema pydicom pra tirar identificador de cabeçalho DICOM com uma "receita" de regras. Esta demo gera 60 arquivos DICOM 100% sintéticos com identificadores brasileiros falsos (CPF e CNS válidos por algoritmo, nome fictício óbvio) colocados nos campos de paciente e também onde eles escapam na prática: descrição do estudo, comentário da imagem, descrição do procedimento, sequência aninhada e tag privada do PACS. Depois roda o `replace_identifiers()` em 3 cenários e procura cada valor plantado em todo elemento do arquivo, inclusive dentro de sequência.

Resultado (26/11/2026, Linux, CPU, Python 3.11.18, deid 0.4.13, pydicom 3.0.2): a receita padrão tirou PatientName, PatientID, OtherPatientIDs, data de nascimento, endereço e telefone do paciente nos **60 de 60** arquivos. Mas **47 de 60** ainda tinham CPF ou CNS inteiro e **55 de 60** algum dado pessoal, todos em texto livre ou tag privada. Com `remove_private=True`: **36 de 60** com CPF ou CNS. Com uma receita extra de 7 linhas (`receita_br.dicom`): **0 de 60**. Nos 3 cenários a receita padrão também apagou SOP, Study e Series Instance UID dos 60 arquivos.

*English: deid 0.4.13 (pydicom 3.0.2) on 60 synthetic DICOM files with fake Brazilian identifiers (CPF tax ID and CNS health card number, valid by checksum). The default recipe removed the patient name, ID, other IDs, birth date, address and phone in 60 of 60 files, but 47 of 60 still carried a full CPF or CNS in free-text fields or a private tag. With `remove_private=True`: 36 of 60. With a 7-line extra recipe: 0 of 60. The default recipe also deletes the SOP, Study and Series Instance UIDs.*

Artigo: https://rogerio.eti.br/deid-dicom-cpf-texto-livre/

## Como rodar (3 comandos)

```bash
pip install -r requirements.txt        # deid, pydicom e pytest com versão fixa
python demo.py                         # gera os 60 DICOM sintéticos numa pasta temporária, roda 3 cenários, grava results/
python -m pytest tests -q -s           # prova a afirmação central em 20 arquivos, em menos de 1 s
```

CPU, sem GPU, sem chave de API, sem conta, sem rede depois do `pip install`. Os `.dcm` ficam numa pasta temporária e somem no fim.

## O que mostra

- `gera_dicom.py`: 60 DICOM CT de 8×8 pixels zerados (seed fixa 20261127). Todo arquivo tem nome, CPF (no PatientID), CNS (no OtherPatientIDs), nascimento, sexo, endereço, telefone e instituição fictícios. Por sorteio: CPF na StudyDescription (40%), nome e CNS no ImageComments (50%), telefone na RequestedProcedureDescription (30%), nome numa RequestAttributesSequence (50%) e CPF numa tag privada `(0009,xx01)` do bloco `SINTETICO_PACS` (50%).
- `demo.py`: salva, roda `replace_identifiers()` e varre todos os elementos com `Dataset.iterall()` atrás dos valores plantados.
- `receita_br.dicom`: 7 linhas `REMOVE` somadas à receita padrão (`DeidRecipe(..., base=True)`).
- `tests/test_deid.py`: em 20 arquivos, a receita padrão tira PatientName e PatientID de todos e ainda assim deixa CPF e tag privada.

## Resultado real

Saída completa em [`results/resultado.txt`](results/resultado.txt) e [`results/resultado.json`](results/resultado.json); o teste em [`results/pytest.txt`](results/pytest.txt); versões em [`results/pip-freeze.txt`](results/pip-freeze.txt).

| Cenário (60 arquivos) | com CPF ou CNS | com dado pessoal* | com nome da instituição | sem os 3 UIDs |
|---|---|---|---|---|
| A receita padrão | 47 | 55 | 60 | 60 |
| B padrão + `remove_private=True` | 36 | 52 | 60 | 60 |
| C padrão + `receita_br.dicom` + `remove_private=True` | 0 | 0 | 0 | 60 |

\* CPF, CNS, nome, nascimento, telefone ou endereço; não conta a instituição.

Onde sobrou, no cenário A (arquivos): InstitutionName 60, tag privada 30, ScheduledProcedureStepDescription (dentro da sequência) 27, ImageComments 26, StudyDescription 23, RequestedProcedureDescription 21. Nascimento e endereço: 0.

## Limites honestos

- **Dado sintético e campos escolhidos por mim.** Onde o identificador escapa num PACS de verdade depende do equipamento e de quem digita. Os percentuais do sorteio são meus, não medição de campo.
- **Só cabeçalho.** Texto queimado no pixel (laudo na imagem, ultrassom) não entra; o deid tem um módulo de pixel que esta demo não testa.
- **A receita extra é bruta.** Ela apaga a descrição do estudo inteira. Em pesquisa você pode precisar dela; aí o caminho é trocar por valor neutro, não apagar.
- **Apagar UID não é anonimizar bem.** Sem SOP, Study e Series Instance UID, o arquivo perde a ligação com o estudo. Pra manter a série, a receita precisa trocar o UID por um novo e consistente, o que esta demo não faz.
- **Não comparei com o perfil do padrão linha a linha.** A página do DICOM PS3.15 (Anexo E) não abriu nesta sessão; conferi a receita lendo o arquivo `deid/data/deid.dicom` instalado (67 linhas `REMOVE` e 6 `ADD` no cabeçalho) e a assinatura de `replace_identifiers()` (`remove_private=False` por padrão).

## Fonte

- deid 0.4.13 (MIT, PyPI, repositório https://github.com/pydicom/deid) e pydicom 3.0.2 (MIT), versões conferidas no PyPI em 26/11/2026.
- Código lido: `deid/dicom/header.py` (`replace_identifiers`) e `deid/data/deid.dicom` (seção `%header`).

## Licença e crédito

MIT, como o resto do repositório. Parte do nursia-research-lab (NursIA, PPGINFOS/UFSC, bolsa FAPESC). Dado 100% sintético: nenhum arquivo DICOM real, nenhum dado de paciente.

Como citar: Rodrigues, R. (2026). *O deid limpa um DICOM brasileiro?* (demo 18). nursia-research-lab. https://github.com/rogeriorrodrigues/nursia-research-lab/tree/main/demos/18-deid-dicom-cpf
