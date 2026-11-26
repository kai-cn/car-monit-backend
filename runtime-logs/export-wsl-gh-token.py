#!/usr/bin/env python3
"""
@description 从本机 GitHub 缓存读取 token 并安全写入 WSL 用户主目录临时文件，仅供 clone 使用。
@author Tencent Hunyuan Hy
@date 2026-11-23 00:50:46
@usage python runtime-logs/export-wsl-gh-token.py
@dependencies 本机 D:\work\runtime-logs\gh_cred.py 与 .gh_token_cache；wsl.exe。
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

token = get_token()
if not token:
    raise SystemExit('NO_GITHUB_TOKEN')
tmp = Path(r'D:\work\runtime-logs\.gh_token_wsl_tmp')
tmp.write_text(token, encoding='utf-8')
try:
    subprocess.run(['wsl', 'bash', '-lc', 'cp /mnt/d/work/runtime-logs/.gh_token_wsl_tmp /home/dev/.gh_token_wsl && chmod 600 /home/dev/.gh_token_wsl'], check=True)
finally:
    tmp.unlink(missing_ok=True)
print('EXPORTED')
