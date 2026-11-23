#!/usr/bin/env python3
"""Patch last confirmed code issues from body.code review.

@description 修复 batchGenCode 空参数空指针与 api PostgreSQL 时间戳减整数类型错误。
@author Tencent Hunyuan Hy
@date 2026-11-23 08:32:28
@usage python3 runtime-logs/patch-last-code-issues.py
@dependencies WSL backend/api master。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')
CTRL = B / 'ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java'


def replace(path, old, new):
    """Replace exact source text."""
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    t = raw.decode('utf-8', errors='replace')
    if old not in t:
        print('NOT_FOUND', path, old[:80])
        return
    t = t.replace(old, new)
    data = (t.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else t).encode('utf-8')
    path.write_bytes(data)
    print('OK', path)


# Exact current batchGenCode block may still be unguarded due CRLF mismatch.
t = CTRL.read_text(encoding='utf-8', errors='replace')
start = t.find('public void batchGenCode(HttpServletResponse response, String tables)')
if start >= 0:
    brace = t.find('{', start)
    end = t.find('\n    }', brace) + len('\n    }')
    old_block = t[start:end]
    new_block = '''public void batchGenCode(HttpServletResponse response, String tables) throws IOException
    {
        String[] tableNames = StringUtils.isEmpty(tables) ? new String[0] : Convert.toStrArray(tables);
        if (tableNames.length == 0) {
            genCode(response, new byte[0]);
            return;
        }
        byte[] data = genTableService.downloadCode(tableNames);
        genCode(response, data == null ? new byte[0] : data);
    }'''
    replace(CTRL, old_block, new_block)

# Locate PostgreSQL timestamp minus integer expressions in api mappers.
for p in A.rglob('*.xml'):
    try:
        t = p.read_text(encoding='utf-8', errors='replace')
    except Exception:
        continue
    if 'interval' in t.lower() or "'- ' ||" in t or " - #{days}" in t:
        print('PG_TIME_CANDIDATE', p)
