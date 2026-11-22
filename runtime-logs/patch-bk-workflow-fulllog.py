#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-bk-workflow-fulllog.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk-parity-diag.yml')
t = p.read_text(encoding='utf-8')
old = 'grep -E \'ERROR|Caused by|APPLICATION FAILED|Exception|Started .* in|Tomcat started\' "$f" | tail -40 || true'
new = 'tail -n 160 "$f" || true'
print('found', old in t)
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('patched', new in t)
