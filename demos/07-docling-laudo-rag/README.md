# 07 · Lab report to RAG chunks with Docling 2.135.0, no model download

A synthetic Brazilian lab report in DOCX, XLSX and Markdown goes through Docling 2.135.0, becomes a DataFrame, and ends as one RAG chunk per test, with the out-of-range flag computed in code. All three formats flagged the same 3 of 6 tests (hemoglobin, fasting glucose, potassium), in 0.07 s or less per file on CPU. The trap is the naive `float()`: it reads leukocytes "7.850" (7,850 in Brazilian format) as 7.85 and turns an in-range test into an alarm.

[Português abaixo](#pt-br)

## Try it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python gerar_laudos.py && .venv/bin/python laudo_rag.py
.venv/bin/python -m pytest -s -q
```

CPU only, no GPU, no API key, no network after `pip install`. PDF is left out on purpose: Docling's PDF pipeline downloads layout and table models on first use, and the converter here accepts only DOCX, XLSX and MD.

## What it does

| File | Role |
|---|---|
| `gerar_laudos.py` | writes one synthetic report (6 tests, fictional patient) as DOCX, XLSX and MD into `dados/`; out-of-range results in bold in DOCX and MD |
| `laudo_rag.py` | Docling conversion, `numero_br` / `faixa_br` parsers, range check, one chunk per test, writes `results/` |
| `tests/test_laudo.py` | 9 tests: same 3 tests flagged in 3 formats, bold matches the math, asterisks in the DOCX cell, the `float()` trap, no patient name in chunks, PDF refused |
| `results/` | real output of the run: `saida.txt`, `pytest.txt`, `resumo.json`, `chunks.jsonl` |

## Result (one run, Python 3.11, Docling 2.135.0, docling-core 2.103.1, Linux)

| Format | Conversion time | Tests read | Out of range | Bold matches the math | HierarchicalChunker chunks | Per-test chunks |
|---|---|---|---|---|---|---|
| DOCX | 0.07 s | 6 | 3 | yes (3 of 3) | 3 | 6 |
| MD | 0.01 s | 6 | 3 | yes (3 of 3) | 3 | 6 |
| XLSX | 0.01 s | 6 | 3 | no bold in file | 1 | 6 |

The DOCX time includes converter warm-up (it runs first).

## Limits

- One synthetic report, six tests, written by the generator. It shows the code does what it says; it does not measure real lab reports.
- Reference ranges must be "min a max". "Inferior a 200", "< 5" or ranges by sex and age break `faixa_br`.
- `numero_br` assumes the Brazilian format. "7.85" in US format becomes 785.
- The first table with a "Resultado" column wins; several tables, other headers or merged cells need your own mapping.
- PDF and `HybridChunker` (downloads a tokenizer) were not run.
- Dropping the patient name from the chunk is not anonymization: file name and collection date still identify. Not clinical advice.

Article: https://rogerio.eti.br/docling-laudo-chunk-rag/

<a id="pt-br"></a>

# 07 · Laudo para chunks de RAG com Docling 2.135.0, sem baixar modelo

Um laudo sintético brasileiro em DOCX, XLSX e Markdown passa pelo Docling 2.135.0, vira DataFrame e termina como um chunk por exame, com a marca de "fora da referência" calculada no código. Os três formatos marcaram os mesmos 3 de 6 exames (hemoglobina, glicose em jejum e potássio), em até 0,07 s por arquivo, só com CPU. A armadilha é o `float()` ingênuo: ele lê os leucócitos "7.850" como 7,85 e transforma um exame dentro da faixa em alarme.

## Como rodar

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python gerar_laudos.py && .venv/bin/python laudo_rag.py
.venv/bin/python -m pytest -s -q
```

Sem GPU, sem chave de API, sem rede depois do `pip install`. PDF fica de fora de propósito: o pipeline de PDF do Docling baixa modelos de layout e de tabela no primeiro uso, e o conversor aceita só DOCX, XLSX e MD.

## Limite honesto

Um laudo sintético, seis exames, gerado por mim: mostra que o código faz o que diz, não mede laudo de laboratório real. A referência precisa estar no formato "mín a máx". O parser serve só para o padrão brasileiro de número. Tirar o nome do paciente do chunk não é anonimizar. Isto não é laudo médico.

Artigo: https://rogerio.eti.br/docling-laudo-chunk-rag/
