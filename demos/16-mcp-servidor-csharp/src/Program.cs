// Servidor MCP mínimo em C#: o que o SDK pede pra subir as 4 ferramentas por HTTP.
// Nada de autenticação, limite de chamadas ou log de auditoria: de propósito,
// pra medir o que vem pronto e o que fica com você.
var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddMcpServer()
    .WithHttpTransport()
    .WithToolsFromAssembly();

var app = builder.Build();
app.MapMcp("/mcp");
app.Run(args.Length > 0 ? args[0] : "http://127.0.0.1:5088");
