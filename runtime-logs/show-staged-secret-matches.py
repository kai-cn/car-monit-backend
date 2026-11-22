#!/usr/bin/env python3

"""
@description 历史脚本 show-staged-secret-matches.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python show-staged-secret-matches.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
import re

import subprocess

from pathlib import Path



ROOT = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3')

names = subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--name-only'],

                       capture_output=True, text=True, encoding='utf-8').stdout.splitlines()

pat = re.compile(r'(?i)(password|passwd|secret|token|Bearer)\s*[:=]?\s*["\']?([A-Za-z0-9._!@#$%^&*+-]{8,})')



def mask(v):

    return v[:3] + '*' * max(0, min(8, len(v) - 3)) + f' (len={len(v)})'



for name in names:

    p = ROOT / name

    if not p.is_file():

        continue

    text = p.read_text(encoding='utf-8', errors='ignore')

    found = []

    for i, line in enumerate(text.splitlines(), 1):

        m = pat.search(line)

        if m:

            found.append(f'{i}: {m.group(1)}={mask(m.group(2))}')

    if found:

        print(name)

        for f in found[:3]:

            print('  ', f)

