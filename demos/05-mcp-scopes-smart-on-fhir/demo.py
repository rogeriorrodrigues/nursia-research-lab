"""Visual run of the four requests. Same server, same tokens, same numbers as tests/.

A nursing student talks to an AI tutor. The tutor is an MCP client with a
read-only token. It may read the chart. It must never write to it, whatever the
prompt says. The refusal has to come from the server, not from the prompt.
"""

import json
import logging
import socket
import sys
import threading
import time
import warnings

warnings.filterwarnings("ignore")  # pydantic-settings forward-reference notice, not ours
logging.disable(logging.INFO)  # httpx and the SDK log every request; the table below is the story

import httpx
import uvicorn

from server import TOKENS, TOOL_SCOPES, app

BASE = "http://127.0.0.1:8000"
HDRS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
G, R, Y, D, B, X = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"

CALLS = [
    ("no token", None, "read_patient", {"patient_id": "p1"}),
    ("tutor (reader)", "tok-reader", "read_patient", {"patient_id": "p1"}),
    ("tutor (reader)", "tok-reader", "create_observation", {"patient_id": "p1", "loinc": "8867-4", "value": 72}),
    ("pipeline (writer)", "tok-writer", "create_observation", {"patient_id": "p1", "loinc": "8867-4", "value": 72}),
]


def call(tool, args, token):
    hdrs = dict(HDRS)
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}}
    return httpx.post(f"{BASE}/mcp", json=body, headers=hdrs, timeout=10)


def summary(r):
    if r.status_code != 200:
        www = r.headers.get("www-authenticate", "")
        www = www.split(", resource_metadata=")[0]  # keep the line short; the pointer is in tests/
        return "  " + D + "WWW-Authenticate: " + X + www.replace('scope=', Y + 'scope=' + X)
    res = json.loads(r.json()["result"]["content"][0]["text"])
    if res["resourceType"] == "Patient":
        n = res["name"][0]
        return f'  Patient/{res["id"]} "{n["given"][0]} {n["family"]}"'
    code = res["code"]["coding"][0]["code"]
    return f'  Observation LOINC {code} = {res["valueQuantity"]["value"]} for {res["subject"]["reference"]}'


def run(pause=0.0):
    print(f"\n{B}MCP scopes per tool, mapped to SMART on FHIR{X}   {D}NursIA Research Lab, demo 05{X}")
    print(f"{D}server {BASE}/mcp, data 100% synthetic{X}\n")
    print(f"{B}Tokens{X} (static strings, no login)")
    for t, at in TOKENS.items():
        print(f"  {t:<11} {at.client_id:<17} {' '.join(at.scopes)}")
    print(f"\n{B}Scope required per tool{X} (TOOL_SCOPES in server.py)")
    for tool, scope in TOOL_SCOPES.items():
        print(f"  {tool:<19} {scope}")
    print(f"\n {B}#  caller             tool                 HTTP{X}")
    statuses = []
    for i, (who, token, tool, args) in enumerate(CALLS, 1):
        time.sleep(pause)
        r = call(tool, args, token)
        statuses.append(r.status_code)
        color = G if r.status_code == 200 else R
        print(f" {i}  {who:<18} {tool:<20} {color}{r.status_code} {r.reason_phrase}{X}")
        print(" " * 43 + summary(r))
    refused = sum(1 for s in statuses if s in (401, 403))
    time.sleep(pause)
    print(f"\n{B}statuses={statuses} refused={refused}/4{X}")
    print("The tutor read the chart (200) and could not write to it (403).")
    print("The refusal is the server's, not the prompt's. Request 3 is the per-tool gate the SDK does not ship.\n")
    return statuses


if __name__ == "__main__":
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", 8000), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    ok = run(pause=0.8) == [401, 200, 403, 200]
    server.should_exit = True
    sys.exit(0 if ok else 1)
