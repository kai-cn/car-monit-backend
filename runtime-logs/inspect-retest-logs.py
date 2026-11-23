#!/usr/bin/env python3
"""Inspect current WSL retest logs for real root causes.

@description 提取 api 下游启动失败、backend Bean 创建失败与缺失表错误上下文。
@author Tencent Hunyuan Hy
@date 2026-11-23 07:38:02
@usage python3 runtime-logs/inspect-retest-logs.py
@dependencies Python 3。
"""
from pathlib import Path

base = Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream')
for name in ['api.log', 'app.log']:
    p = base / name
    print('===', name, p.stat().st_size if p.exists() else 'MISSING', '===')
    if not p.exists():
        continue
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    keys = ['ERROR', 'Exception', 'Caused by', 'APPLICATION FAILED', 'bigScreenExportService',
            'sys_upgrade_info', 'Tomcat started', 'Started ', 'Connection refused', 'Failed']
    hits = [i for i, line in enumerate(lines) if any(k in line for k in keys)]
    for i in hits[:30]:
        print(i + 1, lines[i][:260])
