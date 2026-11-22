#!/usr/bin/env python3
"""Prepare WSL master clones for local commit.

@description 清理误建目录、复制修复脚本到 WSL backend runtime-logs，并检查 Go selftest 的 import 使用情况。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:07:45
@usage python3 runtime-logs/prepare-wsl-master-commit.py
@dependencies WSL master clones。
"""
import shutil
from pathlib import Path

SRC = Path('/mnt/d/work/IdeaProjects/car-monit-backend-new/runtime-logs')
B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')

for repo in [B, A]:
    for p in repo.iterdir():
        if p.name.startswith('D:') and p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            print('REMOVED', p)

names = [
    'analyze-crosslang-code.py', 'analyze-endpoint-code.py', 'check-geometry-tables.sh',
    'finalize-wsl-fixes.py', 'normalize-wsl-eol2.py', 'patch-wsl-master-fixes.py',
    'patch-wsl-master-fixes2.py', 'patch-wsl-master-fixes3.py', 'patch-wsl-master-fixes4.py',
    'patch-wsl-master-fixes5.py', 'patch-wsl-master-fixes6.py', 'repair-wsl-selftest-and-schema.py',
    'summarize-non200.py', 'wsl-audit-fixes.sh', 'wsl-final-review.sh', 'wsl-fix-github-clone.sh',
    'wsl-master-status.sh', 'wsl-sync-master.sh', 'export-wsl-gh-token.py',
]
dst = B / 'runtime-logs'
dst.mkdir(parents=True, exist_ok=True)
for name in names:
    src = SRC / name
    if src.exists():
        shutil.copy2(src, dst / name)
        print('COPIED', name)

selftest = A / 'car-monit-api-go/internal/handler/selftest.go'
t = selftest.read_text(encoding='utf-8', errors='replace')
print('HTTP_USES', t.count('http.'))
print('SLOG_USES', t.count('slog.'))
print('IMPORT_SLOG', '"log/slog"' in t)
