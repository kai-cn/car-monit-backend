#!/usr/bin/env python3
"""
@description 历史脚本 insert-setup-python.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python insert-setup-python.py [args]；具体参数以脚本 argparse 或源码说明为准。
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
marker = '      - name: Start datastores + seed\n'
print('marker count', t.count(marker), 'block already', block in t)
if marker in t and block not in t:
    t = t.replace(marker, block + marker, 1)
p.write_text(t, encoding='utf-8')
print('inserted', block in t, 'after gate', t.index(block) > t.index('- id: gate'))
