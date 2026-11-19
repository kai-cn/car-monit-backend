#!/usr/bin/env python3
from pathlib import Path
p = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')
t = p.read_text(encoding='utf-8')
broken = '''        shell: bash
        run: |
        env:
          RUST_LOG: debug
          RUST_BACKTRACE: '1'
          set -uo pipefail
'''
fixed = '''        shell: bash
        env:
          RUST_LOG: debug
          RUST_BACKTRACE: '1'
        run: |
          set -uo pipefail
'''
assert broken in t
p.write_text(t.replace(broken, fixed, 1), encoding='utf-8')
print('fixed', fixed in p.read_text(encoding='utf-8'))
