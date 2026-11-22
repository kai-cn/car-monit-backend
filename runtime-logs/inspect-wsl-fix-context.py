#!/usr/bin/env python3
"""Inspect WSL master fix context before finalizing.

@description 检查 Go VehicleMonitor 字段、Rust token 配置与 schema 插入点，确保修复可编译可运行。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python3 runtime-logs/inspect-wsl-fix-context.py
@dependencies WSL master clones。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
A = Path('/home/dev/IdeaProjects/car-monit-api')
for label, p, needles in [
    ('backend-go-config', B / 'car-monit-go/internal/config/config.go', ['VehicleMonitor', 'BaseURL']),
    ('api-go-selftest', A / 'car-monit-api-go/internal/handler/selftest.go', ['import', 'slog']),
    ('api-rust-token', A / 'car-monit-api-rust/src/config.rs', ['token', 'secret', 'base64']),
    ('backend-rust-token', B / 'car-monit-rust/src/config.rs', ['token', 'secret', 'base64']),
]:
    print('===', label, '===')
    t = p.read_text(encoding='utf-8', errors='replace')
    lines = t.splitlines()
    hits = [i for i, line in enumerate(lines) if any(n.lower() in line.lower() for n in needles)]
    for i in hits[:12]:
        print(i + 1, lines[i].strip())
