#!/usr/bin/env python3
"""
@description 打印云端基线在 TOKEN 步骤附近的完整日志，定位鉴权失败原因。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/show-token-failure.py <logfile>
@dependencies Python 3 标准库。
"""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace').splitlines()
idx = max((i for i, l in enumerate(lines) if 'TOKEN=$(python3' in l), default=0)
for l in lines[max(0, idx - 25):min(len(lines), idx + 35)]:
    print(l)
