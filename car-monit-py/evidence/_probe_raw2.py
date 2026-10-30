"""Throwaway: show the raw body of one endpoint on Java and Python."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

path = sys.argv[1] if len(sys.argv) > 1 else "/monitor/server"
tokens = json.loads(Path(".sweep_tokens.json").read_text(encoding="utf-8"))

for name, base in (("java", "http://127.0.0.1:8090"), ("python", "http://127.0.0.1:9989")):
    response = httpx.get(
        base + path,
        headers={"Authorization": "Bearer " + tokens[name]},
        timeout=120,
    )
    print("=== %s %s" % (name, response.status_code))
    print(response.text[:1500])
    print()
