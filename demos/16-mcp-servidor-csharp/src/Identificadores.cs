// As 4 ferramentas da demo 13, agora em C#. Mesmo nome, mesma descrição.
// Dado sintético: o CPF e o CNS da nota de teste são gerados por algoritmo.
using System.ComponentModel;
using System.Text.RegularExpressions;
using ModelContextProtocol.Server;

[McpServerToolType]
public static class Identificadores
{
    static readonly Regex Cpf = new(@"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b");
    static readonly Regex Cns = new(@"\b[1-9]\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b");

    static string SoDigitos(string v) => Regex.Replace(v, @"\D", "");

    [McpServerTool(Name = "validar_cpf")]
    [Description("Confere os dois dígitos verificadores de um CPF (11 dígitos, com ou sem pontuação).")]
    public static bool ValidarCpf(string cpf)
    {
        var d = SoDigitos(cpf);
        if (d.Length != 11 || d.Distinct().Count() == 1) return false;
        foreach (var n in new[] { 9, 10 })
        {
            var soma = 0;
            for (var i = 0; i < n; i++) soma += (d[i] - '0') * (n + 1 - i);
            if ((soma * 10) % 11 % 10 != d[n] - '0') return false;
        }
        return true;
    }

    [McpServerTool(Name = "validar_cns")]
    [Description("Confere o Cartão Nacional de Saúde (15 dígitos) pela soma ponderada módulo 11.")]
    public static bool ValidarCns(string cns)
    {
        var d = SoDigitos(cns);
        if (d.Length != 15 || !"126789".Contains(d[0])) return false;
        var soma = 0;
        for (var i = 0; i < 15; i++) soma += (d[i] - '0') * (15 - i);
        return soma % 11 == 0;
    }

    [McpServerTool(Name = "mascarar_identificadores")]
    [Description("Troca CPF e CNS válidos do texto por [CPF] e [CNS]. Número inválido fica como está.")]
    public static string MascararIdentificadores(string texto)
    {
        texto = Cns.Replace(texto, m => ValidarCns(m.Value) ? "[CNS]" : m.Value);
        return Cpf.Replace(texto, m => ValidarCpf(m.Value) ? "[CPF]" : m.Value);
    }

    [McpServerTool(Name = "contar_identificadores")]
    [Description("Conta quantos CPF e CNS válidos e inválidos aparecem no texto, sem devolver os números.")]
    public static Dictionary<string, int> ContarIdentificadores(string texto)
    {
        var cpfs = Cpf.Matches(texto).Select(m => m.Value).ToList();
        var cnss = Cns.Matches(texto).Select(m => m.Value).ToList();
        return new()
        {
            ["cpf_validos"] = cpfs.Count(ValidarCpf),
            ["cpf_invalidos"] = cpfs.Count(c => !ValidarCpf(c)),
            ["cns_validos"] = cnss.Count(ValidarCns),
            ["cns_invalidos"] = cnss.Count(c => !ValidarCns(c)),
        };
    }
}
