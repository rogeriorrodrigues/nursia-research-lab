// Demo 15: Firely .NET SDK (Hl7.Fhir.R4B 6.8.0) + Firely.Fhir.Validation.R4B 3.6.0
// nos mesmos 240 recursos FHIR R4B sintéticos da demo 11 (HealthChain).
// Duas camadas: o deserializador (parser) e o Validator (perfil base do FHIR).
// Reprovado = o parser acusou erro OU o OperationOutcome tem issue error/fatal.
// Uso: dotnet run -c Release --project src -- data/recursos.jsonl results
using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Nodes;
using Firely.Fhir.Validation;
using Hl7.Fhir.Model;
using Hl7.Fhir.Serialization;
using Hl7.Fhir.Specification.Source;
using Hl7.Fhir.Specification.Terminology;

var entrada = args.Length > 0 ? args[0] : "data/recursos.jsonl";
var saida = args.Length > 1 ? args[1] : "results";
Directory.CreateDirectory(saida);

// Categorias e natureza, na mesma ordem da demo 11 (true = forma, false = conteúdo).
var categorias = new (string chave, string desc, bool forma)[] {
    ("obrigatorio_ausente", "campo obrigatório ausente", true),
    ("data_formato_br", "data no formato dd/mm/aaaa", true),
    ("campo_desconhecido", "campo que não existe no recurso", true),
    ("codigo_fora_do_conjunto", "valor fora do conjunto obrigatório (code)", true),
    ("loinc_inventado", "código inventado sob o sistema LOINC", false),
    ("unidade_ucum_invalida", "unidade que não é UCUM válida", false),
    ("referencia_quebrada", "referência pra um Patient que não está no Bundle", false),
    ("cpf_digito_invalido", "CPF com dígito verificador errado", false),
    ("invariante_obs6", "valor e dataAbsentReason juntos (invariante obs-6)", false),
};

// 1. Montagem: pacote da especificação R4B (zip local), terminologia local, sem rede.
var sw = Stopwatch.StartNew();
var fonte = new CachedResolver(ZipSource.CreateValidationSource());
var terminologia = LocalTerminologyService.CreateDefaultForCore(fonte);
var validador = new Validator(fonte, terminologia);
var montagemMs = sw.Elapsed.TotalMilliseconds;

// Deserializador estrito (o padrão do SDK). Em caso de erro devolve o resultado parcial.
var parser = new FhirJsonDeserializer();

var linhas = File.ReadAllLines(entrada);
var resultados = new List<JsonObject>();
var tempos = new List<double>();
foreach (var linha in linhas)
{
    var item = JsonNode.Parse(linha)!.AsObject();
    var json = item["recurso"]!.ToJsonString();
    var t0 = Stopwatch.GetTimestamp();
    var ok = parser.TryDeserializeResource(json, out var recurso, out var errosParser);
    var errosP = (errosParser ?? Enumerable.Empty<Hl7.Fhir.Utility.CodedException>()).Select(e => e.Message).ToList();
    var issues = new List<OperationOutcome.IssueComponent>();
    if (recurso is not null)
        issues = validador.Validate(recurso).Issue;
    var dt = Stopwatch.GetElapsedTime(t0).TotalMilliseconds;
    tempos.Add(dt);
    var erros = issues.Where(i => i.Severity is OperationOutcome.IssueSeverity.Error or OperationOutcome.IssueSeverity.Fatal).ToList();
    var validadorReprovou = erros.Count > 0;
    var parserReprovou = !ok || errosP.Count > 0;
    resultados.Add(new JsonObject {
        ["id"] = item["id"]!.GetValue<string>(),
        ["categoria"] = item["categoria"]!.GetValue<string>(),
        ["parser_reprovou"] = parserReprovou,
        ["validador_reprovou"] = validadorReprovou,
        ["reprovado"] = parserReprovou || validadorReprovou,
        ["erros_parser"] = new JsonArray(errosP.Select(m => (JsonNode)JsonValue.Create(m)!).ToArray()),
        ["issues"] = new JsonArray(issues.Select(i => (JsonNode)new JsonObject {
            ["severity"] = i.Severity?.ToString(),
            ["code"] = i.Details?.Coding?.FirstOrDefault()?.Code ?? i.Code?.ToString(),
            ["expression"] = string.Join(",", i.Expression ?? new List<string>()),
            ["texto"] = i.Details?.Text,
        }).ToArray()),
        ["ms"] = Math.Round(dt, 3),
    });
}

