Firely: Hl7.Fhir.R4B 6.8.0.0, Firely.Fhir.Validation 3.6.0.0, .NET 8.0.34, perfil base R4B, terminologia local, sem rede
Montagem do validador: 240 ms · 1º recurso: 2409 ms · depois: média 16.13 ms, mediana 1.42 ms por recurso

| Categoria | Natureza | HealthChain 0.16.1 | Firely 3.6.0 | só parser | só validador |
|---|---|---|---|---|---|
| campo obrigatório ausente | forma | 20/20 | 20/20 | 20 | 20 |
| data no formato dd/mm/aaaa | forma | 20/20 | 20/20 | 20 | 20 |
| campo que não existe no recurso | forma | 20/20 | 20/20 | 20 | 20 |
| valor fora do conjunto obrigatório (code) | forma | 20/20 | 20/20 | 20 | 20 |
| código inventado sob o sistema LOINC | conteúdo | 0/20 | 0/20 | 0 | 0 |
| unidade que não é UCUM válida | conteúdo | 0/20 | 0/20 | 0 | 0 |
| referência pra um Patient que não está no Bundle | conteúdo | 0/20 | 20/20 | 20 | 20 |
| CPF com dígito verificador errado | conteúdo | 0/20 | 0/20 | 0 | 0 |
| valor e dataAbsentReason juntos (invariante obs-6) | conteúdo | 0/20 | 20/20 | 0 | 20 |
| (controle) recurso válido | - | 0/60 | 0/60 | 0 | 0 |

Firely, defeitos de forma reprovados: 80/80
Firely, defeitos de conteúdo reprovados: 40/100
Firely, defeitos reprovados no total: 120/180
Firely, válidos reprovados por engano: 0/60

Controle da referência (fullUrl trocado por UUID válido, 20 Bundles por variante):
  A) subject pra Patient fora do Bundle: 0 reprovados, 0 com aviso
  B) subject pro Patient do Bundle (controle): 0 reprovados, 0 com aviso
