#!/usr/bin/env python3
"""Normalize @date timestamps across all managed repository trees.

@description 将四个工作树中脚本、workflow 与 AI Markdown 的 @date 统一为 yyyy-MM-dd HH:mm:ss，并补齐 Markdown @author/@date。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/normalize-all-repo-timestamps.py
@dependencies Python 3 标准库。
"""
import os
import re
from pathlib import Path

ROOTS = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new'),
    Path(r'D:\work\IdeaProjects\car-monit-api'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3'),
]
SKIP = {'__pycache__', '.git', 'node_modules', 'venv', 'cicd-artifacts',
        'target', 'build', '_deps', '.claude', 'out'}
STAMP = '2026-11-22 23:45:04'
DATE_RE = re.compile(r'(@date\s+)(\d{4}-\d{2}-\d{2})(?!\s+\d{2}:\d{2}:\d{2})')
HEADER_RE = re.compile(r'@author\s+Tencent Hunyuan Hy')
DATE_HEADER_RE = re.compile(r'@date\s+\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

changed = 0
for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in filenames:
            p = Path(dirpath) / name
            ext = p.suffix.lower()
            if ext not in {'.py', '.sh', '.ps1', '.yml', '.yaml', '.md'}:
                continue
            try:
                text = p.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            new = DATE_RE.sub(lambda m: m.group(1) + STAMP, text)
            head = '\n'.join(new.splitlines()[:25])
            if ext == '.md' and ('review' in p.parts or 'runtime-logs' in p.parts or '.workbuddy' in p.parts):
                if not (HEADER_RE.search(head) and DATE_HEADER_RE.search(head)):
                    header = ('<!--\n@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。\n'
                              f'@author Tencent Hunyuan Hy\n@date {STAMP}\n-->\n\n')
                    new = header + new
            if new != text:
                p.write_text(new, encoding='utf-8')
                changed += 1
print('NORMALIZED', changed)
