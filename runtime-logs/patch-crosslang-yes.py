#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-yes.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Quote YAML 'yes' output comparisons in workflow expressions.

Idea:
- YAML treats bare yes as boolean in some contexts; GitHub expressions expect
  a string literal for step outputs.
- Replace `steps.gate.outputs.run == yes` with `== 'yes'` everywhere.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),
]
for p in FILES:
    t = p.read_text(encoding='utf-8').replace("steps.gate.outputs.run == yes", "steps.gate.outputs.run == 'yes'")
    p.write_text(t, encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
