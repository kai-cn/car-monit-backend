#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-logdir.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\crosslang-fix.yml')
t = p.read_text(encoding='utf-8')
needle = '          docker run -d --name rd -p 6379:6379 redis:7-alpine\n'
add = needle + '          sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath\n          sudo chown -R "$(id -u):$(id -g)" /home/ruoyi\n'
print('sites', t.count(needle))
t = t.replace(needle, add)
p.write_text(t, encoding='utf-8')
print('patched', t.count('sudo mkdir -p /home/ruoyi/logs'))
