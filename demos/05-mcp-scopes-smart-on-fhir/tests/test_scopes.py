"""Four requests, two refusals. Prints the numbers the post cites."""

import socket
import threading
import time

import httpx
import pytest
import uvicorn

from server import app

BASE = "http://127.0.0.1:8000"
HDRS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


def call(tool: str, args: dict, token: str | None):
    hdrs = dict(HDRS)
    if token:
        hdrs["Authorization"] = f"Bearer {token}"
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}}
    return httpx.post(f"{BASE}/mcp", json=body, headers=hdrs, timeout=10)


@pytest.fixture(scope="session", autouse=True)
def live_server():
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", 8000), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield
    server.should_exit = True


def test_no_token_is_401_with_metadata_pointer():
    r = call("read_patient", {"patient_id": "p1"}, token=None)
    assert r.status_code == 401
    assert "resource_metadata=" in r.headers["www-authenticate"]


def test_reader_can_read_patient():
    r = call("read_patient", {"patient_id": "p1"}, token="tok-reader")
    assert r.status_code == 200
    assert "Patient" in r.text


def test_reader_gets_403_on_create_observation():
    r = call("create_observation", {"patient_id": "p1", "loinc": "8867-4", "value": 72}, token="tok-reader")
    assert r.status_code == 403
    www = r.headers["www-authenticate"]
    assert 'error="insufficient_scope"' in www
    assert 'scope="patient/Observation.c"' in www


def test_writer_can_create_observation():
    r = call("create_observation", {"patient_id": "p1", "loinc": "8867-4", "value": 72}, token="tok-writer")
    assert r.status_code == 200
    assert "Observation" in r.text


def test_metadata_is_served():
    r = httpx.get(f"{BASE}/.well-known/oauth-protected-resource/mcp", timeout=10)
    assert r.status_code == 200
    assert r.json()["resource"].rstrip("/") == f"{BASE}/mcp"


def test_print_the_numbers(capsys):
    statuses = [
        call("read_patient", {"patient_id": "p1"}, None).status_code,
        call("read_patient", {"patient_id": "p1"}, "tok-reader").status_code,
        call("create_observation", {"patient_id": "p1", "loinc": "8867-4", "value": 72}, "tok-reader").status_code,
        call("create_observation", {"patient_id": "p1", "loinc": "8867-4", "value": 72}, "tok-writer").status_code,
    ]
    refused = sum(1 for s in statuses if s in (401, 403))
    with capsys.disabled():
        print(f"\nstatuses={statuses} refused={refused}/4 (1x401 no token, 1x403 wrong scope)")
    assert statuses == [401, 200, 403, 200]
