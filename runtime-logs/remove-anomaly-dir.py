#!/usr/bin/env python3
"""
@description 清理误建在仓库根目录的异常目录，避免 git status 噪音。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/remove-anomaly-dir.py
@dependencies Python 3 标准库。
"""
import shutil
from pathlib import Path

repo = Path(r'D:\work\IdeaProjects\car-monit-backend-new')
for p in repo.iterdir():
    if p.is_dir() and p.name.startswith('D') and len(p.name) <= 3 and p.name not in {'docker', 'docs'}:
        shutil.rmtree(p, ignore_errors=True)
        print('REMOVED_ANOMALY')
