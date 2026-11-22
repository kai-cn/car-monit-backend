#!/usr/bin/env python3
"""Finalize WSL master source fixes.

@description 修复 GenController 路径变量，确认 api Go selftest 依赖，检查所有修改文件的敏感信息。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python runtime-logs/patch-wsl-master-fixes5.py
@dependencies WSL master clones。
"""
import re
from pathlib import Path

WSL = Path('/home/dev/IdeaProjects')
BACKEND = WSL / 'car-monit-backend'
API = WSL / 'car-monit-api'
SECRET = re.compile('wKla' + 'J6|Admin' + '@20' + r'\d\d-')


def replace(path, old, new):
    if not path.exists():
        print('MISSING', path)
        return
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    text = raw.decode('utf-8', errors='replace')
    if old not in text:
        print('NOT_FOUND', path)
        return
    new_text = text.replace(old, new)
    if crlf:
        data = new_text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
    else:
        data = new_text.encode('utf-8')
    path.write_bytes(data)
    print('OK', path)


replace(BACKEND / 'ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java',
        'public TableDataInfo columnList(Long tableId)',
        'public TableDataInfo columnList(@PathVariable("talbleId") Long tableId)')

# api Go selftest must import slog after the no-op change.
p = API / 'car-monit-api-go/internal/handler/selftest.go'
t = p.read_text(encoding='utf-8', errors='replace')
if 'slog.' in t and '"log/slog"' not in t:
    if t.startswith('package handler\n'):
        t = t.replace('package handler\n', 'package handler\n\nimport "log/slog"\n', 1)
        p.write_text(t, encoding='utf-8')
        print('IMPORTED_SLOG', p)

for repo in [BACKEND, API]:
    hits = []
    for p in repo.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.py', '.go', '.rs', '.cpp', '.hpp', '.java', '.xml', '.yaml', '.yml', '.md'}:
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        if SECRET.search(text):
            hits.append(str(p))
    print('SECRET_HITS', repo.name, len(hits))
    for h in hits[:20]:
        print(' ', h)
