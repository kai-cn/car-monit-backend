#!/usr/bin/env python3
"""
@description 历史脚本 fix-setup-python-placement.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python fix-setup-python-placement.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\crosslang-fix.yml')
t = p.read_text(encoding='utf-8')
block = """      - name: Setup Python 3.12
        if: steps.gate.outputs.run == 'yes' && matrix.lang == 'python'
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
"""
# Remove every existing copy, then place one only in the candidates job.
t = t.replace(block, '')
cand = t.index('  candidates:\n')
marker = '      - name: Start datastores + seed\n'
pos = t.index(marker, cand)
t = t[:pos] + block + t[pos:]
p.write_text(t, encoding='utf-8')
lines = t.split('\n')
si = next(i for i, l in enumerate(lines) if 'Setup Python 3.12' in l)
gi = next(i for i, l in enumerate(lines) if '- id: gate' in l)
print('setup line', si + 1, 'gate line', gi + 1, 'correct', si > gi)
