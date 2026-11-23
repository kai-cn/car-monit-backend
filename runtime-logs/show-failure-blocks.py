#!/usr/bin/env python3
"""Show failure blocks from local retest logs.

@description 打印 BigScreen Bean、generator 与 api 启动失败的关键异常块。
@author Tencent Hunyuan Hy
@date 2026-11-23 07:38:02
@usage python3 runtime-logs/show-failure-blocks.py
@dependencies Python 3。
"""
from pathlib import Path

base = Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream')
for name, needle, count in [('app.log', "Error creating bean with name 'bigScreenExportController'", 80),
                            ('app.log', "请求地址'/tool/gen/1'", 50),
                            ('api.log', 'Application run failed', 120)]:
    p = base / name
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    idx = next((i for i, line in enumerate(lines) if needle in line), None)
    print('===', name, needle, 'line', (idx + 1) if idx is not None else None, '===')
    if idx is None:
        continue
    for line in lines[idx:idx + count]:
        if any(k in line for k in ['ERROR', 'Caused by', 'Cannot', 'NoSuch', 'Unsatisfied', 'missing', 'not found', 'Exception', 'bean', 'Bean', 'applicable', 'Illegal']):
            print(line[:300])
