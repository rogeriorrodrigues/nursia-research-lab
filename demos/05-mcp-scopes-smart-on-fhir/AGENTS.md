# AGENTS.md

Demo 05 of nursia-research-lab: per-tool scope refusal in an MCP server,
mapped to SMART on FHIR v2 scopes.

Build and test:
- pip install -r requirements.txt
- python3 -m pytest tests -q -s   (prints statuses=[401, 200, 403, 200])
- python3 demo.py                 (same 4 requests, narrated, for screenshots and video)
- python3 server.py               (Streamable HTTP on 127.0.0.1:8000/mcp)

Rules for anyone (human or agent) editing this folder:
- All data is synthetic by construction. Never add real patient data,
  real identifiers or real tokens. Tokens here are fake strings.
- Do not log request bodies or tokens. The gate reads the body only to
  find the tool name.
- Keep server.py under 150 lines. One idea per demo.
- Versions are pinned in requirements.txt. Bumping mcp means re-running
  the tests and updating the numbers in README.md.
