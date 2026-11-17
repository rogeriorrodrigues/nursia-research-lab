# 15 · Firely Validator 3.6.0 nos mesmos 240 recursos FHIR da demo 11

O validador da Firely em .NET (`Firely.Fhir.Validation.R4B` 3.6.0 sobre `Hl7.Fhir.R4B` 6.8.0) reprovou **120 de 180 recursos FHIR defeituosos**, contra 80 do HealthChain 0.16.1 nos mesmos dados: os 80 de forma e **40 dos 100 de conteúdo**. Só 20 desses 40 caíram pelo defeito que eu plantei (a invariante `obs-6`). Os outros 20 são Bundles reprovados por um erro do meu próprio gabarito: o `fullUrl` `urn:uuid:pac-000` não é UUID. Com o `fullUrl` corrigido, a referência pra um Patient fora do Bundle passa: **0 de 20**. LOINC inventado, unidade fora do UCUM e CPF com dígito errado: 0 de 20 cada. Nos 60 válidos: 0 falsos positivos.

*English: Firely .NET validator (Firely.Fhir.Validation.R4B 3.6.0, Hl7.Fhir.R4B 6.8.0, base R4B profiles, local terminology only) on the same 240 synthetic FHIR R4B resources as demo 11. It rejected 120/180 defective resources (HealthChain 0.16.1: 80/180): 80/80 structural and 40/100 content. 20 of those 40 are the planted obs-6 invariant; the other 20 are Bundles rejected because my own fixture used `urn:uuid:pac-000`, which is not a valid UUID. With valid UUIDs, the dangling reference passes (0/20). Invented LOINC code, non-UCUM unit and bad CPF check digit: 0/20 each. 0/60 false positives. Median 1.4 ms per resource after a cold start of about 2.4 s.*

Artigo: https://rogerio.eti.br/firely-validador-fhir-dotnet/

## Como rodar (3 comandos)

Precisa do .NET 8 SDK e de Python 3.11+ (só pro teste).

```bash
dotnet run -c Release --project src -- data/recursos.jsonl results   # restaura do NuGet na 1ª vez; grava results/
pip install -r requirements.txt
python3 -m pytest tests -q -s
```

CPU, sem GPU, sem chave, sem conta. Depois do restore do NuGet, nada sai pra rede: o pacote da especificação R4B vem em `specification.zip` (pacote `Hl7.Fhir.Specification.Data.R4B` 6.8.0) e a terminologia é local.

## O que mostra

- `data/recursos.jsonl`: cópia dos 240 recursos FHIR R4B sintéticos da [demo 11](../11-healthchain-validacao-fhir/) (60 válidos, 180 com um defeito conhecido, 20 por categoria). O teste confere o SHA-256 contra o arquivo da demo 11.
- `data/healthchain-0.16.1-metricas.json`: os números da demo 11, pra montar a tabela lado a lado.
- `src/Program.cs`: passa cada recurso por duas camadas e anota as duas:
  1. o deserializador estrito do SDK (`FhirJsonDeserializer.TryDeserializeResource`), que já recusa forma errada;
  2. o `Validator` com o perfil base R4B, `LocalTerminologyService.CreateDefaultForCore` e nenhum `referenceResolver`. Se o parser recusa, o validador roda no resultado parcial.
  Reprovado = o parser acusou erro **ou** o `OperationOutcome` tem issue `error`/`fatal`.
- Controle da referência: os 20 Bundles de "referência quebrada" rodam de novo com `fullUrl` trocado por UUID válido (determinístico, MD5 do id), em duas variantes: A, `subject` pra um Patient fora do Bundle; B, `subject` pro `fullUrl` do Patient do Bundle.

O trecho que importa:

```csharp
var fonte = new CachedResolver(ZipSource.CreateValidationSource());
var terminologia = LocalTerminologyService.CreateDefaultForCore(fonte);
var validador = new Validator(fonte, terminologia);

var ok = parser.TryDeserializeResource(json, out var recurso, out var errosParser);
var issues = validador.Validate(recurso).Issue;
```

## Resultado (results/tabela.md)

