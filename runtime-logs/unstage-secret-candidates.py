#!/usr/bin/env python3

"""
@description 历史脚本 unstage-secret-candidates.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python unstage-secret-candidates.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
import re

import subprocess

from pathlib import Path



ROOT = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3')

WHITELIST = {'runtime-logs/SESSION-HANDOFF.md', 'runtime-logs/OPS-COMMANDS.md'}

pat = re.compile(r'(?i)(password|passwd|secret|token|Bearer)\s*[:=]?\s*["\']?([A-Za-z0-9._!@#$%^&*+-]{8,})')

names = subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--name-only'],

                       capture_output=True, text=True, encoding='utf-8').stdout.splitlines()

remove = []

for name in names:

    if name in WHITELIST:

        continue

    p = ROOT / name

    if not p.is_file():

        continue

    text = p.read_text(encoding='utf-8', errors='ignore')

    if pat.search(text):

        remove.append(name)

for name in remove:

    subprocess.run(['git', '-C', str(ROOT), 'rm', '-q', '--cached', '--', name], check=False)

print('UNSTAGED', len(remove))

print('REMAINING', len(subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--name-only'],

      capture_output=True, text=True, encoding='utf-8').stdout.splitlines()))

