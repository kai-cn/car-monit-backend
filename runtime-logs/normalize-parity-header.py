#!/usr/bin/env python3
"""
@description 规范化 parity_compare.py 文件头，保留单个标准 docstring，确保 from __future__ 合法。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/normalize-parity-header.py
@dependencies Python 3 标准库。
"""
from pathlib import Path

for repo in [Path(r'D:\work\IdeaProjects\car-monit-backend-new'), Path(r'D:\work\IdeaProjects\car-monit-api')]:
    p = repo / 'scripts/v3/ops/parity/parity_compare.py'
    t = p.read_text(encoding='utf-8', errors='replace')
    start = t.find('"""Compare two probe result JSONs')
    if start < 0:
        continue
    end = t.find('"""', start + 3)
    if end < 0:
        continue
    t = t[:start] + t[end + 3:]
    p.write_text(t, encoding='utf-8')
    print('FIXED', p)