| Categoria | Natureza | HealthChain 0.16.1 | Firely 3.6.0 | parser | validador |
|---|---|---|---|---|---|
| campo obrigatório ausente | forma | 20/20 | 20/20 | 20 | 20 |
| data no formato dd/mm/aaaa | forma | 20/20 | 20/20 | 20 | 20 |
| campo que não existe no recurso | forma | 20/20 | 20/20 | 20 | 20 |
| valor fora do conjunto obrigatório (`code`) | forma | 20/20 | 20/20 | 20 | 20 |
| código inventado sob o sistema LOINC | conteúdo | 0/20 | 0/20 | 0 | 0 |
| unidade que não é UCUM válida | conteúdo | 0/20 | 0/20 | 0 | 0 |
| referência pra um Patient que não está no Bundle | conteúdo | 0/20 | 20/20 (*) | 20 | 20 |
| CPF com dígito verificador errado | conteúdo | 0/20 | 0/20 | 0 | 0 |
| valor e `dataAbsentReason` juntos (invariante `obs-6`) | conteúdo | 0/20 | 20/20 | 0 | 20 |
| (controle) recurso válido | - | 0/60 | 0/60 | 0 | 0 |

(*) Pelo motivo errado: `string 'urn:uuid:pac-000' is not a correct literal for a uri` (`results/exemplo.txt`). Controle com UUID válido (`results/controle-referencia.jsonl`): variante A, 0 de 20 reprovados e 0 com aviso; variante B, 0 de 20.

- Forma: 80 de 80. Conteúdo: 40 de 100, dos quais 20 pelo defeito plantado (`obs-6`). Total: 120 de 180. Válidos reprovados: 0 de 60.
- O parser sozinho já pega os 80 de forma. A invariante `obs-6` é a única categoria que só o `Validator` pega.
- Tempo (`results/saida.txt`, .NET 8.0.34, CPU): montagem do validador 240 ms; o primeiro recurso de cada tipo paga a compilação do perfil (Patient 2,4 s, Observation 2,9 s, Condition 0,29 s, Bundle 0,33 s); depois disso, mediana de 1,42 ms por recurso. A média de 16 ms é puxada por esses quatro. Os 240 recursos levaram 6,3 s somados. Entre três rodadas na mesma máquina a mediana ficou entre 1,33 e 1,58 ms; o resto é determinístico.
- `results/raw.jsonl` guarda, por recurso, as mensagens do parser e do validador; `results/pytest.txt`, a saída do teste.

## Limites honestos

- **O defeito de referência do gabarito da demo 11 estava errado.** `urn:uuid:` pede um UUID; `pac-000` não é. O HealthChain não reclamou disso, a Firely reclamou. O 20/20 da tabela mede o `fullUrl`, não a referência. O número honesto pra referência quebrada é o do controle: 0 de 20.
- **Configuração padrão, sem perfil.** Sem `referenceResolver` e sem perfil que exija `aggregation` `bundled`, o validador não confere se a referência resolve dentro do Bundle. Não testei perfil com `aggregation` nem resolver de referência; com eles o resultado pode mudar.
- **Terminologia só local.** LOINC não vem no pacote da especificação, e a demo não chama servidor de terminologia (tx.fhir.org ou outro). Por isso o LOINC inventado passa sem aviso. A unidade fora do UCUM também passou sem aviso no perfil base. Não testei com servidor de terminologia.
- **CPF não é regra do FHIR.** O dígito verificador só seria checado por um perfil brasileiro com regra própria. Não validei contra perfil BR.
- **O gabarito é meu.** 9 categorias, 20 casos cada, escolhidas por mim. O 120/180 descreve este conjunto, não FHIR real.
- Só o caminho POCO (`Validate(Resource)`) com o deserializador estrito. Não testei `Validate(ElementNode)`, modo permissivo do parser, nem o validador Java da HL7.
- Todo dado é sintético: o CPF passa no dígito verificador mas é sorteado com semente fixa e não pertence a ninguém.

## Fonte

- Firely .NET SDK (`Hl7.Fhir.R4B` 6.8.0, `Hl7.Fhir.Specification.Data.R4B` 6.8.0), BSD-3-Clause: https://github.com/FirelyTeam/firely-net-sdk
- Firely Validator API (`Firely.Fhir.Validation.R4B` 3.6.0, publicado no NuGet em 29/10/2026), BSD-3-Clause: https://github.com/FirelyTeam/firely-validator-api
- Documentação de validação: https://docs.fire.ly/projects/Firely-NET-SDK/en/latest/validation/profile-validation.html
- Invariante `obs-6` (FHIR R4B, Observation): https://hl7.org/fhir/R4B/observation.html#invs
- Gabarito e demo anterior: [demos/11-healthchain-validacao-fhir](../11-healthchain-validacao-fhir/)

NursIA é pesquisa do PPGINFOS/UFSC, com bolsa FAPESC.
