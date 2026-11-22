#!/usr/bin/env python3

"""
@description 历史脚本 grep-classpath.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python grep-classpath.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Extract structured matches (paths/options) from long command lines or logs.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

import sys, re

from pathlib import Path

p = Path(sys.argv[1])

pat = re.compile(sys.argv[2])

for line in p.read_text(errors='replace').splitlines():

    for m in pat.finditer(line):

        print(m.group(0))

