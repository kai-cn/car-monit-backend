#!/usr/bin/env python3
"""Classify final non-200 endpoints by evidence and source code."""
import json
from pathlib import Path
p=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/endpoint-code-analysis.json')
d=json.loads(p.read_text(encoding='utf-8'))
for x in d['endpoints']:
    if x['verdict']=='non_200':
        print(x['endpoint'],x['code'],x['body_prefix'][:500])
