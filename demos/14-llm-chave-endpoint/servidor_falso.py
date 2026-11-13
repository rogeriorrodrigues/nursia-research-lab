"""Endpoint falso compatível com OpenAI, só em 127.0.0.1.

Guarda o cabeçalho Authorization de cada pedido e responde um chat.completion
mínimo. Nada sai da máquina.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silencia o log padrão
        pass

    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        corpo = self.rfile.read(tamanho) if tamanho else b""
        self.server.pedidos.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "model": (json.loads(corpo or b"{}") or {}).get("model"),
            }
        )
        resposta = {
            "id": "chatcmpl-sintetico",
            "object": "chat.completion",
            "created": 0,
            "model": "falso",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        dados = json.dumps(resposta).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)


def subir():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.pedidos = []
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