// 2. Resumo
var porCat = new JsonObject();
foreach (var cat in categorias.Select(c => c.chave).Prepend("valido"))
{
    var rs = resultados.Where(r => r["categoria"]!.GetValue<string>() == cat).ToList();
    porCat[cat] = new JsonObject {
        ["total"] = rs.Count,
        ["reprovados"] = rs.Count(r => r["reprovado"]!.GetValue<bool>()),
        ["pelo_parser"] = rs.Count(r => r["parser_reprovou"]!.GetValue<bool>()),
        ["pelo_validador"] = rs.Count(r => r["validador_reprovou"]!.GetValue<bool>()),
    };
}
var defeituosos = resultados.Where(r => r["categoria"]!.GetValue<string>() != "valido").ToList();
var forma = defeituosos.Where(r => categorias.First(c => c.chave == r["categoria"]!.GetValue<string>()).forma).ToList();
var conteudo = defeituosos.Except(forma).ToList();
var validos = resultados.Except(defeituosos).ToList();
// O primeiro recurso paga a compilação dos perfis; separo do tempo em regime.
var mediaRegime = tempos.Skip(1).Average();
var mediana = tempos.Skip(1).OrderBy(x => x).ElementAt((tempos.Count - 1) / 2);
var metricas = new JsonObject {
    ["hl7.fhir.r4b"] = typeof(Resource).Assembly.GetName().Version!.ToString(),
    ["firely.fhir.validation"] = typeof(Validator).Assembly.GetName().Version!.ToString(),
    ["dotnet"] = Environment.Version.ToString(),
    ["recursos"] = resultados.Count,
    ["montagem_ms"] = Math.Round(montagemMs, 1),
    ["primeiro_recurso_ms"] = Math.Round(tempos[0], 1),
    ["media_regime_ms"] = Math.Round(mediaRegime, 2),
    ["mediana_regime_ms"] = Math.Round(mediana, 2),
    ["por_categoria"] = porCat,
    ["defeitos_total"] = defeituosos.Count,
    ["defeitos_reprovados"] = defeituosos.Count(r => r["reprovado"]!.GetValue<bool>()),
    ["forma_total"] = forma.Count,
    ["forma_reprovados"] = forma.Count(r => r["reprovado"]!.GetValue<bool>()),
    ["conteudo_total"] = conteudo.Count,
    ["conteudo_reprovados"] = conteudo.Count(r => r["reprovado"]!.GetValue<bool>()),
    ["validos_total"] = validos.Count,
    ["validos_reprovados"] = validos.Count(r => r["reprovado"]!.GetValue<bool>()),
};
var opt = new JsonSerializerOptions { WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
File.WriteAllText(Path.Combine(saida, "metricas.json"), metricas.ToJsonString(opt) + "\n");
File.WriteAllLines(Path.Combine(saida, "raw.jsonl"), resultados.Select(r => r.ToJsonString(new JsonSerializerOptions { Encoder = opt.Encoder })));

// 2b. Controle da referência: o fullUrl "urn:uuid:pac-000" do gabarito não é UUID,
// e o parser recusa isso antes de olhar a referência. Aqui troco o fullUrl por um UUID
// válido (determinístico, derivado do id) e rodo duas variantes de cada um dos 20 Bundles:
//   A) UUID válido + subject apontando pra Patient fora do Bundle (o defeito pretendido)
//   B) UUID válido + subject apontando pro fullUrl do Patient do Bundle (controle, deve passar)
static string Uuid(string s) => "urn:uuid:" + new Guid(System.Security.Cryptography.MD5.HashData(System.Text.Encoding.UTF8.GetBytes(s)));
var controle = new List<JsonObject>();
foreach (var linha in linhas)
{
    var item = JsonNode.Parse(linha)!.AsObject();
    if (item["categoria"]!.GetValue<string>() != "referencia_quebrada") continue;
    foreach (var variante in new[] { "A_quebrada", "B_correta" })
    {
        var b = item["recurso"]!.DeepClone().AsObject();
        var entries = b["entry"]!.AsArray();
        var pacUrl = Uuid(entries[0]!["resource"]!["id"]!.GetValue<string>());
        entries[0]!["fullUrl"] = pacUrl;
        entries[1]!["fullUrl"] = Uuid(entries[1]!["resource"]!["id"]!.GetValue<string>());
        if (variante == "B_correta") entries[1]!["resource"]!["subject"]!["reference"] = pacUrl;
        var ok = parser.TryDeserializeResource(b.ToJsonString(), out var rec, out var ep);
        var iss = rec is null ? new List<OperationOutcome.IssueComponent>() : validador.Validate(rec).Issue;
        var err = iss.Where(i => i.Severity is OperationOutcome.IssueSeverity.Error or OperationOutcome.IssueSeverity.Fatal).ToList();
        var warn = iss.Where(i => i.Severity is OperationOutcome.IssueSeverity.Warning).ToList();
        controle.Add(new JsonObject {
            ["id"] = item["id"]!.GetValue<string>(), ["variante"] = variante,
            ["parser_reprovou"] = !ok || (ep?.Any() ?? false),
            ["erros"] = new JsonArray(err.Select(i => (JsonNode)JsonValue.Create($"{string.Join(",", i.Expression ?? new List<string>())}: {i.Details?.Text}")!).ToArray()),
            ["avisos"] = new JsonArray(warn.Select(i => (JsonNode)JsonValue.Create($"{string.Join(",", i.Expression ?? new List<string>())}: {i.Details?.Text}")!).ToArray()),
        });
    }
}
File.WriteAllLines(Path.Combine(saida, "controle-referencia.jsonl"), controle.Select(r => r.ToJsonString(new JsonSerializerOptions { Encoder = opt.Encoder })));
int Rep(string v) => controle.Count(r => r["variante"]!.GetValue<string>() == v && (r["parser_reprovou"]!.GetValue<bool>() || r["erros"]!.AsArray().Count > 0));
int Avi(string v) => controle.Count(r => r["variante"]!.GetValue<string>() == v && r["avisos"]!.AsArray().Count > 0);
metricas["controle_referencia"] = new JsonObject {
    ["A_quebrada_reprovados"] = Rep("A_quebrada"), ["A_quebrada_com_aviso"] = Avi("A_quebrada"),
    ["B_correta_reprovados"] = Rep("B_correta"), ["B_correta_com_aviso"] = Avi("B_correta"), ["total_por_variante"] = controle.Count / 2,
};
File.WriteAllText(Path.Combine(saida, "metricas.json"), metricas.ToJsonString(opt) + "\n");

// 3. Tabela lado a lado com o HealthChain 0.16.1 (results da demo 11, copiado em data/)
var hc = JsonNode.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(entrada)!, "healthchain-0.16.1-metricas.json")))!["por_categoria"]!;
var t = new List<string> {
    $"Firely: Hl7.Fhir.R4B {metricas["hl7.fhir.r4b"]}, Firely.Fhir.Validation {metricas["firely.fhir.validation"]}, .NET {metricas["dotnet"]}, perfil base R4B, terminologia local, sem rede",
    $"Montagem do validador: {montagemMs:F0} ms · 1º recurso: {tempos[0]:F0} ms · depois: média {mediaRegime:F2} ms, mediana {mediana:F2} ms por recurso",
    "",
    "| Categoria | Natureza | HealthChain 0.16.1 | Firely 3.6.0 | só parser | só validador |",
    "|---|---|---|---|---|---|",
};
foreach (var c in categorias)
{
    var f = porCat[c.chave]!;
    var h = hc[c.chave]!;
    t.Add($"| {c.desc} | {(c.forma ? "forma" : "conteúdo")} | {h["reprovados"]}/{h["total"]} | {f["reprovados"]}/{f["total"]} | {f["pelo_parser"]} | {f["pelo_validador"]} |");
}
var v = porCat["valido"]!;
t.Add($"| (controle) recurso válido | - | {hc["valido"]!["reprovados"]}/{hc["valido"]!["total"]} | {v["reprovados"]}/{v["total"]} | {v["pelo_parser"]} | {v["pelo_validador"]} |");
t.Add("");
t.Add($"Firely, defeitos de forma reprovados: {metricas["forma_reprovados"]}/{metricas["forma_total"]}");
t.Add($"Firely, defeitos de conteúdo reprovados: {metricas["conteudo_reprovados"]}/{metricas["conteudo_total"]}");
t.Add($"Firely, defeitos reprovados no total: {metricas["defeitos_reprovados"]}/{metricas["defeitos_total"]}");
t.Add($"Firely, válidos reprovados por engano: {metricas["validos_reprovados"]}/{metricas["validos_total"]}");
var cr = metricas["controle_referencia"]!;
t.Add("");
t.Add($"Controle da referência (fullUrl trocado por UUID válido, {cr["total_por_variante"]} Bundles por variante):");
t.Add($"  A) subject pra Patient fora do Bundle: {cr["A_quebrada_reprovados"]} reprovados, {cr["A_quebrada_com_aviso"]} com aviso");
t.Add($"  B) subject pro Patient do Bundle (controle): {cr["B_correta_reprovados"]} reprovados, {cr["B_correta_com_aviso"]} com aviso");
File.WriteAllLines(Path.Combine(saida, "tabela.md"), t);
foreach (var l in t) Console.WriteLine(l);
