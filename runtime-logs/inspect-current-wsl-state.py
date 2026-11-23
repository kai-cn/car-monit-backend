#!/usr/bin/env python3
"""Inspect current WSL master state and recent evidence.

@description 检查 WSL backend/api master 的 HEAD、远端、未提交文件与 runtime-logs 近期证据。
@author Tencent Hunyuan Hy
@date 2026-11-23 07:38:02
@usage python3 runtime-logs/inspect-current-wsl-state.py
@dependencies WSL master clones。
"""
import subprocess
from pathlib import Path

REPOS = [Path('/home/dev/IdeaProjects/car-monit-backend'),
         Path('/home/dev/IdeaProjects/car-monit-api')]

for repo in REPOS:
    print('===', repo.name, '===')
    print(subprocess.check_output(['git', '-C', str(repo), 'log', '-4', '--oneline'], text=True))
    print('REMOTE', subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'origin/master'], text=True).strip())
    out = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], text=True)
    print('STATUS', len(out.splitlines()))
    for line in out.splitlines()[:40]:
        print(line)

for repo in REPOS:
    logs = repo / 'runtime-logs'
    if not logs.exists():
        continue
    print('=== RECENT', repo.name, '===')
    files = sorted([p for p in logs.rglob('*') if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[:35]:
        print(p.relative_to(logs), p.stat().st_size)
