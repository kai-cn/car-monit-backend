#!/usr/bin/env python3
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
