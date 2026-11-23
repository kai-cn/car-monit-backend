#!/usr/bin/env python3
"""Show PostgreSQL SQL error context from api log."""
from pathlib import Path
p=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/api.log')
lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
for i,l in enumerate(lines):
    if 'operator does not exist: timestamp with time zone - integer' in l:
        for j in range(max(0,i-20),min(len(lines),i+25)):
            print(j+1,lines[j][:500])
        break
