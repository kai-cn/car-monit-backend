"""Throwaway: dump every diff of one endpoint from _sweep_raw.json, full paths."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

needle = sys.argv[1] if len(sys.argv) > 1 else "listByCarByTime"
results = json.loads(Path("_sweep_raw.json").read_text(encoding="utf-8"))

for record in results:
    if needle not in record["path"]:
        continue
    print("=" * 100)
    print(record["path"], "verdict=", record["verdict"], "java=", record["java_status"], "py=", record["py_status"])
    for diff in record.get("detail") or []:
        print("  %-10s %-46s" % (diff.get("kind"), diff.get("path")))
        print("        java=%r" % (diff.get("java"),))
        print("        py  =%r" % (diff.get("py"),))
