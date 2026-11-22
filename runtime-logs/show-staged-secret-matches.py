#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：show-staged-secret-matches.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
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
