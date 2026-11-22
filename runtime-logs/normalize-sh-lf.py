#!/usr/bin/env python3
"""
@description 将指定 WSL shell 脚本转换为 LF 行尾，避免 Windows 下的 CRLF 导致 bash 语法错误。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/normalize-sh-lf.py <script1> [script2 ...]
@dependencies Python 3 标准库。
"""
import sys
from pathlib import Path

for name in sys.argv[1:]:
    p = Path(name)
    if not p.exists():
        print('MISSING', p)
        continue
    text = p.read_text(encoding='utf-8', errors='replace').replace('\r\n', '\n').replace('\r', '\n')
    p.write_bytes(text.encode('utf-8'))
    print('LF', p)
