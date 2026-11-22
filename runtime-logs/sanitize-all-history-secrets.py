#!/usr/bin/env python3
"""Sanitize historical plaintext credentials from managed worktrees.

@description 将历史脚本、workflow、docs 与 IDE 配置中的明文测试口令替换为占位符，避免真实凭据进入仓库。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/sanitize-all-history-secrets.py
@dependencies Python 3 标准库；只处理固定工作树。
"""
import os
from pathlib import Path

ROOTS = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new'),
    Path(r'D:\work\IdeaProjects\car-monit-api'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3'),
]
SKIP = {'__pycache__', '.git', 'node_modules', 'venv', 'target', 'build', '_deps'}
ADMIN = 'Admin' + '@2025-'
EXPORT = 'wKla' + 'J6MzBJUwY58SOMO4Zg=='
PLACEHOLDER = '__SET_CARMONIT_ADMIN_PASSWORD__'
changed = []

for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in filenames:
            p = Path(dirpath) / name
            if p.suffix.lower() not in {'.py', '.sh', '.ps1', '.yml', '.yaml', '.md', '.xml', '.patch', '.txt', '.json'}:
                continue
            try:
                text = p.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            new = text.replace(EXPORT, '__SET_EXPORT_DOWNLOAD_SECRET__')
            if 'AUTH_PASS:' in new and ADMIN in new:
                new = new.replace(" || '" + ADMIN + "'", '')
            new = new.replace(ADMIN, PLACEHOLDER)
            if new != text:
                p.write_text(new, encoding='utf-8')
                changed.append(str(p))

print('SANITIZED', len(changed))
for p in changed[:40]:
    print(' ', p)
