#!/usr/bin/env python3
"""Restore exact original line endings for modified WSL files.

@description 使用 git HEAD 中的原始字节换行风格恢复 WSL master 修改文件，避免整文件 diff。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python3 runtime-logs/normalize-wsl-eol2.py
@dependencies git、WSL master clones。
"""
import subprocess
from pathlib import Path

REPOS = [Path('/home/dev/IdeaProjects/car-monit-backend'), Path('/home/dev/IdeaProjects/car-monit-api')]

for repo in REPOS:
    out = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], text=True)
    for line in out.splitlines():
        if line.startswith('??'):
            continue
        path = line[3:].strip()
        if not path:
            continue
        full = repo / path
        if not full.is_file():
            continue
        try:
            original = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + path])
            current = full.read_bytes()
        except Exception:
            continue
        crlf = original.count(b'\r\n')
        lf = original.count(b'\n')
        target = b'\r\n' if crlf > lf / 2 else b'\n'
        normalized = current.replace(b'\r\n', b'\n').replace(b'\n', target)
        if normalized != current:
            full.write_bytes(normalized)
            print('EOL', path)
