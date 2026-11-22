#!/usr/bin/env python3
"""
@description 清理 runtime-logs 中的明文管理员口令与 JWT token 文件，统一改为环境变量占位。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/sanitize-credentials.py
@dependencies Python 3 标准库；只处理本地 backend master 工作树。
"""
import re
from pathlib import Path

ROOTS = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs'),
    Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3\runtime-logs'),
]
# 用户提供的测试口令只作为待替换模式，不写入任何输出。
PATTERNS = [re.compile('Admin' + '@20' + r'\d\d-')]
replace_count = 0
delete_count = 0

for root in ROOTS:
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        if 'token' in p.name.lower() and p.suffix.lower() in {'.txt', '.json'}:
            p.unlink(missing_ok=True)
            delete_count += 1
            continue
        if p.suffix.lower() not in {'.py', '.ps1', '.sh', '.yml', '.yaml', '.md', '.txt', '.json'}:
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        new = text
        for pat in PATTERNS:
            new = pat.sub('${CARMONIT_ADMIN_PASSWORD}', new)
        if new != text:
            p.write_text(new, encoding='utf-8')
            replace_count += 1

print('REPLACED', replace_count)
print('DELETED_TOKEN_FILES', delete_count)
