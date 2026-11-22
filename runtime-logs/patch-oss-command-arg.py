#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-oss-command-arg.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk-parity-check.yml')
t = p.read_text(encoding='utf-8')
old = '--cmd "env OSS_ENABLE=false \\"$NATIVE\\" --server.port=19902"'
new = '--cmd "env OSS_ENABLE=false \\"$NATIVE\\" --server.port=19902 --oss.enable=false"'
assert old in t
p.write_text(t.replace(old, new, 1), encoding='utf-8')
import yaml
yaml.safe_load(p.read_text(encoding='utf-8'))
print('command arg added', '--oss.enable=false' in t)
