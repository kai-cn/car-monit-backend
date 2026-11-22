#!/usr/bin/env python3
"""
@description 修复生产级注释插入位置错误：将 from __future__ 前的模块 docstring 转为注释，恢复 Python 语法。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/fix-future-import-headers.py
@dependencies Python 3 标准库；只处理两仓库 harness 脚本。
"""
import ast
from pathlib import Path

TARGETS = []
for repo in [Path(r'D:\work\IdeaProjects\car-monit-backend-new'), Path(r'D:\work\IdeaProjects\car-monit-api')]:
    TARGETS.extend(repo.glob('scripts/v3/ops/**/*.py'))

for p in TARGETS:
    text = p.read_text(encoding='utf-8', errors='replace')
    try:
        ast.parse(text)
        continue
    except SyntaxError as e:
        if 'from __future__' not in str(e):
            continue
    lines = text.splitlines(keepends=True)
    idx = next(i for i, l in enumerate(lines) if 'from __future__' in l)
    block_start = None
    for i in range(idx - 1, -1, -1):
        if lines[i].lstrip().startswith('"""') or lines[i].lstrip().startswith("'''"):
            block_start = i
            break
    if block_start is None:
        continue
    delim = '"""' if '"""' in lines[block_start] else "'''"
    block_end = block_start
    if lines[block_start].count(delim) < 2:
        for i in range(block_start + 1, idx):
            if delim in lines[i]:
                block_end = i
                break
    comments = []
    for line in lines[block_start:block_end + 1]:
        s = line.strip().strip(delim).strip()
        comments.append(('# ' + s + '\n') if s else '#\n')
    p.write_text(''.join(lines[:block_start]) + ''.join(comments) + ''.join(lines[block_end + 1:]), encoding='utf-8')
    print('FIXED', p)
