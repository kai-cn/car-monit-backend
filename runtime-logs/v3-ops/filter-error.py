#!/usr/bin/env python3

"""
@description 历史脚本 filter-error.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python filter-error.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Filter long logs down to relevant error/status lines.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

import sys

from pathlib import Path

p = Path(sys.argv[1])

lines = p.read_text(errors='replace').splitlines()

out = [(i + 1, l) for i, l in enumerate(lines)

       if len(l) < 300 and ('error' in l.lower() or 'exception' in l.lower())]

for i, l in out[-int(sys.argv[2] if len(sys.argv) > 2 else 60):]:

    print(f'{i}: {l}')

