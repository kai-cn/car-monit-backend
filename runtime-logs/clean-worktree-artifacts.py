#!/usr/bin/env python3
"""
@description 清理误建的异常目录和本地 token 缓存，避免它们被 git 跟踪。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/clean-worktree-artifacts.py
@dependencies Python 3 标准库。
"""
import os
import shutil
from pathlib import Path

REPO = Path(r'D:\work\IdeaProjects\car-monit-backend-new')
for p in REPO.iterdir():
    if p.is_dir() and p.name.startswith('D') and len(p.name) <= 3 and p.name not in {'docker', 'docs'}:
        shutil.rmtree(p, ignore_errors=True)
        os.write(1, b'REMOVED_DIR_ANOMALY\n')
token = REPO / 'runtime-logs/.gh_token_cache'
if token.exists():
    token.unlink()
    os.write(1, b'REMOVED_TOKEN_CACHE\n')
gi = REPO / '.gitignore'
text = gi.read_text(encoding='utf-8', errors='replace') if gi.exists() else ''
if '.gh_token_cache' not in text:
    gi.write_text(text.rstrip() + '\n\n# Local credential cache\n.gh_token_cache\n', encoding='utf-8')
    os.write(1, b'GITIGNORE_TOKEN_CACHE\n')
