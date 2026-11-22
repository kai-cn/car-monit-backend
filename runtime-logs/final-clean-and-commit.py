#!/usr/bin/env python3
"""
@description 清理最后的明文模式与 NUL 误建文件，检查最终文档结论，并输出待提交清单。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/final-clean-and-commit.py
@dependencies Python 3 标准库。
"""
import re
from pathlib import Path

BK = Path(r'D:\work\IdeaProjects\car-monit-backend-new')
V3 = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3')
API = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3')

p = BK / 'runtime-logs/fix-stale-generators.py'
t = p.read_text(encoding='utf-8')
t = t.replace("'Admin' + '@20' + r'\\d\\d-'", "'ADMIN' + '_PASSWORD_PATTERN'")
p.write_text(t, encoding='utf-8')

for repo in [V3, API]:
    nul = repo / 'NUL'
    if nul.exists():
        nul.unlink()
        print('REMOVED', nul)

for p in [V3 / 'docs/v3/review/13-final-junit-crosslang-20261122.md',
          API / 'docs/v3/review/13-final-junit-crosslang-20261122.md']:
    if p.exists():
        t = p.read_text(encoding='utf-8')
        t = t.replace('全部 job success', 'baseline success；严格对拍候选 failure')
        p.write_text(t, encoding='utf-8')
        print('FIXED', p)

print('CLEANED')
