#!/usr/bin/env python3
"""Inspect BigScreen bean failure and generator null pointers.

@description 从日志与源码定位 BigScreenExportService 注入失败、GenController 空指针的业务根因。
@author Tencent Hunyuan Hy
@date 2026-11-23 07:38:02
@usage python3 runtime-logs/inspect-bigscreen-and-gen.py
@dependencies WSL master 与本机日志。
"""
from pathlib import Path

log = Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/app.log')
lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
for needle in ["Error creating bean with name 'bigScreenExportController'", "请求地址'/tool/gen/1'", "请求地址'/tool/gen/preview/1'"]:
    idx = next((i for i, line in enumerate(lines) if needle in line), None)
    print('===', needle, '===', idx + 1 if idx is not None else None)
    if idx is None:
        continue
    for i in range(idx, min(idx + 90, len(lines))):
        line = lines[i]
        if any(k in line for k in ['Caused by', 'NoSuchBean', 'No qualifying', 'Unsatisfied', 'NullPointerException', 'GenController', 'BigScreen', 'field ', 'parameter ', 'constructor']):
            print(i + 1, line[:400])

B = Path('/home/dev/IdeaProjects/car-monit-backend')
for rel in ['ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/GenController.java',
            'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/bigscreen/BigScreenExportController.java']:
    p = B / rel
    print('=== FILE', rel, '===')
    if p.exists():
        for i, line in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
            if any(k in line for k in ['@GetMapping', 'public ', '@Autowired', 'private ', 'BigScreenExportService']):
                print(i, line.strip()[:220])
