#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Filter long logs down to relevant error/status lines.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import sys
from pathlib import Path
p = Path(sys.argv[1])
lines = p.read_text(errors='replace').splitlines()
out = [(i + 1, l) for i, l in enumerate(lines)
       if len(l) < 300 and ('error' in l.lower() or 'exception' in l.lower())]
for i, l in out[-int(sys.argv[2] if len(sys.argv) > 2 else 60):]:
    print(f'{i}: {l}')
