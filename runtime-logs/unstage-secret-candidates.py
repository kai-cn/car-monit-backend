#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：unstage-secret-candidates.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
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
