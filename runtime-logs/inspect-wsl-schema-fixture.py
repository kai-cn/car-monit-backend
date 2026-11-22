#!/usr/bin/env python3
"""Inspect WSL schema fixture inserted for sys_upgrade_info.

@description 打印 WSL backend master schema 中 sys_upgrade_info 片段，便于修正字段。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python3 runtime-logs/inspect-wsl-schema-fixture.py
@dependencies WSL backend master。
"""
from pathlib import Path

p = Path('/home/dev/IdeaProjects/car-monit-backend/scripts/v3/ops/parity/sql/schema_carmonitdb.sql')
t = p.read_text(encoding='utf-8', errors='replace')
idx = t.find('sys_upgrade_info')
print('INDEX', idx)
print(t[max(0, idx - 200):idx + 900])
