"""CLI da Skill: lê o texto do stdin e aplica uma das 4 ferramentas."""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
import ferramentas  # noqa: E402

if __name__ == "__main__":
    acao, texto = sys.argv[1], sys.stdin.read()
    print(json.dumps(getattr(ferramentas, acao)(texto), ensure_ascii=False))
