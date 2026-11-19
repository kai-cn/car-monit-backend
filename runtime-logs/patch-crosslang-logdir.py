#!/usr/bin/env python3
from pathlib import Path
p = Path(r'D:\work\runtime-logs\crosslang-fix.yml')
t = p.read_text(encoding='utf-8')
needle = '          docker run -d --name rd -p 6379:6379 redis:7-alpine\n'
add = needle + '          sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath\n          sudo chown -R "$(id -u):$(id -g)" /home/ruoyi\n'
print('sites', t.count(needle))
t = t.replace(needle, add)
p.write_text(t, encoding='utf-8')
print('patched', t.count('sudo mkdir -p /home/ruoyi/logs'))
