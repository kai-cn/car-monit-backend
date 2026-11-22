#!/usr/bin/env python3
"""Restore original line endings for modified WSL master files.

@description 按 git HEAD 中原始换行符恢复 WSL master 修改文件，减少整文件 diff 噪音。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python3 runtime-logs/normalize-wsl-eol.py
@dependencies git、WSL master clones。
"""
import subprocess
from pathlib import Path

REPOS = [Path('/home/dev/IdeaProjects/car-monit-backend'), Path('/home/dev/IdeaProjects/car-monit-api')]

for repo in REPOS:
    out = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], text=True)
    for line in out.splitlines():
        status = line[:2]
        path = line[3:]
        if '??' in status or not path:
            continue
        full = repo / path
        if not full.is_file():
            continue
        try:
            original = subprocess.check_output(['git', '-C', str(repo), 'show', 'HEAD:' + path])
            current = full.read_bytes()
        except Exception:
            continue
        original_crlf = original.count(b'\r\n')
        original_lf = original.count(b'\n')
        if original_crlf == 0 or original_crlf < original_lf * 0.5:
            continue
        normalized = current.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        if normalized != current:
            full.write_bytes(normalized)
            print('EOL', path)
