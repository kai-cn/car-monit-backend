#!/usr/bin/env python3
"""
@description 修复批量注释后 workflow 反斜杠续行与下一行之间被插入空行的问题。
@author AI Assistant
@date 2026-11-23
@usage python3 runtime-logs/repair-continuation-after-annotation.py
@dependencies WSL /home/dev/IdeaProjects 下的 backend/api master clone；不访问网络。
"""
from pathlib import Path

ROOTS = [Path('/home/dev/IdeaProjects/car-monit-backend'), Path('/home/dev/IdeaProjects/car-monit-api')]
changed = []

for repo in ROOTS:
    for p in sorted((repo / '.github/workflows').glob('*.yml')):
        raw = p.read_text(encoding='utf-8', errors='replace')
        lines = raw.splitlines(keepends=True)
        out = []
        fixed = False
        for line in lines:
            if out and out[-1].rstrip('\r\n').rstrip().endswith('\\') and not line.strip():
                fixed = True
                continue
            out.append(line)
        if fixed:
            p.write_text(''.join(out), encoding='utf-8')
            changed.append(str(p))
            print('FIXED', p)
print('TOTAL', len(changed))
