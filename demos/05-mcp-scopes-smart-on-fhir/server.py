"""MCP server that refuses per tool, not per server.

Two tools, two SMART on FHIR scopes. The MCP Python SDK checks scopes at the
door (AuthSettings.required_scopes). The per-tool refusal below is ours.
All data is synthetic. Nothing here is a real patient.
"""

import json

from pydantic import AnyHttpUrl
from starlette.routing import Route

from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

RESOURCE = "http://127.0.0.1:8000/mcp"
METADATA = "http://127.0.0.1:8000/.well-known/oauth-protected-resource/mcp"

# Synthetic tokens. A real deployment verifies a JWT from the authorization
# server; the MCP server never issues tokens (it is a resource server only).
TOKENS = {
    "tok-reader": AccessToken(token="tok-reader", client_id="nursia-tutor", scopes=["patient/Patient.r"]),
    "tok-writer": AccessToken(
        token="tok-writer", client_id="nursia-pipeline", scopes=["patient/Patient.r", "patient/Observation.c"]
    ),
}

# SMART on FHIR v2 scope per tool. This map is the whole idea.
TOOL_SCOPES = {
    "read_patient": "patient/Patient.r",
    "create_observation": "patient/Observation.c",
}


class StaticVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        return TOKENS.get(token)


mcp = FastMCP(
    "nursia-scopes-demo",
    token_verifier=StaticVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("http://127.0.0.1:9000"),
        resource_server_url=AnyHttpUrl(RESOURCE),
        required_scopes=["patient/Patient.r"],  # door-level check, SDK does this
    ),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def read_patient(patient_id: str) -> dict:
    """Return a synthetic FHIR R4 Patient."""
    return {"resourceType": "Patient", "id": patient_id, "name": [{"family": "Sintetico", "given": ["Paciente"]}]}


@mcp.tool()
def create_observation(patient_id: str, loinc: str, value: float) -> dict:
    """Create a synthetic FHIR R4 Observation (nothing is persisted)."""
    return {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": loinc}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "valueQuantity": {"value": value},
    }


class ToolScopeGate:
    """HTTP 403 insufficient_scope per tool, as the MCP spec says a server SHOULD.

    The SDK only knows required_scopes for the whole server. This reads the
    JSON-RPC body, finds tools/call, and refuses before the tool runs.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        user = scope.get("user")
        if scope["type"] != "http" or scope["method"] != "POST" or not isinstance(user, AuthenticatedUser):
            return await self.app(scope, receive, send)  # 401 is the SDK's job
        chunks, more = [], True
        while more:
            msg = await receive()
            chunks.append(msg.get("body", b""))
            more = msg.get("more_body", False)
        body = b"".join(chunks)
        try:
            rpc = json.loads(body)
        except ValueError:
            rpc = {}
        needed = TOOL_SCOPES.get(rpc.get("params", {}).get("name")) if rpc.get("method") == "tools/call" else None
        if needed and needed not in user.scopes:
            www = f'Bearer error="insufficient_scope", scope="{needed}", resource_metadata="{METADATA}"'
            payload = json.dumps({"error": "insufficient_scope", "scope": needed}).encode()
            await send({"type": "http.response.start", "status": 403,
                        "headers": [(b"content-type", b"application/json"), (b"www-authenticate", www.encode())]})
            return await send({"type": "http.response.body", "body": payload})

        async def replay():
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay, send)


app = mcp.streamable_http_app()
for route in app.routes:  # insert the per-tool gate inside the SDK's auth middleware
    if isinstance(route, Route) and route.path == "/mcp":
        route.app = ToolScopeGate(route.app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
