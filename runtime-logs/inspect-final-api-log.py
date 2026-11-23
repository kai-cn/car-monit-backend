#!/usr/bin/env python3
"""Inspect final api log for ES and fitting errors."""
from pathlib import Path
p=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/api.log')
lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
for i,l in enumerate(lines):
    if any(k in l for k in ['ES 查询异常','Connection refused','elasticsearch','elastic','9200','trail/list','unified/list']):
        print(i+1,l[:500])
