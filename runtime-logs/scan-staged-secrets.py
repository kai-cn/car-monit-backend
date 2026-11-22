#!/usr/bin/env python3

"""
@description 历史脚本 scan-staged-secrets.py：扫描远端或本地状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python scan-staged-secrets.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
import re

import subprocess

from pathlib import Path



ROOT = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3')

names = subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--name-only'],

                       capture_output=True, text=True, encoding='utf-8').stdout.splitlines()

patterns = [

    re.compile(r'ghp_[A-Za-z0-9]{20,}'),

    re.compile(r'github_pat_[A-Za-z0-9_]{20,}'),

    re.compile(r'Bearer\s+[A-Za-z0-9._-]{20,}'),

    re.compile(r'(?i)(password|passwd|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9._!@#$%^&*+-]{12,}'),

]

hits = []

for name in names:

    p = ROOT / name

    if not p.is_file():

        continue

    try:

        text = p.read_text(encoding='utf-8', errors='ignore')

    except Exception:

        continue

    if any(pat.search(text) for pat in patterns):

        hits.append(name)

print('STAGED_FILES', len(names))

print('POTENTIAL_SECRET_FILES', len(hits))

for h in hits[:40]:

    print(h)

