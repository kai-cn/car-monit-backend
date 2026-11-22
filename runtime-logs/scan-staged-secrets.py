#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：scan-staged-secrets.py
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
