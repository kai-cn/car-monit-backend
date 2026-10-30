"""Throwaway: detailed clustering of the sweep diffs (types included)."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

results = json.loads(Path("_sweep_raw.json").read_text(encoding="utf-8"))

groups: dict = defaultdict(lambda: {"count": 0, "endpoints": set(), "examples": []})

for record in results:
    for diff in record.get("detail") or []:
        if not isinstance(diff, dict) or "path" not in diff:
            continue
        path = re.sub(r"\[\d+\]", "[]", diff["path"])
        field = path.split(".")[-1]
        key = (diff["kind"], field)
        group = groups[key]
        group["count"] += 1
        group["endpoints"].add(record["path"])
        if len(group["examples"]) < 3:
            group["examples"].append(
                (
                    record["path"],
                    repr(diff.get("java"))[:90],
                    repr(diff.get("py"))[:90],
                )
            )

print("=== groups (kind, field) ===")
for (kind, field), group in sorted(groups.items(), key=lambda item: -item[1]["count"]):
    print("\n%-10s %-26s count=%-4d endpoints=%d" % (kind, field, group["count"], len(group["endpoints"])))
    print("            eps: %s" % ", ".join(sorted(group["endpoints"])[:6]))
    for endpoint, java, py in group["examples"]:
        print("            %-46s java=%s" % (endpoint, java))
        print("            %-46s py  =%s" % ("", py))

print("\n\n=== endpoints whose code differs ===")
for record in results:
    if record["verdict"] in {"CODE", "STATUS", "SHAPE-DIFF", "CONN"}:
        print("%-12s %-46s java=%s py=%s" % (record["verdict"], record["path"], record["java_status"], record["py_status"]))
        for diff in record.get("detail") or []:
            print("             ", json.dumps(diff, ensure_ascii=False)[:300])
