healthchain 0.16.1, validate_resource(), R4B, tempo médio 0.16 ms por recurso

| Categoria | Natureza | Reprovados |
|---|---|---|
| campo obrigatório ausente | estrutural | 20/20 |
| data no formato dd/mm/aaaa | estrutural | 20/20 |
| campo que não existe no recurso | estrutural | 20/20 |
| valor fora do conjunto obrigatório (code) | estrutural | 20/20 |
| código inventado sob o sistema LOINC | semântico | 0/20 |
| unidade que não é UCUM válida | semântico | 0/20 |
| referência pra um Patient que não está no Bundle | semântico | 0/20 |
| CPF com dígito verificador errado | semântico | 0/20 |
| valor e dataAbsentReason juntos (invariante obs-6) | semântico | 0/20 |
| (controle) recurso válido | - | 0/60 |

Defeitos estruturais reprovados: 80/80
Defeitos semânticos reprovados: 0/100
Defeitos reprovados no total: 80/180
