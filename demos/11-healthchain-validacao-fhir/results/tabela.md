healthchain 0.16.1, validate_resource(), R4B, tempo médio 0.17 ms por recurso

| Categoria | Natureza | Reprovados |
|---|---|---|
| campo obrigatório ausente | forma | 20/20 |
| data no formato dd/mm/aaaa | forma | 20/20 |
| campo que não existe no recurso | forma | 20/20 |
| valor fora do conjunto obrigatório (code) | forma | 20/20 |
| código inventado sob o sistema LOINC | conteúdo | 0/20 |
| unidade que não é UCUM válida | conteúdo | 0/20 |
| referência pra um Patient que não está no Bundle | conteúdo | 0/20 |
| CPF com dígito verificador errado | conteúdo | 0/20 |
| valor e dataAbsentReason juntos (invariante obs-6) | conteúdo | 0/20 |
| (controle) recurso válido | - | 0/60 |

Defeitos de forma reprovados: 80/80
Defeitos de conteúdo reprovados: 0/100
Defeitos reprovados no total: 80/180
