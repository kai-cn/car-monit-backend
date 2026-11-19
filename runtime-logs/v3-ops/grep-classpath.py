#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Extract structured matches (paths/options) from long command lines or logs.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import sys, re
from pathlib import Path
p = Path(sys.argv[1])
pat = re.compile(sys.argv[2])
for line in p.read_text(errors='replace').splitlines():
    for m in pat.finditer(line):
        print(m.group(0))
