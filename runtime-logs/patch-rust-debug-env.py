#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-rust-debug-env.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')
t = p.read_text(encoding='utf-8')
needle = '''      - name: Probe Rust
        if: steps.gate.outputs.run == 'yes' && matrix.lang == 'rust'
        shell: bash
        run: |
'''
add = needle + '''        env:
          RUST_LOG: debug
          RUST_BACKTRACE: '1'
'''
assert needle in t
p.write_text(t.replace(needle, add, 1), encoding='utf-8')
print('patched', 'RUST_LOG: debug' in t)
